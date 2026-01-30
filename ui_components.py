import os
import json
import re
import requests
import urllib.parse
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QRadioButton, QButtonGroup,
                             QGroupBox, QApplication, QWidget, QCheckBox, QProgressBar,
                             QAbstractItemView, QTimeEdit, QSizePolicy, QDialogButtonBox,
                             QListWidget, QTextEdit, QComboBox, QTableWidget, QSpinBox,
                             QTabWidget, QHeaderView, QProgressDialog, QTreeWidget,
                             QTreeWidgetItem, QSplitter, QTableWidgetItem, QScrollArea,
                             QFrame, QGridLayout, QMenu, QListWidgetItem, QFileDialog)
from PyQt6.QtGui import QDrag, QFont, QIcon, QColor, QAction, QBrush, QPixmap, QPainter, QPen, QCursor
from PyQt6.QtCore import Qt, QMimeData, QPoint, QSize, QTimer, QTime, pyqtSignal

from config import (
    API_URL, APP_VERSION, BANK_ID, BANK_ACCOUNT, BANK_NAME, PRICE_YEAR, PRICE_LIFE,
    DATA_ID6_2025, DANH_MUC_DANG, CHAPTER_NAMES, DB_PATH
)
from utils import get_hwid, open_file_or_url, SchedulerManager
from workers import (
    AutoIDWorker, CleanerWorker, AutoPostWorker, AutoFormWorker, WebServerThread
)
from database import DatabaseManager
from integrations import GoogleManagerFull

# =============================================================================
# WIDGETS
# =============================================================================

class ModernSidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setStyleSheet("""
            QWidget { background-color: #fdfdfd; border-right: 1px solid #e0e0e0; }
            QPushButton {
                text-align: left; padding: 12px 20px; border: none; border-radius: 8px;
                background-color: transparent; color: #555; font-weight: 600; font-size: 15px; margin: 4px 12px;
            }
            QPushButton:hover { background-color: #f5f6fa; color: #2c3e50; }
            QPushButton:checked { background-color: #ED840D; color: white; font-weight: bold; }
            QLabel { color: #95a5a6; font-weight: bold; font-size: 11px; margin-top: 25px; margin-left: 20px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 25, 0, 25)
        layout.setSpacing(6)

        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(25, 0, 20, 20)
        lbl_logo = QLabel("🏛️ BANKAI PRO")
        lbl_logo.setStyleSheet("font-size: 24px; font-weight: 900; color: #d35400; margin: 0; letter-spacing: -0.5px;")
        logo_layout.addWidget(lbl_logo)
        layout.addLayout(logo_layout)

        self.btn_group = QButtonGroup()
        self.btn_group.setExclusive(True)

        self.add_label(layout, "Trung tâm điều khiển")
        self.btn_dashboard = self.add_btn(layout, "🏠  Trang chủ / Thống kê", 0)

        self.add_label(layout, "Ngân hàng câu hỏi")
        self.btn_manual = self.add_btn(layout, "✏️  Soạn đề Thủ công", 1)
        self.btn_matrix = self.add_btn(layout, "🎲  Ma trận 2025 (Auto)", 2)
        self.btn_ai = self.add_btn(layout, "🤖  AI Generator", 3)

        layout.addStretch()
        self.add_label(layout, "Hệ thống")

    def add_label(self, layout, text):
        lbl = QLabel(text)
        layout.addWidget(lbl)

    def add_btn(self, layout, text, id):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_group.addButton(btn, id)
        layout.addWidget(btn)
        return btn

class DragDropListWidget(QListWidget):
    def __init__(self, p=None):
        super().__init__(p)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)

    def startDrag(self, actions):
        i = self.currentItem()
        if not i: return
        q_data = i.data(Qt.ItemDataRole.UserRole)
        if not q_data: return

        content_val = q_data.get('content_tex') or q_data.get('content') or ""
        d = {
            'id': q_data.get('id', 0),
            'content_tex': content_val,
            'content': content_val,
            'dang': q_data.get('dang', 4),
            'level': q_data.get('level', ''),
            'grade': q_data.get('grade', 12),
            'subject': q_data.get('subject', 'D'),
            'chapter': q_data.get('chapter', 1),
            'bai': q_data.get('bai', 1),
            'display': f"[ID:{q_data.get('id')}]"
        }
        mime = QMimeData(); mime.setText(json.dumps(d))
        drag = QDrag(self); drag.setMimeData(mime); drag.exec(Qt.DropAction.CopyAction)

class DropZoneTreeWidget(QTreeWidget):
    items_changed = pyqtSignal()

    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.bk = backend
        self.setAcceptDrops(True)
        self.setHeaderHidden(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

        self.roots = {}
        labels = {
            1: "🟢 PHẦN I: TRẮC NGHIỆM (4 Lựa chọn)",
            2: "🔵 PHẦN II: ĐÚNG / SAI",
            3: "🟠 PHẦN III: TRẢ LỜI NGẮN",
            4: "🟣 TỰ LUẬN / KHÁC"
        }
        font_root = QFont(); font_root.setBold(True); font_root.setPointSize(13)
        for k, v in labels.items():
            root = QTreeWidgetItem([v])
            root.setExpanded(True)
            root.setFont(0, font_root)
            root.setData(0, Qt.ItemDataRole.UserRole, {"type": "root", "dang": k})
            root.setBackground(0, QColor("#f0f0f0"))
            self.addTopLevelItem(root)
            self.roots[k] = root

    def dragEnterEvent(self, e): e.accept() if e.mimeData().hasText() else e.ignore()
    def dragMoveEvent(self, e): e.accept() if e.mimeData().hasText() else e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasText():
            try:
                d = json.loads(e.mimeData().text())
                dang = d.get('dang', 4)
                root = self.roots.get(dang, self.roots[4])
                content_preview = d.get('content_tex', '')[:60].replace("\n", " ")
                txt = f"[ID:{d['id']}] {d.get('level','?')} | {content_preview}..."
                item = QTreeWidgetItem([txt])
                item.setData(0, Qt.ItemDataRole.UserRole, d)
                item.setToolTip(0, d.get('content_tex', ''))
                root.addChild(item)
                root.setExpanded(True)
                e.accept()
                self.items_changed.emit()
            except Exception as err:
                print(f"Lỗi Drop: {err}")
                e.ignore()
        else: e.ignore()

    def open_menu(self, position):
        item = self.itemAt(position)
        if not item or item.parent() is None: return
        menu = QMenu()
        act_replace = menu.addAction("🔄 Đổi câu khác (Tương đương)")
        act_del = menu.addAction("🗑️ Xóa câu này")
        action = menu.exec(self.viewport().mapToGlobal(position))
        if action == act_del:
            item.parent().removeChild(item)
            self.items_changed.emit()
        elif action == act_replace:
            self.replace_question(item)

    def replace_question(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        new_q = self.bk.get_rnd(
            data['grade'], data['subject'], data['chapter'],
            data['bai'], data['level'], data['dang'],
            exc=data['id']
        )
        if new_q:
            new_data = {
                'id': new_q['id'], 'content_tex': new_q['content_tex'],
                'dang': new_q['dang'], 'level': new_q['level'],
                'grade': new_q['grade'], 'subject': new_q['subject'],
                'chapter': new_q['chapter'], 'bai': new_q['bai']
            }
            content_preview = new_q['content_tex'][:60].replace("\n", " ")
            item.setText(0, f"[ID:{new_q['id']}] {new_q['level']} | {content_preview}...")
            item.setData(0, Qt.ItemDataRole.UserRole, new_data)
            item.setToolTip(0, new_q['content_tex'])
        else:
            QMessageBox.warning(self, "Không tìm thấy", "Không còn câu hỏi nào khác tương đương!")

    def get_all_questions(self):
        qs = []
        for i in range(self.topLevelItemCount()):
            root = self.topLevelItem(i)
            for j in range(root.childCount()):
                child = root.child(j)
                qs.append(child.data(0, Qt.ItemDataRole.UserRole))
        return qs

    def clear_all(self):
        for i in range(self.topLevelItemCount()):
            root = self.topLevelItem(i)
            root.takeChildren()
        self.items_changed.emit()

class WatermarkWidget(QWidget):
    def __init__(self, text="BANKAI PRO", parent=None):
        super().__init__(parent)
        self.text = text
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#602C04"))
        painter.setOpacity(0.05)
        font_size = min(self.width(), self.height()) // 10
        font = QFont(".AppleSystemUIFont", font_size, QFont.Weight.Black)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        cx = self.width() / 2
        cy = self.height() / 2
        painter.translate(cx, cy)
        painter.rotate(-30)
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self.text)
        text_h = fm.height()
        painter.drawText(int(-text_w/2), int(text_h/4), self.text)

# =============================================================================
# DIALOGS
# =============================================================================

class ActivationDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mua bản quyền & Kích hoạt BankAI Pro")
        self.setModal(True)
        self.setFixedSize(750, 450)
        self.is_verified = False
        self.hwid = get_hwid()

        main_layout = QHBoxLayout(self)

        left_panel = QGroupBox("1. Mua bản quyền (Quét mã QR)")
        left_layout = QVBoxLayout(left_panel)

        self.rb_year = QRadioButton(f"Gói 1 Năm ({PRICE_YEAR:,} đ)")
        self.rb_life = QRadioButton(f"Gói Vĩnh Viễn ({PRICE_LIFE:,} đ)")
        self.rb_life.setChecked(True)

        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.rb_year)
        self.btn_group.addButton(self.rb_life)

        left_layout.addWidget(QLabel("Chọn gói phần mềm:"))
        left_layout.addWidget(self.rb_year)
        left_layout.addWidget(self.rb_life)

        left_layout.addWidget(QLabel("Nhập Email của bạn (để nhận Key):"))
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("vidu@gmail.com")
        left_layout.addWidget(self.txt_email)

        btn_get_qr = QPushButton("Hiển thị mã QR Thanh toán")
        btn_get_qr.setProperty("class", "btn-primary")
        btn_get_qr.clicked.connect(self.generate_qr)
        left_layout.addWidget(btn_get_qr)

        self.lbl_qr_img = QLabel()
        self.lbl_qr_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_qr_img.setStyleSheet("border: 1px dashed #aaa; background: #f9f9f9;")
        self.lbl_qr_img.setMinimumHeight(200)
        self.lbl_qr_img.setText("Vui lòng nhập Email\nvà bấm nút để lấy mã QR")
        left_layout.addWidget(self.lbl_qr_img)

        main_layout.addWidget(left_panel, 1)

        right_panel = QGroupBox("2. Nhập mã kích hoạt")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        right_layout.addWidget(QLabel("Mã máy (HWID):"))
        txt_hwid = QLineEdit(self.hwid)
        txt_hwid.setReadOnly(True)
        txt_hwid.setStyleSheet("background: #eee; color: #555;")
        right_layout.addWidget(txt_hwid)

        right_layout.addSpacing(20)

        right_layout.addWidget(QLabel("Nhập License Key (Kiểm tra Email):"))
        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("BANKAI-XXXX-XXXX-XXXX")
        self.txt_key.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
        right_layout.addWidget(self.txt_key)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        right_layout.addWidget(self.lbl_status)

        right_layout.addSpacing(10)

        btn_active = QPushButton("Kích hoạt ngay")
        btn_active.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_active.setStyleSheet("background-color: #27ae60; color: white; padding: 12px; font-weight: bold; font-size: 16px;")
        btn_active.clicked.connect(self.check_online)
        right_layout.addWidget(btn_active)

        right_layout.addStretch()
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.reject)
        right_layout.addWidget(btn_close)

        main_layout.addWidget(right_panel, 1)

    def generate_qr(self):
        email = self.txt_email.text().strip()
        if not email or "@" not in email:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Email chính xác để nhận Key!")
            return
        amount = PRICE_LIFE if self.rb_life.isChecked() else PRICE_YEAR
        safe_email = email.replace("@", "AT").replace(".", "DOT").upper()
        content = f"BANKAI {safe_email}"
        encoded_content = urllib.parse.quote(content)
        encoded_name = urllib.parse.quote(BANK_NAME)
        qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{BANK_ACCOUNT}-print.png?amount={amount}&addInfo={encoded_content}&accountName={encoded_name}"

        self.lbl_qr_img.setText("Đang tải mã QR...")
        QApplication.processEvents()

        try:
            data = requests.get(qr_url).content
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.lbl_qr_img.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            self.lbl_qr_img.setText(f"Lỗi tải QR: {str(e)}")

    def check_online(self):
        key = self.txt_key.text().strip()
        if not key:
            self.lbl_status.setStyleSheet("color: red;")
            self.lbl_status.setText("Vui lòng nhập Key!")
            return

        self.lbl_status.setStyleSheet("color: blue;")
        self.lbl_status.setText("Đang kết nối Server kiểm tra...")
        self.txt_key.setEnabled(False)
        QApplication.processEvents()

        try:
            payload = {"key": key, "hwid": self.hwid, "action": "activate", "version": APP_VERSION}
            response = requests.post(API_URL, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    QMessageBox.information(self, "Thành công", "Kích hoạt bản quyền thành công!\nCảm ơn bạn đã sử dụng dịch vụ.")
                    self.save_license(key)
                    self.is_verified = True
                    self.accept()
                else:
                    self.lbl_status.setStyleSheet("color: red;")
                    self.lbl_status.setText(f"Lỗi: {result.get('message')}")
                    self.txt_key.setEnabled(True)
            else:
                self.lbl_status.setText(f"Lỗi mạng: HTTP {response.status_code}")
                self.txt_key.setEnabled(True)

        except Exception as e:
            self.lbl_status.setText(f"Không thể kết nối Server: {str(e)}")
            self.txt_key.setEnabled(True)

    def save_license(self, key):
        data = {"key": key, "hwid": self.hwid}
        save_path = os.path.join(os.path.expanduser("~"), ".bankai_license")
        with open(save_path, "w") as f:
            json.dump(data, f)

class ClassroomControlPanel(QDialog):
    def __init__(self, parent=None, callback_exam=None, callback_homework=None):
        super().__init__(parent)
        self.callback_exam = callback_exam
        self.callback_homework = callback_homework
        self.setWindowTitle("Trung tâm Google Classroom")
        self.setFixedSize(700, 450)
        self.setStyleSheet("""
            QDialog { background-color: #fdfdfd; }
            QPushButton {
                border-radius: 12px; font-weight: bold; font-size: 16px; padding: 15px; border: 2px solid #ddd;
            }
            QPushButton:hover { background-color: #f0f8ff; border-color: #3498db; }
            QLabel { color: #555; font-size: 14px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header = QLabel("CHỌN CHẾ ĐỘ TƯƠNG TÁC CLASSROOM")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 20px; font-weight: 900; color: #2c3e50;")
        layout.addWidget(header)

        grid = QHBoxLayout()
        grid.setSpacing(20)

        btn_hw = QPushButton("📝  GIAO BÀI TẬP (PDF)\n\n(Tạo bài tập tĩnh, nộp file)")
        btn_hw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn_hw.setStyleSheet("background-color: #e8f6f3; color: #16a085;")
        btn_hw.clicked.connect(self.on_homework)
        grid.addWidget(btn_hw)

        btn_exam = QPushButton("🌍  TỔ CHỨC THI ONLINE\n\n(Chấm điểm tự động, realtime)")
        btn_exam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn_exam.setStyleSheet("background-color: #fef5e7; color: #d35400;")
        btn_exam.clicked.connect(self.on_exam)
        grid.addWidget(btn_exam)

        layout.addLayout(grid)

        desc = QLabel("• <b>Giao bài tập:</b> Hệ thống sẽ biên dịch đề thành PDF và đăng lên Classroom.\n"
                      "• <b>Thi Online:</b> Hệ thống tạo phòng thi ảo, học sinh làm bài trên web và đồng bộ điểm.")
        desc.setWordWrap(True)
        desc.setStyleSheet("background: #f9f9f9; padding: 15px; border-radius: 8px;")
        layout.addWidget(desc)

    def on_homework(self):
        self.accept()
        if self.callback_homework: self.callback_homework()

    def on_exam(self):
        self.accept()
        if self.callback_exam: self.callback_exam()

class ID6AssignDialog(QDialog):
    def __init__(self, backend, parent=None, mode='db', data_list=None):
        super().__init__(parent)
        self.backend = backend
        self.mode = mode
        self.local_data = data_list if data_list else []
        self.qs = []
        self.keep_form_state = False

        if self.mode == 'local':
            self.setWindowTitle("⚠️ BỔ SUNG ID6 CÒN THIẾU")
            self.setStyleSheet("QDialog { background-color: #fff8e1; }")
        else:
            self.setWindowTitle("Công cụ Gán ID6 (Database)")

        self.setMinimumSize(1200, 750)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        l = QVBoxLayout(self)

        header_text = "CÔNG CỤ CHUẨN HÓA DỮ LIỆU CÂU HỎI (ID6)"
        if self.mode == 'local': header_text = "⚠️ DANH SÁCH CÂU HỎI THIẾU ID TRONG FILE"
        l.addWidget(QLabel(header_text, alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="font-size: 20px; font-weight: bold; color: #d35400;"))

        spl = QSplitter(Qt.Orientation.Horizontal)

        lw = QWidget(); ll = QVBoxLayout(lw)
        self.tb = QTableWidget(0, 5)
        self.tb.setHorizontalHeaderLabels(["ID", "Preview", "Lớp", "Môn", "Trạng thái"])
        self.tb.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tb.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tb.itemSelectionChanged.connect(self.on_sel)
        ll.addWidget(self.tb)
        spl.addWidget(lw)

        rw = QWidget(); rl = QVBoxLayout(rw)
        self.prev = QTextEdit(); self.prev.setMaximumHeight(200); self.prev.setReadOnly(True)
        rl.addWidget(QLabel("Nội dung Preview:")); rl.addWidget(self.prev)

        grp = QGroupBox("Thông tin định danh (Bộ lọc ID)")
        gl = QGridLayout(grp)

        self.cb_g = QComboBox(); self.cb_g.addItems(["10","11","12"])
        self.cb_g.currentTextChanged.connect(self.upd_ch)
        self.cb_s = QComboBox(); self.cb_s.addItems(["D - Đại số","H - Hình học"])
        self.cb_s.currentTextChanged.connect(self.upd_ch)
        self.cb_c = QComboBox(); self.cb_c.currentIndexChanged.connect(self.upd_bai)
        self.cb_l = QComboBox(); self.cb_l.addItems(["N - NB","H - TH","V - VD","C - VDC"])
        self.cb_l.currentTextChanged.connect(self.upd_prev)
        self.cb_b = QComboBox(); self.cb_b.currentIndexChanged.connect(self.upd_prev)
        self.cb_d = QComboBox()
        for k,v in DANH_MUC_DANG.items(): self.cb_d.addItem(v, k)
        self.cb_d.currentIndexChanged.connect(self.upd_prev)

        gl.addWidget(QLabel("Lớp"),0,0); gl.addWidget(self.cb_g,0,1); gl.addWidget(QLabel("Môn"),0,2); gl.addWidget(self.cb_s,0,3)
        gl.addWidget(QLabel("Chương"),1,0); gl.addWidget(self.cb_c,1,1); gl.addWidget(QLabel("Mức độ"),1,2); gl.addWidget(self.cb_l,1,3)
        gl.addWidget(QLabel("Bài"),2,0); gl.addWidget(self.cb_b,2,1); gl.addWidget(QLabel("Dạng"),2,2); gl.addWidget(self.cb_d,2,3)

        self.lbl_id6 = QLabel("ID6: -", styleSheet="color: green; font-weight: bold; font-size: 18px; margin: 10px;")
        gl.addWidget(self.lbl_id6, 3, 0, 1, 4)
        rl.addWidget(grp)

        bh = QHBoxLayout()
        self.btn_ai = QPushButton("🤖 Tự động điền AI")
        self.btn_ai.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        self.btn_ai.clicked.connect(self.run_auto_ai)
        self.btn_ai.setMinimumHeight(40)

        b_save_one = QPushButton("✅ Gán ID & Tiếp tục")
        b_save_one.setProperty("class", "btn-primary")
        b_save_one.clicked.connect(self.save_one)
        b_save_one.setMinimumHeight(40)

        self.btn_save_all = QPushButton("🔄 Lưu ALL vào DB")
        if self.mode == 'local':
            self.btn_save_all.setText("🚀 Hoàn tất & Nhập kho")
            self.btn_save_all.setProperty("class", "btn-success")

        self.btn_save_all.clicked.connect(self.save_all)
        self.btn_save_all.setMinimumHeight(40)

        bh.addWidget(self.btn_ai)
        bh.addWidget(b_save_one)
        bh.addWidget(self.btn_save_all)
        rl.addLayout(bh)

        spl.addWidget(rw)
        l.addWidget(spl)
        self.upd_ch()

    def run_auto_ai(self):
        main_app = self.parent()
        if not hasattr(main_app, 'ai') or not main_app.ai.is_ready:
            QMessageBox.warning(self, "Lỗi", "AI Engine chưa sẵn sàng. Vui lòng kiểm tra API Key ở màn hình chính.")
            return

        self.btn_ai.setEnabled(False)
        self.btn_ai.setText("Đang phân tích...")

        self.ai_worker = AutoIDWorker(main_app.ai, self.qs, DATA_ID6_2025)
        self.ai_worker.progress.connect(lambda p, m: self.lbl_id6.setText(f"AI: {m}"))
        self.ai_worker.item_finished.connect(self.on_ai_item_done)
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.start()

    def on_ai_item_done(self, row_idx, data):
        try:
            q = self.qs[row_idx]
            g_map = {10:0, 11:1, 12:2}
            g_code = g_map.get(data.get('grade', 12), 2)
            s_code = data.get('subject', 'D')
            c_code = data.get('chapter', 1)
            l_code = data.get('level', 'N')
            b_code = data.get('bai', 1)
            d_code = data.get('dang', 4)

            id6_str = f"{g_code}{s_code}{c_code}{l_code}{b_code}-{d_code}"

            q['grade'] = data.get('grade', 12)
            q['subject'] = s_code
            q['chapter'] = c_code
            q['level'] = l_code
            q['bai'] = b_code
            q['dang'] = d_code
            q['id6'] = id6_str

            self.tb.setItem(row_idx, 2, QTableWidgetItem(str(q['grade'])))
            self.tb.setItem(row_idx, 3, QTableWidgetItem(q['subject']))
            item_status = QTableWidgetItem(f"🤖 {id6_str}")
            item_status.setForeground(QColor("blue"))
            item_status.setToolTip("ID do AI gợi ý. Bấm vào dòng để xem chi tiết bên phải.")
            self.tb.setItem(row_idx, 4, item_status)
            self.tb.scrollToItem(item_status)
        except Exception as e:
            print(f"Lỗi update UI row {row_idx}: {e}")

    def on_ai_finished(self):
        self.btn_ai.setEnabled(True)
        self.btn_ai.setText("🤖 Tự động điền AI")
        QMessageBox.information(self, "Hoàn tất", "AI đã phân tích xong toàn bộ danh sách!\nHãy kiểm tra lại các dòng màu xanh dương và điều chỉnh nếu cần.")

    def load_data(self):
        if self.mode == 'db': self.qs = self.backend.get_unassigned(200)
        else: self.qs = self.local_data

        self.tb.setRowCount(len(self.qs))
        for r, q in enumerate(self.qs):
            display_id = str(q.get('id', f"New-{r+1}"))
            self.tb.setItem(r,0,QTableWidgetItem(display_id))
            self.tb.setItem(r,1,QTableWidgetItem(q['content_tex'][:60].replace("\n", " ") + "..."))
            self.tb.setItem(r,2,QTableWidgetItem(str(q['grade'])))
            self.tb.setItem(r,3,QTableWidgetItem(q['subject']))

            has_id = bool(q.get('id6'))
            status = "✅ Đã gán" if has_id else "❌ Thiếu ID"
            item = QTableWidgetItem(status)
            if has_id: item.setForeground(QColor("green"))
            else: item.setForeground(QColor("red"))
            self.tb.setItem(r,4, item)

    def upd_ch(self):
        try:
            g = int(self.cb_g.currentText())
            s_text = self.cb_s.currentText()
            s = 'D' if 'Đại' in s_text or s_text.startswith('D') else 'H'
        except: return

        self.cb_c.blockSignals(True)
        current_c_data = self.cb_c.currentData()
        self.cb_c.clear()

        if g in DATA_ID6_2025 and s in DATA_ID6_2025[g]:
            chapters_dict = DATA_ID6_2025[g][s]
            for ch_code in sorted(chapters_dict.keys()):
                ch_name = ""
                if 'CHAPTER_NAMES' in globals() and g in CHAPTER_NAMES and s in CHAPTER_NAMES[g]:
                    ch_name = CHAPTER_NAMES[g][s].get(ch_code, "")
                display = f"Chương {ch_code}: {ch_name}" if ch_name else f"Chương {ch_code}"
                self.cb_c.addItem(display, ch_code)
        else:
            self.cb_c.addItem("Không có chương", 0)

        if current_c_data is not None:
            idx = self.cb_c.findData(current_c_data)
            if idx >= 0: self.cb_c.setCurrentIndex(idx)

        self.cb_c.blockSignals(False)
        self.upd_bai()

    def upd_bai(self):
        try:
            g = int(self.cb_g.currentText())
            s_text = self.cb_s.currentText()
            s = 'D' if 'Đại' in s_text or s_text.startswith('D') else 'H'
            c_code = self.cb_c.currentData()
        except: return

        if c_code is None: c_code = 0

        self.cb_b.blockSignals(True)
        current_b_data = self.cb_b.currentData()
        self.cb_b.clear()

        lessons = {}
        if g in DATA_ID6_2025 and s in DATA_ID6_2025[g] and c_code in DATA_ID6_2025[g][s]:
            lessons = DATA_ID6_2025[g][s][c_code]

        if lessons:
            for k, v in lessons.items():
                self.cb_b.addItem(f"Bài {k}: {v}", k)
        else:
            self.cb_b.addItem("Bài 1", 1)

        if current_b_data is not None:
            idx = self.cb_b.findData(current_b_data)
            if idx >= 0: self.cb_b.setCurrentIndex(idx)

        self.cb_b.blockSignals(False)
        self.upd_prev()

    def upd_prev(self):
        try:
            g_code = int(self.cb_g.currentText()) - 10
            s_code = self.cb_s.currentText()[0]
            c_code = self.cb_c.currentData() or 0
            l_code = self.cb_l.currentText()[0]
            b_code = self.cb_b.currentData() or 1
            d_code = self.cb_d.currentData()
            self.id6_str = f"{g_code}{s_code}{c_code}{l_code}{b_code}-{d_code}"
            self.lbl_id6.setText(f"Dự kiến ID: {self.id6_str}")
        except:
            self.lbl_id6.setText("ID6: ...")

    def on_sel(self):
        if (r:=self.tb.currentRow()) >= 0:
            q = self.qs[r]
            self.prev.setText(q['content_tex'])
            if self.keep_form_state: self.keep_form_state = False; return
            try:
                self.cb_g.blockSignals(True)
                self.cb_s.blockSignals(True)
                grade_idx = self.cb_g.findText(str(q.get('grade', 12)))
                if grade_idx >= 0: self.cb_g.setCurrentIndex(grade_idx)
                subj = q.get('subject')
                if not subj: subj = 'D'
                for i in range(self.cb_s.count()):
                    if self.cb_s.itemText(i).startswith(str(subj)): self.cb_s.setCurrentIndex(i); break
                self.cb_g.blockSignals(False)
                self.cb_s.blockSignals(False)
                self.upd_ch()
                if q.get('chapter'):
                    idx = self.cb_c.findData(q['chapter'])
                    if idx >= 0: self.cb_c.setCurrentIndex(idx); self.upd_bai()
                if q.get('bai'):
                    idx_b = self.cb_b.findData(q['bai'])
                    if idx_b >= 0: self.cb_b.setCurrentIndex(idx_b)
                lev = q.get('level')
                if lev:
                    for i in range(self.cb_l.count()):
                        if self.cb_l.itemText(i).startswith(str(lev)): self.cb_l.setCurrentIndex(i); break
                dang = q.get('dang')
                if dang:
                    idx_d = self.cb_d.findData(dang)
                    if idx_d >= 0: self.cb_d.setCurrentIndex(idx_d)
            except Exception as e: print(f"Lỗi load form: {e}")

    def inject_id_to_tex(self, original_tex, id6):
        if re.search(r"\\begin\s*\{ex\}\s*%\[.*?\]", original_tex):
            new_tex = re.sub(r"(\\begin\s*\{ex\}\s*%\[)(.*?)(\])", f"\\g<1>{id6}]", original_tex)
        else:
            new_tex = re.sub(r"(\\begin\s*\{ex\})", f"\\1%[{id6}]", original_tex, count=1)
        return new_tex

    def save_one(self):
        if (r := self.tb.currentRow()) < 0: return
        q_data = self.qs[r]
        current_tex = q_data['content_tex']
        new_content_tex = self.inject_id_to_tex(current_tex, self.id6_str)
        new_g = int(self.cb_g.currentText())
        new_s = 'D' if 'Đại' in self.cb_s.currentText() else 'H'
        new_ch = int(self.cb_c.currentData()) if self.cb_c.currentData() else 0
        new_l = self.cb_l.currentText()[0]
        new_bai = self.cb_b.currentData() or 1
        new_dang = self.cb_d.currentData()

        if self.mode == 'db':
            self.backend.update_id6(
                q_data['id'], self.id6_str, new_g, new_s, new_ch, new_l, new_bai, new_dang, new_content_tex
            )
        else:
            q_data.update({
                'id6': self.id6_str, 'grade': new_g, 'subject': new_s,
                'chapter': new_ch, 'level': new_l, 'bai': new_bai,
                'dang': new_dang, 'content_tex': new_content_tex
            })

        self.tb.setItem(r, 2, QTableWidgetItem(str(new_g)))
        self.tb.setItem(r, 3, QTableWidgetItem(new_s))
        self.tb.setItem(r, 4, QTableWidgetItem(f"✅ ID: {self.id6_str}"))
        self.tb.item(r, 4).setForeground(QColor("green"))
        self.prev.setText(new_content_tex)
        self.keep_form_state = True
        if r + 1 < self.tb.rowCount(): self.tb.selectRow(r + 1)

    def save_all(self):
        if self.mode == 'local':
            missing_count = sum(1 for q in self.qs if not q.get('id6'))
            if missing_count > 0:
                if QMessageBox.question(self, "Xác nhận", f"Còn {missing_count} câu thiếu ID. Tiếp tục?",
                                      QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                    return
            self.accept()
        else:
            if QMessageBox.question(self, "Xác nhận", "Gán ID hiện tại cho TOÀN BỘ danh sách?") == QMessageBox.StandardButton.Yes:
                prog = QProgressDialog("Đang cập nhật...", "Hủy", 0, len(self.qs), self)
                prog.setWindowModality(Qt.WindowModality.WindowModal)
                for i, q in enumerate(self.qs):
                    if prog.wasCanceled(): break
                    prog.setValue(i)
                    new_content = self.inject_id_to_tex(q['content_tex'], self.id6_str)
                    bai_val = self.cb_b.currentData() or 1
                    self.backend.update_id6(
                        q['id'], self.id6_str, int(self.cb_g.currentText()), 'D' if 'Đại' in self.cb_s.currentText() else 'H',
                        int(self.cb_c.currentData()) if self.cb_c.currentData() else 0, self.cb_l.currentText()[0],
                        bai_val, self.cb_d.currentData(), new_content
                    )
                    self.tb.setItem(i, 2, QTableWidgetItem(self.cb_g.currentText()))
                    self.tb.setItem(i, 3, QTableWidgetItem('D' if 'Đại' in self.cb_s.currentText() else 'H'))
                    self.tb.setItem(i, 4, QTableWidgetItem("✅ Đã Lưu"))
                QMessageBox.information(self, "Thành công", "Đã cập nhật xong!")

class LessonPlannerWidget(QWidget):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.selected_ids = set()
        self.setup_ui()
        self.cb_grade.setCurrentText("12")
        self.update_chapter_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        filter_group = QGroupBox("Bộ Lọc (Đồng bộ ID6)")
        fl_layout = QGridLayout()
        self.cb_grade = QComboBox(); self.cb_grade.addItems(["10", "11", "12"])
        self.cb_subject = QComboBox()
        self.cb_subject.addItem("Đại số / Giải tích", "D")
        self.cb_subject.addItem("Hình học", "H")
        self.cb_chapter = QComboBox(); self.cb_bai = QComboBox();
        self.cb_level = QComboBox(); self.cb_level.addItem("Tất cả", "")
        self.cb_level.addItems(["N - Nhận biết", "H - Thông hiểu", "V - Vận dụng", "C - Vận dụng cao"])
        self.cb_dang = QComboBox(); self.cb_dang.addItem("Tất cả", 0)
        for k, v in DANH_MUC_DANG.items(): self.cb_dang.addItem(v, k)

        fl_layout.addWidget(QLabel("Lớp:"),0,0); fl_layout.addWidget(self.cb_grade,0,1)
        fl_layout.addWidget(QLabel("Môn:"),0,2); fl_layout.addWidget(self.cb_subject,0,3)
        fl_layout.addWidget(QLabel("Chương:"),1,0); fl_layout.addWidget(self.cb_chapter,1,1)
        fl_layout.addWidget(QLabel("Bài:"),1,2); fl_layout.addWidget(self.cb_bai,1,3)
        fl_layout.addWidget(QLabel("Mức:"),2,0); fl_layout.addWidget(self.cb_level,2,1)
        fl_layout.addWidget(QLabel("Dạng:"),2,2); fl_layout.addWidget(self.cb_dang,2,3)

        self.cb_grade.currentIndexChanged.connect(self.update_chapter_list)
        self.cb_subject.currentIndexChanged.connect(self.update_chapter_list)
        self.cb_chapter.currentIndexChanged.connect(self.update_lesson_list)

        btn_layout = QHBoxLayout()
        btn_scan = QPushButton("♻️ Chuẩn hóa Data"); btn_scan.clicked.connect(self.scan_metadata)
        btn_filter = QPushButton("🔍 LỌC CÂU HỎI"); btn_filter.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_filter.clicked.connect(self.load_data)
        btn_copy = QPushButton("📋 COPY LATEX (Siêu tốc)"); btn_copy.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_copy.clicked.connect(self.copy_to_clipboard)

        btn_layout.addWidget(btn_scan); btn_layout.addStretch()
        btn_layout.addWidget(btn_filter); btn_layout.addWidget(btn_copy)

        filter_group.setLayout(fl_layout); layout.addWidget(filter_group); layout.addLayout(btn_layout)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Chọn", "ID", "ID6", "Chương", "Bài", "Dạng", "Nội dung"])
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        self.lbl_count = QLabel("Sẵn sàng."); layout.addWidget(self.lbl_count)

    def update_chapter_list(self):
        try:
            g = int(self.cb_grade.currentText())
            s = self.cb_subject.currentData()
        except: return
        self.cb_chapter.clear(); self.cb_chapter.addItem("Tất cả", 0)
        if g in DATA_ID6_2025 and s in DATA_ID6_2025[g]:
            chapters = DATA_ID6_2025[g][s]
            for k in chapters.keys(): self.cb_chapter.addItem(f"Chương {k}", k)
        self.update_lesson_list()

    def update_lesson_list(self):
        try:
            g = int(self.cb_grade.currentText())
            s = self.cb_subject.currentData()
            c = self.cb_chapter.currentData()
        except: return
        self.cb_bai.clear(); self.cb_bai.addItem("Tất cả", 0)
        if c and c != 0:
            lessons = DATA_ID6_2025.get(g, {}).get(s, {}).get(c, {})
            for k, v in lessons.items(): self.cb_bai.addItem(f"Bài {k}: {v}", k)

    def load_data(self):
        lvl = self.cb_level.currentText()
        lvl_val = lvl[0] if lvl and lvl != "Tất cả" else ""
        filters = {
            "grade": self.cb_grade.currentText(), "subject": self.cb_subject.currentData(),
            "chapter": self.cb_chapter.currentData(), "bai": self.cb_bai.currentData(),
            "dang": self.cb_dang.currentData(), "level": lvl_val
        }
        clean_filters = {k: v for k, v in filters.items() if v and v != 0}
        rows = DatabaseManager.get_filtered_questions(self.db_path, clean_filters)
        self.table.setRowCount(0); self.table.blockSignals(True)
        for r in rows:
            row = self.table.rowCount(); self.table.insertRow(row)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if r["id"] in self.selected_ids else Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, chk)
            self.table.setItem(row, 1, QTableWidgetItem(str(r["id"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(r["id6"] or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(r["chapter"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(r["bai"])))
            dang_str = DANH_MUC_DANG.get(r["dang"], str(r["dang"]))
            self.table.setItem(row, 5, QTableWidgetItem(dang_str))
            self.table.setItem(row, 6, QTableWidgetItem(r["content_tex"][:60].replace("\n"," ")+"..."))
        self.table.blockSignals(False); self.table.itemChanged.connect(self.handle_check)
        self.lbl_count.setText(f"Tìm thấy: {len(rows)} câu.")

    def handle_check(self, item):
        if item.column() == 0:
            q_id = int(self.table.item(item.row(), 1).text())
            if item.checkState() == Qt.CheckState.Checked: self.selected_ids.add(q_id)
            else: self.selected_ids.discard(q_id)
            self.lbl_count.setText(f"Đã chọn: {len(self.selected_ids)} câu")

    def copy_to_clipboard(self):
        if not self.selected_ids:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn câu hỏi nào!"); return
        import sqlite3
        conn = sqlite3.connect(self.db_path); conn.row_factory = sqlite3.Row
        ids = list(self.selected_ids); final_text = []
        chunk_size = 500
        for i in range(0, len(ids), chunk_size):
            chunk = ids[i:i + chunk_size]
            placeholders = ','.join(['?'] * len(chunk))
            rows = conn.execute(f"SELECT content_tex FROM questions WHERE id IN ({placeholders})", chunk).fetchall()
            for r in rows:
                if r["content_tex"]: final_text.append(r["content_tex"].strip())
        conn.close()
        if final_text:
            QApplication.clipboard().setText("\n\n".join(final_text))
            QMessageBox.information(self, "Thành công", f"Đã copy {len(final_text)} câu hỏi!")
        else: QMessageBox.warning(self, "Lỗi", "Không lấy được nội dung!")

    def scan_metadata(self):
        msg = QMessageBox.question(self, "Chuẩn hóa", "Quét lại toàn bộ DB để điền cột Dạng/Bài cho đúng chuẩn?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg == QMessageBox.StandardButton.Yes:
            c = DatabaseManager.auto_scan_metadata(self.db_path)
            QMessageBox.information(self, "Xong", f"Đã cập nhật {c} câu hỏi.")
            self.load_data()

class ImageManagerDialog(QDialog):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.image_map = {}
        self.db_refs = {}
        self.setWindowTitle("🖼️ Quản lý Thư viện Hình ảnh LaTeX")
        self.setMinimumSize(900, 600)
        self.lib_file = os.path.join(os.path.dirname(DB_PATH), "image_lib.json")
        self.load_library()
        self.setup_ui()
        self.scan_database()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel("<b>HƯỚNG DẪN:</b> Công cụ này giúp tìm tất cả lệnh <code>\\includegraphics{...}</code> và thay thế đường dẫn ảnh.")
        info.setStyleSheet("background: #e8f6f3; padding: 10px; border-radius: 5px; color: #2c3e50;")
        layout.addWidget(info)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tên ảnh gốc (trong TeX)", "Số câu dùng", "Đường dẫn/Link mới (Cloud/Imgur...)", "Trạng thái"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        btn_box = QHBoxLayout()
        self.lbl_stat = QLabel("Đang quét...")
        btn_reload = QPushButton("🔄 Quét lại DB"); btn_reload.clicked.connect(self.scan_database)
        btn_save = QPushButton("💾 Lưu thư viện & Cập nhật DB"); btn_save.setProperty("class", "btn-primary"); btn_save.clicked.connect(self.apply_changes)
        btn_close = QPushButton("Đóng"); btn_close.clicked.connect(self.accept)
        btn_box.addWidget(self.lbl_stat); btn_box.addStretch(); btn_box.addWidget(btn_reload); btn_box.addWidget(btn_save); btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def load_library(self):
        try:
            if os.path.exists(self.lib_file):
                with open(self.lib_file, 'r', encoding='utf-8') as f: self.image_map = json.load(f)
        except: self.image_map = {}

    def scan_database(self):
        self.table.setRowCount(0); self.db_refs = {}
        all_qs = self.backend.conn.execute("SELECT id, content_tex FROM questions").fetchall()
        count_total_imgs = 0
        for q in all_qs:
            qid = q['id']; content = q['content_tex']
            if not content: continue
            matches = re.findall(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}", content)
            for img_name in matches:
                img_name = img_name.strip()
                if img_name not in self.db_refs: self.db_refs[img_name] = []
                self.db_refs[img_name].append(qid)
                count_total_imgs += 1
        self.table.setRowCount(len(self.db_refs))
        for row, (img_name, qids) in enumerate(self.db_refs.items()):
            self.table.setItem(row, 0, QTableWidgetItem(img_name))
            self.table.setItem(row, 1, QTableWidgetItem(str(len(qids))))
            new_link = self.image_map.get(img_name, "")
            self.table.setItem(row, 2, QTableWidgetItem(new_link))
            status = "Đã khớp thư viện" if new_link else "Chưa có link"
            self.table.setItem(row, 3, QTableWidgetItem(status))
        self.lbl_stat.setText(f"Tìm thấy {len(self.db_refs)} ảnh khác nhau trong {count_total_imgs} vị trí.")

    def apply_changes(self):
        updates_map = {}
        for row in range(self.table.rowCount()):
            old_name = self.table.item(row, 0).text()
            new_link = self.table.item(row, 2).text().strip()
            if new_link and new_link != old_name:
                updates_map[old_name] = new_link
                self.image_map[old_name] = new_link
        if not updates_map: QMessageBox.information(self, "Thông báo", "Không có thay đổi nào cần cập nhật."); return
        try:
            with open(self.lib_file, 'w', encoding='utf-8') as f: json.dump(self.image_map, f, indent=2, ensure_ascii=False)
        except Exception as e: QMessageBox.warning(self, "Lỗi lưu file", str(e))
        if QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn thay thế link cho {len(updates_map)} ảnh?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        progress = QProgressDialog("Đang cập nhật Database...", "Hủy", 0, len(updates_map), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        total_edited = 0
        try:
            self.backend.conn.execute("BEGIN TRANSACTION")
            for i, (old, new) in enumerate(updates_map.items()):
                progress.setValue(i)
                if progress.wasCanceled(): break
                qids = self.db_refs.get(old, [])
                if not qids: continue
                placeholders = ','.join('?' * len(qids))
                rows = self.backend.conn.execute(f"SELECT id, content_tex FROM questions WHERE id IN ({placeholders})", qids).fetchall()
                for r in rows:
                    qid = r['id']; content = r['content_tex']
                    pattern = r"(\\includegraphics(?:\[.*?\])?)\{" + re.escape(old) + r"\}"
                    new_content = re.sub(pattern, r"\1{" + new + "}", content)
                    if new_content != content:
                        self.backend.conn.execute("UPDATE questions SET content_tex = ? WHERE id = ?", (new_content, qid))
                        total_edited += 1
            self.backend.conn.commit()
            progress.setValue(len(updates_map))
            QMessageBox.information(self, "Thành công", f"Đã cập nhật {total_edited} câu hỏi!")
            self.scan_database()
        except Exception as e:
            self.backend.conn.rollback()
            QMessageBox.critical(self, "Lỗi Update", f"Có lỗi xảy ra, đã hoàn tác: {e}")

class MatrixEditorDialog(QDialog):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.bk = backend
        self.setWindowTitle("🎛️ BỘ ĐIỀU KHIỂN MA TRẬN & TRÍCH XUẤT ĐỀ")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.final_questions = []
        self.setup_ui()
        self.upd_mat()

    def setup_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(10, 10, 10, 10)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel); left_layout.setContentsMargins(0, 0, 0, 0)
        gb_scope = QGroupBox("1. CẤU HÌNH PHẠM VI"); gb_layout = QGridLayout(gb_scope)
        self.mat_g = QComboBox(); self.mat_g.addItems(["Lớp 12", "Lớp 11", "Lớp 10", "Tổng hợp THPT (10-12)"])
        self.mat_s = QComboBox(); self.mat_s.addItems(["Đại số / Giải tích", "Hình học", "Tất cả (Toán chung)"])
        self.mat_chap_filter = QComboBox(); self.mat_chap_filter.addItem("Hiển thị tất cả", 0)
        gb_layout.addWidget(QLabel("Khối lớp:"), 0, 0); gb_layout.addWidget(self.mat_g, 0, 1)
        gb_layout.addWidget(QLabel("Môn học:"), 1, 0); gb_layout.addWidget(self.mat_s, 1, 1)
        gb_layout.addWidget(QLabel("Lọc chương:"), 2, 0); gb_layout.addWidget(self.mat_chap_filter, 2, 1)
        self.mat_g.currentTextChanged.connect(self.upd_mat)
        self.mat_s.currentTextChanged.connect(self.upd_mat)
        self.mat_chap_filter.currentIndexChanged.connect(self.filter_mat_table)
        left_layout.addWidget(gb_scope)
        self.mat_tb = QTableWidget()
        self.mat_tb.setColumnCount(10)
        self.mat_tb.setHorizontalHeaderLabels(["Nội dung", "I.NB", "I.TH", "I.VD", "II.NB", "II.TH", "II.VD", "III.NB", "III.TH", "III.VD"])
        header = self.mat_tb.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 10): header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed); self.mat_tb.setColumnWidth(i, 45)
        self.mat_tb.verticalHeader().setVisible(False)
        left_layout.addWidget(self.mat_tb)
        tool_frame = QFrame(); tool_layout = QVBoxLayout(tool_frame); tool_layout.setContentsMargins(0, 5, 0, 5)
        btn_row = QHBoxLayout()
        b_fill = QPushButton("⚡ Copy dòng 1"); b_fill.clicked.connect(self.quick_fill)
        b_reset = QPushButton("🧹 Xóa trắng"); b_reset.clicked.connect(self.reset_values)
        btn_row.addWidget(b_fill); btn_row.addWidget(b_reset); btn_row.addStretch()
        tool_layout.addLayout(btn_row)
        self.lbl_sum = QLabel("Tổng: 0 câu")
        self.lbl_sum.setStyleSheet("background: #ecf0f1; padding: 8px; border-radius: 4px; border: 1px solid #bdc3c7;")
        tool_layout.addWidget(self.lbl_sum)
        left_layout.addWidget(tool_frame)
        self.btn_extract = QPushButton("⏩ TRÍCH XUẤT ĐỀ THI >>")
        self.btn_extract.setMinimumHeight(50)
        self.btn_extract.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        self.btn_extract.clicked.connect(self.extract_exam)
        left_layout.addWidget(self.btn_extract)
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel); right_layout.setContentsMargins(0, 0, 0, 0)
        gb_res = QGroupBox("2. DANH SÁCH CÂU HỎI ĐÃ CHỌN"); gb_res_layout = QVBoxLayout(gb_res)
        self.res_list = QListWidget(); self.res_list.setAlternatingRowColors(True)
        self.res_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.res_list.customContextMenuRequested.connect(self.open_context_menu)
        self.res_list.itemClicked.connect(self.preview_item)
        gb_res_layout.addWidget(self.res_list)
        gb_res_layout.addWidget(QLabel("<b>Xem trước Code LaTeX:</b>"))
        self.preview_txt = QTextEdit(); self.preview_txt.setFixedHeight(150); self.preview_txt.setReadOnly(True)
        gb_res_layout.addWidget(self.preview_txt)
        right_layout.addWidget(gb_res)
        footer = QHBoxLayout()
        self.lbl_status = QLabel("Chưa có câu hỏi.")
        b_finish = QPushButton("✅ HOÀN TẤT & TẠO ĐỀ")
        b_finish.setMinimumHeight(50)
        b_finish.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        b_finish.clicked.connect(self.accept_exam)
        footer.addWidget(self.lbl_status); footer.addStretch(); footer.addWidget(b_finish)
        right_layout.addLayout(footer)
        splitter.addWidget(left_panel); splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2); splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

    def _get_display_label(self, q, idx):
        subj_map = {'D': 'Đại', 'H': 'Hình'}
        dang_map = {1: 'TN', 2: 'Đ/S', 3: 'TLN', 4: 'TL'}
        g = q.get('grade', '?'); s = subj_map.get(q.get('subject', ''), q.get('subject', ''))
        ch = q.get('chapter', '?'); bai = q.get('bai', '?'); lev = q.get('level', '?')
        d_str = dang_map.get(q.get('dang', 4), 'TL')
        content_clean = q.get('content_tex', '').replace("\n", " ").strip()
        if len(content_clean) > 80: content_clean = content_clean[:80] + "..."
        return f"Câu {idx}: [{g}-{s}] [C{ch}.B{bai}] [{lev}] [{d_str}] - {content_clean}"

    def upd_mat(self):
        target_grades = [12, 11, 10] if "Tổng hợp" in self.mat_g.currentText() else [int(self.mat_g.currentText().split()[-1])]
        target_subjs = ['D', 'H'] if "Tất cả" in self.mat_s.currentText() else (['D'] if 'Đại' in self.mat_s.currentText() else ['H'])
        self.mat_tb.setRowCount(0); self.mat_chap_filter.blockSignals(True)
        self.mat_chap_filter.clear(); self.mat_chap_filter.addItem("Hiển thị tất cả", 0)
        row_idx = 0
        for g in target_grades:
            for s in target_subjs:
                if g not in DATA_ID6_2025 or s not in DATA_ID6_2025[g]: continue
                self.mat_tb.insertRow(row_idx)
                h_item = QTableWidgetItem(f"--- LỚP {g} - {'ĐẠI SỐ' if s=='D' else 'HÌNH HỌC'} ---")
                h_item.setBackground(QColor("#d35400")); h_item.setForeground(QColor("white")); h_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.mat_tb.setItem(row_idx, 0, h_item); self.mat_tb.setSpan(row_idx, 0, 1, 10); row_idx += 1
                chapters = DATA_ID6_2025[g][s]
                for ch_code, lessons in chapters.items():
                    self.mat_chap_filter.addItem(f"[{g}{s}] Chương {ch_code}", f"{g}_{s}_{ch_code}")
                    for bai_code, bai_name in lessons.items():
                        self.mat_tb.insertRow(row_idx)
                        item_name = QTableWidgetItem(f"C{ch_code}.B{bai_code}: {bai_name}")
                        item_name.setData(Qt.ItemDataRole.UserRole, {'g':g, 's':s, 'ch':ch_code, 'bai':bai_code})
                        item_name.setToolTip(bai_name)
                        self.mat_tb.setItem(row_idx, 0, item_name)
                        for c in range(1, 10):
                            sb = QSpinBox(); sb.setRange(0, 50); sb.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
                            sb.setAlignment(Qt.AlignmentFlag.AlignCenter); sb.valueChanged.connect(self.calc_sum)
                            if 1<=c<=3: sb.setStyleSheet("background:#e3f2fd; color:#1565c0;")
                            elif 4<=c<=6: sb.setStyleSheet("background:#fff3e0; color:#e65100;")
                            else: sb.setStyleSheet("background:#f3e5f5; color:#7b1fa2;")
                            self.mat_tb.setCellWidget(row_idx, c, sb)
                        row_idx += 1
        self.mat_chap_filter.blockSignals(False); self.calc_sum()

    def filter_mat_table(self):
        val = self.mat_chap_filter.currentData()
        for r in range(self.mat_tb.rowCount()):
            item = self.mat_tb.item(r, 0)
            if not item: self.mat_tb.setRowHidden(r, False); continue
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data: continue
            self.mat_tb.setRowHidden(r, (val != 0 and f"{data['g']}_{data['s']}_{data['ch']}" != val))

    def calc_sum(self):
        s1 = s2 = s3 = 0
        for r in range(self.mat_tb.rowCount()):
            if self.mat_tb.cellWidget(r, 1):
                s1 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(1, 4))
                s2 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(4, 7))
                s3 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(7, 10))
        total = s1 + s2 + s3
        self.lbl_sum.setText(f"<span style='font-size:16px; font-weight:bold'>TỔNG: <span style='color:red'>{total}</span> câu</span> | P1: {s1} | P2: {s2} | P3: {s3}")

    def quick_fill(self):
        vals = {}
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and self.mat_tb.cellWidget(r, 1):
                for c in range(1, 10): vals[c] = self.mat_tb.cellWidget(r, c).value()
                break
        if not vals: return
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and self.mat_tb.cellWidget(r, 1):
                for c in range(1, 10): self.mat_tb.cellWidget(r, c).setValue(vals[c])

    def reset_values(self):
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and self.mat_tb.cellWidget(r, 1):
                for c in range(1, 10): self.mat_tb.cellWidget(r, c).setValue(0)

    def extract_exam(self):
        self.res_list.clear(); self.final_questions = []; missing = []
        col_map = {1:(1,'N'), 2:(1,'H'), 3:(1,'V'), 4:(2,'N'), 5:(2,'H'), 6:(2,'V'), 7:(3,'N'), 8:(3,'H'), 9:(3,'V')}
        for r in range(self.mat_tb.rowCount()):
            item = self.mat_tb.item(r, 0);
            if not item: continue
            d = item.data(Qt.ItemDataRole.UserRole)
            if not d: continue
            for c in range(1, 10):
                cnt = self.mat_tb.cellWidget(r, c).value()
                if cnt > 0:
                    dang, lev = col_map[c]
                    for _ in range(cnt):
                        q = self.bk.get_rnd(d['g'], d['s'], d['ch'], d['bai'], lev, dang)
                        if q:
                            self.final_questions.append(q)
                            item = QListWidgetItem(self._get_display_label(q, self.res_list.count() + 1))
                            item.setData(Qt.ItemDataRole.UserRole, q)
                            self.res_list.addItem(item)
                        else: missing.append(f"[{d['g']}{d['s']}-C{d['ch']}.B{d['bai']}-{lev}] Dạng {dang}")
        self.lbl_status.setText(f"Đã lấy {self.res_list.count()} câu. (Thiếu {len(missing)} câu)")
        if missing: QMessageBox.warning(self, "Thiếu dữ liệu", f"Không tìm thấy {len(missing)} câu hỏi!")

    def preview_item(self, item):
        q = item.data(Qt.ItemDataRole.UserRole)
        self.preview_txt.setText(q['content_tex'])

    def open_context_menu(self, pos):
        item = self.res_list.itemAt(pos)
        if not item: return
        menu = QMenu()
        act_swap = menu.addAction("🔄 Đổi câu khác tương đương")
        if menu.exec(self.res_list.viewport().mapToGlobal(pos)) == act_swap: self.swap_question(item)

    def swap_question(self, item):
        old_q = item.data(Qt.ItemDataRole.UserRole)
        new_q = self.bk.get_rnd(old_q['grade'], old_q['subject'], old_q['chapter'], old_q['bai'], old_q['level'], old_q['dang'], exc=old_q['id'])
        if new_q:
            item.setData(Qt.ItemDataRole.UserRole, new_q)
            idx = self.res_list.row(item)
            item.setText(self._get_display_label(new_q, idx + 1))
            self.preview_txt.setText(new_q['content_tex'])
            self.final_questions[idx] = new_q
            QMessageBox.information(self, "Xong", f"Đã đổi sang câu ID: {new_q['id']}")
        else: QMessageBox.warning(self, "Hết câu", "Không còn câu hỏi khác tương đương!")

    def accept_exam(self):
        if not self.final_questions: QMessageBox.warning(self, "Trống", "Chưa có câu hỏi nào!"); return
        self.accept()

class AIClonerDialog(QDialog):
    def __init__(self, ai_engine, base_question, parent=None):
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.base_question = base_question
        self.variants = []
        self.setWindowTitle("🤖 AI Tạo biến thể câu hỏi")
        self.setMinimumSize(900, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🤖 AI TẠO BIẾN THỂ CÂU HỎI"))
        group_original = QGroupBox("📝 Câu hỏi gốc:")
        original_layout = QVBoxLayout(group_original)
        self.original_text = QTextEdit()
        self.original_text.setPlainText(self.base_question.get('content_tex', ''))
        self.original_text.setMaximumHeight(150); self.original_text.setReadOnly(True)
        original_layout.addWidget(self.original_text)
        layout.addWidget(group_original)
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Số lượng biến thể:"))
        self.num_spin = QSpinBox(); self.num_spin.setRange(1, 10); self.num_spin.setValue(5)
        control_layout.addWidget(self.num_spin)
        self.btn_generate = QPushButton("🤖 Tạo biến thể"); self.btn_generate.clicked.connect(self.generate_variants)
        control_layout.addWidget(self.btn_generate); control_layout.addStretch()
        layout.addLayout(control_layout)
        group_results = QGroupBox("📋 Kết quả:")
        results_layout = QVBoxLayout(group_results)
        self.results_list = QListWidget(); self.results_list.itemClicked.connect(self.on_variant_selected)
        results_layout.addWidget(self.results_list)
        self.variant_preview = QTextEdit(); self.variant_preview.setMaximumHeight(200); self.variant_preview.setReadOnly(True)
        results_layout.addWidget(QLabel("Xem trước:")); results_layout.addWidget(self.variant_preview)
        layout.addWidget(group_results)
        btn_layout = QHBoxLayout()
        btn_close = QPushButton("❌ Đóng"); btn_close.clicked.connect(self.reject)
        btn_layout.addStretch(); btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def generate_variants(self):
        if not self.ai_engine.is_ready: QMessageBox.warning(self, "Lỗi", "AI Engine chưa sẵn sàng!"); return
        num = self.num_spin.value()
        progress = QProgressDialog("Đang tạo biến thể...", "Hủy", 0, num, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal); progress.show()
        self.results_list.clear(); self.variants = []
        for i in range(num):
            if progress.wasCanceled(): break
            progress.setValue(i)
            variant = self.ai_engine.generate_safe(self.base_question.get('content_tex', ''))
            if variant and isinstance(variant, tuple): variant = variant[0] # generate_safe returns tuple
            if variant:
                self.variants.append(variant)
                self.results_list.addItem(QListWidgetItem(f"Biến thể {i+1}"))
        progress.setValue(num)
        if self.variants: QMessageBox.information(self, "Thành công", f"Đã tạo {len(self.variants)} biến thể!")

    def on_variant_selected(self, item):
        idx = self.results_list.row(item)
        if 0 <= idx < len(self.variants): self.variant_preview.setPlainText(self.variants[idx])

class APIKeyDialog(QDialog):
    def __init__(self, current_key="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Cấu hình API Key Gemini")
        self.setModal(True); self.setMinimumWidth(700)
        self.setup_ui(current_key)

    def setup_ui(self, current_key):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🔑 NHẬP API KEY GEMINI ĐỂ SỬ DỤNG TÍNH NĂNG AI"))
        guide = QTextEdit(); guide.setReadOnly(True); guide.setMaximumHeight(220)
        guide.setHtml("<h3 style='color:#27ae60;'>📋 HƯỚNG DẪN LẤY API KEY GEMINI (MIỄN PHÍ)</h3>...")
        layout.addWidget(guide)
        key_layout = QHBoxLayout()
        self.key_input = QLineEdit(); self.key_input.setText(current_key); self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addWidget(self.key_input)
        btn_save = QPushButton("💾 Lưu & Tiếp tục"); btn_save.clicked.connect(self.accept)
        layout.addLayout(key_layout); layout.addWidget(btn_save)

    def get_key(self): return self.key_input.text().strip()

class StatisticsDashboard(QDialog):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.bk = backend
        self.setWindowTitle("📊 Dashboard Thống Kê")
        self.setMinimumSize(1150, 800)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.lbl_v = QLabel("0")
        layout.addWidget(QLabel("TỔNG CÂU HỎI:")); layout.addWidget(self.lbl_v)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["Danh mục", "Tổng", "NB", "TH", "VD", "VDC"])
        layout.addWidget(self.tree)

    def load_data(self):
        total, level_map, details = self.bk.get_dashboard_stats()
        self.lbl_v.setText(f"{total:,}")
        data_tree = {}
        for r in details:
            g, s, c, l, count = r
            try: g = int(g); c = int(c)
            except: continue
            if g not in data_tree: data_tree[g] = {}
            if s not in data_tree[g]: data_tree[g][s] = {}
            if c not in data_tree[g][s]: data_tree[g][s][c] = {'total': 0, 'N':0, 'H':0, 'V':0, 'C':0}
            node = data_tree[g][s][c]
            node['total'] += count
            if l in node: node[l] += count
        self.tree.clear()
        for g in sorted(data_tree.keys()):
            g_item = QTreeWidgetItem(self.tree); g_item.setText(0, f"Khối {g}")
            for s in data_tree[g]:
                s_item = QTreeWidgetItem(g_item); s_item.setText(0, s)
                for c in data_tree[g][s]:
                    c_item = QTreeWidgetItem(s_item); c_item.setText(0, f"Chương {c}")
                    stats = data_tree[g][s][c]
                    c_item.setText(1, str(stats['total']))

class MixConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Cấu hình trộn đề")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.sp_num = QSpinBox(); self.sp_num.setValue(4)
        layout.addWidget(QLabel("Số lượng đề:")); layout.addWidget(self.sp_num)
        self.sp_start = QSpinBox(); self.sp_start.setRange(100, 9999); self.sp_start.setValue(101)
        layout.addWidget(QLabel("Mã bắt đầu:")); layout.addWidget(self.sp_start)
        btn = QPushButton("OK"); btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_data(self): return {'num': self.sp_num.value(), 'start': self.sp_start.value()}

class TemplateLibraryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_template = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        # Simplified content
        btn = QPushButton("Áp dụng"); btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_selected_template(self): return self.selected_template

class ClassroomDialog(QDialog):
    def __init__(self, question_objects, parent=None):
        super().__init__(parent)
        self.questions = question_objects
        self.setWindowTitle("📚 Đăng bài lên Google Classroom")
        self.setFixedSize(600, 680)
        self.google = GoogleManagerFull()
        self.setup_ui()
        QTimer.singleShot(100, self.init_google)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.txt_title = QLineEdit(); layout.addWidget(QLabel("Tiêu đề:")); layout.addWidget(self.txt_title)
        self.txt_desc = QTextEdit(); layout.addWidget(QLabel("Mô tả:")); layout.addWidget(self.txt_desc)
        self.cb_courses = QComboBox(); layout.addWidget(QLabel("Chọn lớp:")); layout.addWidget(self.cb_courses)
        self.lbl_status = QLabel("Checking..."); layout.addWidget(self.lbl_status)
        self.pbar = QProgressBar(); layout.addWidget(self.pbar)
        self.btn_upload = QPushButton("Đăng bài"); self.btn_upload.clicked.connect(self.start_upload)
        layout.addWidget(self.btn_upload)

    def init_google(self):
        try:
            self.google.authenticate()
            for c in self.google.get_courses(): self.cb_courses.addItem(c['name'], c['id'])
            self.lbl_status.setText("Ready")
        except Exception as e: self.lbl_status.setText(str(e))

    def start_upload(self):
        if not self.txt_title.text(): return
        self.worker = AutoFormWorker(self.google, self.questions, self.txt_title.text(), self.cb_courses.currentData())
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.finished.connect(lambda l: (QMessageBox.information(self,"OK",l), self.accept()))
        self.worker.start()

class ExamConfigDialog(QDialog):
    def __init__(self, questions, parent=None):
        super().__init__(parent)
        self.questions = questions
        self.final_questions = []
        self.tex_path = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.inp_title = QLineEdit("ĐỀ THI"); layout.addWidget(QLabel("Tên:")); layout.addWidget(self.inp_title)
        self.inp_time = QSpinBox(); self.inp_time.setValue(90); layout.addWidget(QLabel("Phút:")); layout.addWidget(self.inp_time)
        self.inp_variants = QSpinBox(); self.inp_variants.setValue(1); layout.addWidget(QLabel("Mã đề:")); layout.addWidget(self.inp_variants)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept_data); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def accept_data(self):
        self.final_questions = self.questions # Simplification
        self.accept()

    def get_config(self):
        return {"title": self.inp_title.text(), "time": self.inp_time.value(), "questions": self.final_questions, "external_tex": self.tex_path, "num_variants": self.inp_variants.value()}

class HistoryDialog(QDialog):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.bk = backend
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(); self.table.setColumnCount(5)
        layout.addWidget(self.table)

    def load_data(self):
        res = self.bk.get_exam_results()
        self.table.setRowCount(len(res))
        for i, r in enumerate(res):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(r['score'])))

class ExamMonitorDialog(QDialog):
    def __init__(self, web_thread, parent=None):
        super().__init__(parent)
        self.web_thread = web_thread
        self.setup_ui()
        self.web_thread.students_changed.connect(self.update_table)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.lbl_url = QLabel("URL: " + self.web_thread.public_url); layout.addWidget(self.lbl_url)
        self.table = QTableWidget(); layout.addWidget(self.table)
        btn = QPushButton("Giao bài"); btn.clicked.connect(self.distribute)
        layout.addWidget(btn)

    def update_table(self, students):
        self.table.setRowCount(len(students))
        for i, s in enumerate(students):
            self.table.setItem(i, 0, QTableWidgetItem(s['name']))

    def distribute(self):
        self.web_thread.distribute_exam([]) # Send all

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Hướng dẫn sử dụng..."))

class AdvancedExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.template_path = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.chk_sol = QCheckBox("Lời giải"); layout.addWidget(self.chk_sol)
        self.chk_shuffle = QCheckBox("Trộn"); layout.addWidget(self.chk_shuffle)
        self.chk_key = QCheckBox("Bảng đáp án"); layout.addWidget(self.chk_key)
        self.chk_pdf = QCheckBox("Biên dịch PDF"); layout.addWidget(self.chk_pdf)
        btn = QPushButton("OK"); btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_config(self):
        return {"template": self.template_path, "show_sol": self.chk_sol.isChecked(), "shuffle": self.chk_shuffle.isChecked(), "table": self.chk_key.isChecked(), "compile": self.chk_pdf.isChecked()}

class FileCleanerDialog(QDialog):
    def __init__(self, ai, parent=None):
        super().__init__(parent)
        self.ai = ai
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.txt_path = QLineEdit(); layout.addWidget(self.txt_path)
        btn = QPushButton("Start"); btn.clicked.connect(self.start)
        layout.addWidget(btn)

    def start(self):
        if not self.txt_path.text(): return
        self.worker = CleanerWorker(self.txt_path.text(), self.ai)
        self.worker.start()

class QuickEditDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.new_content = content
        layout = QVBoxLayout(self)
        self.edit = QTextEdit(); self.edit.setText(content)
        layout.addWidget(self.edit)
        btn = QPushButton("Save"); btn.clicked.connect(self.save)
        layout.addWidget(btn)
    def save(self): self.new_content = self.edit.toPlainText(); self.accept()

class ImageMappingDialog(QDialog):
    def __init__(self, names, adir, parent=None):
        super().__init__(parent)
        self.mapping = {}
        self.names = names
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(len(self.names), 2)
        for i, n in enumerate(self.names): self.table.setItem(i, 0, QTableWidgetItem(n))
        layout.addWidget(self.table)
        btn = QPushButton("OK"); btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class AutoSchedulerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Simplified
        layout.addWidget(QLabel("Schedule Task"))
        btn = QPushButton("Save"); btn.clicked.connect(self.accept)
        layout.addWidget(btn)

def check_license_system():
    license_path = os.path.join(os.path.expanduser("~"), ".bankai_license")
    if os.path.exists(license_path):
        try:
            with open(license_path, "r") as f:
                data = json.load(f)
                if data.get("hwid") == get_hwid(): return True
        except: pass
    dlg = ActivationDialog()
    dlg.exec()
    return dlg.is_verified
