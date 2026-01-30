import os
import sys
import re
import time
import json
import asyncio
import socket
import shutil
import sqlite3
import copy
import hashlib
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal

# Import external libraries for Web Server
try:
    import uvicorn
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pyngrok import ngrok, conf
except ImportError:
    pass # Handle missing deps if necessary

from config import (
    LATEX_TEMPLATE, DATA_ID6_2025, CACHE_DIR, WEB_UI_TEMPLATE, DB_PATH
)
from utils import (
    LatexParser, PDFCompiler, ImageCompiler, ExamMixer, SchedulerManager,
    extract_metadata_from_tex, LatexCleaner
)
from integrations import GoogleManagerFull
from database import Backend

# =============================================================================
# WORKER THREADS
# =============================================================================

class AssignmentUploadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, questions, title, description, course_id, google_mgr):
        super().__init__()
        self.questions = questions
        self.title = title
        self.description = description
        self.course_id = course_id
        self.google_mgr = google_mgr

    def run(self):
        try:
            self.progress.emit("Đang biên soạn nội dung PDF...")

            body_content = [
                r"\begin{center}\textbf{\Large " + self.title + r"}\end{center}",
                r"\setcounter{ex}{0}"
            ]

            sanitized_qs = []
            for q in self.questions:
                if 'dang' not in q: q['dang'] = 4
                sanitized_qs.append(q)
            sanitized_qs.sort(key=lambda x: x['dang'])

            current_dang = None
            section_titles = {
                1: r"\section*{PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.}",
                2: r"\section*{PHẦN II. Câu trắc nghiệm đúng sai.}",
                3: r"\section*{PHẦN III. Câu trắc nghiệm trả lời ngắn.}",
                4: r"\section*{PHẦN IV. Tự luận / Khác}"
            }

            for q in sanitized_qs:
                dang = q['dang']
                if dang != current_dang:
                    if dang in section_titles:
                        body_content.append(r"\vspace{0.5cm}" + section_titles[dang] + r"\vspace{0.2cm}")
                    current_dang = dang
                body_content.append(q.get('content_tex', ''))

            tex_body = "\n".join(body_content)
            final_tex = LATEX_TEMPLATE.replace("__CONTENT__", tex_body)

            self.progress.emit("Đang biên dịch PDF (LaTeX)...")
            pdf_name = f"homework_{int(time.time())}"
            msg, pdf_path = PDFCompiler.compile_tex_to_pdf(final_tex, pdf_name)

            if not pdf_path:
                self.finished.emit(False, f"Lỗi biên dịch: {msg}")
                return

            self.progress.emit("Đang tải lên Google Classroom...")
            success, result = self.google_mgr.create_assignment_with_pdf(
                self.course_id, self.title, self.description, pdf_path
            )

            if success:
                self.finished.emit(True, result)
            else:
                self.finished.emit(False, f"Lỗi API: {result}")

        except Exception as e:
            self.finished.emit(False, f"Lỗi không xác định: {str(e)}")

class CacheCleanupWorker(QThread):
    def run(self):
        try:
            if os.path.exists(CACHE_DIR):
                for f in os.listdir(CACHE_DIR):
                    if not f.endswith(".svg"):
                        try:
                            fp = os.path.join(CACHE_DIR, f)
                            os.remove(fp)
                        except: pass
        except: pass

class ExamPreparerWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, dict)

    def __init__(self, questions, title, duration=90, external_tex=None, num_variants=1):
        super().__init__()
        self.questions = list(questions)
        self.title = title
        self.duration = duration
        self.external_tex = external_tex
        self.num_variants = num_variants

    def run(self):
        try:
            self.progress.emit("Đang xử lý dữ liệu...")

            variants_list = []
            mixer = ExamMixer()

            for v_idx in range(self.num_variants):
                code = str(101 + v_idx)
                self.progress.emit(f"Đang tạo mã đề {code} ({v_idx+1}/{self.num_variants})...")

                qs_clone = copy.deepcopy(self.questions)

                if self.num_variants > 1 or not self.external_tex:
                    random.shuffle(qs_clone)

                if mixer:
                    for q in qs_clone:
                        if q.get('dang', 4) == 1:
                            tex = q.get('content_tex', '')
                            new_tex, new_key = mixer.permute_content(tex)
                            q['content_tex'] = new_tex
                            q['key'] = new_key

                for q in qs_clone: q['dang'] = q.get('dang', 4)
                qs_clone.sort(key=lambda x: x['dang'])

                full_content = [
                    r"\begin{center}\textbf{\Large " + f"{self.title} (Mã đề {code})" + r"}\end{center}",
                    r"\setcounter{ex}{0}"
                ]

                exam_matrix = []
                current_dang = None

                section_titles = {
                    1: r"\section*{PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.} \textbf{\textit{Thí sinh trả lời các câu sau. Mỗi câu hỏi thí sinh chỉ lựa chọn một phương án.}}",
                    2: r"\section*{PHẦN II. Câu trắc nghiệm đúng sai.} \textbf{\textit{Thí sinh trả lời các câu sau. Trong mỗi ý {\bfseries a)}, {\bfseries b)}, {\bfseries c)}, {\bfseries d)} ở mỗi câu, thí sinh chọn đúng hoặc sai.}}",
                    3: r"\section*{PHẦN III. Câu trắc nghiệm trả lời ngắn.} \textbf{\textit{Thí sinh trả lời các câu sau.}}",
                    4: r"\section*{PHẦN IV. Tự luận / Khác}"
                }

                for idx, q in enumerate(qs_clone):
                    dang = q['dang']
                    tex = q.get('content_tex', q.get('content', ''))

                    if dang != current_dang:
                        if dang in section_titles:
                            full_content.append(r"\vspace{0.5cm}")
                            full_content.append(section_titles[dang])
                            full_content.append(r"\vspace{0.2cm}")
                        current_dang = dang

                    full_content.append(tex)

                    final_key = q.get('key')
                    explanation = ""

                    extracted_key, extracted_expl = extract_metadata_from_tex(tex, dang)
                    if not final_key or final_key == '?':
                        final_key = extracted_key
                    if extracted_expl:
                        explanation = extracted_expl

                    exam_matrix.append({
                        "id": idx + 1,
                        "type": dang,
                        "key": final_key,
                        "explanation": explanation
                    })

                final_tex = ""
                if self.external_tex and os.path.exists(self.external_tex) and self.num_variants == 1:
                    with open(self.external_tex, 'r', encoding='utf-8') as f: final_tex = f.read()
                else:
                    tex_body = "\n".join(full_content)
                    final_tex = LATEX_TEMPLATE.replace("__CONTENT__", tex_body)

                pdf_name = f"exam_{code}_{int(time.time())}"
                msg, pdf_path = PDFCompiler.compile_tex_to_pdf(final_tex, pdf_name)

                if pdf_path:
                    variants_list.append({
                        "code": code,
                        "pdf_filename": f"{pdf_name}.pdf",
                        "exam_matrix": exam_matrix
                    })

            if not variants_list:
                self.finished.emit(False, {"error": "Không tạo được đề nào!"})
                return

            first = variants_list[0]
            result_payload = {
                "title": self.title,
                "duration": self.duration * 60,
                "pdf_filename": first["pdf_filename"],
                "exam_matrix": first["exam_matrix"],
                "variants": variants_list
            }
            self.finished.emit(True, result_payload)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, {"error": f"Lỗi hệ thống: {str(e)}"})

class AutoIDWorker(QThread):
    progress = pyqtSignal(int, str)
    item_finished = pyqtSignal(int, dict)
    finished = pyqtSignal()

    def __init__(self, ai_engine, questions, syllabus_data):
        super().__init__()
        self.ai = ai_engine
        self.questions = questions
        self.syllabus = syllabus_data

    def run(self):
        syllabus_text = json.dumps(self.syllabus, ensure_ascii=False)
        total = len(self.questions)
        for idx, q in enumerate(self.questions):
            if self.isInterruptionRequested(): break

            if q.get('id6'): continue

            self.progress.emit(int((idx/total)*100), f"Đang phân tích câu {idx+1}/{total}...")

            content = q['content_tex']
            if len(content) > 2000: content = content[:2000] + "..."

            prompt = f"""
            Bạn là chuyên gia phân loại câu hỏi Toán THPT Việt Nam (2025).
            Dựa vào "Khung chương trình" dưới đây:
            {syllabus_text}

            Hãy phân tích nội dung câu hỏi sau và xác định nó thuộc Lớp, Môn, Chương, Bài nào.

            Nội dung câu hỏi:
            "{content}"

            Yêu cầu Output: Trả về JSON duy nhất (không giải thích thêm) theo định dạng:
            {{
                "grade": 10/11/12,
                "subject": "D" (Đại số/Giải tích) hoặc "H" (Hình học),
                "chapter": (số chương, ví dụ 1),
                "bai": (số bài, ví dụ 2),
                "level": "N" (Nhận biết) / "H" (Thông hiểu) / "V" (Vận dụng) / "C" (Vận dụng cao),
                "dang": 1 (Trắc nghiệm) / 2 (Đúng sai) / 3 (Trả lời ngắn) / 4 (Tự luận)
            }}
            Lưu ý:
            - Nếu có lệnh \\choice -> dang=1
            - Nếu có lệnh \\choiceTF -> dang=2
            - Nếu có lệnh \\shortans -> dang=3
            - Mức độ (level): Dựa vào độ khó của bài toán.
            """

            try:
                response = self.ai.model.generate_content(prompt)
                txt = response.text.strip()

                match = re.search(r"\{.*\}", txt, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    data = json.loads(json_str)
                else:
                    clean_txt = txt.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_txt)

                self.item_finished.emit(idx, data)
                time.sleep(1.5)

            except Exception as e:
                print(f"Lỗi AI câu {idx}: {e}")

        self.finished.emit()

class BatchAIWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    def __init__(self, ai, base_qs, num, start_code):
        super().__init__()
        self.ai, self.base_qs, self.num, self.start_code = ai, base_qs, num, start_code
    def run(self):
        res = {}
        total = self.num * len(self.base_qs)
        if total == 0: self.finished.emit({}); return
        for i in range(self.num):
            code = self.start_code + i
            res[code] = []
            for idx, q in enumerate(self.base_qs):
                p = int(((i * len(self.base_qs) + idx) / total) * 100)
                self.progress.emit(p, f"Đề {code}: Xử lý câu {idx+1}...")
                time.sleep(0.1)

                content_text = q.get('content_tex')
                if not content_text:
                    content_text = q.get('content')

                if not content_text:
                    continue

                try:
                    new_c, key = self.ai.generate_safe(content_text)
                    res[code].append({
                        "idx": idx + 1,
                        "content": new_c,
                        "key": key,
                        "orig_id": q.get('id', 0),
                        "dang": q.get('dang', 4)
                    })
                except Exception as e:
                    print(f"❌ Error generating question {idx+1}: {e}")
                    res[code].append({
                        "idx": idx + 1,
                        "content": content_text,
                        "key": "A (Error)",
                        "orig_id": q.get('id', 0),
                        "dang": q.get('dang', 4)
                    })

        self.finished.emit(res)

class ImportWorker(QThread):
    progress = pyqtSignal(int, str)
    analysis_done = pyqtSignal(list, dict)
    error = pyqtSignal(str)

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        all_questions = []
        all_images = {}

        local_bk = Backend()

        try:
            n = len(self.files)
            for i, f in enumerate(self.files):
                if self.isInterruptionRequested(): break

                p = int((i / n) * 100)
                fname = os.path.basename(f)
                self.progress.emit(p, f"Đang phân tích: {fname}...")

                qs, imgs = local_bk.analyze_tex_file(f)
                all_questions.extend(qs)
                all_images.update(imgs)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            if hasattr(local_bk, 'conn'):
                local_bk.conn.close()

        self.analysis_done.emit(all_questions, all_images)

class SingleRegenWorker(QThread):
    done = pyqtSignal(str, str)
    def __init__(self, ai, tex): super().__init__(); self.ai, self.tex = ai, tex
    def run(self): c, k = self.ai.generate_safe(self.tex); self.done.emit(c, k)

class CleanerWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list, str, list, str, list)

    def __init__(self, file_path, ai_engine, check_ai=False):
        super().__init__()
        self.file_path = file_path
        self.ai = ai_engine
        self.check_ai = check_ai

    def normalize_text(self, text):
        text = re.sub(r'%.*', '', text)
        text = re.sub(r'\s+', '', text)
        return text.strip()

    def run(self):
        try:
            self.progress.emit(10, "Đang đọc file...")
            content = ""
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f: content = f.read()
            except:
                with open(self.file_path, 'r', encoding='utf-16') as f: content = f.read()

            if "\\begin{document}" in content:
                header = content.split("\\begin{document}")[0] + "\\begin{document}\n"
            else:
                header = LATEX_TEMPLATE.replace("\\begin{document}", "") + "\n\\begin{document}\n"

            matches = re.finditer(r"(\\begin\s*\{ex\}.*?\\end\s*\{ex\})", content, re.DOTALL)

            unique_questions = []
            seen_hashes = set()
            duplicates_count = 0
            questions_to_ai = []

            total_matches = len(re.findall(r"\\begin\s*\{ex\}", content))
            processed = 0

            for m in matches:
                processed += 1
                raw_tex = m.group(1)

                clean_content = self.normalize_text(raw_tex)
                content_hash = hashlib.md5(clean_content.encode('utf-8')).hexdigest()

                if content_hash in seen_hashes:
                    duplicates_count += 1
                    continue

                seen_hashes.add(content_hash)
                unique_questions.append(raw_tex)

                questions_to_ai.append({
                    "id": len(unique_questions),
                    "content": raw_tex
                })

                if not self.check_ai:
                    p = 10 + int((processed / (total_matches or 1)) * 40)
                    self.progress.emit(p, f"Đang lọc trùng: {processed}/{total_matches}...")

            clean_path = self.file_path.replace(".tex", "_CLEANED.tex")
            self.save_to_file(clean_path, header, unique_questions)

            ai_errors = []

            if self.check_ai and self.ai and self.ai.is_ready:
                batch_size = 5
                total_batches = (len(questions_to_ai) + batch_size - 1) // batch_size

                for i in range(0, len(questions_to_ai), batch_size):
                    batch = questions_to_ai[i : i + batch_size]

                    batch_text = ""
                    for q in batch:
                        batch_text += f"--- CÂU SỐ {q['id']} ---\n{q['content']}\n\n"

                    prompt = f"""
                    Kiểm tra lỗi Chính tả và Logic Toán học cho các câu LaTeX sau:
                    {batch_text}
                    Chỉ trả về JSON format như sau (Nếu không có lỗi thì trả về danh sách rỗng):
                    [
                        {{"id": "Số thứ tự câu", "type": "Tên lỗi", "desc": "Mô tả chi tiết"}}
                    ]
                    Không giải thích gì thêm. Bắt buộc định dạng JSON.
                    """

                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            p_percent = 50 + int((i / len(questions_to_ai)) * 50)
                            self.progress.emit(p_percent, f"AI đang soát: Batch {i//batch_size + 1}/{total_batches} (Lần {attempt+1})")

                            response = self.ai.model.generate_content(prompt)
                            txt = response.text.strip().replace("```json", "").replace("```", "")

                            import json
                            batch_errors = json.loads(txt)
                            if isinstance(batch_errors, list):
                                ai_errors.extend(batch_errors)

                            time.sleep(2)
                            break

                        except Exception as e:
                            err_str = str(e)
                            if "429" in err_str or "quota" in err_str.lower():
                                wait_time = 65
                                self.progress.emit(p_percent, f"⚠️ Hết quota! Đang nghỉ {wait_time}s để hồi phục...")
                                time.sleep(wait_time)
                            else:
                                print(f"❌ Lỗi khác batch {i}: {e}")
                                break

            stats = [len(unique_questions), duplicates_count, len(ai_errors)]
            self.finished.emit(ai_errors, clean_path, stats, header, unique_questions)

        except Exception as e:
            self.progress.emit(0, f"Lỗi Critical: {str(e)}")
            self.finished.emit([], "", [], "", [])

    def save_to_file(self, path, header, questions):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(header)
                f.write("\n\n".join(questions))
                f.write("\n\\end{document}")
        except Exception as e:
            print(f"Lỗi ghi file: {e}")

class AutoFormWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, google_mgr, question_list, exam_title, course_id):
        super().__init__()
        self.google = google_mgr
        self.questions = question_list
        self.title = exam_title
        self.course_id = course_id

    def detect_question_type(self, tex_content):
        clean_tex = re.sub(r'(?<!\\)%.*', '', tex_content)
        if r"\choiceTF" in clean_tex: return 2
        if r"\choice" in clean_tex: return 1
        if r"\shortans" in clean_tex: return 3
        return 4

    def run(self):
        try:
            if not self.questions:
                self.error.emit("❌ Lỗi: Không tìm thấy câu hỏi nào!")
                return

            self.google.authenticate()
            total_q = len(self.questions)
            form_requests = []

            current_form_index = 0

            self.progress.emit(5, "📝 Đang khởi tạo Google Form...")
            form_id, form_link = self.google.create_quiz_form(self.title, "Đề thi được tạo bởi BankAI Pro")

            for idx, q in enumerate(self.questions):
                try:
                    p = 10 + int((idx / total_q) * 80)
                    self.progress.emit(p, f"Đang xử lý câu {idx+1}/{total_q}...")

                    detected_dang = self.detect_question_type(q['content_tex'])
                    q['dang'] = detected_dang

                    parts = LatexParser.split_question_parts(q['content_tex'])

                    stem_img_id = self.compile_and_upload(parts['stem'], f"q{idx}_stem")

                    sol_img_id = None
                    if parts['solution']:
                        sol_content = r"\textbf{Lời giải chi tiết:}\\" + parts['solution']
                        sol_img_id = self.compile_and_upload(sol_content, f"q{idx}_sol")

                    opt_img_ids = []
                    if (detected_dang == 1 or detected_dang == 2) and parts['options']:
                        for opt_i, opt_tex in enumerate(parts['options']):
                            clean_opt = opt_tex.replace(r"\True", "").strip()
                            o_id = self.compile_and_upload(clean_opt, f"q{idx}_opt{opt_i}")
                            opt_img_ids.append(o_id)

                    items = self.build_form_items_list(idx, q, parts, stem_img_id, opt_img_ids, sol_img_id, current_form_index)

                    if items:
                        form_requests.extend(items)
                        current_form_index += len(items)

                except Exception as e:
                    print(f"Lỗi xử lý câu {idx+1}: {e}")

            if form_requests:
                self.progress.emit(90, "☁️ Đang đồng bộ dữ liệu lên Google Form...")

                chunk_size = 10
                total_reqs = len(form_requests)

                for i in range(0, total_reqs, chunk_size):
                    chunk = form_requests[i : i + chunk_size]
                    print(f"📤 Đang gửi gói request {i}-{i+len(chunk)}/{total_reqs}...")
                    try:
                        self.google.batch_update_form(form_id, chunk)
                        time.sleep(1)
                    except Exception as e:
                        print(f"⚠️ Lỗi gửi gói {i}: {e}")
                        time.sleep(2)
                        try:
                            self.google.batch_update_form(form_id, chunk)
                        except:
                            print(f"❌ Bỏ qua gói {i}.")

            self.progress.emit(95, "📄 Đang tạo file PDF đề gốc...")
            full_tex = LATEX_TEMPLATE.replace("__CONTENT__", "\n".join([q['content_tex'] for q in self.questions]))
            msg, pdf_path = PDFCompiler.compile_tex_to_pdf(full_tex, "Full_Exam")

            pdf_id = None
            if pdf_path and os.path.exists(pdf_path):
                pdf_id = self.google.upload_to_drive(pdf_path)

            self.progress.emit(98, "🏫 Đang đăng bài lên Lớp học...")
            materials = [{'link': {'url': form_link, 'title': '📝 LINK LÀM BÀI TRỰC TUYẾN'}}]
            if pdf_id:
                materials.append({'driveFile': {'driveFile': {'id': pdf_id}}})

            coursework = {
                'title': self.title,
                'workType': 'ASSIGNMENT',
                'state': 'PUBLISHED',
                'maxPoints': 10,
                'materials': materials
            }
            res = self.google.service_class.courses().courseWork().create(
                courseId=self.course_id, body=coursework).execute()

            self.progress.emit(100, "Hoàn tất!")
            self.finished.emit(res.get('alternateLink'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

    def compile_and_upload(self, tex_content, name_prefix):
        if not tex_content or not tex_content.strip(): return None
        img_path = ImageCompiler.compile_question_to_png(tex_content, name_prefix)
        if img_path and os.path.exists(img_path):
            file_id = self.google.upload_image(img_path)
            time.sleep(0.5)
            return file_id
        return None

    def build_form_items_list(self, index, q_data, parts, stem_id, opt_ids, sol_id, start_index):
        requests = []
        current_idx = start_index

        if stem_id:
            requests.append({
                "createItem": {
                    "item": {
                        "title": f"Đề bài câu {index+1}",
                        "imageItem": {
                            "image": {
                                "sourceUri": f"https://drive.google.com/uc?export=view&id={stem_id}",
                                "properties": {"alignment": "CENTER"}
                            }
                        }
                    },
                    "location": {"index": current_idx}
                }
            })
            current_idx += 1

        dang = q_data.get('dang', 4)
        feedback = None
        if sol_id:
            sol_url = f"https://drive.google.com/file/d/{sol_id}/view"
            feedback = {"text": f"Xem lời giải:\n{sol_url}"}

        q_item = {
            "createItem": {
                "item": {
                    "title": f"Câu {index+1}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "grading": {
                                "pointValue": 1,
                                "correctAnswers": {"answers": []}
                            }
                        }
                    }
                },
                "location": {"index": current_idx}
            }
        }

        q_body = q_item['createItem']['item']['questionItem']['question']

        if dang == 1:
            ops = []
            labels = ["A", "B", "C", "D"]
            correct_char = q_data.get('key', 'A')
            for i in range(4):
                op = {"value": labels[i]}
                if i < len(opt_ids): op["image"] = {"sourceUri": f"https://drive.google.com/uc?export=view&id={opt_ids[i]}"}
                ops.append(op)
            q_body['choiceQuestion'] = {"type": "RADIO", "options": ops}
            key_idx = {'A':0,'B':1,'C':2,'D':3}.get(correct_char, 0)
            q_body['grading']['correctAnswers']['answers'] = [{"value": ops[key_idx]['value']}]
            if feedback: q_body['grading']['whenRight'] = q_body['grading']['whenWrong'] = feedback

        elif dang == 2:
            ops = []
            cor_vals = []
            labels = ["a", "b", "c", "d"]
            raw_opts = parts['options'] if parts['options'] else ["a","b","c","d"]
            for i, txt in enumerate(raw_opts):
                val = f"({labels[i] if i<4 else i})"
                op = {"value": val}
                if i < len(opt_ids): op["image"] = {"sourceUri": f"https://drive.google.com/uc?export=view&id={opt_ids[i]}"}
                else: op["value"] += " " + txt.replace(r"\True","").strip()
                ops.append(op)
                if r"\True" in txt: cor_vals.append({"value": val})
            q_body['choiceQuestion'] = {"type": "CHECKBOX", "options": ops}
            q_body['grading']['correctAnswers']['answers'] = cor_vals
            if feedback: q_body['grading']['whenRight'] = q_body['grading']['whenWrong'] = feedback

        elif dang == 3:
            q_body['textQuestion'] = {}
            ans = str(q_data.get('correct_val', q_data.get('key', '')))
            q_body['grading']['correctAnswers']['answers'] = [{"value": ans}]
            if feedback: q_body['grading']['generalFeedback'] = feedback

        else:
            q_body['textQuestion'] = {"paragraph": True}
            if feedback: q_body['grading']['generalFeedback'] = feedback

        requests.append(q_item)
        return requests

class AutoPostWorker(QThread):
    finished = pyqtSignal(str, str)

    def __init__(self, task, google_mgr):
        super().__init__()
        self.task = task
        self.google = google_mgr

    def run(self):
        local_bk = Backend()

        try:
            cfg = self.task['config']
            questions = []

            for _ in range(cfg['num_q']):
                q = local_bk.get_rnd(
                    cfg['grade'], cfg['subject'], cfg['chapter'],
                    0, cfg['level'], 0
                )
                if q: questions.append(q)

            if not questions:
                q_backup = local_bk.get_rnd(cfg['grade'], cfg['subject'], cfg['chapter'], 0, None, 0)
                if q_backup: questions.append(q_backup)

            if not questions:
                raise Exception("Không tìm thấy đủ câu hỏi trong ngân hàng dữ liệu!")

            content_list = []

            header_text = (
                r"\begin{center}" + "\n"
                r"\textbf{\large BÀI TẬP TỰ LUYỆN - " + f"{self.task['run_date']}}}" + "\n"
                r"\\[0.2cm] \textit{(Hệ thống tự động)}" + "\n"
                r"\end{center}" + "\n"
                r"\setcounter{ex}{0}" + "\n"
            )
            content_list.append(header_text)

            for q in questions:
                clean_q = re.sub(r"\\True", "", q['content_tex'])
                content_list.append(clean_q)

            body_content = "\n".join(content_list)
            full_tex = LATEX_TEMPLATE.replace("__CONTENT__", body_content)

            msg, pdf_path = PDFCompiler.compile_tex_to_pdf(full_tex, f"auto_exam_{self.task['id']}")

            if not pdf_path or not os.path.exists(pdf_path):
                raise Exception(f"Lỗi biên dịch PDF: {msg}")

            self.google.authenticate()
            file_id = self.google.upload_to_drive(pdf_path)

            title = f"Bài tập tự luyện ngày {self.task['run_date']}"
            desc = (f"Hệ thống tự động gửi bài.\n"
                    f"- Môn: {'Đại số' if cfg['subject']=='D' else 'Hình học'} 1{cfg['grade']%10}\n"
                    f"- Chương: {cfg['chapter']}\n"
                    f"- Mức độ: {cfg['level']}\n"
                    f"- Số câu: {len(questions)}")

            link = self.google.create_assignment(self.task['course_id'], title, desc, file_id)
            self.finished.emit(self.task['id'], f"Success: {link}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(self.task['id'], f"Error: {str(e)}")

        finally:
            if hasattr(local_bk, 'conn'):
                local_bk.conn.close()

# =============================================================================
# WEB SERVER HELPERS
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def register(self, websocket: WebSocket, client_id: str, name: str):
        self.active_connections[client_id] = {
            "ws": websocket,
            "name": name,
            "status": "waiting"
        }

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def broadcast_exam(self, exam_data, target_ids):
        for cid in target_ids:
            if cid in self.active_connections:
                client = self.active_connections[cid]
                try:
                    await client["ws"].send_json({
                        "type": "START_EXAM",
                        "data": exam_data
                    })
                    client["status"] = "doing"
                except:
                    self.disconnect(cid)

    def get_list(self):
        return [{"id": k, "name": v["name"], "status": v["status"]} for k,v in self.active_connections.items()]

manager = ConnectionManager()

class WebServerThread(QThread):
    students_changed = pyqtSignal(list)
    server_ready = pyqtSignal(str)
    result_received = pyqtSignal(str, float)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.port = 8080
        self.ngrok_auth_token = "38b8oxhy3hT98ZoeqO7kl8RJaJP_axFQ8v4mjEtV5EvSwLzb"
        self.public_url = ""
        self.ip_address = "0.0.0.0"
        self.gg_sync = None
        self.exam_dir = os.path.join(os.path.expanduser("~"), ".bankai_exams")
        if not os.path.exists(self.exam_dir): os.makedirs(self.exam_dir)

    def find_closing_brace(self, text, open_pos):
        balance = 1
        i = open_pos + 1
        n = len(text)
        while i < n:
            char = text[i]
            if char == '\\' and i + 1 < n: i += 2; continue
            if char == '{': balance += 1
            elif char == '}': balance -= 1
            if balance == 0: return i
            i += 1
        return -1

    def extract_key_from_tex(self, tex, q_type):
        if not tex: return None
        if q_type == 1:
            m = re.search(r"\[KEY:\s*([A-D])\]", tex, re.IGNORECASE)
            if m: return m.group(1).upper()
            m = re.search(r"\\choice", tex)
            if m:
                curr = m.end()
                for idx in range(4):
                     while curr < len(tex) and tex[curr].isspace(): curr += 1
                     if curr >= len(tex) or tex[curr] != '{': break
                     end = self.find_closing_brace(tex, curr)
                     if end == -1: break
                     if "\\True" in tex[curr+1:end]: return ['A','B','C','D'][idx]
                     curr = end + 1
            return "?"
        elif q_type == 2:
            m = re.search(r"\\choiceTF", tex)
            res = {}
            if m:
                curr = m.end()
                for sub in ['a','b','c','d']:
                     while curr < len(tex) and tex[curr].isspace(): curr += 1
                     if curr >= len(tex) or tex[curr] != '{': break
                     end = self.find_closing_brace(tex, curr)
                     if end == -1: break
                     res[sub] = "Đ" if "\\True" in tex[curr+1:end] else "S"
                     curr = end + 1
            return res if res else None
        elif q_type == 3:
            m = re.search(r"\\shortans", tex)
            if m:
                 curr = m.end()
                 while curr < len(tex) and tex[curr].isspace(): curr += 1
                 if curr < len(tex) and tex[curr] == '{':
                     end = self.find_closing_brace(tex, curr)
                     if end != -1: return tex[curr+1:end].strip()
            return "?"
        return None

    def calculate_score(self, exam_matrix, user_answers):
        s1 = s2 = s3 = 0.0
        review_data = {}

        p1 = [q for q in exam_matrix if q['type'] == 1]
        p2 = [q for q in exam_matrix if q['type'] == 2]
        p3 = [q for q in exam_matrix if q['type'] == 3]

        val_p1 = (3.0 / len(p1)) if p1 else 0
        val_p2 = (4.0 / len(p2)) if p2 else 0
        val_p3 = (3.0 / len(p3)) if p3 else 0

        for q in exam_matrix:
            qid = str(q['id'])
            ua = user_answers.get(qid)

            q_key = q.get('key')
            if not q_key or q_key == '?':
                content = q.get('content_tex') or q.get('content')
                q_key = self.extract_key_from_tex(content, q['type'])

            q_type = q['type']

            item_review = {
                "is_correct": False,
                "user_selected": ua,
                "correct_answer": q_key,
                "explanation": q.get('explanation', ""),
                "type": q_type
            }

            if q_type == 1:
                if str(ua) == str(q_key):
                    s1 += val_p1
                    item_review['is_correct'] = True
            elif q_type == 2:
                correct_count = 0
                sub_details = {}
                if isinstance(q_key, dict):
                    if not isinstance(ua, dict): ua = {}
                    for sub in ['a','b','c','d']:
                        k_val = q_key.get(sub)
                        u_val = ua.get(sub)
                        is_corr = (u_val == k_val)
                        if is_corr: correct_count += 1
                        sub_details[sub] = {'correct': is_corr, 'user': u_val, 'key': k_val}

                ratio = {1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}.get(correct_count, 0)
                s2 += val_p2 * ratio
                item_review['is_correct'] = (correct_count == 4)
                item_review['sub_details'] = sub_details

            elif q_type == 3:
                def norm(s): return str(s or "").replace(" ", "").replace(",", ".").lower()
                if norm(ua) == norm(q_key):
                    s3 += val_p3
                    item_review['is_correct'] = True

            review_data[qid] = item_review

        return round(s1 + s2 + s3, 2), review_data

    def set_exam_data(self, data):
        self.exam_data = data
        self.exam_id = data.get('examId', 'default')
        if 'examId' in data:
            self.save_exam_file(self.exam_id, data)
        print(f"✅ Server loaded exam data: {self.exam_id}")

    def save_exam_file(self, exam_id, data):
        filepath = os.path.join(self.exam_dir, f"{exam_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"💾 Đã lưu đề thi: {exam_id}")

    def load_exam_file(self, exam_id):
        filepath = os.path.join(self.exam_dir, f"{exam_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def sync_score(self, exam_data, name, email, score):
        cid = exam_data.get('courseId')
        cwid = exam_data.get('courseWorkId')
        if not cid or not cwid: return

        if not self.gg_sync:
            try: self.gg_sync = GoogleManagerFull(); self.gg_sync.authenticate()
            except: return

        try:
            print(f"🔄 Đang đồng bộ điểm cho đề {exam_data.get('title')}...")
            service = self.gg_sync.service_class
            students = service.courses().students().list(courseId=cid).execute().get('students', [])
            user_id = None
            target_email = email.strip().lower()
            target_name = name.strip().lower()

            for s in students:
                p = s.get('profile', {})
                api_email = p.get('emailAddress', '').lower()
                api_name = p.get('name', {}).get('fullName', '').lower()
                if api_email and api_email == target_email: user_id = s['userId']; break
                if not api_email and api_name == target_name: user_id = s['userId']; break

            if user_id:
                subs = service.courses().courseWork().studentSubmissions().list(
                    courseId=cid, courseWorkId=cwid, userId=user_id).execute().get('studentSubmissions', [])
                if subs:
                    body = {'draftGrade': float(score), 'assignedGrade': float(score)}
                    service.courses().courseWork().studentSubmissions().patch(
                        courseId=cid, courseWorkId=cwid, id=subs[0]['id'],
                        updateMask='assignedGrade,draftGrade', body=body).execute()
                    print("✅ Đã vào sổ điểm!")
        except Exception as e: print(f"❌ Lỗi Sync: {e}")

    def distribute_exam(self, target_ids):
        if hasattr(self, 'exam_data') and self.exam_data:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.broadcast_exam(self.exam_data, target_ids))
            loop.close()

    def run(self):
        try:
            print("🔄 Đang dọn dẹp các kết nối cũ...")
            from pyngrok import ngrok
            ngrok.kill()
            if sys.platform != "win32":
                os.system("pkill -9 ngrok")
            time.sleep(2)
        except:
            pass

        if self.ngrok_auth_token:
            conf.get_default().auth_token = self.ngrok_auth_token
            conf.get_default().region = "us"

        app = FastAPI()
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

        @app.get("/exam/{exam_id}")
        async def get_exam_ui(exam_id: str):
            data = self.load_exam_file(exam_id)
            if data:
                students = data.get('students', [])
                json_students = json.dumps(students, ensure_ascii=False).replace("</script>", "<\\/script>")
                html = WEB_UI_TEMPLATE.replace("__STUDENT_LIST__", json_students)
                return HTMLResponse(content=html)
            return HTMLResponse(content="<h1>❌ Đề thi không tồn tại hoặc đã bị xóa!</h1>")

        @app.get("/api/pdf/{filename}")
        async def get_pdf(filename: str):
            path = os.path.join(os.path.expanduser("~"), ".bankai_build", filename)
            return FileResponse(path) if os.path.exists(path) else {"error": "PDF not found"}

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await manager.connect(websocket)
            try:
                while True:
                    data = json.loads(await websocket.receive_text())

                    if data.get('type') == 'JOIN':
                        exam_id = data.get('exam_id')
                        exam_data = self.load_exam_file(exam_id)

                        if exam_data:
                            manager.register(websocket, data['id'], f"{data['name']} [{exam_id}]")

                            payload = exam_data
                            variants = exam_data.get('variants', [])
                            if variants:
                                import random
                                selected_variant = random.choice(variants)
                                payload = exam_data.copy()
                                payload['pdf_filename'] = selected_variant['pdf_filename']
                                payload['exam_matrix'] = selected_variant['exam_matrix']
                                payload['variant_code'] = selected_variant['code']

                            sanitized_payload = payload.copy()
                            if 'exam_matrix' in sanitized_payload:
                                import copy
                                sanitized_matrix = copy.deepcopy(sanitized_payload['exam_matrix'])
                                for q in sanitized_matrix:
                                    if 'key' in q: del q['key']
                                sanitized_payload['exam_matrix'] = sanitized_matrix

                            await websocket.send_json({"type": "START_EXAM", "data": sanitized_payload})
                            self.students_changed.emit(manager.get_list())
                        else:
                            await websocket.send_json({"type": "ERROR", "message": "Không tìm thấy dữ liệu đề thi!"})

                    elif data.get('type') == 'SUBMIT':
                        exam_id = data.get('exam_id')
                        variant_code = data.get('variant_code')
                        user_answers = data.get('detail', {})

                        exam_data = self.load_exam_file(exam_id)
                        if exam_data:
                            target_matrix = exam_data.get('exam_matrix', [])
                            variants = exam_data.get('variants', [])

                            if variants and variant_code:
                                for v in variants:
                                    if str(v['code']) == str(variant_code):
                                        target_matrix = v['exam_matrix']
                                        break

                            final_score, review_data = self.calculate_score(target_matrix, user_answers)

                            try:
                                conn = sqlite3.connect(self.db_path)
                                conn.execute("INSERT INTO exam_results (student_name, exam_title, score, detail) VALUES (?, ?, ?, ?)",
                                    (f"{data['name']} ({data['email']})", exam_data.get('title'), final_score, json.dumps(review_data, ensure_ascii=False)))
                                conn.commit(); conn.close()

                                self.result_received.emit(f"{data['name']} - {exam_data.get('title')}", float(final_score))
                                self.sync_score(exam_data, data['name'], data['email'], final_score)
                            except: pass

                            await websocket.send_json({
                                "type": "SCORE_RESULT",
                                "data": {
                                    "score": final_score,
                                    "review_data": review_data
                                }
                            })

            except WebSocketDisconnect:
                # Handle disconnection if needed
                pass
            except Exception as e:
                print(f"WS Error: {e}")

        MY_DOMAIN = "oncologic-premeditative-nada.ngrok-free.dev"
        try:
            ngrok.kill()
            success = False
            for i in range(3):
                try:
                    time.sleep(2)
                    self.public_url = ngrok.connect(self.port, domain=MY_DOMAIN).public_url
                    self.server_ready.emit(self.public_url)
                    success = True; break
                except: pass
            if not success:
                self.public_url = ngrok.connect(self.port).public_url
                self.server_ready.emit(self.public_url)
        except Exception as e: self.server_ready.emit(f"Lỗi Ngrok: {e}")

        config = uvicorn.Config(app, host="0.0.0.0", port=self.port, log_level="critical", proxy_headers=True)
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if hasattr(self, 'server') and self.server:
            self.server.should_exit = True

        try:
            from pyngrok import ngrok
            ngrok.kill()
            if sys.platform != "win32":
                os.system("pkill -9 ngrok")
        except:
            pass

        if not self.wait(3000):
            self.terminate()
