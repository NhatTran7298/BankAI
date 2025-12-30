import os
# =============================================================================
# [FIX LỖI CRASH TRÊN MACOS] - QUAN TRỌNG: PHẢI ĐẶT TRÊN CÙNG
# =============================================================================
os.environ['GRPC_DNS_RESOLVER'] = 'native'
os.environ['GRPC_POLL_STRATEGY'] = 'poll'
os.environ['no_proxy'] = '*'
# =============================================================================

import sys
import re
import sqlite3
import time
import json
import google.generativeai as genai
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QTextEdit, QMessageBox, QDialog,
                             QComboBox, QListWidgetItem, QTableWidget, 
                             QSpinBox, QTabWidget, QHeaderView, QProgressDialog, 
                             QTreeWidget, QTreeWidgetItem, QSplitter, QLineEdit,
                             QTableWidgetItem, QScrollArea, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QFont, QIcon, QColor

# =============================================================================
# 1. CẤU HÌNH
# =============================================================================
# --- CẤU HÌNH ĐƯỜNG DẪN AN TOÀN CHO MACOS ---
# Lấy đường dẫn thư mục Documents của người dùng
user_documents = os.path.expanduser("~/Documents")
# Tạo thư mục dữ liệu riêng: Documents/BankAI_Data
DB_FOLDER = os.path.join(user_documents, "BankAI_Data") 
DB_NAME = "bank_pro.db"

# Tự động tạo thư mục nếu chưa có
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)
# ---------------------------------------------
MY_API_KEY = "AIzaSyBPgphlODj_7lGm2xGU4sqf52DZD08U5QM"

# Cấu trúc chương học
CHUONG_DAI_SO = {
    10: {
        1: "Mệnh đề. Tập hợp",
        2: "BPT và hệ BPT bậc nhất hai ẩn",
        3: "Hàm số bậc hai và đồ thị",
        6: "Thống kê",
        7: "Bất phương trình bậc 2 một ẩn",
        8: "Đại số tổ hợp",
        10: "Xác suất",
    },
    11: {
        1: "Hàm số lượng giác và phương trình lượng giác",
        2: "Dãy số. Cấp số cộng. Cấp số nhân",
        3: "Giới hạn. Hàm số liên tục",
        5: "Các số đặc trưng đo xu thế trung tâm cho mẫu số liệu ghép nhóm",
        6: "Hàm số mũ và hàm số lôgarít",
        7: "Đạo hàm",
        9: "Xác suất",
    },
    12: {
        1: "Ứng dụng đạo hàm để khảo sát hàm số",
        3: "Các số đặc trưng đo mức độ phân tán cho mẫu số liệu ghép nhóm",
        4: "Nguyên hàm, tích phân và ứng dụng",
        6: "Một số yếu tố xác suất",
    }
}

CHUONG_HINH_HOC = {
    10: {
        4: "Hệ thức lượng trong tam giác",
        5: "Véctơ (chưa xét tọa độ)",
        9: "Phương pháp toạ độ trong mặt phẳng (Oxy)",
    },
    11: {
        4: "Đường thẳng, mặt phẳng. Quan hệ song song trong không gian",
        8: "Quan hệ vuông góc trong không gian",
    },
    12: {
        2: "Tọa độ của véc-tơ trong không gian",
        5: "Phương trình mặt phẳng, đường thẳng, mặt cầu trong không gian Oxyz",
    }
}

MUC_DO = {
    'N': 'Nhận biết',
    'H': 'Thông hiểu', 
    'V': 'Vận dụng',
    'C': 'Vận dụng cao',
}

LATEX_TEMPLATE = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{vietnam}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{tkz-tab}
\usepackage[left=2cm,right=2cm,top=2cm,bottom=2cm]{geometry}
\newcounter{ex}
\newenvironment{ex}[1][]{\refstepcounter{ex}\par\medskip\noindent\textbf{Câu \theex.} #1}{\par\medskip}
\newcommand{\choice}[4]{\par\noindent\begin{tabular}{p{0.22\textwidth}p{0.22\textwidth}p{0.22\textwidth}p{0.22\textwidth}}\textbf{A.} #1 & \textbf{B.} #2 & \textbf{C.} #3 & \textbf{D.} #4\end{tabular}}
\newcommand{\loigiai}[1]{\par\noindent\textit{\textbf{Lời giải:}} #1}
\begin{document}
"""
# =============================================================================
# DANH MỤC DẠNG CÂU HỎI
# =============================================================================
DANH_MUC_DANG = {
    1: "Trắc nghiệm 4 lựa chọn",
    2: "Đúng/Sai",
    3: "Trả lời ngắn",
    4: "Tự luận",
}

# Để dễ so sánh khi import
DANG_KEYWORDS = {
    1: [r'\\choice{', r'\\choice['],           # Trắc nghiệm 4 đáp án
    2: [r'\\choiceTF{'],                        # Đúng/Sai
    3: [r'\\shortans{'],                        # Trả lời ngắn
    4: [],                                      # Tự luận: không có choice nào ở trên
}

# =============================================================================
# 2. AI ENGINE (ĐÃ SỬA LỖI)
# =============================================================================
class AIEngine:
    def __init__(self):
        self.is_ready = False
        try:
            genai.configure(api_key=MY_API_KEY)
            
            # 1. Cấu hình Safety Settings để tránh bị chặn nhầm
            # BLOCK_NONE giúp AI không chặn các nội dung toán học/học thuật
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            self.generation_config = genai.types.GenerationConfig(
                temperature=0.2, 
                max_output_tokens=8192,
            )
            
            # 2. Sửa tên Model thành gemini-1.5-pro (bản ổn định và mạnh nhất hiện tại)
            # Hoặc dùng 'gemini-1.5-flash' nếu muốn tốc độ nhanh hơn
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-pro', 
                safety_settings=safety_settings,
                generation_config=self.generation_config
            )
            self.is_ready = True
            print("✅ AI Engine khởi tạo thành công")
        except Exception as e:
            print(f"❌ Lỗi Init AI: {e}")
            self.is_ready = False

    def _force_structure(self, ai_text, original_tex):
        """Đảm bảo cấu trúc LaTeX đúng format"""
        ai_text = ai_text.replace("\\begin{question}", "").replace("\\end{question}", "")
        
        if "\\begin{ex}" not in ai_text:
            ai_text = f"\\begin{{ex}}\n{ai_text.strip()}\n\\end{{ex}}"
        
        if "\\begin{ex}" in ai_text and "\\end{ex}" not in ai_text:
            ai_text = ai_text.strip() + "\n\\end{ex}"
            
        if "\\choice" not in ai_text and "\\item" in ai_text:
            return original_tex 
        
        return ai_text

    def generate_safe(self, tex):
        """Tạo câu hỏi mới với xử lý lỗi an toàn"""
        if not self.is_ready: 
            return tex, "A"
        
        prompt = f"""
        Nhiệm vụ: Với vai trò là một giáo viên toán cấp THPT, hãy tạo 1 câu hỏi tương tự câu bên dưới (có thể là thay số liệu, hoặc đổi câu hỏi khác nhưng với chuẩn kiến thức tương đương, giữ nguyên dạng toán).
        Đối với các bài toán có hình ảnh được vẽ bằng code Tikz hãy tạo hình ảnh tương tự cũng bằng code Tikz
        YÊU CẦU BẮT BUỘC VỀ FORMAT (KHÔNG ĐƯỢC SAI):
        1. Giữ nguyên lệnh \\begin{{ex}} ... \\end{{ex}}
        2. Giữ nguyên các lệnh \\choice{{}}{{}}{{}}{{}} \\choiceTF{{}}{{}}{{}}{{}} \shortans{{}}(Không dùng \\item, phải đủ 4 phương án)
        3. Giữ nguyên lệnh \\loigiai{{}} và viết lời giải chi tiết.
        4. Output code LaTeX thuần. Dòng cuối cùng của output ghi chính xác: [KEY: X] (với X là đáp án đúng A,B,C,D).
        CÂU GỐC:
        {tex}
        """
        try:
            res = self.model.generate_content(prompt)
            
            # 3. Kiểm tra phản hồi trước khi truy cập .text
            if not res.candidates:
                print("❌ AI không trả về candidate nào.")
                return tex, "A"
                
            # Kiểm tra xem có bị chặn bởi Safety filter không
            if res.candidates[0].finish_reason == 3: # 3 là SAFETY
                print("⚠️ Bị chặn bởi Safety Filter. Đang thử lại...")
                return tex, "A"

            # Truy cập text an toàn
            try:
                txt = res.text.strip()
            except ValueError:
                print("⚠️ Lỗi truy cập .text (Có thể do finish_reason).")
                # Fallback nếu có parts nhưng không có text liền mạch
                if res.parts:
                    txt = res.parts[0].text.strip()
                else:
                    return tex, "A"

            key = "A"
            m = re.search(r"\[KEY:\s*([A-D])\]", txt, re.IGNORECASE)
            if m:
                key = m.group(1).upper()
                txt = txt.replace(m.group(0), "")
            txt = txt.replace("```latex", "").replace("```tex", "").replace("```", "").strip()
            final_txt = self._force_structure(txt, tex)
            return final_txt, key
        except Exception as e:
            print(f"❌ Lỗi AI generate chi tiết: {e}")
            return tex, "A"
        
# =============================================================================
# 3. WORKERS
# =============================================================================
class BatchAIWorker(QThread):
    """Worker thread để chạy AI batch không block UI"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    
    def __init__(self, ai, base_qs, num, start_code):
        super().__init__()
        self.ai = ai
        self.base_qs = base_qs
        self.num = num
        self.start_code = start_code  # Đổi tên để tránh trùng với method start()

    def run(self):
        res = {}
        total = self.num * len(self.base_qs)
        if total == 0: 
            self.finished.emit({})
            return

        for i in range(self.num):
            code = self.start_code + i  # Dùng start_code thay vì start
            res[code] = []
            for idx, q in enumerate(self.base_qs):
                percent = int(((i * len(self.base_qs) + idx) / total) * 100)
                self.progress.emit(percent, f"Đề {code}: Xử lý câu {idx+1}...")
                
                time.sleep(0.5)
                
                new_c, key = self.ai.generate_safe(q['content'])
                res[code].append({
                    "idx": idx + 1, 
                    "content": new_c, 
                    "key": key, 
                    "orig_id": q['id']
                })
        
        self.finished.emit(res)

class SingleRegenWorker(QThread):
    """Worker thread để tạo lại 1 câu"""
    done = pyqtSignal(str, str)
    
    def __init__(self, ai, tex):
        super().__init__()
        self.ai = ai
        self.tex = tex
    
    def run(self):
        c, k = self.ai.generate_safe(self.tex)
        self.done.emit(c, k)

# =============================================================================
# 4. DATABASE BACKEND
# =============================================================================
class Backend:
    """Quản lý database câu hỏi"""
    def __init__(self):
        if not os.path.exists(DB_FOLDER):
            os.makedirs(DB_FOLDER)
        
        self.conn = sqlite3.connect(
            os.path.join(DB_FOLDER, DB_NAME), 
            check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Khởi tạo bảng nếu chưa có"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                grade INTEGER,
                subject TEXT, 
                chapter INTEGER, 
                level TEXT, 
                content_tex TEXT, 
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        
        # Auto-migrate: Thêm các cột ID6 nếu chưa có
        self._migrate_to_id6()
    
    def _migrate_to_id6(self):
        """Tự động migrate database thêm cột ID6"""
        try:
            # Kiểm tra cột hiện có
            cursor = self.conn.execute("PRAGMA table_info(questions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Thêm các cột mới nếu chưa có
            columns_to_add = [
                ('id6', 'TEXT'),
                ('bai', 'INTEGER'),
                ('dang', 'INTEGER'),
            ]
            
            for col_name, col_type in columns_to_add:
                if col_name not in columns:
                    self.conn.execute(f"ALTER TABLE questions ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Đã thêm cột: {col_name}")
            
            self.conn.commit()
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")

def import_tex(self, path):
    """Import file TeX vào database + tự động phân loại dạng"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return 0
    
    matches = re.finditer(
        r"\\begin\s*\{ex\}(.*?)\\end\s*\{ex\}", 
        content, 
        re.DOTALL
    )
    cnt = 0
    
    for m in matches:
        raw = m.group(0)
        block = m.group(1)  # nội dung bên trong ex
        
        # Parse metadata từ comment %[XDYNY]
        g, s, ch, l = 10, "D", 1, "N"
        metadata = re.search(r'%\[(\d+)([DH])(\d+)([NHVCT])', raw)
        if metadata:
            grade_code, s, ch, l = metadata.groups()
            grade_map = {'0': 10, '1': 11, '2': 12}
            g = grade_map.get(grade_code, int(grade_code) if grade_code.isdigit() else 10)
        
        # === PHÂN LOẠI DẠNG CÂU HỎI ===
        dang = 4  # mặc định là tự luận
        
        # Kiểm tra từ trên xuống dưới theo mức độ đặc trưng
        if any(re.search(pat, block) for pat in DANG_KEYWORDS[1]):
            dang = 1
        elif any(re.search(pat, block) for pat in DANG_KEYWORDS[2]):
            dang = 2
        elif any(re.search(pat, block) for pat in DANG_KEYWORDS[3]):
            dang = 3
        # còn lại là tự luận (4)
        
        self.conn.execute(
            """
            INSERT INTO questions 
            (grade, subject, chapter, level, content_tex, raw_data, dang) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (g, s, int(ch), l, raw, raw, dang)
        )
        cnt += 1
    
    self.conn.commit()
    return cnt

def get_all_filtered(self, grade=None, subject=None, chapter=None, level=None, dang=None, limit=None):
    query = "SELECT * FROM questions WHERE 1=1"
    params = []
    
    if grade:    query += " AND grade=?";    params.append(grade)
    if subject:  query += " AND subject=?";  params.append(subject)
    if chapter:  query += " AND chapter=?";  params.append(chapter)
    if level:    query += " AND level=?";    params.append(level)
    if dang is not None and dang != 0:  # 0 nghĩa là tất cả
        query += " AND dang=?"
        params.append(dang)
    
    query += " ORDER BY id"
    
    if limit:
        query += f" LIMIT {limit}"
    
    results = self.conn.execute(query, tuple(params)).fetchall()
    return [dict(r) for r in results]


def get_rnd(self, g, s, ch, l, dang=None, exc=None):
    query = "SELECT * FROM questions WHERE grade=? AND subject=? AND chapter=? AND level=?"
    params = [g, s, ch, l]
    
    if dang is not None and dang != 0:
        query += " AND dang=?"
        params.append(dang)
    
    if exc:
        query += " AND id != ?"
        params.append(exc)
    
    result = self.conn.execute(
        query + " ORDER BY RANDOM() LIMIT 1", 
        tuple(params)
    ).fetchone()
    
    return dict(result) if result else None
    
    def get_by_id(self, qid):
        """Lấy câu hỏi theo ID"""
        result = self.conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
        return dict(result) if result else None
    
    def get_stats(self):
        """Lấy thống kê tổng quan"""
        stats = {}
        for grade in [10, 11, 12]:
            stats[grade] = {}
            for subject in ['D', 'H']:
                cursor = self.conn.execute(
                    "SELECT chapter, level, COUNT(*) as cnt FROM questions WHERE grade=? AND subject=? GROUP BY chapter, level",
                    (grade, subject)
                )
                stats[grade][subject] = {}
                for row in cursor:
                    ch, lv, cnt = row
                    if ch not in stats[grade][subject]:
                        stats[grade][subject][ch] = {}
                    stats[grade][subject][ch][lv] = cnt
        return stats

# =============================================================================
# 5. DRAG & DROP WIDGETS
# =============================================================================
class DragDropListWidget(QListWidget):
    """ListWidget hỗ trợ drag & drop"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    
    def startDrag(self, supportedActions):
        """Bắt đầu drag"""
        item = self.currentItem()
        if not item:
            return
        
        q_data = item.data(Qt.ItemDataRole.UserRole)
        if not q_data:
            return
        
        # Tạo mime data
        mime_data = QMimeData()
        drag_data = {
            'id': q_data['id'],
            'content': q_data['content_tex'],
            'display': f"[L{q_data['grade']}-{q_data['subject']}{q_data['chapter']}-{q_data['level']}]"
        }
        mime_data.setText(json.dumps(drag_data))
        
        # Tạo drag
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)

class DropZoneListWidget(QListWidget):
    """ListWidget là drop zone (khu vực thả)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            data = event.mimeData().text()
            try:
                q_data = json.loads(data)
                # Dùng QListWidget.count() thay vì self.count()
                current_count = QListWidget.count(self)
                item = QListWidgetItem(f"Câu {current_count + 1}: {q_data['display']}")
                item.setData(Qt.ItemDataRole.UserRole, q_data)
                self.addItem(item)
                event.accept()
            except Exception as e:
                print(f"Drop error: {e}")
                event.ignore()
        else:
            event.ignore()

# =============================================================================
# 6. ID6 ASSIGNMENT DIALOG  
# =============================================================================
class ID6AssignDialog(QDialog):
    """Dialog để gán ID6 cho các câu hỏi chưa có ID"""
    
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.unassigned_questions = []
        self.setWindowTitle("Gán ID6 cho câu hỏi")
        self.setMinimumSize(1200, 700)
        self.setup_ui()
        self.load_unassigned_questions()
    
    def setup_ui(self):
        """Tạo giao diện"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📝 DANH SÁCH CÂU HỎI CHƯA CÓ ID6")
        header_font = QFont("Arial", 16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #e74c3c; padding: 10px;")
        layout.addWidget(header)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Danh sách câu hỏi:"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Nội dung", "Lớp", "Môn", "Chương", "Mức độ", "Trạng thái"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.table)
        splitter.addWidget(left_widget)
        
        # Right panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("👁️ XEM TRƯỚC & GÁN ID6"))
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(250)
        right_layout.addWidget(self.preview)
        
        # Form
        form_group = QWidget()
        form_group.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        form_layout = QVBoxLayout(form_group)
        form_layout.addWidget(QLabel("🏷️ CHỌN ID6:"))
        
        # Grade
        grade_layout = QHBoxLayout()
        grade_layout.addWidget(QLabel("Lớp:"))
        self.grade_cb = QComboBox()
        self.grade_cb.addItems(["10", "11", "12"])
        self.grade_cb.currentTextChanged.connect(self.update_chapters)
        grade_layout.addWidget(self.grade_cb)
        grade_layout.addStretch()
        form_layout.addLayout(grade_layout)
        
        # Subject
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Môn:"))
        self.subject_cb = QComboBox()
        self.subject_cb.addItems(["D - Đại số", "H - Hình học"])
        self.subject_cb.currentTextChanged.connect(self.update_chapters)
        subject_layout.addWidget(self.subject_cb)
        subject_layout.addStretch()
        form_layout.addLayout(subject_layout)
        
        # Chapter
        chapter_layout = QHBoxLayout()
        chapter_layout.addWidget(QLabel("Chương:"))
        self.chapter_cb = QComboBox()
        chapter_layout.addWidget(self.chapter_cb)
        chapter_layout.addStretch()
        form_layout.addLayout(chapter_layout)
        
        # Level
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Mức độ:"))
        self.level_cb = QComboBox()
        self.level_cb.addItems(["N - Nhận biết", "H - Thông hiểu", "V - Vận dụng", "C - Vận dụng cao"])
        level_layout.addWidget(self.level_cb)
        level_layout.addStretch()
        form_layout.addLayout(level_layout)
        
        # Bai
        bai_layout = QHBoxLayout()
        bai_layout.addWidget(QLabel("Bài:"))
        self.bai_cb = QComboBox()
        self.bai_cb.addItems([str(i) for i in range(1, 10)])
        bai_layout.addWidget(self.bai_cb)
        bai_layout.addStretch()
        form_layout.addLayout(bai_layout)
        
        # Dang
        dang_layout = QHBoxLayout()
        dang_layout.addWidget(QLabel("Dạng:"))
        self.dang_cb = QComboBox()
        self.dang_cb.addItems([str(i) for i in range(1, 10)])
        dang_layout.addWidget(self.dang_cb)
        dang_layout.addStretch()
        form_layout.addLayout(dang_layout)
        
        # ID6 Preview
        self.id6_preview_label = QLabel("ID6: -")
        self.id6_preview_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2ecc71; padding: 10px;")
        form_layout.addWidget(self.id6_preview_label)
        
        for cb in [self.grade_cb, self.subject_cb, self.chapter_cb, self.level_cb, self.bai_cb, self.dang_cb]:
            cb.currentTextChanged.connect(self.update_id6_preview)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_assign = QPushButton("✅ GÁN ID6 CHO CÂU NÀY")
        btn_assign.clicked.connect(self.assign_current)
        btn_assign.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        btn_layout.addWidget(btn_assign)
        
        btn_assign_all = QPushButton("🔄 GÁN CHO TẤT CẢ")
        btn_assign_all.clicked.connect(self.assign_all_same)
        btn_assign_all.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px;")
        btn_layout.addWidget(btn_assign_all)
        form_layout.addLayout(btn_layout)
        
        right_layout.addWidget(form_group)
        splitter.addWidget(right_widget)
        layout.addWidget(splitter)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        btn_close = QPushButton("❌ Đóng")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)
        
        self.update_chapters()
    
    def update_chapters(self):
        grade = int(self.grade_cb.currentText())
        subject_code = self.subject_cb.currentText()[0]
        
        self.chapter_cb.blockSignals(True)
        self.chapter_cb.clear()
        
        chapters = CHUONG_DAI_SO if subject_code == 'D' else CHUONG_HINH_HOC
        for ch_num, ch_name in sorted(chapters.get(grade, {}).items()):
            self.chapter_cb.addItem(f"{ch_num} - {ch_name}")
        
        self.chapter_cb.blockSignals(False)
        self.update_id6_preview()
    
    def update_id6_preview(self):
        try:
            grade = int(self.grade_cb.currentText())
            grade_code = str(grade - 10)
            subject_code = self.subject_cb.currentText()[0]
            chapter_text = self.chapter_cb.currentText()
            if not chapter_text:
                return
            chapter = chapter_text.split(" - ")[0]
            level = self.level_cb.currentText()[0]
            bai = self.bai_cb.currentText()
            dang = self.dang_cb.currentText()
            
            id6 = f"{grade_code}{subject_code}{chapter}{level}{bai}-{dang}"
            self.id6_preview_label.setText(f"ID6: {id6}")
        except:
            self.id6_preview_label.setText("ID6: -")
    
    def load_unassigned_questions(self):
        self.table.setRowCount(0)
        self.unassigned_questions = []
        
        cursor = self.backend.conn.execute("""
            SELECT id, content_tex, grade, subject, chapter, level, raw_data
            FROM questions
            WHERE id6 IS NULL OR id6 = 'UNKNOWN' OR id6 = ''
            ORDER BY id
        """)
        
        for row in cursor:
            q_id, content, grade, subject, chapter, level, raw = row
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            
            self.table.setItem(row_pos, 0, QTableWidgetItem(str(q_id)))
            preview = content[:50] + "..." if len(content) > 50 else content
            self.table.setItem(row_pos, 1, QTableWidgetItem(preview.replace("\\begin{ex}", "")))
            self.table.setItem(row_pos, 2, QTableWidgetItem(str(grade) if grade else "-"))
            self.table.setItem(row_pos, 3, QTableWidgetItem(subject if subject else "-"))
            self.table.setItem(row_pos, 4, QTableWidgetItem(str(chapter) if chapter else "-"))
            self.table.setItem(row_pos, 5, QTableWidgetItem(level if level else "-"))
            self.table.setItem(row_pos, 6, QTableWidgetItem("⚠️ Chưa gán"))
            
            self.unassigned_questions.append({'id': q_id, 'content': content, 'raw': raw, 'grade': grade, 'subject': subject, 'chapter': chapter, 'level': level})
        
        count = len(self.unassigned_questions)
        self.setWindowTitle(f"Gán ID6 cho câu hỏi ({count} câu chưa gán)")
    
    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        q_id = int(self.table.item(row, 0).text())
        question = next((q for q in self.unassigned_questions if q['id'] == q_id), None)
        if question:
            self.preview.setText(question['content'])
    
    def assign_current(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Lỗi", "Hãy chọn một câu hỏi!")
            return
        
        row = selected[0].row()
        q_id = int(self.table.item(row, 0).text())
        id6 = self.id6_preview_label.text().replace("ID6: ", "")
        if id6 == "-":
            return
        
        grade_code = id6[0]
        grade = int(grade_code) + 10
        subject = id6[1]
        match = re.search(r'\d+', id6[2:])
        chapter = int(match.group()) if match else 1
        level = re.search(r'[NHVC]', id6).group() if re.search(r'[NHVC]', id6) else 'N'
        bai = int(id6.split(level)[1].split('-')[0]) if level in id6 else 1
        dang = int(id6.split('-')[1]) if '-' in id6 else 1
        
        try:
            self.backend.conn.execute("""
                UPDATE questions
                SET id6=?, grade=?, subject=?, chapter=?, level=?, bai=?, dang=?
                WHERE id=?
            """, (id6, grade, subject, chapter, level, bai, dang, q_id))
            self.backend.conn.commit()
            
            self.table.setItem(row, 6, QTableWidgetItem("✅ Đã gán"))
            QMessageBox.information(self, "Thành công", f"Đã gán ID6: {id6}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi: {e}")
    
    def assign_all_same(self):
        id6 = self.id6_preview_label.text().replace("ID6: ", "")
        if id6 == "-":
            return
        
        reply = QMessageBox.question(self, "Xác nhận", f"Gán ID6: {id6} cho TẤT CẢ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        grade_code = id6[0]
        grade = int(grade_code) + 10
        subject = id6[1]
        match = re.search(r'\d+', id6[2:])
        chapter = int(match.group()) if match else 1
        level = re.search(r'[NHVC]', id6).group() if re.search(r'[NHVC]', id6) else 'N'
        bai = int(id6.split(level)[1].split('-')[0]) if level in id6 else 1
        dang = int(id6.split('-')[1]) if '-' in id6 else 1
        
        try:
            for q in self.unassigned_questions:
                self.backend.conn.execute("""
                    UPDATE questions
                    SET id6=?, grade=?, subject=?, chapter=?, level=?, bai=?, dang=?
                    WHERE id=?
                """, (id6, grade, subject, chapter, level, bai, dang, q['id']))
            self.backend.conn.commit()
            QMessageBox.information(self, "Thành công", f"Đã gán!")
            self.load_unassigned_questions()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))



# =============================================================================
# 6. MAIN APPLICATION
# =============================================================================
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.bk = Backend()
        self.ai = AIEngine()
        self.current_exam = []  # Đề hiện tại
        self.generated_exams = {}  # Các đề đã tạo bằng AI
        
        self.setWindowTitle("🎓 NGÂN HÀNG CÂU HỎI TOÁN - PHIÊN BẢN PRO")
        self.setGeometry(100, 100, 1400, 900)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addLayout(toolbar)
        
        # Main content
        self.stack = QTabWidget()
        self.stack.addTab(self.create_home_page(), "🏠 Trang chủ")
        self.stack.addTab(self.create_manual_exam_page(), "✏️ Tạo đề thủ công")
        self.stack.addTab(self.create_matrix_exam_page(), "🎲 Tạo đề theo ma trận")
        self.stack.addTab(self.create_ai_exam_page(), "🤖 Tạo đề bằng AI")
        
        layout.addWidget(self.stack)
        
        # Load stats
        self.load_stats()
    
    def create_toolbar(self):
        """Tạo thanh công cụ"""
        toolbar = QHBoxLayout()
        
        btn_import = QPushButton("📥 Nhập File TeX")
        btn_import.clicked.connect(self.import_files)
        btn_import.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
        
        btn_stats = QPushButton("📊 Thống kê")
        btn_stats.clicked.connect(self.show_stats)
        btn_stats.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px; font-weight: bold;")
        
        btn_export = QPushButton("💾 Xuất đề")
        btn_export.clicked.connect(self.export_exam)
        btn_export.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        
        toolbar.addWidget(btn_import)
        toolbar.addWidget(btn_stats)

        btn_assign_id6 = QPushButton("🏷️ Gán ID6")
        btn_assign_id6.clicked.connect(self.show_id6_assignment)
        btn_assign_id6.setStyleSheet("background-color: #f39c12; color: white; padding: 5px 15px; border-radius: 3px;")
        toolbar.addWidget(btn_assign_id6)
        
        toolbar.addStretch()
        toolbar.addWidget(btn_export)
        
        return toolbar
    
    def create_home_page(self):
        """Tạo trang chủ với kệ sách"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("📚 CHỌN LỚP ĐỂ BẮT ĐẦU")
        title_font = QFont("Arial", 24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Grade selection
        grade_layout = QHBoxLayout()
        grade_layout.addStretch()
        
        for grade in [10, 11, 12]:
            btn = QPushButton(f"📚\nLỚP {grade}")
            btn.setMinimumSize(250, 200)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#e74c3c' if grade == 10 else '#f39c12' if grade == 11 else '#3498db'};
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    border-radius: 15px;
                }}
                QPushButton:hover {{
                    background-color: {'#c0392b' if grade == 10 else '#e67e22' if grade == 11 else '#2980b9'};
                }}
            """)
            btn.clicked.connect(lambda checked, g=grade: self.select_grade(g))
            grade_layout.addWidget(btn)
        
        grade_layout.addStretch()
        layout.addLayout(grade_layout)
        
        # Stats preview
        self.stats_label = QLabel("Đang tải thống kê...")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        return widget
    
    def create_manual_exam_page(self):
        """Tạo trang tạo đề thủ công (drag & drop)"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left: Filter & Question bank
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Filter
        filter_group = QFrame()
        filter_group.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        filter_layout = QGridLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Dạng:"), 4, 0)
        self.manual_dang_cb = QComboBox()
        self.manual_dang_cb.addItem("Tất cả", 0)
        for d_id, d_name in DANH_MUC_DANG.items():
            self.manual_dang_cb.addItem(d_name, d_id)
        filter_layout.addWidget(self.manual_dang_cb, 4, 1)

        btn_filter = QPushButton("🔍 Lọc câu hỏi")
        btn_filter.clicked.connect(self.filter_questions)
        filter_layout.addWidget(btn_filter, 5, 0, 1, 2)
        
        filter_layout.addWidget(QLabel("Lớp:"), 0, 0)
        self.manual_grade_cb = QComboBox()
        self.manual_grade_cb.addItems(["Tất cả", "Lớp 10", "Lớp 11", "Lớp 12"])
        self.manual_grade_cb.currentTextChanged.connect(self.update_manual_filters)
        filter_layout.addWidget(self.manual_grade_cb, 0, 1)
        
        filter_layout.addWidget(QLabel("Môn:"), 1, 0)
        self.manual_subject_cb = QComboBox()
        self.manual_subject_cb.addItems(["Tất cả", "Đại số/Giải tích", "Hình học"])
        self.manual_subject_cb.currentTextChanged.connect(self.update_manual_filters)
        filter_layout.addWidget(self.manual_subject_cb, 1, 1)
        
        filter_layout.addWidget(QLabel("Chương:"), 2, 0)
        self.manual_chapter_cb = QComboBox()
        self.manual_chapter_cb.addItem("Tất cả")
        # KHÔNG connect signal để user có thể chọn tự do
        filter_layout.addWidget(self.manual_chapter_cb, 2, 1)
        
        filter_layout.addWidget(QLabel("Mức độ:"), 3, 0)
        self.manual_level_cb = QComboBox()
        self.manual_level_cb.addItems(["Tất cả", "Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao", "Toán thực tế"])
        # KHÔNG connect signal để user có thể chọn tự do
        filter_layout.addWidget(self.manual_level_cb, 3, 1)
        
        btn_filter = QPushButton("🔍 Lọc câu hỏi")
        btn_filter.clicked.connect(self.filter_questions)
        filter_layout.addWidget(btn_filter, 4, 0, 1, 2)
        
        left_layout.addWidget(QLabel("📋 BỘ LỌC CÂU HỎI"))
        left_layout.addWidget(filter_group)
        
        # Question bank
        left_layout.addWidget(QLabel("💾 NGÂN HÀNG CÂU HỎI (Kéo vào đề →)"))
        self.manual_question_list = DragDropListWidget()
        self.manual_question_list.itemClicked.connect(self.preview_question)
        left_layout.addWidget(self.manual_question_list)
        
        # Preview
        left_layout.addWidget(QLabel("👁️ XEM TRƯỚC"))
        self.manual_preview = QTextEdit()
        self.manual_preview.setReadOnly(True)
        self.manual_preview.setMaximumHeight(200)
        left_layout.addWidget(self.manual_preview)
        
        # Right: Exam composition
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        right_layout.addWidget(QLabel("📝 ĐỀ THI ĐANG SOẠN"))
        self.manual_exam_list = DropZoneListWidget()
        right_layout.addWidget(self.manual_exam_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("🗑️ Xóa tất cả")
        btn_clear.clicked.connect(lambda: self.manual_exam_list.clear())
        btn_remove = QPushButton("❌ Xóa câu đã chọn")
        btn_remove.clicked.connect(self.remove_selected_question)
        btn_save = QPushButton("💾 Lưu đề")
        btn_save.clicked.connect(self.save_manual_exam)
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_remove)
        btn_layout.addWidget(btn_save)
        right_layout.addLayout(btn_layout)
        
        # Add panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        return widget
    
    def create_matrix_exam_page(self):
        """Tạo trang tạo đề theo ma trận"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grade & Subject selection
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Lớp:"))
        self.matrix_grade_cb = QComboBox()
        self.matrix_grade_cb.addItems(["Lớp 10", "Lớp 11", "Lớp 12"])
        self.matrix_grade_cb.currentTextChanged.connect(self.update_matrix_chapters)
        select_layout.addWidget(self.matrix_grade_cb)
        
        select_layout.addWidget(QLabel("Môn:"))
        self.matrix_subject_cb = QComboBox()
        self.matrix_subject_cb.addItems(["Đại số/Giải tích", "Hình học"])
        self.matrix_subject_cb.currentTextChanged.connect(self.update_matrix_chapters)
        select_layout.addWidget(self.matrix_subject_cb)
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # Matrix table
        layout.addWidget(QLabel("📊 MA TRẬN ĐẶC TẢ (Số lượng câu hỏi theo chương và mức độ)"))
        self.matrix_table = QTableWidget()
        self.matrix_table.setColumnCount(6)
        self.matrix_table.setHorizontalHeaderLabels(["Chương", "NB", "TH", "VD", "VDC", "TT"])
        self.matrix_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.matrix_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_generate = QPushButton("🎲 TẠO ĐỀ NGẪU NHIÊN")
        btn_generate.clicked.connect(self.generate_matrix_exam)
        btn_generate.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 10px;")
        btn_layout.addWidget(btn_generate)
        layout.addLayout(btn_layout)
        
        # Result
        layout.addWidget(QLabel("📝 ĐỀ ĐÃ TẠO"))
        self.matrix_result_list = QListWidget()
        self.matrix_result_list.itemClicked.connect(self.preview_matrix_question)
        layout.addWidget(self.matrix_result_list)
        
        # Preview
        layout.addWidget(QLabel("👁️ XEM TRƯỚC"))
        self.matrix_preview = QTextEdit()
        self.matrix_preview.setReadOnly(True)
        self.matrix_preview.setMaximumHeight(200)
        layout.addWidget(self.matrix_preview)
        
        # Initialize
        self.update_matrix_chapters()
        
        return widget
    
    def create_ai_exam_page(self):
        """Tạo trang tạo đề bằng AI"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left: Base exam
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("📝 ĐỀ GỐC (Chọn từ đề thủ công hoặc ma trận)"))
        self.ai_base_list = QListWidget()
        left_layout.addWidget(self.ai_base_list)
        
        # Config
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Số đề cần tạo:"))
        self.ai_num_exams = QSpinBox()
        self.ai_num_exams.setRange(1, 50)
        self.ai_num_exams.setValue(3)
        config_layout.addWidget(self.ai_num_exams)
        
        config_layout.addWidget(QLabel("Mã đề bắt đầu:"))
        self.ai_start_code = QSpinBox()
        self.ai_start_code.setRange(100, 999)
        self.ai_start_code.setValue(101)
        config_layout.addWidget(self.ai_start_code)
        config_layout.addStretch()
        left_layout.addLayout(config_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("📂 Tải đề gốc")
        btn_load.clicked.connect(self.load_base_exam)
        btn_generate = QPushButton("🤖 TẠO ĐỀ BẰNG AI")
        btn_generate.clicked.connect(self.generate_ai_exams)
        btn_generate.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; padding: 10px;")
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_generate)
        left_layout.addLayout(btn_layout)
        
        # Right: Generated exams
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        right_layout.addWidget(QLabel("🎯 CÁC ĐỀ ĐÃ TẠO"))
        self.ai_exam_tree = QTreeWidget()
        self.ai_exam_tree.setHeaderHidden(True)
        self.ai_exam_tree.itemClicked.connect(self.preview_ai_question)
        right_layout.addWidget(self.ai_exam_tree)
        
        # Buttons for regeneration
        regen_layout = QHBoxLayout()
        btn_regen = QPushButton("♻️ Tạo lại câu này")
        btn_regen.clicked.connect(self.regenerate_question)
        regen_layout.addWidget(btn_regen)
        right_layout.addLayout(regen_layout)
        
        # Preview
        right_layout.addWidget(QLabel("👁️ XEM TRƯỚC & CHỈNH SỬA"))
        self.ai_preview = QTextEdit()
        self.ai_preview.setMaximumHeight(250)
        right_layout.addWidget(self.ai_preview)
        
        # Add panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        return widget
    
    # =========================================================================
    # HOME PAGE FUNCTIONS
    # =========================================================================
    def select_grade(self, grade):
        """Chọn lớp và chuyển tab"""
        self.matrix_grade_cb.setCurrentText(f"Lớp {grade}")
        self.stack.setCurrentIndex(2)  # Chuyển đến tab ma trận
    
    def load_stats(self):
        """Load thống kê"""
        try:
            stats = self.bk.get_stats()
            total = 0
            for grade_data in stats.values():
                for subject_data in grade_data.values():
                    for chapter_data in subject_data.values():
                        total += sum(chapter_data.values())
            
            self.stats_label.setText(f"💾 Tổng số câu hỏi trong ngân hàng: {total} câu")
        except:
            self.stats_label.setText("⚠️ Chưa có dữ liệu")
    
    
    def show_id6_assignment(self):
        """Hiển thị dialog gán ID6"""
        dialog = ID6AssignDialog(self.bk, self)
        dialog.exec()
        self.load_stats()

    def show_stats(self):
        """Hiển thị thống kê chi tiết"""
        stats = self.bk.get_stats()
        msg = "📊 THỐNG KÊ NGÂN HÀNG CÂU HỎI\n\n"
        
        for grade in [10, 11, 12]:
            msg += f"{'='*50}\n"
            msg += f"LỚP {grade}\n"
            msg += f"{'='*50}\n"
            
            for subject_code, subject_name in [('D', 'Đại số/Giải tích'), ('H', 'Hình học')]:
                if subject_code in stats[grade]:
                    msg += f"\n📖 {subject_name}:\n"
                    for ch, levels in sorted(stats[grade][subject_code].items()):
                        ch_name = (CHUONG_DAI_SO if subject_code == 'D' else CHUONG_HINH_HOC).get(grade, {}).get(int(ch), f"Chương {ch}")
                        total_ch = sum(levels.values())
                        msg += f"  Chương {ch} ({ch_name}): {total_ch} câu\n"
                        for lv, cnt in sorted(levels.items()):
                            msg += f"    - {MUC_DO.get(lv, lv)}: {cnt} câu\n"
        
        QMessageBox.information(self, "Thống kê", msg)
    
    # =========================================================================
    # MANUAL EXAM FUNCTIONS
    # =========================================================================
    def update_manual_filters(self, _=None):
        """Cập nhật filter khi thay đổi lớp/môn"""
        grade_text = self.manual_grade_cb.currentText()
        subject_text = self.manual_subject_cb.currentText()
        
        # Lưu giá trị hiện tại của chapter trước khi clear
        current_chapter = self.manual_chapter_cb.currentText()
        
        # Block signals CHỈ khi update
        self.manual_chapter_cb.blockSignals(True)
        
        # Cập nhật danh sách chương
        self.manual_chapter_cb.clear()
        self.manual_chapter_cb.addItem("Tất cả")
        
        if grade_text != "Tất cả" and subject_text != "Tất cả":
            grade = int(grade_text.split()[-1])
            subject_code = 'D' if 'Đại' in subject_text else 'H'
            chapters = CHUONG_DAI_SO if subject_code == 'D' else CHUONG_HINH_HOC
            
            if grade in chapters:
                for ch_num, ch_name in chapters[grade].items():
                    self.manual_chapter_cb.addItem(f"Chương {ch_num}: {ch_name}")
        
        # Thử restore giá trị cũ nếu còn tồn tại
        idx = self.manual_chapter_cb.findText(current_chapter)
        if idx >= 0:
            self.manual_chapter_cb.setCurrentIndex(idx)
        
        # Unblock signals - giờ user có thể chọn tự do
        self.manual_chapter_cb.blockSignals(False)
    
    def filter_questions(self):
        """Lọc và hiển thị câu hỏi"""
        self.manual_question_list.clear()
        
        # Parse filter
        grade = None
        subject = None
        chapter = None
        level = None
        
        grade_text = self.manual_grade_cb.currentText()
        if grade_text != "Tất cả":
            grade = int(grade_text.split()[-1])
        
        subject_text = self.manual_subject_cb.currentText()
        if subject_text != "Tất cả":
            subject = 'D' if 'Đại' in subject_text else 'H'
        
        chapter_text = self.manual_chapter_cb.currentText()
        if chapter_text != "Tất cả":
            chapter = int(chapter_text.split()[1].rstrip(':'))
        
        level_text = self.manual_level_cb.currentText()
        if level_text != "Tất cả":
            level_map = {'Nhận biết': 'N', 'Thông hiểu': 'H', 'Vận dụng': 'V', 'Vận dụng cao': 'C', 'Toán thực tế': 'T'}
            level = level_map.get(level_text)
        
        dang = None
        if self.manual_dang_cb.currentData() is not None:
            dang_val = self.manual_dang_cb.currentData()
            dang = dang_val if dang_val != 0 else None
        
        questions = self.bk.get_all_filtered(grade, subject, chapter, level, dang=dang, limit=100)
        
        # Hiển thị (thêm thông tin dạng)
        for q in questions:
            dang_name = DANH_MUC_DANG.get(q['dang'], "Không xác định")
            display = f"[L{q['grade']}-{q['subject']}{q['chapter']}-{q['level']}] [{dang_name[:3]}] ID:{q['id']}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, q)
            self.manual_question_list.addItem(item)
            
        # Query
        questions = self.bk.get_all_filtered(grade, subject, chapter, level, limit=100)
        
        # Display
        for q in questions:
            display = f"[L{q['grade']}-{q['subject']}{q['chapter']}-{q['level']}] ID:{q['id']}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, q)
            self.manual_question_list.addItem(item)
        
        QMessageBox.information(self, "Kết quả", f"Tìm thấy {len(questions)} câu hỏi")
    
    def preview_question(self, item):
        """Xem trước câu hỏi"""
        q = item.data(Qt.ItemDataRole.UserRole)
        if q:
            self.manual_preview.setText(q['content_tex'])
    
    def remove_selected_question(self):
        """Xóa câu đã chọn trong đề"""
        current_row = self.manual_exam_list.currentRow()
        if current_row >= 0:
            self.manual_exam_list.takeItem(current_row)
            # Cập nhật lại số thứ tự
            for i in range(self.manual_exam_list.count()):
                item = self.manual_exam_list.item(i)
                q_data = item.data(Qt.ItemDataRole.UserRole)
                item.setText(f"Câu {i+1}: {q_data['display']}")
    
    def save_manual_exam(self):
        """Lưu đề thủ công"""
        if self.manual_exam_list.count() == 0:
            QMessageBox.warning(self, "Lỗi", "Đề thi trống!")
            return
        
        self.current_exam = []
        for i in range(self.manual_exam_list.count()):
            item = self.manual_exam_list.item(i)
            q_data = item.data(Qt.ItemDataRole.UserRole)
            self.current_exam.append({
                'id': q_data['id'],
                'content': q_data['content'],
                'display': q_data['display']
            })
        
        QMessageBox.information(self, "Thành công", f"Đã lưu đề với {len(self.current_exam)} câu hỏi!")
    
    # =========================================================================
    # MATRIX EXAM FUNCTIONS
    # =========================================================================
    def update_matrix_chapters(self, _=None):
        """Cập nhật bảng ma trận theo lớp/môn"""
        grade_text = self.matrix_grade_cb.currentText()
        subject_text = self.matrix_subject_cb.currentText()
        
        grade = int(grade_text.split()[-1])
        subject_code = 'D' if 'Đại' in subject_text else 'H'
        chapters = CHUONG_DAI_SO if subject_code == 'D' else CHUONG_HINH_HOC
        
        if grade in chapters:
            # Block signals để tránh trigger không cần thiết
            self.matrix_table.blockSignals(True)
            
            self.matrix_table.setRowCount(len(chapters[grade]))
            for row, (ch_num, ch_name) in enumerate(chapters[grade].items()):
                # Tên chương
                item = QTableWidgetItem(f"C{ch_num}: {ch_name}")
                item.setData(Qt.ItemDataRole.UserRole, ch_num)
                self.matrix_table.setItem(row, 0, item)
                
                # Các ô nhập số lượng
                for col in range(1, 6):
                    spin = QSpinBox()
                    spin.setRange(0, 20)
                    spin.setValue(0)
                    self.matrix_table.setCellWidget(row, col, spin)
            
            # Unblock signals
            self.matrix_table.blockSignals(False)
    
    def generate_matrix_exam(self):
        """Tạo đề theo ma trận"""
        grade_text = self.matrix_grade_cb.currentText()
        subject_text = self.matrix_subject_cb.currentText()
        
        grade = int(grade_text.split()[-1])
        subject_code = 'D' if 'Đại' in subject_text else 'H'
        
        self.current_exam = []
        self.matrix_result_list.clear()
        
        level_map = ['N', 'H', 'V', 'C', 'T']
        
        for row in range(self.matrix_table.rowCount()):
            ch_num = self.matrix_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            for col in range(1, 6):
                count = self.matrix_table.cellWidget(row, col).value()
                level = level_map[col - 1]
                
                for _ in range(count):
                    q = self.bk.get_rnd(grade, subject_code, ch_num, level)
                    if q:
                        self.current_exam.append(q)
                        display = f"[C{ch_num}-{MUC_DO[level]}]"
                        item = QListWidgetItem(f"Câu {len(self.current_exam)}: {display}")
                        item.setData(Qt.ItemDataRole.UserRole, q)
                        self.matrix_result_list.addItem(item)
        
        if len(self.current_exam) > 0:
            QMessageBox.information(self, "Thành công", f"Đã tạo đề với {len(self.current_exam)} câu hỏi!")
        else:
            QMessageBox.warning(self, "Lỗi", "Không đủ câu hỏi trong ngân hàng!")
    
    def preview_matrix_question(self, item):
        """Xem trước câu hỏi từ ma trận"""
        q = item.data(Qt.ItemDataRole.UserRole)
        if q:
            self.matrix_preview.setText(q['content_tex'])
    
    # =========================================================================
    # AI EXAM FUNCTIONS
    # =========================================================================
    def load_base_exam(self):
        """Load đề gốc"""
        if len(self.current_exam) == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa có đề gốc! Hãy tạo đề ở tab 'Tạo đề thủ công' hoặc 'Tạo đề theo ma trận'")
            return
        
        self.ai_base_list.clear()
        for idx, q in enumerate(self.current_exam):
            display = q.get('display', f"ID:{q['id']}")
            item = QListWidgetItem(f"Câu {idx+1}: {display}")
            item.setData(Qt.ItemDataRole.UserRole, q)
            self.ai_base_list.addItem(item)
        
        QMessageBox.information(self, "Thành công", f"Đã load {len(self.current_exam)} câu hỏi!")
    
    def generate_ai_exams(self):
        """Tạo nhiều đề bằng AI"""
        if self.ai_base_list.count() == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa load đề gốc!")
            return
        
        if not self.ai.is_ready:
            QMessageBox.warning(self, "Lỗi", "AI chưa sẵn sàng!")
            return
        
        # Progress dialog
        self.pd = QProgressDialog("Đang tạo đề bằng AI...", "Hủy", 0, 100, self)
        self.pd.setWindowModality(Qt.WindowModality.WindowModal)
        
        # Get base questions
        base_qs = []
        for i in range(self.ai_base_list.count()):
            item = self.ai_base_list.item(i)
            q = item.data(Qt.ItemDataRole.UserRole)
            base_qs.append({'id': q['id'], 'content': q['content_tex']})
        
        # Start worker
        self.wk = BatchAIWorker(
            self.ai,
            base_qs,
            self.ai_num_exams.value(),
            self.ai_start_code.value()
        )
        
        self.wk.progress.connect(lambda v, m: (self.pd.setValue(v), self.pd.setLabelText(m)))
        self.wk.finished.connect(self.on_ai_exams_done)
        self.wk.start()
    
    def on_ai_exams_done(self, results):
        """Xử lý kết quả AI"""
        self.pd.close()
        self.generated_exams = results
        self.ai_exam_tree.clear()
        
        for code, questions in results.items():
            root = QTreeWidgetItem([f"📝 Đề {code}"])
            root.setData(0, Qt.ItemDataRole.UserRole, {'type': 'exam', 'code': code})
            
            for q in questions:
                child = QTreeWidgetItem([f"Câu {q['idx']}"])
                child.setData(0, Qt.ItemDataRole.UserRole, {'type': 'question', 'code': code, 'idx': q['idx']-1})
                root.addChild(child)
            
            self.ai_exam_tree.addTopLevelItem(root)
        
        self.ai_exam_tree.expandAll()
        QMessageBox.information(self, "Thành công", f"Đã tạo {len(results)} đề!")
    
    def preview_ai_question(self, item):
        """Xem trước câu hỏi AI"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data['type'] == 'question':
            code = data['code']
            idx = data['idx']
            q = self.generated_exams[code][idx]
            self.ai_preview.setText(f"{q['content']}\n\n[ĐÁP ÁN: {q['key']}]")
    
    def regenerate_question(self):
        """Tạo lại câu hỏi"""
        item = self.ai_exam_tree.currentItem()
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data['type'] != 'question':
            QMessageBox.warning(self, "Lỗi", "Hãy chọn một câu hỏi!")
            return
        
        code = data['code']
        idx = data['idx']
        q = self.generated_exams[code][idx]
        
        # Tìm câu gốc
        orig = None
        for base_q in self.current_exam:
            if base_q['id'] == q['orig_id']:
                orig = base_q['content_tex']
                break
        
        if not orig:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy câu gốc!")
            return
        
        # Regenerate
        self.rg = SingleRegenWorker(self.ai, orig)
        self.rg.done.connect(lambda nc, nk: self.on_regen_done(code, idx, nc, nk))
        self.rg.start()
    
    def on_regen_done(self, code, idx, new_content, new_key):
        """Callback khi tạo lại xong"""
        self.generated_exams[code][idx]['content'] = new_content
        self.generated_exams[code][idx]['key'] = new_key
        self.ai_preview.setText(f"{new_content}\n\n[ĐÁP ÁN: {new_key}]")
        QMessageBox.information(self, "Thành công", "Đã tạo lại câu hỏi!")
    
    # =========================================================================
    # COMMON FUNCTIONS
    # =========================================================================
    def import_files(self):
        """Import file TeX"""
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn file TeX", "", "TeX Files (*.tex)")
        if files:
            total = 0
            for f in files:
                total += self.bk.import_tex(f)
            QMessageBox.information(self, "Thành công", f"Đã import {total} câu hỏi!")
            self.load_stats()
    
    def export_exam(self):
        """Xuất đề thi"""
        # Chọn nguồn xuất
        msg = QMessageBox()
        msg.setWindowTitle("Xuất đề")
        msg.setText("Chọn loại đề cần xuất:")
        btn_manual = msg.addButton("Đề thủ công/Ma trận", QMessageBox.ButtonRole.ActionRole)
        btn_ai = msg.addButton("Các đề AI", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        
        if msg.clickedButton() == btn_manual:
            self.export_manual_exam()
        elif msg.clickedButton() == btn_ai:
            self.export_ai_exams()
    
    def export_manual_exam(self):
        """Xuất đề thủ công"""
        if len(self.current_exam) == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa có đề để xuất!")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Lưu đề", "De_Thi.tex", "TeX Files (*.tex)")
        if not path:
            return
        
        try:
            content = []
            content.append("\\begin{center}\\textbf{ĐỀ THI}\\end{center}")
            
            for idx, q in enumerate(self.current_exam):
                content.append(f"% Câu {idx+1}\n{q['content_tex']}")
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(LATEX_TEMPLATE + "\n".join(content) + "\n\\end{document}")
            
            QMessageBox.information(self, "Thành công", f"Đã xuất đề: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi xuất: {e}")
    
    def export_ai_exams(self):
        """Xuất các đề AI"""
        if len(self.generated_exams) == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa có đề AI để xuất!")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Lưu các đề", "De_AI.tex", "TeX Files (*.tex)")
        if not path:
            return
        
        try:
            fc = []
            xls = []
            
            for code, qs in self.generated_exams.items():
                bd = [f"\\begin{{center}}\\textbf{{MÃ ĐỀ: {code}}}\\end{{center}}"]
                rd = {'Mã đề': code}
                
                for q in qs:
                    content = q['content']
                    if not content.strip().startswith("\\begin{ex}"):
                        content = f"\\begin{{ex}}\n{content}\n\\end{{ex}}"
                    
                    bd.append(f"% Câu {q['idx']}\n{content}")
                    rd[str(q['idx'])] = q['key']
                
                fc.append("\n".join(bd))
                fc.append("\\newpage")
                xls.append(rd)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(LATEX_TEMPLATE + "\n".join(fc) + "\n\\end{document}")
            
            pd.DataFrame(xls).to_excel(path.replace(".tex", ".xlsx"), index=False)
            
            QMessageBox.information(self, "Thành công", f"Đã xuất:\n- {path}\n- {path.replace('.tex', '.xlsx')}")
        
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi xuất: {e}")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)