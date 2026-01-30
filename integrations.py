import os
import re
import time
import json
import logging
import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Tắt log rác của thư viện Google
logging.getLogger('google.generativeai').setLevel(logging.ERROR)

class AIEngine:
    def __init__(self, api_key):
        self.is_ready = False
        if not api_key: return

        genai.configure(api_key=api_key.strip())
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            self.generation_config = genai.types.GenerationConfig(temperature=0.25, max_output_tokens=8192)
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',  # Cập nhật model mới nhất
                safety_settings=safety_settings,
                generation_config=self.generation_config
            )
            self.is_ready = True
            print("✅ AI Engine: Ready (Gemini 2.5 Flash)")
        except Exception as e:
            print(f"❌ AI Init Error: {e}")
            self.is_ready = False

    def _force_structure(self, ai_text, original_tex):
        ai_text = ai_text.replace("\\begin{question}", "").replace("\\end{question}", "")
        if "\\begin{ex}" not in ai_text: ai_text = f"\\begin{{ex}}\n{ai_text.strip()}\n\\end{{ex}}"
        if "\\begin{ex}" in ai_text and "\\end{ex}" not in ai_text: ai_text = ai_text.strip() + "\n\\end{ex}"
        if "\\choice" not in ai_text and "\\shortans" not in ai_text and "\\item" in ai_text: return original_tex
        return ai_text

    def generate_safe(self, tex):
        """
        Tạo một câu hỏi mới tương tự bằng Gemini API, với cơ chế retry khi gặp quota.
        """
        if not self.is_ready:
            print("❌ AI Engine chưa sẵn sàng, trả về câu gốc")
            return tex, "A"

        prompt = f"""
    Bạn là giáo viên Toán THPT chuyên nghiệp.

    Nhiệm vụ: Tạo 1 câu hỏi TƯƠNG TỰ (cùng dạng toán, cùng mức độ khó) với câu mẫu sau.
    Thay đổi số liệu, ngữ cảnh một cách hợp lý.

    YÊU CẦU NGHIÊM NGẶT VỀ OUTPUT:
    1. Chỉ trả về code LaTeX thuần túy, bắt đầu bằng \\begin{{ex}} và kết thúc bằng \\end{{ex}}
    2. Giữ nguyên cấu trúc câu hỏi:
    - Trắc nghiệm 4 lựa chọn: dùng \\choice{{A}}{{B}}{{C}}{{D}}
    - Đúng/Sai: dùng \\choiceTF{{A}}{{B}}{{C}}{{D}}
    - Trả lời ngắn: dùng \\shortans{{...}}
    3. Luôn có phần lời giải đầy đủ trong \\loigiai{{...}}
    4. Cuối phần lời giải, thêm dòng comment đánh dấu đáp án đúng:
    % [KEY: X]    (X là A, B, C hoặc D)

    CÂU HỎI MẪU (để tham khảo):
    {tex}

    Bắt đầu output ngay từ \\begin{{ex}}, KHÔNG thêm bất kỳ lời giải thích hay text nào ngoài LaTeX.
        """.strip()

        max_retries = 5
        base_wait_seconds = 10

        for attempt in range(max_retries):
            try:
                print(f"📡 Gọi Gemini API (thử lần {attempt + 1}/{max_retries})...")

                res = self.model.generate_content(prompt)

                if not res.candidates:
                    print("⚠️ Không nhận được candidates từ API")
                    return tex, "A"

                if hasattr(res.candidates[0], 'finish_reason') and res.candidates[0].finish_reason == 3:
                    print("⚠️ Bị chặn bởi bộ lọc an toàn (finish_reason=3)")
                    return tex, "A"

                txt = res.text.strip()
                txt = txt.replace("```latex", "").replace("```tex", "").replace("```", "").strip()

                key = "A"
                key_match = re.search(r"\[KEY:\s*([A-D])\s*\]", txt, re.IGNORECASE)
                if key_match:
                    key = key_match.group(1).strip().upper()
                    txt = txt.replace(key_match.group(0), "").strip()

                structured_text = self._force_structure(txt, tex)

                print(f"✅ Thành công! Đáp án đúng: {key}")
                return structured_text, key

            except Exception as e:
                error_str = str(e).lower()

                if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                    wait_time = base_wait_seconds * (2 ** attempt)
                    print(f"⚠️ Quota exceeded (429) → chờ {wait_time} giây (lần {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Lỗi khác khi gọi API: {str(e)}")
                    return tex, "A"

        print(f"❌ Đã thử {max_retries} lần nhưng thất bại → trả về câu hỏi gốc")
        return tex, "A"

class GoogleManagerFull:
    # Scope đầy đủ cho: Classroom, Drive và Google Forms
    SCOPES = [
        'https://www.googleapis.com/auth/classroom.courses.readonly',
        'https://www.googleapis.com/auth/classroom.rosters.readonly',
        'https://www.googleapis.com/auth/classroom.coursework.students',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/forms.body'
    ]

    def __init__(self):
        self.creds = None
        self.service_class = None
        self.service_drive = None
        self.service_forms = None
        self.token_path = os.path.join(os.path.expanduser("~"), ".bankai_data", "token.json")
        self.cred_path = "credentials.json"

    def authenticate(self):
        """Xác thực OAuth2 (Có cơ chế tự động fix lỗi Token/Scope)"""
        try:
            if os.path.exists(self.token_path):
                self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                    except Exception:
                        print("Token hết hạn hoặc sai Scope -> Xóa để cấp mới.")
                        if os.path.exists(self.token_path): os.remove(self.token_path)
                        self.creds = None

                if not self.creds:
                    if not os.path.exists(self.cred_path):
                        raise FileNotFoundError("Chưa có file credentials.json! Hãy tải từ Google Cloud Console.")

                    flow = InstalledAppFlow.from_client_secrets_file(self.cred_path, self.SCOPES)
                    self.creds = flow.run_local_server(port=0, open_browser=True)

                parent_dir = os.path.dirname(self.token_path)
                if not os.path.exists(parent_dir): os.makedirs(parent_dir)
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())

            self.service_class = build('classroom', 'v1', credentials=self.creds)
            self.service_drive = build('drive', 'v3', credentials=self.creds)
            self.service_forms = build('forms', 'v1', credentials=self.creds)

        except Exception as e:
            if "invalid_scope" in str(e):
                if os.path.exists(self.token_path): os.remove(self.token_path)
                raise Exception("Lỗi Quyền (Scope). Đã xóa token cũ. Vui lòng CHẠY LẠI phần mềm và đăng nhập lại!")
            raise e

    def get_students(self, course_id):
        """Lấy danh sách học sinh trong lớp"""
        students = []
        try:
            page_token = None
            while True:
                response = self.service_class.courses().students().list(
                    courseId=course_id,
                    pageToken=page_token,
                    pageSize=100
                ).execute()

                for s in response.get('students', []):
                    profile = s.get('profile', {})
                    students.append({
                        'name': profile.get('name', {}).get('fullName', 'Unknown'),
                        'email': profile.get('emailAddress', ''),
                        'id': profile.get('id', '')
                    })

                page_token = response.get('nextPageToken', None)
                if not page_token:
                    break
        except Exception as e:
            print(f"Lỗi lấy danh sách học sinh: {e}")
        return students

    def get_courses(self):
        """Lấy danh sách lớp học đang hoạt động"""
        results = self.service_class.courses().list(courseStates=['ACTIVE']).execute()
        return results.get('courses', [])

    def upload_to_drive(self, file_path):
        """Upload file PDF lên Drive và trả về ID"""
        file_metadata = {'name': os.path.basename(file_path)}
        media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
        file = self.service_drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')

    def create_assignment(self, course_id, title, description, drive_file_id):
        """Tạo bài tập Classroom (Cách cũ - chỉ PDF)"""
        coursework = {
            'title': title,
            'description': description,
            'workType': 'ASSIGNMENT',
            'state': 'PUBLISHED',
            'maxPoints': 10,
            'materials': [
                {'driveFile': {'driveFile': {'id': drive_file_id}}}
            ]
        }
        coursework = self.service_class.courses().courseWork().create(
            courseId=course_id, body=coursework).execute()
        return coursework.get('alternateLink')

    def create_assignment_with_pdf(self, course_id, title, description, pdf_path):
        """Workflow đầy đủ: Upload PDF -> Tạo bài tập"""
        try:
            file_id = self.upload_to_drive(pdf_path)
            link = self.create_assignment(course_id, title, description, file_id)
            return True, link
        except Exception as e:
            return False, str(e)

    def upload_image(self, file_path):
        """Upload ảnh lên Drive, SET PUBLIC và trả về ID"""
        file_metadata = {'name': os.path.basename(file_path)}
        media = MediaFileUpload(file_path, mimetype='image/png')

        file = self.service_drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')

        try:
            self.service_drive.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
        except Exception as e:
            print(f"Lỗi set permission: {e}")

        return file_id

    def create_quiz_form(self, title, description):
        """Tạo một Google Form mới và sau đó chuyển sang chế độ Quiz"""
        initial_body = {
            "info": {
                "title": title
            }
        }
        form = self.service_forms.forms().create(body=initial_body).execute()
        form_id = form['formId']

        update_body = {
            "requests": [
                {
                    "updateSettings": {
                        "settings": {
                            "quizSettings": {
                                "isQuiz": True
                            }
                        },
                        "updateMask": "quizSettings.isQuiz"
                    }
                },
                {
                    "updateFormInfo": {
                        "info": {
                            "description": description
                        },
                        "updateMask": "description"
                    }
                }
            ]
        }
        self.service_forms.forms().batchUpdate(formId=form_id, body=update_body).execute()

        return form_id, form['responderUri']

    def batch_update_form(self, form_id, requests):
        """Gửi lệnh cập nhật form (thêm câu hỏi hàng loạt)"""
        body = {'requests': requests}
        self.service_forms.forms().batchUpdate(formId=form_id, body=body).execute()
