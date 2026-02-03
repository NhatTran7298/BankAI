# Thêm đoạn này vào ngay sau các dòng import os, sys
import os
import sys

# --- CHÈN THÊM VÀO ĐẦU FILE (Sau các import khác) ---
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Các quyền cần thiết: Đọc khóa học, đọc danh sách học sinh, chấm điểm
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.rosters.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students'
]
# -----------------------------------------------------
# [QUAN TRỌNG] Cấu hình PATH cho macOS để tìm thấy pdflatex và poppler khi chạy dạng .app
if sys.platform == 'darwin':
    os.environ['PATH'] += ':/usr/local/bin:/opt/homebrew/bin:/Library/TeX/texbin'

# Hàm lấy đường dẫn tài nguyên (Hỗ trợ PyInstaller)
def resource_path(relative_path):
    """Lấy đường dẫn tuyệt đối của tài nguyên, dùng được cho cả dev và PyInstaller"""
    try:
        # PyInstaller tạo ra thư mục temp này
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# Thêm vào đầu file
import shutil

# Thêm hàm dọn dẹp vào class MainApp (gọi khi closeEvent)
def cleanup_cache(self):
    # Chỉ xóa các file tạm, giữ lại SVG
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            if not f.endswith(".svg"):
                try:
                    os.remove(os.path.join(CACHE_DIR, f))
                except: pass
import os
import sys
import re
import sqlite3
import time
import json
import logging
import random
import shutil
import subprocess
import platform
import warnings
import os.path
# =============================================================================
# MODULE BẢN QUYỀN (LICENSE SYSTEM)
# =============================================================================
import uuid
import platform
import hashlib
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QRadioButton, QButtonGroup, 
                             QGroupBox, QApplication, QWidget, QCheckBox, QProgressBar, QAbstractItemView, QTimeEdit, QSizePolicy, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer, QTime

# --- TẮT CẢNH BÁO GOOGLE DEPRECATED ---
# Để console sạch sẽ, không hiện chữ đỏ lòm
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# 🔥 URL API CỦA BẠN (Đã cập nhật)
API_URL = "https://script.google.com/macros/s/AKfycbxDJmIsjLWXHuq0aq-IY5Rk67jK1G6dLWfVPicuyk2hxMTcz2ePHs_UEmoUkUvd3fgtRA/exec"

APP_VERSION = "1.0"
# --- CẤU HÌNH THANH TOÁN (Sửa thông tin của bạn vào đây) ---
BANK_ID = "BIDV"           # Mã ngân hàng (MB, VCB, ACB, BIDV...)
BANK_ACCOUNT = "6612853484" # Số tài khoản của bạn
BANK_NAME = "TRAN NAM NHAT" # Tên chủ tài khoản (Không dấu)

PRICE_YEAR = 400000    # 400k
PRICE_LIFE = 800000    # 800k

def get_hwid():
    """Lấy mã định danh phần cứng (Hardware ID) duy nhất của máy"""
    try:
        mac = uuid.getnode()
        node = platform.node()
        system = platform.system()
        # Kết hợp các thông số để tạo chuỗi duy nhất
        raw_id = f"{mac}-{node}-{system}"
        # Mã hóa MD5 để ngắn gọn và bảo mật hơn
        return hashlib.md5(raw_id.encode()).hexdigest().upper()
    except:
        return "UNKNOWN-DEVICE-ID"

class ActivationDialog(QDialog):
    """Hộp thoại Kích hoạt & Thanh toán tích hợp"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mua bản quyền & Kích hoạt BankAI Pro")
        self.setModal(True)
        self.setFixedSize(750, 450) # Mở rộng size để chứa QR
        self.is_verified = False
        self.hwid = get_hwid()
        
        # Layout chính chia 2 cột
        main_layout = QHBoxLayout(self)
        
        # ================= CỘT TRÁI: MUA HÀNG (TẠO QR) =================
        left_panel = QGroupBox("1. Mua bản quyền (Quét mã QR)")
        left_layout = QVBoxLayout(left_panel)
        
        # 1. Chọn gói
        self.rb_year = QRadioButton(f"Gói 1 Năm ({PRICE_YEAR:,} đ)")
        self.rb_life = QRadioButton(f"Gói Vĩnh Viễn ({PRICE_LIFE:,} đ)")
        self.rb_life.setChecked(True) # Mặc định chọn gói to
        
        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.rb_year)
        self.btn_group.addButton(self.rb_life)
        
        left_layout.addWidget(QLabel("Chọn gói phần mềm:"))
        left_layout.addWidget(self.rb_year)
        left_layout.addWidget(self.rb_life)
        
        # 2. Nhập Email (Để tạo nội dung chuyển khoản)
        left_layout.addWidget(QLabel("Nhập Email của bạn (để nhận Key):"))
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("vidu@gmail.com")
        left_layout.addWidget(self.txt_email)
        
        # 3. Nút lấy mã QR
        btn_get_qr = QPushButton("Hiển thị mã QR Thanh toán")
        btn_get_qr.setProperty("class", "btn-primary")
        btn_get_qr.clicked.connect(self.generate_qr)
        left_layout.addWidget(btn_get_qr)
        
        # 4. Khu vực hiển thị ảnh QR
        self.lbl_qr_img = QLabel()
        self.lbl_qr_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_qr_img.setStyleSheet("border: 1px dashed #aaa; background: #f9f9f9;")
        self.lbl_qr_img.setMinimumHeight(200)
        self.lbl_qr_img.setText("Vui lòng nhập Email\nvà bấm nút để lấy mã QR")
        left_layout.addWidget(self.lbl_qr_img)
        
        main_layout.addWidget(left_panel, 1) # Tỷ lệ 1

        # ================= CỘT PHẢI: KÍCH HOẠT =================
        right_panel = QGroupBox("2. Nhập mã kích hoạt")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Thông tin HWID
        right_layout.addWidget(QLabel("Mã máy (HWID):"))
        txt_hwid = QLineEdit(self.hwid)
        txt_hwid.setReadOnly(True)
        txt_hwid.setStyleSheet("background: #eee; color: #555;")
        right_layout.addWidget(txt_hwid)
        
        right_layout.addSpacing(20)
        
        # Ô nhập Key
        right_layout.addWidget(QLabel("Nhập License Key (Kiểm tra Email):"))
        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("BANKAI-XXXX-XXXX-XXXX")
        self.txt_key.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
        right_layout.addWidget(self.txt_key)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        right_layout.addWidget(self.lbl_status)
        
        right_layout.addSpacing(10)
        
        # Nút kích hoạt
        btn_active = QPushButton("Kích hoạt ngay")
        btn_active.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_active.setStyleSheet("background-color: #27ae60; color: white; padding: 12px; font-weight: bold; font-size: 16px;")
        btn_active.clicked.connect(self.check_online)
        right_layout.addWidget(btn_active)
        
        # Nút đóng
        right_layout.addStretch()
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.reject)
        right_layout.addWidget(btn_close)

        main_layout.addWidget(right_panel, 1) # Tỷ lệ 1

    def generate_qr(self):
        """Tạo mã QR VietQR động dựa trên gói đã chọn"""
        email = self.txt_email.text().strip()
        if not email or "@" not in email:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Email chính xác để nhận Key!")
            return
            
        # 1. Xác định số tiền
        amount = PRICE_LIFE if self.rb_life.isChecked() else PRICE_YEAR
        
        # 2. Tạo nội dung chuyển khoản chuẩn: BANKAI EMAIL
        # Thay thế ký tự đặc biệt để tránh lỗi ngân hàng (tùy chọn, nhưng nên làm)
        # Ví dụ: nam@gmail.com -> BANKAI NAMATGMAILDOTCOM (để khớp với logic Backend)
        safe_email = email.replace("@", "AT").replace(".", "DOT").upper()
        content = f"BANKAI {safe_email}"
        
        # 3. Tạo URL VietQR (API miễn phí)
        # Cấu trúc: https://img.vietqr.io/image/{BANK_ID}-{ACC_NO}-print.png?amount={...}&addInfo={...}&accountName={...}
        import urllib.parse
        encoded_content = urllib.parse.quote(content)
        encoded_name = urllib.parse.quote(BANK_NAME)
        
        qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{BANK_ACCOUNT}-print.png?amount={amount}&addInfo={encoded_content}&accountName={encoded_name}"
        
        # 4. Tải ảnh về và hiển thị
        self.lbl_qr_img.setText("Đang tải mã QR...")
        QApplication.processEvents()
        
        try:
            import requests
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
            # Gửi dữ liệu lên Google Sheet
            import requests
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
        """Lưu key vào máy"""
        data = {"key": key, "hwid": self.hwid}
        save_path = os.path.join(os.path.expanduser("~"), ".bankai_license")
        with open(save_path, "w") as f:
            json.dump(data, f)

def check_license_system():
    """Hàm kiểm tra bản quyền chính (Gọi hàm này trước khi vào App)"""
    license_path = os.path.join(os.path.expanduser("~"), ".bankai_license")
    
    # 1. Kiểm tra file license đã lưu trên máy chưa
    if os.path.exists(license_path):
        try:
            with open(license_path, "r") as f:
                data = json.load(f)
                # Kiểm tra HWID trong file có khớp với máy này không (Chống copy file license)
                if data.get("hwid") == get_hwid():
                    return True # Đã kích hoạt hợp lệ
        except:
            pass # File lỗi thì coi như chưa kích hoạt
    
    # 2. Nếu chưa hợp lệ, hiện bảng kích hoạt
    dlg = ActivationDialog()
    dlg.exec()
    return dlg.is_verified
# =============================================================================

def open_file_or_url(path):
    """Mở file hoặc URL tương thích đa nền tảng (Win/Mac/Linux)"""
    system = platform.system()
    if system == 'Windows':
        os.startfile(path)
    elif system == 'Darwin':  # macOS
        subprocess.call(('open', path))
    else:  # Linux
        subprocess.call(('xdg-open', path))
# =============================================================================
# [FIX LỖI CRASH TRÊN MACOS] - QUAN TRỌNG: PHẢI ĐẶT TRÊN CÙNG
# =============================================================================
os.environ['GRPC_DNS_RESOLVER'] = 'native'
os.environ['GRPC_POLL_STRATEGY'] = 'poll'
os.environ['no_proxy'] = '*'

# Tắt log rác của thư viện Google
logging.getLogger('google.generativeai').setLevel(logging.ERROR)

# Tìm dòng from PyQt6.QtWidgets import ... và thêm QSplashScreen vào
import PyQt6.QtWidgets
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QTextEdit, QMessageBox, QDialog,
                             QComboBox, QListWidgetItem, QTableWidget, 
                             QSpinBox, QTabWidget, QHeaderView, QProgressDialog, 
                             QTreeWidget, QTreeWidgetItem, QSplitter, QLineEdit,
                             QTableWidgetItem, QScrollArea, QFrame, QGridLayout,
                             QGroupBox, QSplashScreen, QStackedWidget) # <--- Thêm QSplashScreen

# Tìm dòng from PyQt6.QtGui import ... và thêm QPixmap, QPainter vào
from PyQt6.QtGui import QDrag, QFont, QIcon, QColor, QAction, QBrush, QPixmap, QPainter, QPen, QCursor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QPoint, QSize
# =============================================================================
# QUẢN LÝ API KEY CÁ NHÂN
# =============================================================================
import json
from pathlib import Path

API_CONFIG_FILE = Path(os.path.expanduser("~")) / "Documents" / "BankAI_Data" / "api_config.json"

def load_api_key():
    """Đọc API Key từ file cấu hình nếu có"""
    if API_CONFIG_FILE.exists():
        try:
            with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("gemini_api_key", "")
        except:
            return ""
    return ""

def save_api_key(key):
    """Lưu API Key vào file cấu hình"""
    API_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"gemini_api_key": key.strip()}, f, indent=2)

# =============================================================================
# 0. STYLE SHEET (GIAO DIỆN HIỆN ĐẠI)
# =============================================================================
APP_STYLE = """
/* Tổng thể ứng dụng */
QMainWindow {
    background-color: #f4f6f9;
}
QWidget {
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: #2c3e50;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #dcdde1;
    background: white;
    border-radius: 6px;
    top: -1px; 
}
QTabBar::tab {
    background: #ecf0f1;
    border: 1px solid #dcdde1;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
    color: #7f8c8d;
}
QTabBar::tab:selected {
    background: white;
    border-bottom-color: white;
    color: #2980b9;
}

/* Các nút bấm (Buttons) */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #bdc3c7;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    color: #2c3e50;
}
QPushButton:hover {
    background-color: #ecf0f1;
    border-color: #95a5a6;
}
QPushButton:pressed {
    background-color: #bdc3c7;
}

/* Nút chính (Primary - Blue) */
QPushButton[class="btn-primary"] {
    background-color: #3498db;
    color: white;
    border: none;
}
QPushButton[class="btn-primary"]:hover {
    background-color: #2980b9;
}

/* Nút thành công (Success - Green) */
QPushButton[class="btn-success"] {
    background-color: #2ecc71;
    color: white;
    border: none;
}
QPushButton[class="btn-success"]:hover {
    background-color: #27ae60;
}

/* Nút cảnh báo/xóa (Danger - Red) */
QPushButton[class="btn-danger"] {
    background-color: #e74c3c;
    color: white;
    border: none;
}
QPushButton[class="btn-danger"]:hover {
    background-color: #c0392b;
}

/* Nút cam (Warning) */
QPushButton[class="btn-warning"] {
    background-color: #f39c12;
    color: white;
    border: none;
}
QPushButton[class="btn-warning"]:hover {
    background-color: #d35400;
}

/* Input Fields & Combo Boxes */
QLineEdit, QComboBox, QSpinBox {
    padding: 6px;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    background-color: white;
    selection-background-color: #3498db;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #3498db;
}

/* Tables & Lists */
QTableWidget, QListWidget, QTreeWidget {
    background-color: white;
    border: 1px solid #dcdde1;
    border-radius: 6px;
    gridline-color: #ecf0f1;
    selection-background-color: #3498db;
    selection-color: white;
}
QHeaderView::section {
    background-color: #ecf0f1;
    padding: 8px;
    border: none;
    font-weight: bold;
    color: #2c3e50;
    border-bottom: 2px solid #bdc3c7;
    border-right: 1px solid #bdc3c7;
}

/* Group Box */
QGroupBox {
    font-weight: bold;
    border: 1px solid #bdc3c7;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 15px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
    color: #2980b9;
}

/* Text Edit */
QTextEdit {
    border: 1px solid #bdc3c7;
    border-radius: 6px;
    background-color: #fdfdfd;
}
"""

# =============================================================================
# 1. CẤU HÌNH & HẰNG SỐ HỆ THỐNG
# =============================================================================
# Xử lý đường dẫn Database thông minh (Tự động nhận diện khi đóng gói App)
# =============================================================================
# CẤU HÌNH ĐƯỜNG DẪN DATABASE (TỰ ĐỘNG TẠO MỚI CHO NGƯỜI DÙNG)
# =============================================================================
def get_database_path():
    db_filename = "bank_pro.db"
    
    # [FIX] Đổi sang thư mục ẩn tại Home Directory để tránh iCloud sync
    # Thay vì "Documents/BankAI_Data", ta dùng ".bankai_data" nằm ở thư mục gốc user
    user_data_dir = os.path.join(os.path.expanduser("~"), ".bankai_data")
    
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
        
    writable_db_path = os.path.join(user_data_dir, db_filename)
    
    # Logic kiểm tra và copy DB mẫu (giữ nguyên như cũ)
    if not os.path.exists(writable_db_path):
        source_path = None
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            potential_source = os.path.join(base_path, db_filename)
            if os.path.exists(potential_source): source_path = potential_source
            else:
                 potential_source = os.path.join(os.path.dirname(base_path), "Resources", db_filename)
                 if os.path.exists(potential_source): source_path = potential_source
        
        if source_path:
            try: shutil.copy2(source_path, writable_db_path)
            except: pass
        else:
            print(f"🆕 Tạo Database mới tại: {writable_db_path}")

    return writable_db_path

# Gán đường dẫn cuối cùng
DB_PATH = get_database_path()
print(f"📂 Database đang sử dụng: {DB_PATH}")


# API Key (Thay bằng key của bạn nếu cần)
MY_API_KEY = ""

# =============================================================================
# DỮ LIỆU CẤU TRÚC CHƯƠNG - BÀI (CHUẨN HÓA THEO FILE PDF ID6)
# =============================================================================
# =============================================================================
# DANH MỤC TÊN CHƯƠNG CHUẨN (CHỈ LẤY ĐẠI SỐ & HÌNH HỌC ĐỂ LÀM GỌN THỐNG KÊ)
# =============================================================================
CHAPTER_NAMES = {
    10: {
        'D': {1: "Mệnh đề. Tập hợp", 2: "BPT và hệ BPT bậc nhất hai ẩn", 3: "Hàm số bậc hai và đồ thị", 
              6: "Thống kê", 7: "Bất phương trình bậc 2 một ẩn", 8: "Đại số tổ hợp", 10: "Xác suất"},
        'H': {4: "Hệ thức lượng trong tam giác", 5: "Véctơ", 9: "Phương pháp toạ độ trong mặt phẳng (Oxy)"}
    },
    11: {
        'D': {1: "Hàm số lượng giác và PT lượng giác", 2: "Dãy số. CSC. CSN", 3: "Giới hạn. Hàm số liên tục", 
              5: "Các số đặc trưng (Ghép nhóm)", 6: "Hàm số mũ và lôgarít", 7: "Đạo hàm", 9: "Xác suất"},
        'H': {4: "Quan hệ song song trong không gian", 8: "Quan hệ vuông góc trong không gian"}
    },
    12: {
        'D': {1: "Ứng dụng đạo hàm", 3: "Các số đặc trưng (Ghép nhóm)", 4: "Nguyên hàm, tích phân", 6: "Xác suất"},
        'H': {2: "Tọa độ của véc-tơ (Oxyz)", 5: "PT mặt phẳng, đường thẳng, mặt cầu"}
    }
}

DATA_ID6_2025 = {
    10: {
        'D': { # ĐẠI SỐ 10
            1: { # Chương 1. Mệnh đề. Tập hợp
                1: "Mệnh đề",
                2: "Tập hợp",
                3: "Các phép toán tập hợp"
            },
            2: { # Chương 2. BPT và hệ BPT bậc nhất hai ẩn
                1: "Bất phương trình bậc nhất hai ẩn",
                2: "Hệ bất phương trình bậc nhất hai ẩn"
            },
            3: { # Chương 3. Hàm số bậc hai và đồ thị
                1: "Hàm số và đồ thị",
                2: "Hàm số bậc hai"
            },
            6: { # Chương 6. Thống kê
                1: "Số gần đúng. Sai số",
                2: "Mô tả và biểu diễn dữ liệu",
                3: "Các số đặc trưng đo xu thế trung tâm",
                4: "Các số đặc trưng đo mức độ phân tán"
            },
            7: { # Chương 7. Bất phương trình bậc 2 một ẩn
                1: "Dấu của tam thức bậc 2",
                2: "Giải bất phương trình bậc 2 một ẩn",
                3: "Phương trình quy về phương trình bậc hai"
            },
            8: { # Chương 8. Đại số tổ hợp
                1: "Quy tắc cộng - quy tắc nhân",
                2: "Hoán vị. Chỉnh hợp. Tổ hợp",
                3: "Nhị thức Newton"
            },
            10: { # Chương 10. Xác suất
                1: "Không gian mẫu và biến cố",
                2: "Xác suất của biến cố"
            }
        },
        'H': { # HÌNH HỌC 10
            4: { # Chương 4. Hệ thức lượng trong tam giác
                1: "Giá trị lượng giác của góc (0-180)",
                2: "Định lý sin và định lý côsin",
                3: "Giải tam giác và ứng dụng thực tế"
            },
            5: { # Chương 5. Véctơ (chưa xét tọa độ)
                1: "Khái niệm véctơ",
                2: "Tổng và hiệu của hai véctơ",
                3: "Tích của một số với véctơ",
                4: "Tích vô hướng (chưa xét tọa độ)"
            },
            9: { # Chương 9. Phương pháp toạ độ trong mặt phẳng (Oxy)
                1: "Toạ độ của véctơ",
                2: "Tích vô hướng (theo tọa độ)",
                3: "Đường thẳng trong mặt phẳng toạ độ",
                4: "Đường tròn trong mặt phẳng toạ độ",
                5: "Ba đường conic trong mặt phẳng toạ độ"
            }
        }
    },
    11: {
        'D': { # ĐẠI SỐ - GIẢI TÍCH 11
            1: { # Chương 1. Hàm số lượng giác và PT lượng giác
                1: "Góc lượng giác",
                2: "Giá trị lượng giác của một góc lượng giác",
                3: "Các công thức lượng giác",
                4: "Hàm số lượng giác và đồ thị",
                5: "Phương trình lượng giác cơ bản",
                6: "Phương trình lượng giác thường gặp (Giảm tải)"
            },
            2: { # Chương 2. Dãy số. CSC. CSN
                1: "Dãy số",
                2: "Cấp số cộng",
                3: "Cấp số nhân"
            },
            3: { # Chương 3. Giới hạn. Hàm số liên tục
                1: "Giới hạn của dãy số",
                2: "Giới hạn của hàm số",
                3: "Hàm số liên tục"
            },
            5: { # Chương 5. Các số đặc trưng... (Ghép nhóm)
                1: "Số trung bình và mốt của mẫu số liệu ghép nhóm",
                2: "Trung vị và tứ phân vị của mẫu số liệu ghép nhóm"
            },
            6: { # Chương 6. Hàm số mũ và hàm số lôgarít
                1: "Phép tính luỹ thừa",
                2: "Phép tính lôgarít",
                3: "Hàm số mũ. Hàm số lôgarít",
                4: "Phương trình, BPT mũ và lôgarít",
                5: "Các phương pháp giải được giảm tải"
            },
            7: { # Chương 7. Đạo hàm
                1: "Đạo hàm",
                2: "Các quy tắc đạo hàm",
                3: "Đạo hàm cấp hai"
            },
            9: { # Chương 9. Xác suất
                1: "Biến cố giao và quy tắc nhân xác suất",
                2: "Biến cố hợp và quy tắc cộng xác suất"
            }
        },
        'H': { # HÌNH HỌC 11
            4: { # Chương 4. Quan hệ song song trong không gian
                1: "Điểm, đường thẳng và mặt phẳng",
                2: "Hai đường thẳng song song",
                3: "Đường thẳng và mặt phẳng song song",
                4: "Hai mặt phẳng song song",
                5: "Hình lăng trụ và hình hộp (xiên)",
                6: "Phép chiếu song song"
            },
            8: { # Chương 8. Quan hệ vuông góc trong không gian
                1: "Hai đường thẳng vuông góc",
                2: "Đường thẳng vuông góc với mặt phẳng",
                3: "Phép chiếu vuông góc",
                4: "Hai mặt phẳng vuông góc",
                5: "Khoảng cách",
                6: "Góc giữa đường thẳng và mặt phẳng. Góc nhị diện",
                7: "Hình lăng trụ đứng. Hình chóp đều. Thể tích"
            }
        }
    },
    12: {
        'D': { # GIẢI TÍCH 12
            1: { # Chương 1. Ứng dụng đạo hàm
                1: "Sự đồng biến và nghịch biến của hàm số",
                2: "Cực trị của hàm số",
                3: "Giá trị lớn nhất và giá trị nhỏ nhất",
                4: "Đường tiệm cận",
                5: "Khảo sát sự biến thiên và vẽ đồ thị hàm số"
            },
            3: { # Chương 3. Các số đặc trưng... (Ghép nhóm)
                1: "Khoảng biến thiên, khoảng tứ phân vị (Ghép nhóm)",
                2: "Phương sai, độ lệch chuẩn (Ghép nhóm)"
            },
            4: { # Chương 4. Nguyên hàm, tích phân
                1: "Nguyên hàm",
                2: "Tích phân",
                3: "Ứng dụng thực tế và hình học của tích phân"
            },
            6: { # Chương 6. Một số yếu tố xác suất
                1: "Xác suất có điều kiện",
                2: "Công thức xác suất toàn phần. Công thức Bayes"
            }
        },
        'H': { # HÌNH HỌC 12 (Oxyz)
            2: { # Chương 2. Tọa độ của véc-tơ
                1: "Véc-tơ và các phép toán véc-tơ (chưa toạ độ)",
                2: "Toạ độ của véc-tơ và các công thức"
            },
            5: { # Chương 5. PT mặt phẳng, đường thẳng, mặt cầu
                1: "Phương trình mặt phẳng",
                2: "Phương trình đường thẳng trong không gian",
                3: "Phương trình mặt cầu trong không gian"
            }
        }
    }
}

MUC_DO = {
    'N': 'Nhận biết',
    'H': 'Thông hiểu', 
    'V': 'Vận dụng',
    'C': 'Vận dụng cao',
    'T': 'Toán thực tế'
}

# Danh mục 4 dạng câu hỏi
DANH_MUC_DANG = {
    1: "Trắc nghiệm (4 lựa chọn)",
    2: "Đúng/Sai",
    3: "Trả lời ngắn",
    4: "Tự luận",
}

# =============================================================================
# TEMPLATE LATEX AN TOÀN (FIX LỖI EMERGENCY STOP)
# =============================================================================
# Thay thế toàn bộ biến LATEX_TEMPLATE bằng đoạn này:
LATEX_TEMPLATE = r"""
\documentclass[12pt,a4paper]{article} % [FIX] Dùng article cho an toàn

% --- GÓI CƠ BẢN & TIẾNG VIỆT ---
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage[shorthands=off,vietnamese]{babel}
\usepackage{amsmath,amssymb,mathrsfs}
\usepackage{geometry}
\geometry{top=1.5cm, bottom=1.5cm, left=2cm, right=1.5cm} % Căn lề rộng để dễ đọc trên web

% --- ĐỒ HỌA & MÀU SẮC ---
\usepackage{graphicx, xcolor, tikz, tkz-euclide, pgfplots}
\usepackage{tikz-3dplot,tkz-tab,tabvar}
\usepackage{tcolorbox}
\pgfplotsset{compat=1.18}
\usetikzlibrary{arrows, calc, intersections, angles, quotes, backgrounds, shapes.geometric}

% --- ĐỊNH NGHĨA MÀU (Theo file của bạn để tránh lỗi) ---
\definecolor{mainbrown}{HTML}{582704}
\definecolor{mainbrown1}{HTML}{AD5A04}
\definecolor{myframe1}{HTML}{B93A30}
\definecolor{mauVD}{HTML}{AC203D}
\definecolor{mauBT}{HTML}{041F60}

% --- CẤU HÌNH EX_TEST (XỬ LÝ LỖI ẨN CÂU HỎI) ---
\IfFileExists{ex_test.sty}{
    \usepackage[dethi]{ex_test}
    % [FIX QUAN TRỌNG] Ghi đè OPTN: addquestions=1 (Hiện câu hỏi), exbreak=0 (Không ngắt trang vô lý)
    \OPTN{exbreak=0,explain=0,kindTF=0,addanswers=1,addquestions=1} 
}{
    % --- DỰ PHÒNG (FALLBACK) ---
    \newcounter{ex}
    \newenvironment{ex}{\stepcounter{ex}\par\noindent\textbf{Câu \theex.}}{\par\vspace{0.5cm}}
    \newenvironment{bt}{\begin{ex}}{\end{ex}}
    \newenvironment{vd}{\begin{ex}}{\end{ex}}
    \newcommand{\choice}[4]{\par\noindent\begin{tabular}{p{0.22\textwidth}p{0.22\textwidth}p{0.22\textwidth}p{0.22\textwidth}}\textbf{A.} #1 & \textbf{B.} #2 & \textbf{C.} #3 & \textbf{D.} #4\end{tabular}}
    \newcommand{\choiceTF}[4]{\par\noindent\begin{itemize}\item a) #1 \item b) #2 \item c) #3 \item d) #4\end{itemize}}
    \newcommand{\shortans}[1]{\par\noindent\textbf{Đáp án:} \underline{#1}}
    \newcommand{\loigiai}[1]{\par\noindent\textit{\textbf{Lời giải:} #1}}
    \def\True{}
}

% --- LỆNH BỔ TRỢ ---
\usepackage{esvect}
\def\vec{\vv}
% [FIX] ĐỊNH NGHĨA HỆ PHƯƠNG TRÌNH (QUAN TRỌNG)
\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}
\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}
\begin{document}
% [FIX] Thêm null để đảm bảo luôn có ít nhất 1 object trên trang (tránh lỗi No output)
\null
__CONTENT__
\end{document}
"""

# =============================================================================
# 2. AI ENGINE (XỬ LÝ THÔNG MINH 4 DẠNG)
# =============================================================================
class AIEngine:
    def __init__(self, api_key):
        self.is_ready = False
        if not api_key: return
        import google.generativeai as genai

        genai.configure(api_key=api_key.strip())
        try:
            genai.configure(api_key=api_key.strip())
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
        
        Args:
            tex (str): Nội dung LaTeX của câu hỏi mẫu
            
        Returns:
            tuple: (nội dung LaTeX mới đã chuẩn hóa, key đáp án đúng: 'A'/'B'/'C'/'D')
        """
        if not self.is_ready:
            print("❌ AI Engine chưa sẵn sàng, trả về câu gốc")
            return tex, "A"

        # Prompt được viết lại rõ ràng, chi tiết hơn để Gemini trả về đúng định dạng
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

                # Kiểm tra response hợp lệ
                if not res.candidates:
                    print("⚠️ Không nhận được candidates từ API")
                    return tex, "A"

                if hasattr(res.candidates[0], 'finish_reason') and res.candidates[0].finish_reason == 3:
                    print("⚠️ Bị chặn bởi bộ lọc an toàn (finish_reason=3)")
                    return tex, "A"

                # Lấy nội dung trả về
                txt = res.text.strip()
                txt = txt.replace("```latex", "").replace("```tex", "").replace("```", "").strip()

                # Trích xuất KEY nếu có
                key = "A"
                key_match = re.search(r"\[KEY:\s*([A-D])\s*\]", txt, re.IGNORECASE)
                if key_match:
                    key = key_match.group(1).strip().upper()
                    txt = txt.replace(key_match.group(0), "").strip()

                # Chuẩn hóa cấu trúc LaTeX (giữ nguyên hàm cũ của bạn)
                structured_text = self._force_structure(txt, tex)

                print(f"✅ Thành công! Đáp án đúng: {key}")
                return structured_text, key

            except Exception as e:
                error_str = str(e).lower()

                # Xử lý lỗi quota (429)
                if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                    wait_time = base_wait_seconds * (2 ** attempt)  # 30s → 60s → 120s → 240s → 480s
                    print(f"⚠️ Quota exceeded (429) → chờ {wait_time} giây (lần {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                # Các lỗi khác → không retry, trả về câu gốc ngay
                else:
                    print(f"❌ Lỗi khác khi gọi API: {str(e)}")
                    return tex, "A"

        # Hết lượt thử
        print(f"❌ Đã thử {max_retries} lần nhưng thất bại → trả về câu hỏi gốc")
        return tex, "A"
# =============================================================================
# 3. BACKGROUND WORKERS
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
            
            # 1. Generate TeX Body
            body_content = [
                r"\begin{center}\textbf{\Large " + self.title + r"}\end{center}",
                r"\setcounter{ex}{0}"
            ]
            
            # Simple sorting/grouping similar to ExamPreparerWorker
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
            
            # 2. Compile PDF
            self.progress.emit("Đang biên dịch PDF (LaTeX)...")
            import time
            pdf_name = f"homework_{int(time.time())}"
            msg, pdf_path = PDFCompiler.compile_tex_to_pdf(final_tex, pdf_name)
            
            if not pdf_path:
                self.finished.emit(False, f"Lỗi biên dịch: {msg}")
                return

            # 3. Upload & Create Assignment
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
                # Xóa các file cũ hơn 1 ngày hoặc xóa hết
                for f in os.listdir(CACHE_DIR):
                    if not f.endswith(".svg"): # Giữ lại SVG
                        try:
                            fp = os.path.join(CACHE_DIR, f)
                            # Kiểm tra thời gian tạo, nếu muốn
                            os.remove(fp)
                        except: pass
        except: pass

def extract_metadata_from_tex(tex, q_type):
    """Trích xuất Key và Lời giải từ nội dung LaTeX"""
    key = "?"
    explanation = ""
    try:
        # 1. Lấy lời giải
        expl, _ = LatexParser.extract_command(tex, "loigiai")
        if expl: explanation = expl.strip()
        
        # 2. Lấy Key
        if q_type == 1: # MCQ
            m = re.search(r"\[KEY:\s*([A-D])\]", tex, re.IGNORECASE)
            if m: key = m.group(1).upper()
            else:
                args, _ = LatexParser.extract_multiple_args(tex, "choice")
                for i, arg in enumerate(args):
                    if "\\True" in arg: key = ['A','B','C','D'][i]; break
        elif q_type == 2: # TF
            args, _ = LatexParser.extract_multiple_args(tex, "choiceTF")
            if args:
                tf_res = {}
                for i, arg in enumerate(args):
                    sub = ['a','b','c','d'][i]
                    tf_res[sub] = "Đ" if "\\True" in arg else "S"
                key = tf_res
        elif q_type == 3: # Short
            k, _ = LatexParser.extract_command(tex, "shortans")
            if k: key = k.strip()
    except: pass
    return key, explanation

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
            import random, copy, time
            
            variants_list = []
            
            # Khởi tạo Mixer
            mixer = ExamMixer() if 'ExamMixer' in globals() else None

            # LOOP VARIANT
            for v_idx in range(self.num_variants):
                code = str(101 + v_idx)
                self.progress.emit(f"Đang tạo mã đề {code} ({v_idx+1}/{self.num_variants})...")
                
                # 1. Clone & Shuffle
                qs_clone = copy.deepcopy(self.questions)
                
                # Chỉ trộn câu hỏi nếu tạo nhiều mã đề HOẶC không dùng file ngoài
                if self.num_variants > 1 or not self.external_tex:
                    random.shuffle(qs_clone)
                
                # 2. Trộn đáp án (Chỉ Trắc nghiệm)
                if mixer:
                    for q in qs_clone:
                        if q.get('dang', 4) == 1: # TN
                            tex = q.get('content_tex', '')
                            # Hàm permute_content trả về (tex_mới, key_mới)
                            new_tex, new_key = mixer.permute_content(tex)
                            q['content_tex'] = new_tex
                            q['key'] = new_key

                # 3. Sắp xếp lại theo Dạng (để in ra PDF đẹp)
                for q in qs_clone: q['dang'] = q.get('dang', 4)
                qs_clone.sort(key=lambda x: x['dang'])

                # 4. Generate Body
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
                    
                    # [Standardize] Extract Key & Explanation
                    final_key = q.get('key')
                    explanation = ""
                    
                    # Luôn kiểm tra lại từ TeX để lấy key/explanation chính xác nhất
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

                # 5. Compile PDF
                final_tex = ""
                if self.external_tex and os.path.exists(self.external_tex) and self.num_variants == 1:
                    # Nếu dùng file ngoài và chỉ 1 đề -> Dùng nguyên bản
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

            # Result Payload
            first = variants_list[0]
            result_payload = {
                "title": self.title,
                "duration": self.duration * 60,
                # Backward compat
                "pdf_filename": first["pdf_filename"],
                "exam_matrix": first["exam_matrix"],
                # New feature
                "variants": variants_list
            }
            self.finished.emit(True, result_payload)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, {"error": f"Lỗi hệ thống: {str(e)}"})

class AutoIDWorker(QThread):
    progress = pyqtSignal(int, str)
    item_finished = pyqtSignal(int, dict) # Trả về row_index và dữ liệu dự đoán
    finished = pyqtSignal()

    def __init__(self, ai_engine, questions, syllabus_data):
        super().__init__()
        self.ai = ai_engine
        self.questions = questions # Danh sách các câu hỏi trong bảng
        self.syllabus = syllabus_data # DATA_ID6_2025 để AI tham chiếu

    def run(self):
        # Chuyển syllabus thành text rút gọn để tiết kiệm token
        syllabus_text = json.dumps(self.syllabus, ensure_ascii=False)
        
        total = len(self.questions)
        for idx, q in enumerate(self.questions):
            if self.isInterruptionRequested(): break
            
            # Chỉ xử lý các câu chưa có ID
            if q.get('id6'): continue

            self.progress.emit(int((idx/total)*100), f"Đang phân tích câu {idx+1}/{total}...")
            
            content = q['content_tex']
            if len(content) > 2000: content = content[:2000] + "..." # Cắt ngắn nếu quá dài

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
                # Gọi AI
                response = self.ai.model.generate_content(prompt)
                txt = response.text.strip()
                
                # [FIX] Robust parsing: Try to find JSON object structure
                match = re.search(r"\{.*\}", txt, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    data = json.loads(json_str)
                else:
                    # Fallback: try raw cleaning
                    clean_txt = txt.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_txt)
                
                # Gửi kết quả về UI
                self.item_finished.emit(idx, data)
                
                # Nghỉ nhẹ để tránh spam API
                time.sleep(1.5) 
                
            except Exception as e:
                print(f"Lỗi AI câu {idx}: {e}")
                # print(f"Raw response: {txt if 'txt' in locals() else 'None'}")
        
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
                
                # --- FIX LỖI KeyError: 'content' ---
                # Kiểm tra cả 'content_tex' và 'content', nếu không có thì bỏ qua
                content_text = q.get('content_tex')
                if not content_text:
                    content_text = q.get('content')
                
                if not content_text:
                    print(f"⚠️ Warning: Câu {idx+1} không có nội dung, bỏ qua.")
                    continue
                # -----------------------------------

                try:
                    new_c, key = self.ai.generate_safe(content_text)
                    res[code].append({
                        "idx": idx + 1, 
                        "content": new_c, 
                        "key": key, 
                        "orig_id": q.get('id', 0),
                        "dang": q.get('dang', 4) # Copy dang cau hoi
                    })
                except Exception as e:
                    print(f"❌ Error generating question {idx+1}: {e}")
                    # Thêm câu gốc vào nếu lỗi để không bị thiếu
                    res[code].append({
                        "idx": idx + 1, 
                        "content": content_text, 
                        "key": "A (Error)", 
                        "orig_id": q.get('id', 0),
                        "dang": q.get('dang', 4)
                    })

        self.finished.emit(res)

# Thay thế class ImportWorker cũ
class ImportWorker(QThread):
    progress = pyqtSignal(int, str)
    analysis_done = pyqtSignal(list, dict)  # Trả về: (Danh sách câu hỏi, Danh sách ảnh)
    error = pyqtSignal(str)

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        all_questions = []
        all_images = {}
        
        # [FIX] Khởi tạo Backend cục bộ cho luồng này
        # Điều này tạo một kết nối SQLite riêng, an toàn tuyệt đối cho Thread
        local_bk = Backend() 
        
        try:
            n = len(self.files)
            for i, f in enumerate(self.files):
                if self.isInterruptionRequested(): break
                
                p = int((i / n) * 100)
                fname = os.path.basename(f)
                self.progress.emit(p, f"Đang phân tích: {fname}...")
                
                # Sử dụng hàm của backend cục bộ
                qs, imgs = local_bk.analyze_tex_file(f)
                all_questions.extend(qs)
                all_images.update(imgs)
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # [QUAN TRỌNG] Đóng kết nối cục bộ khi luồng kết thúc
            if hasattr(local_bk, 'conn'):
                local_bk.conn.close()
            
        # Gửi dữ liệu về luồng chính để lưu (Main Thread sẽ thực hiện lệnh INSERT)
        self.analysis_done.emit(all_questions, all_images)

class SingleRegenWorker(QThread):
    done = pyqtSignal(str, str)
    def __init__(self, ai, tex): super().__init__(); self.ai, self.tex = ai, tex
    def run(self): c, k = self.ai.generate_safe(self.tex); self.done.emit(c, k)

class PDFCompiler:
    """Biên dịch file PDF đề gốc - Tự động copy file sty và Debug lỗi chi tiết"""
    @staticmethod
    def compile_tex_to_pdf(tex_content, output_name):
        import subprocess
        import os
        import shutil
        
        build_dir = os.path.join(os.path.expanduser("~"), ".bankai_build")
        if not os.path.exists(build_dir): os.makedirs(build_dir)
        
        # [QUAN TRỌNG] Copy file ex_test.sty từ thư mục chạy app vào thư mục build
        # Để LaTeX tìm thấy gói lệnh định dạng đề thi
        # Sử dụng hàm resource_path để tìm file ex_test.sty đã đóng gói
        if getattr(sys, 'frozen', False):
            # Nếu đang chạy trong app đóng gói -> Lấy từ thư mục tạm của PyInstaller
            current_dir = sys._MEIPASS
        else:
            # Nếu đang chạy code thường -> Lấy thư mục hiện tại
            current_dir = os.path.dirname(os.path.abspath(__file__)) 
        sty_name = "ex_test.sty"
        src_sty = os.path.join(current_dir, sty_name)
        dst_sty = os.path.join(build_dir, sty_name)
        
        if os.path.exists(src_sty):
            try:
                shutil.copy(src_sty, dst_sty)
                print(f"✅ Đã copy {sty_name} vào thư mục build.")
            except Exception as e:
                print(f"⚠️ Cảnh báo: Không copy được {sty_name}: {e}")
        else:
            print(f"⚠️ Cảnh báo: Không tìm thấy file {sty_name} tại {current_dir}")
        
        tex_path = os.path.join(build_dir, f"{output_name}.tex")
        pdf_path = os.path.join(build_dir, f"{output_name}.pdf")

        try:
            # Ghi file tex
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(tex_content)
            
            # Biên dịch (Timeout 60s)
            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={build_dir}", tex_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60
            )
            
            if os.path.exists(pdf_path):
                return "Thành công", pdf_path
            else:
                # [DEBUG] In 50 dòng cuối của log lỗi ra màn hình để bạn biết sửa chỗ nào
                log_content = process.stdout.decode('utf-8', errors='ignore')
                print(f"\n❌ LỖI CHI TIẾT KHI TẠO PDF ({output_name}):")
                print("="*60)
                print(log_content[-1500:]) # In 1500 ký tự cuối
                print("="*60)
                return "Lỗi biên dịch LaTeX (Xem log chi tiết ở trên)", None

        except Exception as e:
            return str(e), None

class ImageCompiler:
    """Biên dịch đoạn code LaTeX sang file ảnh PNG (Đã sửa lỗi xung đột ký tự %)"""
    @staticmethod
    def compile_question_to_png(tex_content, output_name):
        from pdf2image import convert_from_path
        import subprocess
        import os
        
        # Template tương thích với file Khai báo của bạn
        template = r"""
\documentclass[preview,border=3pt,varwidth=18cm]{standalone} % Dùng varwidth để gói văn bản dài
\usepackage[utf8]{inputenc}   
\usepackage[T5]{fontenc}      
\usepackage[vietnamese]{babel}
\usepackage{amsmath,amssymb,mathrsfs,mathabx}
\usepackage{tikz, tkz-euclide, pgfplots, tikz-3dplot}
\usepackage[most]{tcolorbox}
\usepackage{esvect}

% --- Load gói màu sắc ---
\usepackage{xcolor}
\definecolor{mainbrown}{HTML}{582704}
\definecolor{mauVD}{HTML}{AC203D}
\definecolor{mauBT}{HTML}{041F60}

% --- Cấu hình TikZ ---
\usetikzlibrary{arrows, calc, intersections, angles, quotes, backgrounds, shapes.geometric}
\usetikzlibrary{decorations.markings, bending, patterns.meta, shadows}
\pgfplotsset{compat=1.18}

% --- Load ex_test (nếu có) ---
\IfFileExists{ex_test.sty}{\usepackage[dethi]{ex_test}}{}

% --- Lệnh hỗ trợ ---
\def\vec{\vv}
\def\True{} 
\renewcommand{\arraystretch}{1.2}
% [FIX] ĐỊNH NGHĨA HỆ PHƯƠNG TRÌNH (QUAN TRỌNG)
\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}
\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}
\begin{document}
__CONTENT__
\end{document}
""" 
        # SỬA LỖI: Dùng .replace() thay vì % để tránh lỗi syntax với ký tự % trong LaTeX
        full_tex = template.replace("__CONTENT__", tex_content)

        # Thư mục build tạm
        build_dir = os.path.join(os.path.expanduser("~"), ".bankai_build")
        if not os.path.exists(build_dir): os.makedirs(build_dir)
        
        tex_path = os.path.join(build_dir, f"{output_name}.tex")
        pdf_path = os.path.join(build_dir, f"{output_name}.pdf")
        png_path = os.path.join(build_dir, f"{output_name}.png")

        try:
            # B1: Ghi file TeX (Ghi full_tex chứ không phải template gốc)
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(full_tex)
            
            # B2: Gọi lệnh pdflatex để biên dịch
            # Timeout 30s để xử lý hình vẽ phức tạp
            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={build_dir}", tex_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
            )
            
            # Nếu không tạo được PDF -> Lỗi LaTeX
            if not os.path.exists(pdf_path):
                print(f"❌ Lỗi biên dịch LaTeX ({output_name}):")
                # In 10 dòng cuối của log lỗi để debug
                print(process.stdout.decode('utf-8', errors='ignore')[-500:]) 
                return None
            
            # B3: Chuyển PDF sang PNG bằng pdf2image
            try:
                images = convert_from_path(pdf_path, dpi=400)
                if images:
                    images[0].save(png_path, 'PNG')
                    print(f"✅ Đã tạo ảnh: {output_name}")
                    return png_path
            except Exception as e_poppler:
                print(f"❌ Lỗi Poppler (pdf2image): {e_poppler}")
                print("💡 Gợi ý: Bạn cần cài đặt Poppler và thêm vào PATH.")
                return None

        except Exception as e:
            print(f"❌ Lỗi hệ thống ImageCompiler: {e}")
        
        return None

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
        self.service_forms = None # Service mới
        self.token_path = os.path.join(os.path.expanduser("~"), ".bankai_data", "token.json")
        self.cred_path = "credentials.json"

    def authenticate(self):
        """Xác thực OAuth2 (Có cơ chế tự động fix lỗi Token/Scope)"""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        try:
            if os.path.exists(self.token_path):
                self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            # Kiểm tra hiệu lực token
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                    except Exception:
                        # Nếu refresh lỗi (do đổi scope), xóa token để đăng nhập lại
                        print("Token hết hạn hoặc sai Scope -> Xóa để cấp mới.")
                        if os.path.exists(self.token_path): os.remove(self.token_path)
                        self.creds = None
                
                if not self.creds:
                    if not os.path.exists(self.cred_path):
                        raise FileNotFoundError("Chưa có file credentials.json! Hãy tải từ Google Cloud Console.")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(self.cred_path, self.SCOPES)
                    self.creds = flow.run_local_server(port=0, open_browser=True)
                
                # Lưu token mới
                parent_dir = os.path.dirname(self.token_path)
                if not os.path.exists(parent_dir): os.makedirs(parent_dir)
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())

            # Khởi tạo Services
            self.service_class = build('classroom', 'v1', credentials=self.creds)
            self.service_drive = build('drive', 'v3', credentials=self.creds)
            self.service_forms = build('forms', 'v1', credentials=self.creds)

        except Exception as e:
            # Nếu gặp lỗi invalid_scope, tự động xóa token để lần sau chạy lại sẽ đăng nhập mới
            if "invalid_scope" in str(e):
                if os.path.exists(self.token_path): os.remove(self.token_path)
                raise Exception("Lỗi Quyền (Scope). Đã xóa token cũ. Vui lòng CHẠY LẠI phần mềm và đăng nhập lại!")
            raise e

    # --- CÁC HÀM CŨ (QUAN TRỌNG) ---
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
        from googleapiclient.http import MediaFileUpload
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
            # 1. Upload file lên Drive
            file_id = self.upload_to_drive(pdf_path)
            
            # 2. Tạo bài tập với file đính kèm
            link = self.create_assignment(course_id, title, description, file_id)
            return True, link
        except Exception as e:
            return False, str(e)

    # --- CÁC HÀM MỚI (CHO GOOGLE FORMS & ẢNH) ---
    # Tìm trong class GoogleManagerFull
    def upload_image(self, file_path):
        """Upload ảnh lên Drive, SET PUBLIC và trả về ID (Fix lỗi Failed to fetch)"""
        from googleapiclient.http import MediaFileUpload
        file_metadata = {'name': os.path.basename(file_path)}
        media = MediaFileUpload(file_path, mimetype='image/png')
        
        # 1. Upload file
        file = self.service_drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        
        # 2. [QUAN TRỌNG] Cấp quyền "Anyone can view" để Google Forms có thể đọc được ảnh
        try:
            self.service_drive.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
        except Exception as e:
            print(f"Lỗi set permission: {e}")
            
        return file_id

    def create_quiz_form(self, title, description):
        """Tạo một Google Form mới và sau đó chuyển sang chế độ Quiz (Đã Fix lỗi API 400)"""
        # 1. Tạo Form (Google bắt buộc chỉ được gửi info.title lúc tạo)
        initial_body = {
            "info": {
                "title": title
            }
        }
        form = self.service_forms.forms().create(body=initial_body).execute()
        form_id = form['formId']
        
        # 2. Gửi lệnh cập nhật bổ sung: Bật Quiz + Thêm mô tả
        # Phải tách ra bước 2 mới được chấp nhận
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
# =============================================================================
# 4. DATABASE BACKEND
# =============================================================================
class Backend:
    # Thêm vào class Backend
    def get_dashboard_stats(self):
        """Lấy số liệu thống kê chi tiết cho Dashboard"""
        # 1. Tổng số câu toàn ngân hàng
        total = self.conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        
        # 2. Thống kê theo mức độ (Toàn bộ)
        levels = self.conn.execute("SELECT level, COUNT(*) FROM questions GROUP BY level").fetchall()
        level_map = {row[0]: row[1] for row in levels}
        
        # 3. Thống kê chi tiết Group theo: Lớp -> Môn -> Chương
        # Query này sẽ nhóm dữ liệu để ta dựng cây thư mục
        query = """
            SELECT grade, subject, chapter, level, COUNT(*) 
            FROM questions 
            GROUP BY grade, subject, chapter, level
            ORDER BY grade, subject, chapter
        """
        rows = self.conn.execute(query).fetchall()
        
        return total, level_map, rows

    def __init__(self):
        # check_same_thread=False là bắt buộc
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # [FIX] Bật chế độ WAL để tăng tốc và tránh lỗi I/O khi ghi nhiều
        try:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
        except:
            pass
            
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, grade INTEGER, subject TEXT, chapter INTEGER, level TEXT, content_tex TEXT, raw_data TEXT, dang INTEGER DEFAULT 4, id6 TEXT, bai INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        self.conn.commit()
        self._migrate_db()
        # [MỚI] Bảng lưu kết quả thi
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                exam_title TEXT,
                score REAL,
                detail TEXT, -- Lưu JSON chi tiết đúng sai
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        self._migrate_db()
    
    def _migrate_db(self):
        try:
            cur = self.conn.execute("PRAGMA table_info(questions)")
            cols = [r[1] for r in cur.fetchall()]
            if 'dang' not in cols: self.conn.execute("ALTER TABLE questions ADD COLUMN dang INTEGER DEFAULT 4")
            if 'id6' not in cols: self.conn.execute("ALTER TABLE questions ADD COLUMN id6 TEXT")
            if 'bai' not in cols: self.conn.execute("ALTER TABLE questions ADD COLUMN bai INTEGER")
            self.conn.commit()
        except: pass

# Tìm và thay thế hàm import_tex cũ bằng đoạn này
    # Tìm trong class Backend và thay thế hàm analyze_tex_file cũ
    def analyze_tex_file(self, path):
        """
        Phiên bản nâng cấp: Quét ID6 mọi vị trí + Tự động bóc tách Chương/Bài/Dạng chuẩn xác
        [FIX] Sửa lỗi nhận diện sai dạng Trắc nghiệm thành Tự luận
        """
        questions = []
        detected_images = {}
        
        try:
            with open(path, 'r', encoding='utf-8') as f: content = f.read()
        except:
            try: 
                with open(path, 'r', encoding='utf-16') as f: content = f.read()
            except: return [], {}

        # Regex tìm khối câu hỏi (ex hoặc bt)
        matches = re.finditer(r"\\begin\s*\{(?:ex|bt)\}(.*?)\\end\s*\{(?:ex|bt)\}", content, re.DOTALL)
        
        for m in matches:
            raw = m.group(0) # Toàn bộ khối \begin...\end
            block = m.group(1) # Nội dung bên trong
            
            # --- 1. QUÉT TÌM ID6 Ở BẤT KỲ VỊ TRÍ NÀO ---
            id_pattern = r"\[([0-2])([DHC])(\d+)([NHVC])(\d+)-(\d+)\]"
            id_match = re.search(id_pattern, raw)
            
            # Giá trị mặc định nếu không tìm thấy ID
            id6 = None
            g, s, ch, l, bai, dang_id = 12, "D", 1, "N", 0, 0
            
            if id_match:
                full_tag = id_match.group(0)
                id6 = full_tag.replace("[", "").replace("]", "")
                gc, sc, chc, lc, bc, dc = id_match.groups()
                
                g = {'0':10, '1':11, '2':12}.get(gc, 12)
                s = sc
                ch = int(chc)
                l = lc
                bai = int(bc)
                dang_id = int(dc)
            else:
                # Fallback: Thử tìm ID kiểu cũ
                short_match = re.search(r"\[([0-2])([DHC])(\d+)([NHVCTYBKG])\]", raw)
                if short_match:
                    full_tag = short_match.group(0)
                    id6 = full_tag.replace("[", "").replace("]", "")
                    gc, sc, chc, lc = short_match.groups()
                    g = {'0':10, '1':11, '2':12}.get(gc, 12)
                    s = sc
                    ch = int(chc)
                    l_map = {'Y':'N', 'B':'H', 'K':'V', 'G':'C'}
                    l = l_map.get(lc, lc)

            # --- 2. XÁC ĐỊNH LOẠI CÂU HỎI [ĐÃ SỬA LỖI TẠI ĐÂY] ---
            # Logic cũ quá khắt khe (bắt buộc có { hoặc [). Logic mới chỉ cần chứa từ khóa.
            # Ưu tiên check \choiceTF trước vì từ này chứa cả chữ "choice"
            dang = 4 # Mặc định Tự luận
            
            if r"\choiceTF" in block: 
                dang = 2 # Đúng/Sai
            elif r"\choice" in block: 
                dang = 1 # Trắc nghiệm
            elif r"\shortans" in block: 
                dang = 3 # Trả lời ngắn
            
            # --- 3. QUÉT ẢNH ---
            img_matches = re.findall(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}", raw)
            tex_dir = os.path.dirname(path)
            for img in img_matches:
                candidate_path = os.path.join(tex_dir, img.strip())
                if os.path.exists(candidate_path): 
                    detected_images[img.strip()] = candidate_path.replace("\\", "/")

            q_obj = {
                'grade': g, 'subject': s, 'chapter': ch, 'level': l,
                'content_tex': raw, 'raw_data': raw, 'dang': dang,
                'id6': id6, 'bai': bai
            }
            questions.append(q_obj)
            
        return questions, detected_images

    def insert_questions_list(self, q_list):
        """Lưu danh sách câu hỏi đã xử lý vào Database"""
        added = 0
        skipped = 0
        
        # Bắt đầu transaction để lưu nhanh
        self.conn.execute("BEGIN TRANSACTION")
        try:
            for q in q_list:
                # Check trùng
                exists = self.conn.execute("SELECT 1 FROM questions WHERE content_tex = ?", (q['content_tex'],)).fetchone()
                if exists:
                    skipped += 1
                    continue
                
                self.conn.execute(
                    "INSERT INTO questions (grade, subject, chapter, level, content_tex, raw_data, dang, id6, bai) VALUES (?,?,?,?,?,?,?,?,?)",
                    (q['grade'], q['subject'], q['chapter'], q['level'], q['content_tex'], q['raw_data'], q['dang'], q['id6'], q['bai'])
                )
                added += 1
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
            
        return added, skipped

    # Cập nhật trong class Backend
    def get_all_filtered(self, g, s, c, b, l, dang, limit=None): # Thêm tham số b (bài)
        q = "SELECT * FROM questions WHERE 1=1"
        p = []
        if g: q+=" AND grade=?"; p.append(g)
        if s: q+=" AND subject=?"; p.append(s)
        if c: q+=" AND chapter=?"; p.append(c)
        if b and b!=0: q+=" AND bai=?"; p.append(b) # Lọc theo bài
        if l: q+=" AND level=?"; p.append(l)
        if dang and dang!=0: q+=" AND dang=?"; p.append(dang)
        q += " ORDER BY id"
        if limit: q += f" LIMIT {limit}"
        return [dict(r) for r in self.conn.execute(q, tuple(p)).fetchall()]

    def get_rnd(self, g, s, ch, bai, l, dang=None, exc=None): # Thêm tham số bai
        q = "SELECT * FROM questions WHERE grade=? AND subject=? AND chapter=? AND level=?"
        p = [g, s, ch, l]
        if bai and bai != 0: q+=" AND bai=?"; p.append(bai) # Lọc theo bài
        if dang and dang!=0: q+=" AND dang=?"; p.append(dang)
        if exc: q+=" AND id != ?"; p.append(exc)
        res = self.conn.execute(q+" ORDER BY RANDOM() LIMIT 1", tuple(p)).fetchone()
        return dict(res) if res else None
    
    def get_stats(self):
        stats = {}
        for g in [10,11,12]:
            stats[g] = {}
            for s in ['D','H']:
                res = self.conn.execute("SELECT chapter, level, COUNT(*) FROM questions WHERE grade=? AND subject=? GROUP BY chapter, level", (g,s)).fetchall()
                stats[g][s] = {}
                for r in res:
                    if r[0] not in stats[g][s]: stats[g][s][r[0]] = {}
                    stats[g][s][r[0]][r[1]] = r[2]
        return stats

    def get_unassigned(self, limit=100):
        return [dict(r) for r in self.conn.execute("SELECT * FROM questions WHERE id6 IS NULL OR id6 = '' LIMIT ?", (limit,)).fetchall()]
        
    def get_exam_results(self):
        """Lấy toàn bộ lịch sử thi"""
        return self.conn.execute("SELECT * FROM exam_results ORDER BY submitted_at DESC").fetchall()

    # Tìm hàm này trong class Backend và thay thế toàn bộ
    def update_id6(self, qid, id6, g, s, c, l, b, d, new_content):
        """Cập nhật ID6 và Nội dung LaTeX mới vào Database"""
        query = """
            UPDATE questions 
            SET id6=?, grade=?, subject=?, chapter=?, level=?, bai=?, dang=?, content_tex=? 
            WHERE id=?
        """
        self.conn.execute(query, (id6, g, s, c, l, b, d, new_content, qid))
        self.conn.commit()

# =============================================================================
# 5. CUSTOM WIDGETS
# =============================================================================
class ModernSidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260) # Sidebar width
        self.setStyleSheet("""
            QWidget { background-color: #fdfdfd; border-right: 1px solid #e0e0e0; }
            QPushButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                background-color: transparent;
                color: #555;
                font-weight: 600;
                font-size: 15px;
                margin: 4px 12px;
            }
            QPushButton:hover {
                background-color: #f5f6fa;
                color: #2c3e50;
            }
            QPushButton:checked {
                background-color: #ED840D; /* Original Brand Color */
                color: white;
                font-weight: bold;
            }
            QLabel {
                color: #95a5a6; font-weight: bold; font-size: 11px;
                margin-top: 25px; margin-left: 20px; margin-bottom: 8px;
                text-transform: uppercase; letter-spacing: 0.5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 25, 0, 25)
        layout.setSpacing(6)
        
        # Logo Area
        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(25, 0, 20, 20)
        lbl_logo = QLabel("🏛️ BANKAI PRO")
        lbl_logo.setStyleSheet("font-size: 24px; font-weight: 900; color: #d35400; margin: 0; letter-spacing: -0.5px;")
        logo_layout.addWidget(lbl_logo)
        layout.addLayout(logo_layout)
        
        self.btn_group = QButtonGroup()
        self.btn_group.setExclusive(True)
        
        # Navigation Items
        self.add_label(layout, "Trung tâm điều khiển")
        self.btn_dashboard = self.add_btn(layout, "🏠  Trang chủ / Thống kê", 0)
        
        self.add_label(layout, "Ngân hàng câu hỏi")
        self.btn_manual = self.add_btn(layout, "✏️  Soạn đề Thủ công", 1)
        self.btn_matrix = self.add_btn(layout, "🎲  Ma trận 2025 (Auto)", 2)
        self.btn_ai = self.add_btn(layout, "🤖  AI Generator", 3)
        # --- [CHÈN VÀO ĐÂY] ---
        self.btn_classroom = self.add_btn(layout, "🏫  Google Classroom", 4)
        self.btn_dashboard = self.add_btn(layout, "📊 Thống kê & Phân tích", 5)
        # ----------------------
        
        layout.addStretch()
        
        # Bottom Items
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
    def __init__(self, p=None): super().__init__(p); self.setDragEnabled(True); self.setSelectionMode(QListWidget.SelectionMode.SingleSelection); self.setAlternatingRowColors(True)
    def startDrag(self, actions):
        i = self.currentItem()
        if not i: return
        q_data = i.data(Qt.ItemDataRole.UserRole)
        if not q_data: return
        
        content_val = q_data.get('content_tex') or q_data.get('content') or ""
        
        # [FIX QUAN TRỌNG] Bổ sung đầy đủ các trường dữ liệu khi kéo thả
        # Trước đây bị thiếu 'dang', 'level'... nên sang bên kia bị mất thông tin
        d = {
            'id': q_data.get('id', 0),
            'content_tex': content_val,
            'content': content_val,
            'dang': q_data.get('dang', 4),  # <--- BẮT BUỘC PHẢI CÓ DÒNG NÀY
            'level': q_data.get('level', ''),
            'grade': q_data.get('grade', 12),
            'subject': q_data.get('subject', 'D'),
            'chapter': q_data.get('chapter', 1),
            'bai': q_data.get('bai', 1),
            'display': f"[ID:{q_data.get('id')}]" # Hiển thị rút gọn bên danh sách đích
        }
        
        mime = QMimeData(); mime.setText(json.dumps(d))
        drag = QDrag(self); drag.setMimeData(mime); drag.exec(Qt.DropAction.CopyAction)

class DropZoneTreeWidget(QTreeWidget):
    """
    Widget thả câu hỏi dạng Cây phân loại + Menu chuột phải đổi câu hỏi
    """
    # Tín hiệu báo danh sách thay đổi để cập nhật thống kê
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
        
        # Khởi tạo 4 nhóm chính (Root Items)
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
            # Lưu loại dạng vào user data để nhận diện
            root.setData(0, Qt.ItemDataRole.UserRole, {"type": "root", "dang": k})
            # Set màu nền nhẹ cho header
            root.setBackground(0, QColor("#f0f0f0"))
            self.addTopLevelItem(root)
            self.roots[k] = root

    def dragEnterEvent(self, e): e.accept() if e.mimeData().hasText() else e.ignore()
    def dragMoveEvent(self, e): e.accept() if e.mimeData().hasText() else e.ignore()
    
    def dropEvent(self, e):
        if e.mimeData().hasText():
            try:
                d = json.loads(e.mimeData().text())
                dang = d.get('dang', 4) # Mặc định là 4 nếu ko có
                
                # Tìm root tương ứng
                root = self.roots.get(dang, self.roots[4])
                
                # Tạo item con
                content_preview = d.get('content_tex', '')[:60].replace("\n", " ")
                txt = f"[ID:{d['id']}] {d.get('level','?')} | {content_preview}..."
                
                item = QTreeWidgetItem([txt])
                item.setData(0, Qt.ItemDataRole.UserRole, d)
                item.setToolTip(0, d.get('content_tex', ''))
                
                root.addChild(item)
                root.setExpanded(True)
                e.accept()
                
                # Phát tín hiệu cập nhật thống kê
                self.items_changed.emit()
            except Exception as err:
                print(f"Lỗi Drop: {err}")
                e.ignore()
        else: e.ignore()

    def open_menu(self, position):
        item = self.itemAt(position)
        # Chỉ hiện menu nếu click vào câu hỏi (không phải header nhóm)
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
        
        # Tìm câu hỏi ngẫu nhiên khác trong DB khớp tiêu chí
        # Điều kiện: Cùng Lớp, Môn, Chương, Bài, Mức độ, Dạng VÀ KHÁC ID cũ
        new_q = self.bk.get_rnd(
            data['grade'], data['subject'], data['chapter'], 
            data['bai'], data['level'], data['dang'], 
            exc=data['id'] # Loại trừ ID hiện tại
        )
        
        if new_q:
            # Tạo data mới chuẩn format kéo thả
            new_data = {
                'id': new_q['id'],
                'content_tex': new_q['content_tex'],
                'dang': new_q['dang'],
                'level': new_q['level'],
                'grade': new_q['grade'],
                'subject': new_q['subject'],
                'chapter': new_q['chapter'],
                'bai': new_q['bai']
            }
            
            # Cập nhật hiển thị Item
            content_preview = new_q['content_tex'][:60].replace("\n", " ")
            item.setText(0, f"[ID:{new_q['id']}] {new_q['level']} | {content_preview}...")
            item.setData(0, Qt.ItemDataRole.UserRole, new_data)
            item.setToolTip(0, new_q['content_tex'])
            
            # Hiệu ứng báo thành công (Flash item nếu muốn, ở đây dùng MsgBox nhẹ)
            # QMessageBox.information(self, "Thành công", f"Đã đổi sang câu ID: {new_q['id']}")
        else:
            QMessageBox.warning(self, "Không tìm thấy", "Không còn câu hỏi nào khác tương đương trong ngân hàng!")

    def get_all_questions(self):
        """Hàm tiện ích lấy toàn bộ câu hỏi từ cây"""
        qs = []
        # Duyệt qua 4 nhóm
        for i in range(self.topLevelItemCount()):
            root = self.topLevelItem(i)
            for j in range(root.childCount()):
                child = root.child(j)
                qs.append(child.data(0, Qt.ItemDataRole.UserRole))
        return qs
    
    def clear_all(self):
        """Xóa hết con của các root"""
        for i in range(self.topLevelItemCount()):
            root = self.topLevelItem(i)
            root.takeChildren()
        self.items_changed.emit()

# =============================================================================
# 6. ID6 DIALOG
# =============================================================================
class ClassroomControlPanel(QDialog):
    """Bảng điều khiển Trung tâm Classroom (Split UI)"""
    def __init__(self, parent=None, callback_exam=None, callback_homework=None):
        super().__init__(parent)
        self.callback_exam = callback_exam
        self.callback_homework = callback_homework
        self.setWindowTitle("Trung tâm Google Classroom")
        self.setFixedSize(700, 450)
        self.setStyleSheet("""
            QDialog { background-color: #fdfdfd; }
            QPushButton {
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
                padding: 15px;
                border: 2px solid #ddd;
            }
            QPushButton:hover {
                background-color: #f0f8ff;
                border-color: #3498db;
            }
            QLabel { color: #555; font-size: 14px; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("CHỌN CHẾ ĐỘ TƯƠNG TÁC CLASSROOM")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 20px; font-weight: 900; color: #2c3e50;")
        layout.addWidget(header)
        
        # Grid Buttons
        grid = QHBoxLayout()
        grid.setSpacing(20)
        
        # Mode A: Giao bài tập
        btn_hw = QPushButton("📝  GIAO BÀI TẬP (PDF)\n\n(Tạo bài tập tĩnh, nộp file)")
        btn_hw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn_hw.setIcon(QIcon(":/icons/pdf.png")) # Placeholder
        btn_hw.setStyleSheet("background-color: #e8f6f3; color: #16a085;")
        btn_hw.clicked.connect(self.on_homework)
        grid.addWidget(btn_hw)
        
        # Mode B: Thi Online
        btn_exam = QPushButton("🌍  TỔ CHỨC THI ONLINE\n\n(Chấm điểm tự động, realtime)")
        btn_exam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn_exam.setStyleSheet("background-color: #fef5e7; color: #d35400;")
        btn_exam.clicked.connect(self.on_exam)
        grid.addWidget(btn_exam)
        
        layout.addLayout(grid)
        
        # Description
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
    """
    Dialog gán ID6 (Fix: Cập nhật hiển thị Lớp/Môn trên bảng sau khi lưu)
    """
    def __init__(self, backend, parent=None, mode='db', data_list=None):
        super().__init__(parent)
        self.backend = backend
        self.mode = mode 
        self.local_data = data_list if data_list else []
        self.qs = []
        self.keep_form_state = False # Cờ đánh dấu để giữ form khi lưu
        
        if self.mode == 'local':
            self.setWindowTitle("⚠️ BỔ SUNG ID6 CÒN THIẾU (TRƯỚC KHI NHẬP KHO)")
            self.setStyleSheet("QDialog { background-color: #fff8e1; }")
        else:
            self.setWindowTitle("Công cụ Gán ID6 (Database)")
            
        self.setMinimumSize(1200, 750)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        l = QVBoxLayout(self)
        
        header_text = "CÔNG CỤ CHUẨN HÓA DỮ LIỆU CÂU HỎI (ID6)"
        if self.mode == 'local':
            header_text = "⚠️ DANH SÁCH CÂU HỎI THIẾU ID TRONG FILE"
            
        l.addWidget(QLabel(header_text, alignment=Qt.AlignmentFlag.AlignCenter, 
                           styleSheet="font-size: 20px; font-weight: bold; color: #d35400;"))
        
        spl = QSplitter(Qt.Orientation.Horizontal)
        
        # Cột trái: Bảng danh sách
        lw = QWidget(); ll = QVBoxLayout(lw)
        self.tb = QTableWidget(0, 5)
        self.tb.setHorizontalHeaderLabels(["ID", "Preview", "Lớp", "Môn", "Trạng thái"])
        self.tb.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tb.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tb.itemSelectionChanged.connect(self.on_sel)
        ll.addWidget(self.tb)
        spl.addWidget(lw)
        
        # Cột phải: Form nhập liệu
        rw = QWidget(); rl = QVBoxLayout(rw)
        self.prev = QTextEdit(); self.prev.setMaximumHeight(200); self.prev.setReadOnly(True)
        rl.addWidget(QLabel("Nội dung Preview:")); rl.addWidget(self.prev)
        
        grp = QGroupBox("Thông tin định danh (Bộ lọc ID)")
        gl = QGridLayout(grp)
        
        self.cb_g = QComboBox(); self.cb_g.addItems(["10","11","12"])
        self.cb_g.currentTextChanged.connect(self.upd_ch) 
        
        self.cb_s = QComboBox(); self.cb_s.addItems(["D - Đại số","H - Hình học"])
        self.cb_s.currentTextChanged.connect(self.upd_ch) 
        
        self.cb_c = QComboBox()
        self.cb_c.currentIndexChanged.connect(self.upd_bai) 
        
        self.cb_l = QComboBox(); self.cb_l.addItems(["N - NB","H - TH","V - VD","C - VDC"])
        self.cb_l.currentTextChanged.connect(self.upd_prev)
        
        self.cb_b = QComboBox()
        self.cb_b.currentIndexChanged.connect(self.upd_prev)
        
        self.cb_d = QComboBox(); 
        for k,v in DANH_MUC_DANG.items(): self.cb_d.addItem(v, k)
        self.cb_d.currentIndexChanged.connect(self.upd_prev)
        
        gl.addWidget(QLabel("Lớp"),0,0); gl.addWidget(self.cb_g,0,1); gl.addWidget(QLabel("Môn"),0,2); gl.addWidget(self.cb_s,0,3)
        gl.addWidget(QLabel("Chương"),1,0); gl.addWidget(self.cb_c,1,1); gl.addWidget(QLabel("Mức độ"),1,2); gl.addWidget(self.cb_l,1,3)
        gl.addWidget(QLabel("Bài"),2,0); gl.addWidget(self.cb_b,2,1); gl.addWidget(QLabel("Dạng"),2,2); gl.addWidget(self.cb_d,2,3)
        
        self.lbl_id6 = QLabel("ID6: -", styleSheet="color: green; font-weight: bold; font-size: 18px; margin: 10px;")
        gl.addWidget(self.lbl_id6, 3, 0, 1, 4)
        rl.addWidget(grp)
        
        bh = QHBoxLayout()
        # [MỚI] Nút chạy AI
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
        
        # Thêm nút AI vào layout
        bh.addWidget(self.btn_ai) 
        bh.addWidget(b_save_one)
        bh.addWidget(self.btn_save_all)
        rl.addLayout(bh)
        
        spl.addWidget(rw)
        l.addWidget(spl)
        
        self.upd_ch()

    # --- CÁC HÀM MỚI ĐỂ XỬ LÝ AI ---
    def run_auto_ai(self):
        """Kích hoạt luồng chạy AI"""
        # Kiểm tra xem MainApp có truyền ai_engine vào Backend không, 
        # hoặc ta cần lấy từ parent (MainApp)
        # Cách đơn giản: Truy cập qua parent nếu parent là MainApp
        main_app = self.parent()
        if not hasattr(main_app, 'ai') or not main_app.ai.is_ready:
            QMessageBox.warning(self, "Lỗi", "AI Engine chưa sẵn sàng. Vui lòng kiểm tra API Key ở màn hình chính.")
            return

        self.btn_ai.setEnabled(False)
        self.btn_ai.setText("Đang phân tích...")
        
        # Tạo worker
        self.ai_worker = AutoIDWorker(main_app.ai, self.qs, DATA_ID6_2025)
        self.ai_worker.progress.connect(lambda p, m: self.lbl_id6.setText(f"AI: {m}")) # Tận dụng label ID6 để hiện tiến trình
        self.ai_worker.item_finished.connect(self.on_ai_item_done)
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.start()

    def on_ai_item_done(self, row_idx, data):
        """Khi AI phân tích xong 1 câu -> Cập nhật vào dữ liệu tạm và bảng"""
        try:
            q = self.qs[row_idx]
            
            # 1. Tính toán chuỗi ID6 từ dữ liệu AI trả về
            # Quy tắc map: Grade: 10->0, 11->1, 12->2
            g_map = {10:0, 11:1, 12:2}
            g_code = g_map.get(data.get('grade', 12), 2)
            s_code = data.get('subject', 'D')
            c_code = data.get('chapter', 1)
            l_code = data.get('level', 'N')
            b_code = data.get('bai', 1)
            d_code = data.get('dang', 4) # Loại câu hỏi (1-4) hoặc dạng toán
            
            # Tạo chuỗi ID6: [GSCLB-D]
            id6_str = f"{g_code}{s_code}{c_code}{l_code}{b_code}-{d_code}"
            
            # 2. Cập nhật vào dict dữ liệu (trong bộ nhớ)
            q['grade'] = data.get('grade', 12)
            q['subject'] = s_code
            q['chapter'] = c_code
            q['level'] = l_code
            q['bai'] = b_code
            q['dang'] = d_code
            q['id6'] = id6_str # Lưu ID dự kiến
            
            # 3. Cập nhật hiển thị trên Bảng
            self.tb.setItem(row_idx, 2, QTableWidgetItem(str(q['grade'])))
            self.tb.setItem(row_idx, 3, QTableWidgetItem(q['subject']))
            
            # Cột trạng thái: Hiển thị ID do AI gợi ý (Màu xanh dương để phân biệt)
            item_status = QTableWidgetItem(f"🤖 {id6_str}")
            item_status.setForeground(QColor("blue"))
            item_status.setToolTip("ID do AI gợi ý. Bấm vào dòng để xem chi tiết bên phải.")
            self.tb.setItem(row_idx, 4, item_status)
            
            # Tự động cuộn xuống dòng đang xử lý
            self.tb.scrollToItem(item_status)
            
        except Exception as e:
            print(f"Lỗi update UI row {row_idx}: {e}")

    def on_ai_finished(self):
        self.btn_ai.setEnabled(True)
        self.btn_ai.setText("🤖 Tự động điền AI")
        QMessageBox.information(self, "Hoàn tất", "AI đã phân tích xong toàn bộ danh sách!\nHãy kiểm tra lại các dòng màu xanh dương và điều chỉnh nếu cần.")

    def load_data(self):
        if self.mode == 'db':
            self.qs = self.backend.get_unassigned(200)
        else:
            self.qs = self.local_data
            
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
            # Xử lý chuỗi "D - Đại số" hoặc "10"
            s_text = self.cb_s.currentText()
            s = 'D' if 'Đại' in s_text or s_text.startswith('D') else 'H'
        except: return

        self.cb_c.blockSignals(True)
        current_c_data = self.cb_c.currentData()
        self.cb_c.clear()
        
        # [FIX] Sử dụng DATA_ID6_2025 và CHAPTER_NAMES thay vì biến cũ
        if g in DATA_ID6_2025 and s in DATA_ID6_2025[g]:
            chapters_dict = DATA_ID6_2025[g][s]
            for ch_code in sorted(chapters_dict.keys()):
                # Lấy tên chương từ CHAPTER_NAMES nếu có
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
        
        # [FIX] Lấy bài học từ DATA_ID6_2025
        lessons = {}
        if g in DATA_ID6_2025 and s in DATA_ID6_2025[g] and c_code in DATA_ID6_2025[g][s]:
            lessons = DATA_ID6_2025[g][s][c_code]
            
        if lessons:
            for k, v in lessons.items():
                self.cb_b.addItem(f"Bài {k}: {v}", k)
        else:
            self.cb_b.addItem("Bài 1", 1) # Giá trị mặc định
            
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
            
            if self.keep_form_state:
                self.keep_form_state = False 
                return 

            try:
                self.cb_g.blockSignals(True)
                self.cb_s.blockSignals(True)
                
                # Load Lớp
                grade_idx = self.cb_g.findText(str(q.get('grade', 12)))
                if grade_idx >= 0: self.cb_g.setCurrentIndex(grade_idx)
                
                # Load Môn
                # [FIX LỖI] Xử lý trường hợp subject bị None
                subj = q.get('subject')
                if not subj: subj = 'D' # Mặc định là Đại số nếu dữ liệu trống
                
                for i in range(self.cb_s.count()):
                    # Ép kiểu str(subj) để đảm bảo không bị lỗi NoneType
                    if self.cb_s.itemText(i).startswith(str(subj)):
                        self.cb_s.setCurrentIndex(i); break
                
                self.cb_g.blockSignals(False)
                self.cb_s.blockSignals(False)
                self.upd_ch() # Load lại danh sách chương tương ứng lớp/môn
                
                # Load Chương
                if q.get('chapter'):
                    idx = self.cb_c.findData(q['chapter'])
                    if idx >= 0: 
                        self.cb_c.setCurrentIndex(idx)
                        self.upd_bai() # Load bài
                    
                # Load Bài
                if q.get('bai'):
                    idx_b = self.cb_b.findData(q['bai'])
                    if idx_b >= 0: self.cb_b.setCurrentIndex(idx_b)

                # Load Mức độ
                lev = q.get('level')
                if lev:
                    for i in range(self.cb_l.count()):
                        # [FIX LỖI] Ép kiểu str(lev) để an toàn
                        if self.cb_l.itemText(i).startswith(str(lev)):
                            self.cb_l.setCurrentIndex(i); break
                            
                # Load Dạng (Mới)
                dang = q.get('dang')
                if dang:
                    idx_d = self.cb_d.findData(dang)
                    if idx_d >= 0: self.cb_d.setCurrentIndex(idx_d)
                    
            except Exception as e: 
                print(f"Lỗi load form: {e}")

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
                q_data['id'], self.id6_str, 
                new_g, new_s, new_ch, new_l, new_bai, new_dang, 
                new_content_tex
            )
        else:
            q_data.update({
                'id6': self.id6_str, 'grade': new_g, 'subject': new_s,
                'chapter': new_ch, 'level': new_l, 'bai': new_bai,
                'dang': new_dang, 'content_tex': new_content_tex
            })
        
        # --- CẬP NHẬT HIỂN THỊ TRÊN BẢNG ---
        self.tb.setItem(r, 2, QTableWidgetItem(str(new_g))) # Cột Lớp
        self.tb.setItem(r, 3, QTableWidgetItem(new_s))    # Cột Môn
        
        self.tb.setItem(r, 4, QTableWidgetItem(f"✅ ID: {self.id6_str}"))
        self.tb.item(r, 4).setForeground(QColor("green"))
        self.prev.setText(new_content_tex)
        
        # Bật cờ giữ form trước khi chuyển dòng
        self.keep_form_state = True
        
        if r + 1 < self.tb.rowCount(): 
            self.tb.selectRow(r + 1)

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
                        q['id'], self.id6_str, 
                        int(self.cb_g.currentText()), 
                        'D' if 'Đại' in self.cb_s.currentText() else 'H',
                        int(self.cb_c.currentData()) if self.cb_c.currentData() else 0, 
                        self.cb_l.currentText()[0],
                        bai_val, self.cb_d.currentData(), new_content
                    )
                    # Cập nhật hiển thị bảng khi lưu all
                    self.tb.setItem(i, 2, QTableWidgetItem(self.cb_g.currentText()))
                    self.tb.setItem(i, 3, QTableWidgetItem('D' if 'Đại' in self.cb_s.currentText() else 'H'))
                    self.tb.setItem(i, 4, QTableWidgetItem("✅ Đã Lưu"))
                QMessageBox.information(self, "Thành công", "Đã cập nhật xong!")

# =============================================================================
# MODULE QUẢN LÝ DATABASE (ĐÃ FIX LỖI DATA & COPY AN TOÀN)
# =============================================================================
class DatabaseManager:
    @staticmethod
    def migrate_db(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(questions)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # Đảm bảo có đủ các cột chuẩn
        required = {
            "subject": "TEXT", "chapter": "INTEGER", "bai": "INTEGER",
            "level": "TEXT", "dang": "INTEGER", "id6": "TEXT"
        }
        for col, dtype in required.items():
            if col not in columns:
                cursor.execute(f"ALTER TABLE questions ADD COLUMN {col} {dtype} DEFAULT NULL")
        conn.commit(); conn.close()

    @staticmethod
    def get_filtered_questions(db_path, filters):
        conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
        
        # Chọn các cột cần thiết
        query = "SELECT id, content_tex, level, id6, dang, chapter, bai FROM questions WHERE 1=1"
        params = []
        
        # Áp dụng bộ lọc (Chỉ thêm điều kiện nếu giá trị khác 0/Rỗng)
        if filters.get("grade"):
            query += " AND grade = ?"; params.append(int(filters["grade"]))
        if filters.get("subject"):
            query += " AND subject = ?"; params.append(filters["subject"])
        if filters.get("chapter"):
            query += " AND chapter = ?"; params.append(int(filters["chapter"]))
        if filters.get("bai"):
            query += " AND bai = ?"; params.append(int(filters["bai"]))
        if filters.get("level"):
            query += " AND level = ?"; params.append(filters["level"])
        if filters.get("dang"):
            query += " AND dang = ?"; params.append(int(filters["dang"]))
            
        query += " ORDER BY id DESC LIMIT 1000" # Tăng giới hạn hiển thị
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows
    
    # Tìm trong class DatabaseManager và thay thế hàm auto_scan_metadata cũ
    @staticmethod
    def auto_scan_metadata(db_path):
        """Quét lại toàn bộ DB để cập nhật cột 'bai', 'dang', 'id6' từ nội dung TeX"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lấy tất cả câu hỏi
        cursor.execute("SELECT id, content_tex FROM questions")
        rows = cursor.fetchall()
        
        count = 0
        id_pattern = r"\[([0-2])([DHC])(\d+)([NHVC])(\d+)-(\d+)\]"
        
        print("Đang chuẩn hóa dữ liệu...")
        
        cursor.execute("BEGIN TRANSACTION")
        try:
            for r in rows:
                q_id, content = r[0], r[1]
                updates = []
                vals = []
                
                # 1. Quét tìm ID6 chuẩn
                match = re.search(id_pattern, content)
                if match:
                    # Bóc tách dữ liệu
                    full_id = match.group(0).replace("[", "").replace("]", "")
                    gc, sc, chc, lc, bc, dc = match.groups()
                    
                    g_val = {'0':10, '1':11, '2':12}.get(gc, 12)
                    
                    # Cập nhật các trường: id6, grade, subject, chapter, level, bai
                    updates.append("id6 = ?"); vals.append(full_id)
                    updates.append("grade = ?"); vals.append(g_val)
                    updates.append("subject = ?"); vals.append(sc)
                    updates.append("chapter = ?"); vals.append(int(chc))
                    updates.append("level = ?"); vals.append(lc)
                    updates.append("bai = ?"); vals.append(int(bc))
                
                # 2. Quét lại Dạng (Hình thức thi)
                dang_val = 4
                if "\\choiceTF" in content: dang_val = 2
                elif "\\choice" in content: dang_val = 1
                elif "\\shortans" in content: dang_val = 3
                
                updates.append("dang = ?"); vals.append(dang_val)
                
                # Thực hiện Update
                if updates:
                    sql = f"UPDATE questions SET {', '.join(updates)} WHERE id = ?"
                    vals.append(q_id)
                    cursor.execute(sql, vals)
                    count += 1
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Lỗi Scan: {e}")
            
        conn.close()
        return count

# =============================================================================
# WIDGET SOẠN BÀI: GIAO DIỆN CHUẨN (GIỐNG SOẠN ĐỀ THỦ CÔNG)
# =============================================================================
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QTextEdit, QMessageBox, QDialog,
                             QComboBox, QListWidgetItem, QTableWidget, 
                             QSpinBox, QTabWidget, QHeaderView, QProgressDialog, 
                             QTreeWidget, QTreeWidgetItem, QSplitter, QLineEdit,
                             QTableWidgetItem, QScrollArea, QFrame, QGridLayout,
                             QGroupBox, QSplashScreen, QMenu, QInputDialog) # <--- THÊM QMenu VÀO ĐÂY

# =============================================================================
# WIDGET SOẠN BÀI (ĐÃ FIX LỖI NameError VÀ ĐỒNG BỘ DATA_ID6_2025)
# =============================================================================
class LessonPlannerWidget(QWidget):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.selected_ids = set()
        self.setup_ui()
        # Mặc định load lớp 12
        self.cb_grade.setCurrentText("12")
        self.update_chapter_list()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- KHUNG BỘ LỌC CHUẨN ---
        filter_group = QGroupBox("Bộ Lọc (Đồng bộ ID6)")
        fl_layout = QGridLayout()
        
        # 1. LỚP & 2. MÔN
        self.cb_grade = QComboBox(); self.cb_grade.addItems(["10", "11", "12"])
        self.cb_subject = QComboBox()
        self.cb_subject.addItem("Đại số / Giải tích", "D")
        self.cb_subject.addItem("Hình học", "H")
        
        # 3. CHƯƠNG & 4. BÀI
        self.cb_chapter = QComboBox(); 
        self.cb_bai = QComboBox(); 
        
        # 5. MỨC ĐỘ
        self.cb_level = QComboBox(); self.cb_level.addItem("Tất cả", "")
        self.cb_level.addItems(["N - Nhận biết", "H - Thông hiểu", "V - Vận dụng", "C - Vận dụng cao"])
        
        # 6. DẠNG
        self.cb_dang = QComboBox(); self.cb_dang.addItem("Tất cả", 0)
        if 'DANH_MUC_DANG' in globals():
            for k, v in DANH_MUC_DANG.items(): self.cb_dang.addItem(v, k)
        else:
            self.cb_dang.addItem("Trắc nghiệm", 1); self.cb_dang.addItem("Đúng/Sai", 2)
            
        # Layout
        fl_layout.addWidget(QLabel("Lớp:"),0,0); fl_layout.addWidget(self.cb_grade,0,1)
        fl_layout.addWidget(QLabel("Môn:"),0,2); fl_layout.addWidget(self.cb_subject,0,3)
        fl_layout.addWidget(QLabel("Chương:"),1,0); fl_layout.addWidget(self.cb_chapter,1,1)
        fl_layout.addWidget(QLabel("Bài:"),1,2); fl_layout.addWidget(self.cb_bai,1,3)
        fl_layout.addWidget(QLabel("Mức:"),2,0); fl_layout.addWidget(self.cb_level,2,1)
        fl_layout.addWidget(QLabel("Dạng:"),2,2); fl_layout.addWidget(self.cb_dang,2,3)
        
        # Events
        self.cb_grade.currentIndexChanged.connect(self.update_chapter_list)
        self.cb_subject.currentIndexChanged.connect(self.update_chapter_list)
        self.cb_chapter.currentIndexChanged.connect(self.update_lesson_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_scan = QPushButton("♻️ Chuẩn hóa Data"); btn_scan.clicked.connect(self.scan_metadata)
        btn_filter = QPushButton("🔍 LỌC CÂU HỎI"); 
        btn_filter.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_filter.clicked.connect(self.load_data)
        
        btn_copy = QPushButton("📋 COPY LATEX (Siêu tốc)"); 
        btn_copy.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_copy.clicked.connect(self.copy_to_clipboard)
        
        btn_layout.addWidget(btn_scan); btn_layout.addStretch()
        btn_layout.addWidget(btn_filter); btn_layout.addWidget(btn_copy)
        
        filter_group.setLayout(fl_layout); layout.addWidget(filter_group); layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Chọn", "ID", "ID6", "Chương", "Bài", "Dạng", "Nội dung"])
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self.preview_question)
        layout.addWidget(self.table)
        
        self.lbl_count = QLabel("Sẵn sàng."); layout.addWidget(self.lbl_count)

    def update_chapter_list(self):
        """Cập nhật danh sách chương từ DATA_ID6_2025"""
        try:
            g = int(self.cb_grade.currentText())
            s = self.cb_subject.currentData() # D hoặc H
        except: return

        self.cb_chapter.clear(); self.cb_chapter.addItem("Tất cả", 0)
        
        # --- FIX LỖI TẠI ĐÂY: Dùng DATA_ID6_2025 thay vì biến cũ ---
        if g in DATA_ID6_2025 and s in DATA_ID6_2025[g]:
            chapters = DATA_ID6_2025[g][s]
            for k in chapters.keys():
                # Lấy tên bài đầu tiên làm tên đại diện hoặc chỉ hiện số chương
                self.cb_chapter.addItem(f"Chương {k}", k)
        
        self.update_lesson_list()

    def update_lesson_list(self):
        """Cập nhật danh sách bài học"""
        try:
            g = int(self.cb_grade.currentText())
            s = self.cb_subject.currentData()
            c = self.cb_chapter.currentData()
        except: return

        self.cb_bai.clear(); self.cb_bai.addItem("Tất cả", 0)
        
        # Load bài học từ DATA_ID6_2025
        if c and c != 0:
            lessons = DATA_ID6_2025.get(g, {}).get(s, {}).get(c, {})
            for k, v in lessons.items():
                self.cb_bai.addItem(f"Bài {k}: {v}", k)

    def load_data(self):
        # Lấy level chỉ lấy ký tự đầu (N, H, V, C)
        lvl = self.cb_level.currentText()
        lvl_val = lvl[0] if lvl and lvl != "Tất cả" else ""
        
        filters = {
            "grade": self.cb_grade.currentText(),
            "subject": self.cb_subject.currentData(),
            "chapter": self.cb_chapter.currentData(),
            "bai": self.cb_bai.currentData(), # Lọc theo Bài
            "dang": self.cb_dang.currentData(),
            "level": lvl_val
        }
        # Loại bỏ bộ lọc rỗng
        clean_filters = {k: v for k, v in filters.items() if v and v != 0}
        
        # Gọi Backend để lấy dữ liệu
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
            
            dang_str = DANH_MUC_DANG.get(r["dang"], str(r["dang"])) if 'DANH_MUC_DANG' in globals() else str(r["dang"])
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

    def preview_question(self, item): pass 

    def copy_to_clipboard(self):
        if not self.selected_ids:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn câu hỏi nào!"); return
        
        conn = sqlite3.connect(self.db_path); conn.row_factory = sqlite3.Row
        ids = list(self.selected_ids)
        final_text = []
        
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
        else:
            QMessageBox.warning(self, "Lỗi", "Không lấy được nội dung!")

    def scan_metadata(self):
        msg = QMessageBox.question(self, "Chuẩn hóa", "Quét lại toàn bộ DB để điền cột Dạng/Bài cho đúng chuẩn?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg == QMessageBox.StandardButton.Yes:
            c = DatabaseManager.auto_scan_metadata(self.db_path)
            QMessageBox.information(self, "Xong", f"Đã cập nhật {c} câu hỏi.")
            self.load_data()

class ImageManagerDialog(QDialog):
    """Công cụ quản lý và thay thế đường dẫn ảnh trong LaTeX"""
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.image_map = {} # Lưu mapping: {tên_gốc: link_mới}
        self.db_refs = {}   # Lưu tham chiếu: {tên_gốc: [id_câu_hỏi, ...]}
        self.setWindowTitle("🖼️ Quản lý Thư viện Hình ảnh LaTeX")
        self.setMinimumSize(900, 600)
        
        # Load thư viện đã lưu trước đó (nếu có)
        self.lib_file = os.path.join(os.path.dirname(DB_PATH), "image_lib.json")
        self.load_library()
        
        self.setup_ui()
        self.scan_database()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        info = QLabel("<b>HƯỚNG DẪN:</b> Công cụ này giúp tìm tất cả lệnh <code>\\includegraphics{...}</code> và thay thế đường dẫn ảnh.<br>"
                      "1. Nhập link ảnh mới vào cột 'Đường dẫn/Link mới'.<br>"
                      "2. Bấm 'Lưu & Cập nhật' để sửa code LaTeX trong Database.")
        info.setStyleSheet("background: #e8f6f3; padding: 10px; border-radius: 5px; color: #2c3e50;")
        layout.addWidget(info)

        # Bảng hiển thị
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tên ảnh gốc (trong TeX)", "Số câu dùng", "Đường dẫn/Link mới (Cloud/Imgur...)", "Trạng thái"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Nút bấm
        btn_box = QHBoxLayout()
        self.lbl_stat = QLabel("Đang quét...")
        
        btn_reload = QPushButton("🔄 Quét lại DB")
        btn_reload.clicked.connect(self.scan_database)
        
        btn_save = QPushButton("💾 Lưu thư viện & Cập nhật DB")
        btn_save.setProperty("class", "btn-primary")
        btn_save.clicked.connect(self.apply_changes)
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)

        btn_box.addWidget(self.lbl_stat)
        btn_box.addStretch()
        btn_box.addWidget(btn_reload)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def load_library(self):
        """Đọc file json lưu mapping cũ"""
        try:
            if os.path.exists(self.lib_file):
                with open(self.lib_file, 'r', encoding='utf-8') as f:
                    self.image_map = json.load(f)
        except: self.image_map = {}

    def scan_database(self):
        """Quét DB tìm tất cả includegraphics"""
        self.table.setRowCount(0)
        self.db_refs = {}
        all_qs = self.backend.conn.execute("SELECT id, content_tex FROM questions").fetchall()
        
        count_total_imgs = 0
        
        for q in all_qs:
            qid = q['id']
            content = q['content_tex']
            if not content: continue
            
            # Regex tìm tên ảnh trong \includegraphics[...]{TEN_ANH}
            # Bắt cả trường hợp có hoặc không có []
            matches = re.findall(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}", content)
            
            for img_name in matches:
                img_name = img_name.strip()
                if img_name not in self.db_refs:
                    self.db_refs[img_name] = []
                self.db_refs[img_name].append(qid)
                count_total_imgs += 1

        # Hiển thị lên bảng
        self.table.setRowCount(len(self.db_refs))
        for row, (img_name, qids) in enumerate(self.db_refs.items()):
            # Cột 1: Tên gốc
            item_name = QTableWidgetItem(img_name)
            item_name.setFlags(Qt.ItemFlag.ItemIsEnabled) # Read only
            self.table.setItem(row, 0, item_name)
            
            # Cột 2: Số lượng
            self.table.setItem(row, 1, QTableWidgetItem(str(len(qids))))
            
            # Cột 3: Link mới (Load từ thư viện nếu có)
            new_link = self.image_map.get(img_name, "")
            self.table.setItem(row, 2, QTableWidgetItem(new_link))
            
            # Cột 4: Trạng thái
            status = "Đã khớp thư viện" if new_link else "Chưa có link"
            self.table.setItem(row, 3, QTableWidgetItem(status))

        self.lbl_stat.setText(f"Tìm thấy {len(self.db_refs)} ảnh khác nhau trong {count_total_imgs} vị trí.")

    def apply_changes(self):
        """Thực hiện replace trong DB và lưu file json"""
        updates_map = {} # {tên_gốc: tên_mới} để chạy update
        
        # 1. Lấy dữ liệu từ bảng
        for row in range(self.table.rowCount()):
            old_name = self.table.item(row, 0).text()
            new_link = self.table.item(row, 2).text().strip()
            
            if new_link and new_link != old_name:
                updates_map[old_name] = new_link
                self.image_map[old_name] = new_link # Cập nhật vào bộ nhớ để lưu file json

        if not updates_map:
            QMessageBox.information(self, "Thông báo", "Không có thay đổi nào cần cập nhật.")
            return

        # 2. Lưu file thư viện json
        try:
            with open(self.lib_file, 'w', encoding='utf-8') as f:
                json.dump(self.image_map, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi lưu file", str(e))

        # 3. Cập nhật Database (Xử lý hàng loạt)
        confirm = QMessageBox.question(self, "Xác nhận", 
                                       f"Bạn có chắc muốn thay thế link cho {len(updates_map)} ảnh?\nHành động này sẽ sửa đổi nội dung câu hỏi trong Database.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm != QMessageBox.StandardButton.Yes: return

        # Logic Update: Duyệt qua từng ảnh cần sửa -> Duyệt qua các câu hỏi chứa nó -> Replace
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
                
                # Lấy nội dung các câu hỏi liên quan
                placeholders = ','.join('?' * len(qids))
                rows = self.backend.conn.execute(f"SELECT id, content_tex FROM questions WHERE id IN ({placeholders})", qids).fetchall()
                
                for r in rows:
                    qid = r['id']
                    content = r['content_tex']
                    
                    # Thay thế chuỗi: \includegraphics{old} -> \includegraphics{new}
                    # Dùng regex sub để an toàn hơn replace string đơn thuần
                    # Pattern tìm chính xác cụm trong {}
                    pattern = r"(\\includegraphics(?:\[.*?\])?)\{" + re.escape(old) + r"\}"
                    new_content = re.sub(pattern, r"\1{" + new + "}", content)
                    
                    if new_content != content:
                        self.backend.conn.execute("UPDATE questions SET content_tex = ? WHERE id = ?", (new_content, qid))
                        total_edited += 1
            
            self.backend.conn.commit()
            progress.setValue(len(updates_map))
            QMessageBox.information(self, "Thành công", f"Đã cập nhật {total_edited} câu hỏi!\nThư viện ảnh đã được lưu.")
            self.scan_database() # Refresh lại bảng
            
        except Exception as e:
            self.backend.conn.rollback()
            QMessageBox.critical(self, "Lỗi Update", f"Có lỗi xảy ra, đã hoàn tác: {e}")

class ImageMappingDialog(QDialog):
    """Hộp thoại map ảnh từ file TeX ngoài vào đường dẫn cục bộ"""
    def __init__(self, image_names, default_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔗 Liên kết Hình ảnh (External TeX)")
        self.setMinimumSize(900, 600)
        self.image_names = sorted(list(set(image_names))) # Unique names
        self.default_dir = default_dir
        self.mapping = {} # {filename: path}
        
        self.setup_ui()
        # Tự động tìm trong thư mục chứa file TeX trước
        self.auto_scan(self.default_dir)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        info = QLabel(f"⚠️ Phát hiện {len(self.image_names)} hình ảnh được nhúng trong file TeX.\n"
                      "Vui lòng đảm bảo các đường dẫn ảnh là chính xác (đường dẫn tuyệt đối) để hệ thống có thể biên dịch.")
        info.setStyleSheet("background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; font-weight: bold;")
        layout.addWidget(info)
        
        # Table
        self.table = QTableWidget(len(self.image_names), 3)
        self.table.setHorizontalHeaderLabels(["Tên ảnh (Trong TeX)", "Đường dẫn thực tế trên máy", "Thao tác"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        for i, name in enumerate(self.image_names):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            
            item_path = QTableWidgetItem("")
            item_path.setForeground(QColor("red")) # Mặc định đỏ (chưa tìm thấy)
            self.table.setItem(i, 1, item_path)
            
            btn = QPushButton("📂 Chọn file")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, r=i: self.browse_image(r))
            self.table.setCellWidget(i, 2, btn)
            
        # Action Buttons
        btn_box = QHBoxLayout()
        btn_scan = QPushButton("🔄 Quét ảnh trong thư mục...")
        btn_scan.clicked.connect(self.manual_scan)
        
        btn_ok = QPushButton("✅ Xác nhận & Cập nhật Link")
        btn_ok.setProperty("class", "btn-primary")
        btn_ok.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Bỏ qua (Giữ nguyên)")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addWidget(btn_scan)
        btn_box.addStretch()
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def auto_scan(self, directory):
        """Tự động tìm ảnh trong thư mục và điền vào bảng"""
        if not directory or not os.path.exists(directory): return
        
        # Tạo map {filename: fullpath} trong folder (quét đệ quy nhẹ)
        files_in_dir = {}
        try:
            # Chỉ quét 1 cấp thư mục để tránh treo nếu folder quá lớn, hoặc dùng os.listdir
            for f in os.listdir(directory):
                full = os.path.join(directory, f)
                if os.path.isfile(full):
                    files_in_dir[f] = full
        except: pass
        
        # Điền vào bảng
        count_found = 0
        for i in range(self.table.rowCount()):
            name_in_tex = self.table.item(i, 0).text()
            
            # Logic 1: Nếu tên trong TeX là đường dẫn tuyệt đối và tồn tại -> OK
            if os.path.isabs(name_in_tex) and os.path.exists(name_in_tex):
                 self.set_path(i, name_in_tex)
                 count_found += 1
                 continue

            # Logic 2: Lấy tên file (basename) để đối chiếu
            basename = os.path.basename(name_in_tex)
            
            # Nếu tìm thấy trong folder hiện tại
            if basename in files_in_dir:
                self.set_path(i, files_in_dir[basename])
                count_found += 1
            # Logic 3: Thử check đường dẫn tương đối
            else:
                 candidate = os.path.join(directory, name_in_tex)
                 if os.path.exists(candidate):
                     self.set_path(i, candidate)
                     count_found += 1

    def manual_scan(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa ảnh")
        if d: self.auto_scan(d)

    def browse_image(self, row):
        name = self.table.item(row, 0).text()
        f, _ = QFileDialog.getOpenFileName(self, f"Tìm ảnh: {name}", self.default_dir, "Images (*.png *.jpg *.jpeg *.pdf *.eps)")
        if f:
            self.set_path(row, f)

    def set_path(self, row, path):
        path = path.replace("\\", "/") # Chuẩn hóa path cho LaTeX
        self.table.setItem(row, 1, QTableWidgetItem(path))
        self.table.item(row, 1).setToolTip(path)
        self.table.item(row, 1).setForeground(QColor("green")) # Đổi màu xanh

    def accept(self):
        # Collect data
        for i in range(self.table.rowCount()):
            name = self.table.item(i, 0).text()
            path = self.table.item(i, 1).text()
            if path and os.path.exists(path):
                self.mapping[name] = path
        super().accept()

# =============================================================================
# 7. MAIN APP
# =============================================================================

# =============================================================================
# TEMPLATE LIBRARY - TÍNH NĂNG MỚI V2.0
# =============================================================================
# =============================================================================
# EXAM MIXER - BỘ TRỘN ĐỀ THÔNG MINH (THEO CẤU TRÚC 2025)
# =============================================================================
# =============================================================================
# DIALOG CẤU HÌNH TRỘN ĐỀ
# =============================================================================
class MixConfigDialog(QDialog):
    """Dialog cấu hình trộn đề: Hỗ trợ mã đề 3 số hoặc 4 số"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Cấu hình trộn đề")
        self.setMinimumSize(450, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # GroupBox nhập liệu
        grp = QGroupBox("Thiết lập thông số")
        form = QGridLayout(grp)
        form.setVerticalSpacing(15) # Tăng khoảng cách cho dễ nhìn
        
        # 1. Số lượng đề
        self.sp_num = QSpinBox()
        self.sp_num.setRange(1, 48)
        self.sp_num.setValue(4)
        self.sp_num.setSuffix(" đề")
        
        # 2. Tùy chọn kiểu mã đề (MỚI)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["3 chữ số (VD: 101, 102...)", "4 chữ số (VD: 1001, 1002...)"])
        self.cb_mode.currentIndexChanged.connect(self.on_mode_change)
        
        # 3. Mã bắt đầu
        self.sp_start = QSpinBox()
        self.sp_start.setRange(100, 999) # Mặc định là 3 số
        self.sp_start.setValue(101)
        
        # Thêm vào Layout
        form.addWidget(QLabel("Số lượng đề cần tạo:"), 0, 0)
        form.addWidget(self.sp_num, 0, 1)
        
        form.addWidget(QLabel("Kiểu mã đề:"), 1, 0)
        form.addWidget(self.cb_mode, 1, 1)
        
        form.addWidget(QLabel("Mã bắt đầu:"), 2, 0)
        form.addWidget(self.sp_start, 2, 1)
        
        layout.addWidget(grp)
        
        # Nút bấm
        btns = QHBoxLayout()
        b_ok = QPushButton("🚀 Bắt đầu trộn")
        b_ok.clicked.connect(self.accept)
        b_ok.setProperty("class", "btn-primary") # Style xanh
        b_ok.setDefault(True)
        
        b_cancel = QPushButton("Hủy")
        b_cancel.clicked.connect(self.reject)
        
        btns.addStretch()
        btns.addWidget(b_ok)
        btns.addWidget(b_cancel)
        layout.addLayout(btns)

    def on_mode_change(self):
        """Tự động cập nhật khoảng giá trị khi user đổi kiểu mã đề"""
        idx = self.cb_mode.currentIndex()
        if idx == 0: 
            # Chế độ 3 số: 100 -> 999
            self.sp_start.setRange(100, 999)
            self.sp_start.setValue(101)
        else: 
            # Chế độ 4 số: 1000 -> 9999
            self.sp_start.setRange(1000, 9999)
            self.sp_start.setValue(1001)

    def get_data(self):
        return {
            'num': self.sp_num.value(),
            'start': self.sp_start.value()
        }

# --- FIX LỖI TRÀN MÀN HÌNH (AUTO FIT + SCROLL) ---
class ClassroomDialog(QDialog):
    def __init__(self, question_objects, parent=None): # Nhận list object
        super().__init__(parent)
        self.questions = question_objects
        self.setWindowTitle("📚 Đăng bài lên Google Classroom")
        
        # 1. Kích thước hợp lý (tránh lỗi full screen che mất dialog khác)
        # [OPTIMIZATION] Set fixed size compatible with small screens
        self.setFixedSize(600, 680)
        
        self.google = GoogleManagerFull()
        self.courses = []
        
        # Setup giao diện chính
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # --- VÙNG CUỘN (SCROLL AREA) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        
        # Tiêu đề
        lbl_t = QLabel("<b>1. Tiêu đề bài tập:</b>")
        lbl_t.setWordWrap(True)
        layout.addWidget(lbl_t)
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("VD: Kiểm tra 15 phút - Hình học")
        layout.addWidget(self.txt_title)
        
        # Mô tả
        lbl_d = QLabel("<b>Hướng dẫn/Mô tả:</b>")
        lbl_d.setWordWrap(True)
        layout.addWidget(lbl_d)
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText("Nhập lời dặn dò học sinh...")
        self.txt_desc.setMinimumHeight(100) 
        layout.addWidget(self.txt_desc)
        
        # Chọn lớp
        lbl_c = QLabel("<b>2. Chọn lớp học:</b>")
        lbl_c.setWordWrap(True)
        layout.addWidget(lbl_c)
        self.cb_courses = QComboBox()
        self.cb_courses.setMinimumHeight(40) # Cao hơn để dễ chọn trên màn cảm ứng
        layout.addWidget(self.cb_courses)
        
        # Trạng thái
        layout.addSpacing(10)
        self.lbl_status = QLabel("Đang kết nối Google...")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lbl_status)
        
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        layout.addWidget(self.pbar)
        
        layout.addStretch() # Đẩy nội dung lên
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # --- NÚT BẤM (LUÔN HIỆN Ở ĐÁY) ---
        btns = QHBoxLayout()
        self.btn_upload = QPushButton("🚀 Đăng bài ngay")
        self.btn_upload.clicked.connect(self.start_upload)
        self.btn_upload.setEnabled(False)
        self.btn_upload.setProperty("class", "btn-primary")
        self.btn_upload.setMinimumHeight(50) # Nút to
        self.btn_upload.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.reject)
        btn_close.setMinimumHeight(50)
        
        btns.addWidget(self.btn_upload)
        btns.addWidget(btn_close)
        main_layout.addLayout(btns)
        
        # Auto login
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self.init_google) 

    def init_google(self):
        try:
            self.google.authenticate()
            self.courses = self.google.get_courses()
            self.cb_courses.clear()
            for c in self.courses:
                self.cb_courses.addItem(f"{c['name']}", c['id'])
            self.lbl_status.setText("✅ Đã kết nối. Sẵn sàng.")
            self.btn_upload.setEnabled(True)
        except Exception as e:
            self.lbl_status.setText(f"Lỗi Auth: {e}")
            self.btn_upload.setText("Lỗi kết nối")
            self.btn_upload.setEnabled(False)

    def start_upload(self):
        if not self.txt_title.text(): return QMessageBox.warning(self,"Thiếu","Nhập tiêu đề!")
        
        # --- [QUAN TRỌNG] SỬ DỤNG AutoFormWorker THAY VÌ UploadWorker ---
        self.worker = AutoFormWorker(
            self.google, 
            self.questions, # Truyền danh sách câu hỏi
            self.txt_title.text(), 
            self.cb_courses.currentData()
        )
        
        self.worker.progress.connect(lambda v,m: (self.pbar.setValue(v), self.lbl_status.setText(m)))
        self.worker.finished.connect(lambda l: (
            QMessageBox.information(self,"Thành công",f"Đã đăng bài tập!\nLink: {l}"), 
            self.accept()
        ))
        self.worker.error.connect(lambda e: QMessageBox.critical(self,"Lỗi Upload", e))
        self.worker.start()
        self.btn_upload.setEnabled(False)

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
        import time
        try:
            if not self.questions:
                self.error.emit("❌ Lỗi: Không tìm thấy câu hỏi nào!")
                return
                
            self.google.authenticate()
            total_q = len(self.questions)
            form_requests = []
            
            # [QUAN TRỌNG] Biến đếm vị trí item trên Form (Bắt đầu từ 0)
            # Biến này sẽ tăng dần mỗi khi ta thêm 1 item (ảnh hoặc câu hỏi)
            current_form_index = 0

            self.progress.emit(5, "📝 Đang khởi tạo Google Form...")
            form_id, form_link = self.google.create_quiz_form(self.title, "Đề thi được tạo bởi BankAI Pro")
            
            for idx, q in enumerate(self.questions):
                try:
                    p = 10 + int((idx / total_q) * 80)
                    self.progress.emit(p, f"Đang xử lý câu {idx+1}/{total_q}...")
                    
                    # Detect dạng
                    detected_dang = self.detect_question_type(q['content_tex'])
                    q['dang'] = detected_dang 
                    
                    # Bóc tách
                    parts = LatexParser.split_question_parts(q['content_tex'])
                    
                    # Biên dịch ảnh
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

                    # --- TẠO REQUEST VỚI INDEX LIÊN TỤC ---
                    # Gọi hàm build và nhận lại danh sách items + số lượng item đã tạo
                    items = self.build_form_items_list(idx, q, parts, stem_img_id, opt_img_ids, sol_img_id, current_form_index)
                    
                    if items:
                        form_requests.extend(items)
                        # Cập nhật index cho câu tiếp theo
                        current_form_index += len(items)
                        
                except Exception as e:
                    print(f"Lỗi xử lý câu {idx+1}: {e}")

            # Gửi Request (Chia nhỏ để tránh lỗi 500)
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

            # Tạo PDF
            self.progress.emit(95, "📄 Đang tạo file PDF đề gốc...")
            full_tex = LATEX_TEMPLATE.replace("__CONTENT__", "\n".join([q['content_tex'] for q in self.questions]))
            msg, pdf_path = PDFCompiler.compile_tex_to_pdf(full_tex, "Full_Exam")
            
            pdf_id = None
            if pdf_path and os.path.exists(pdf_path):
                pdf_id = self.google.upload_to_drive(pdf_path)
            
            # Đăng bài
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
        import time
        if not tex_content or not tex_content.strip(): return None
        img_path = ImageCompiler.compile_question_to_png(tex_content, name_prefix)
        if img_path and os.path.exists(img_path):
            file_id = self.google.upload_image(img_path)
            time.sleep(0.5) 
            return file_id
        return None

    def build_form_items_list(self, index, q_data, parts, stem_id, opt_ids, sol_id, start_index):
        """
        Tạo danh sách item cho Form với Index được truyền vào chính xác
        start_index: Vị trí bắt đầu chèn item trong Form
        """
        requests = []
        current_idx = start_index # Biến đếm nội bộ
        
        # ITEM 1: ẢNH ĐỀ BÀI (NẾU CÓ)
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
                    "location": {"index": current_idx} # Sử dụng index tuần tự
                }
            })
            current_idx += 1 # Tăng index sau khi thêm

        # ITEM 2: CÂU HỎI
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
                "location": {"index": current_idx} # Sử dụng index tuần tự
            }
        }
        
        q_body = q_item['createItem']['item']['questionItem']['question']
        
        if dang == 1: # Trắc nghiệm
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

        elif dang == 2: # Đúng/Sai
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

        elif dang == 3: # Điền khuyết
            q_body['textQuestion'] = {}
            ans = str(q_data.get('correct_val', q_data.get('key', '')))
            q_body['grading']['correctAnswers']['answers'] = [{"value": ans}]
            if feedback: q_body['grading']['generalFeedback'] = feedback
            
        else: # Tự luận
            q_body['textQuestion'] = {"paragraph": True}
            if feedback: q_body['grading']['generalFeedback'] = feedback

        requests.append(q_item)
        return requests

class ExamMixer:
    """
    Class xử lý trộn đề (Phiên bản Fix lỗi cấu trúc):
    - Sử dụng thuật toán đếm ngoặc {} để tách phương án chính xác tuyệt đối.
    - Hỗ trợ công thức Toán phức tạp trong đáp án (\frac, \sqrt, ...).
    """
    
    def find_closing_brace(self, text, open_pos):
        """Hàm tìm vị trí dấu đóng ngoặc tương ứng"""
        balance = 1
        i = open_pos + 1
        n = len(text)
        while i < n:
            char = text[i]
            # Bỏ qua ký tự được escape (vd: \{ \})
            if char == '\\' and i + 1 < n:
                i += 2
                continue
            
            if char == '{':
                balance += 1
            elif char == '}':
                balance -= 1
            
            if balance == 0:
                return i
            i += 1
        return -1

    def permute_content(self, text):
        """
        Input: Nội dung câu hỏi (LaTeX)
        Output: (Nội dung đã trộn, Ký tự đáp án đúng A/B/C/D)
        """
        # 1. Tìm vị trí lệnh \choice
        # Regex chỉ dùng để tìm điểm bắt đầu, không dùng để capture nội dung
        match = re.search(r"\\choice(?:\s*\[.*?\])?", text)
        
        if not match:
            # Nếu không tìm thấy \choice, trả về như cũ (có thể là tự luận hoặc lỗi)
            # Cố gắng tìm Key trong comment nếu có
            key_match = re.search(r"\[KEY:\s*([A-D])\]", text, re.IGNORECASE)
            return text, (key_match.group(1).upper() if key_match else "?")

        start_idx = match.end()
        full_command_start = match.start()
        
        # 2. Tách 4 phương án bằng cách đếm ngoặc
        options = []
        current_idx = start_idx
        
        try:
            for _ in range(4):
                # Bỏ qua khoảng trắng giữa các phương án
                while current_idx < len(text) and text[current_idx].isspace():
                    current_idx += 1
                
                if current_idx >= len(text) or text[current_idx] != '{':
                    # Lỗi cấu trúc (không đủ 4 cặp ngoặc) -> Trả về gốc
                    return text, "A"
                
                close_idx = self.find_closing_brace(text, current_idx)
                if close_idx == -1: return text, "A" # Lỗi ngoặc không đóng
                
                # Lấy nội dung bên trong {}
                content = text[current_idx+1 : close_idx]
                options.append(content)
                current_idx = close_idx + 1
                
            full_command_end = current_idx
            
        except Exception as e:
            print(f"Lỗi parse choice: {e}")
            return text, "A"

        # 3. Tìm đáp án đúng (\True)
        correct_idx = -1
        clean_options = []
        
        for idx, opt in enumerate(options):
            if "\\True" in opt:
                correct_idx = idx
                clean_options.append(opt.replace("\\True", "").strip())
            else:
                clean_options.append(opt.strip())
        
        # Fallback: Nếu không có \True, tìm trong comment [KEY: X]
        if correct_idx == -1:
            key_match = re.search(r"\[KEY:\s*([A-D])\]", text, re.IGNORECASE)
            if key_match:
                key_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
                correct_idx = key_map.get(key_match.group(1).upper(), -1)

        # 4. Trộn thứ tự
        indices = [0, 1, 2, 3]
        import random
        random.shuffle(indices)
        
        # 5. Xây dựng lại nội dung mới
        new_options_tex = ""
        for i in indices:
            opt_content = clean_options[i]
            if i == correct_idx:
                opt_content = "\\True " + opt_content
            new_options_tex += f"{{{opt_content}}}" # Bọc lại bằng {}
            
        # 6. Thay thế khối \choice cũ bằng khối mới
        # Giữ lại phần text trước và sau \choice (lời dẫn, lời giải...)
        prefix = text[:full_command_start]
        suffix = text[full_command_end:]
        
        # Giữ nguyên phần đầu lệnh (vd: \choice hoặc \choice[2])
        command_head = text[match.start():match.end()].strip()
        
        new_text = f"{prefix}{command_head}{new_options_tex}{suffix}"
        
        # 7. Xác định Key mới
        new_key_char = "?"
        if correct_idx != -1:
            new_correct_idx = indices.index(correct_idx)
            inv_key_map = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            new_key_char = inv_key_map[new_correct_idx]

        return new_text, new_key_char

    def mix_exam(self, questions, num_variants=1, start_code=101):
        """Logic trộn đề (Giữ nguyên logic cũ, chỉ thay đổi permute_content)"""
        import random
        mixed_results = {} 
        
        p1 = [q for q in questions if q.get('dang') == 1] # TN
        p2 = [q for q in questions if q.get('dang') == 2] # Đ/S
        p3 = [q for q in questions if q.get('dang') == 3] # TLN
        others = [q for q in questions if q.get('dang') not in [1, 2, 3]]

        for i in range(num_variants):
            exam_code = start_code + i
            variant_qs = []
            
            # Trộn câu hỏi TN và đảo đáp án
            curr_p1 = [q.copy() for q in p1] 
            random.shuffle(curr_p1) 
            
            final_p1 = []
            for q in curr_p1:
                content = q.get('content_tex', '')
                new_content, new_key = self.permute_content(content)
                
                # Cập nhật [KEY: ...] để đồng bộ
                if re.search(r"\[KEY:.*?\]", new_content):
                     new_content = re.sub(r"\[KEY:.*?\]", f"[KEY: {new_key}]", new_content)
                else:
                     new_content += f"\n% [KEY: {new_key}]"
                
                q_new = q.copy()
                q_new['content_tex'] = new_content
                q_new['final_key'] = new_key 
                final_p1.append(q_new)

            # Các phần khác chỉ đảo thứ tự câu
            curr_p2 = [q.copy() for q in p2]; random.shuffle(curr_p2)
            curr_p3 = [q.copy() for q in p3]; random.shuffle(curr_p3)
            curr_others = [q.copy() for q in others]
            
            variant_qs.extend(final_p1)
            variant_qs.extend(curr_p2)
            variant_qs.extend(curr_p3)
            variant_qs.extend(curr_others)
            
            mixed_results[exam_code] = variant_qs
            
        return mixed_results
    
class TemplateLibraryDialog(QDialog):
    """Dialog quản lý thư viện mẫu ma trận đề thi (Cập nhật chuẩn 2025)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_template = None
        self.setWindowTitle("📋 Thư viện Ma trận Đề thi (Chuẩn 2025)")
        self.setMinimumSize(900, 650)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📋 THƯ VIỆN CẤU TRÚC ĐỀ THI 2025")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #c0392b; padding: 10px; text-transform: uppercase;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab { min-width: 150px; padding: 10px; }
            QTabBar::tab:selected { background: #fff3e0; color: #d35400; border-bottom: 2px solid #d35400; }
        """)
        
        # Tab 1: Đề chuẩn Bộ GD & Sở
        preset_tab = self._create_preset_tab()
        tabs.addTab(preset_tab, "🏆 Đề Thi Chuẩn (Bộ/Sở)")
        
        # Tab 2: Kiểm tra định kỳ
        school_tab = self._create_school_tab()
        tabs.addTab(school_tab, "🏫 Kiểm Tra Định Kỳ")
        
        layout.addWidget(tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_use = QPushButton("✅ Áp dụng mẫu này")
        btn_use.clicked.connect(self.accept)
        btn_use.setProperty("class", "btn-success")
        btn_use.setMinimumHeight(40)
        
        btn_cancel = QPushButton("❌ Đóng")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_use)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def _create_preset_tab(self):
        """Tab chứa các đề thi chuẩn quốc gia"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cấu trúc: 12 câu TN (Part 1) - 4 câu Đ/S (Part 2) - 6 câu TLN (Part 3)
        presets = [
            {
                'key': 'thpt_2025_chuan',
                'name': '🏆 ĐỀ TỐT NGHIỆP THPT 2025 (Chuẩn)',
                'desc': 'Cấu trúc 12 - 4 - 6 (90 phút)\n• Phần I: 12 câu (3đ)\n• Phần II: 4 câu (4đ)\n• Phần III: 6 câu (3đ)',
                'icon': '🇻🇳',
                # Matrix phân bố số lượng câu hỏi vào các mức độ (NB, TH, VD)
                # Cột 1-3: Phần I (NB, TH, VD)
                # Cột 4-6: Phần II (NB, TH, VD) - Lưu ý: Phần II thường tính theo ý, ở đây tính theo câu
                # Cột 7-9: Phần III (NB, TH, VD)
                'matrix': {
                    1: 4, 2: 4, 3: 4,   # Phần I: 12 câu (Chia đều mức độ)
                    4: 1, 5: 2, 6: 1,   # Phần II: 4 câu (Thiên về TH/VD)
                    7: 0, 8: 2, 9: 4    # Phần III: 6 câu (Thiên về VD/VDC)
                }
            },
            {
                'key': 'thpt_2025_kho',
                'name': '🔥 Đề Luyện Thi Vận Dụng Cao (Nâng cao)',
                'desc': 'Tăng cường câu hỏi Vận dụng & Vận dụng cao\nDành cho lớp chọn/ôn thi điểm 9+',
                'icon': '💪',
                'matrix': {
                    1: 2, 2: 4, 3: 6,   # Phần I: Giảm NB, tăng VD
                    4: 0, 5: 2, 6: 2,   # Phần II: Khó hơn
                    7: 0, 8: 1, 9: 5    # Phần III: Rất khó
                }
            }
        ]
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        clayout = QVBoxLayout(content)
        
        for p in presets:
            clayout.addWidget(self._create_preset_button(p))
        clayout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    def _create_school_tab(self):
        """Tab chứa các đề kiểm tra trường học"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        presets = [
            {
                'key': 'gk_2025',
                'name': '📝 Đề Giữa Kỳ (Cấu trúc mới)',
                'desc': 'Quy mô rút gọn của đề THPT 2025\nThường dùng: 12 TN + 2 Đ/S + 2 TLN (hoặc tuỳ chỉnh)',
                'icon': '📊',
                'matrix': { # Tổng ~16-20 câu
                    1: 6, 2: 4, 3: 2,   # 12 câu TN
                    4: 1, 5: 1, 6: 0,   # 2 câu Đ/S
                    7: 0, 8: 1, 9: 1    # 2 câu TLN
                }
            },
            {
                'key': 'ck_2025',
                'name': '📚 Đề Cuối Kỳ (Cấu trúc mới)',
                'desc': 'Tương đương đề THPTQG nhưng giới hạn chương\nCấu trúc đầy đủ 12 - 4 - 6',
                'icon': '🎓',
                'matrix': {
                    1: 4, 2: 4, 3: 4,
                    4: 1, 5: 2, 6: 1,
                    7: 0, 8: 2, 9: 4
                }
            },
            {
                'key': '15p_tn',
                'name': '⏱️ Kiểm tra 15 phút (Trắc nghiệm)',
                'desc': '10 Câu trắc nghiệm 4 lựa chọn (Phần I)',
                'icon': '⚡',
                'matrix': {
                    1: 4, 2: 4, 3: 2, # Chỉ có Phần I
                    4: 0, 5: 0, 6: 0,
                    7: 0, 8: 0, 9: 0
                }
            },
            {
                'key': '45p_mix',
                'name': '⏱️ Kiểm tra 1 Tiết (Hỗn hợp)',
                'desc': 'Kết hợp 3 phần: 12 TN + 2 Đ/S + 2 TLN',
                'icon': '📝',
                'matrix': {
                    1: 6, 2: 4, 3: 2,
                    4: 1, 5: 1, 6: 0,
                    7: 0, 8: 1, 9: 1
                }
            }
        ]
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        clayout = QVBoxLayout(content)
        
        for p in presets:
            clayout.addWidget(self._create_preset_button(p))
        clayout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    def _create_preset_button(self, preset):
        btn = QPushButton()
        btn.setMinimumHeight(90)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #f5f6fa;
                border: 1px solid #3498db;
                border-left: 5px solid #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border: 1px solid #2980b9;
                border-left: 5px solid #2980b9;
            }
        """)
        
        # Nội dung nút
        text = f"{preset['icon']}  {preset['name']}\n      {preset['desc'].replace(chr(10), chr(10)+'      ')}"
        btn.setText(text)
        
        # Lưu dữ liệu matrix vào button để lấy ra khi chọn
        btn.setProperty("matrix_data", preset['matrix'])
        btn.setProperty("template_key", preset['key'])
        
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.clicked.connect(lambda: self._on_btn_clicked(btn))
        
        return btn
    
    def _on_btn_clicked(self, btn):
        self.selected_template = btn.property("matrix_data")
        # Reset style các nút khác (do autoexclusive chỉ handle logic check)
    
    def get_selected_template(self):
        """Trả về dictionary cấu hình matrix"""
        return self.selected_template

# =============================================================================
# MODULE LÀM SẠCH FILE & CHECK LỖI AI
# =============================================================================
# =============================================================================
# MODULE LÀM SẠCH FILE & CHECK LỖI AI (WORKER)
# =============================================================================
# =============================================================================
# MODULE LÀM SẠCH FILE & CHECK LỖI AI (WORKER) - PHIÊN BẢN SMART RETRY
# =============================================================================
class CleanerWorker(QThread):
    progress = pyqtSignal(int, str)
    # (List lỗi, Đường dẫn file sạch, Thống kê, Header gốc, List câu hỏi sạch)
    finished = pyqtSignal(list, str, list, str, list) 

    def __init__(self, file_path, ai_engine, check_ai=False):
        super().__init__()
        self.file_path = file_path
        self.ai = ai_engine
        self.check_ai = check_ai

    def normalize_text(self, text):
        """Chuẩn hóa để so sánh trùng lặp"""
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
            
            # --- 1. Tách Header gốc ---
            if "\\begin{document}" in content:
                header = content.split("\\begin{document}")[0] + "\\begin{document}\n"
            else:
                header = LATEX_TEMPLATE.replace("\\begin{document}", "") + "\n\\begin{document}\n"

            # --- 2. Tách câu hỏi và Lọc trùng ---
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

            # --- 3. Ghi file sạch lần đầu ---
            clean_path = self.file_path.replace(".tex", "_CLEANED.tex")
            self.save_to_file(clean_path, header, unique_questions)
            
            # --- 4. Check lỗi bằng AI (SMART RETRY) ---
            ai_errors = []
            
            if self.check_ai and self.ai and self.ai.is_ready:
                batch_size = 5 
                total_batches = (len(questions_to_ai) + batch_size - 1) // batch_size
                
                for i in range(0, len(questions_to_ai), batch_size):
                    batch = questions_to_ai[i : i + batch_size]
                    
                    # Chuẩn bị Prompt
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
                    
                    # --- CƠ CHẾ THỬ LẠI KHI GẶP LỖI 429 ---
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
                            
                            # Nếu thành công -> Thoát vòng lặp retry -> Sang batch tiếp theo
                            time.sleep(2) # Nghỉ nhẹ 2s để tránh spam
                            break 
                            
                        except Exception as e:
                            err_str = str(e)
                            # Nếu gặp lỗi 429 (Quota)
                            if "429" in err_str or "quota" in err_str.lower():
                                wait_time = 65 # Đợi 65 giây (Google yêu cầu ~60s)
                                self.progress.emit(p_percent, f"⚠️ Hết quota! Đang nghỉ {wait_time}s để hồi phục...")
                                print(f"⚠️ Quota exceeded. Waiting {wait_time}s...")
                                time.sleep(wait_time)
                                # Sau khi ngủ xong, vòng lặp for sẽ chạy lại (attempt tăng lên)
                            else:
                                print(f"❌ Lỗi khác batch {i}: {e}")
                                break # Lỗi khác thì bỏ qua batch này luôn
            
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

class QuickEditDialog(QDialog):
    """Hộp thoại sửa nhanh nội dung câu hỏi"""
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(800, 600)
        self.new_content = None
        
        layout = QVBoxLayout(self)
        
        # Hướng dẫn
        lbl = QLabel("💡 Sửa trực tiếp nội dung LaTeX bên dưới và bấm Lưu. File sẽ được cập nhật ngay lập tức.")
        lbl.setStyleSheet("color: #2980b9; font-style: italic;")
        layout.addWidget(lbl)
        
        # Vùng soạn thảo
        self.editor = QTextEdit()
        self.editor.setPlainText(content)
        self.editor.setStyleSheet("font-family: Consolas, 'Courier New'; font-size: 14px;")
        layout.addWidget(self.editor)
        
        # Nút bấm
        btns = QHBoxLayout()
        btn_save = QPushButton("💾 Lưu thay đổi")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.save)
        
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        
        btns.addStretch()
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        
    def save(self):
        self.new_content = self.editor.toPlainText()
        self.accept()

class FileCleanerDialog(QDialog):
    def __init__(self, ai_engine, parent=None):
        super().__init__(parent)
        self.ai = ai_engine
        self.setWindowTitle("🧹 Làm sạch File & Check Lỗi AI")
        self.setMinimumSize(900, 700)
        
        # Biến lưu trữ dữ liệu trong bộ nhớ để sửa trực tiếp
        self.clean_questions = [] # List các câu hỏi
        self.file_header = ""     # Header của file
        self.clean_file_path = "" # Đường dẫn file output
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Input file
        h1 = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Chọn file .tex gốc...")
        btn_browse = QPushButton("📂 Chọn File")
        btn_browse.clicked.connect(self.browse_file)
        h1.addWidget(self.txt_path)
        h1.addWidget(btn_browse)
        layout.addLayout(h1)
        
        # Option AI
        self.chk_ai = QCheckBox("Dùng AI dò lỗi (Chính tả/Đáp số)")
        if self.ai and self.ai.is_ready: self.chk_ai.setChecked(True)
        else: self.chk_ai.setEnabled(False); self.chk_ai.setText("Dùng AI (Chưa có Key)")
        layout.addWidget(self.chk_ai)
        
        self.btn_run = QPushButton("🚀 Bắt đầu Quét")
        self.btn_run.setProperty("class", "btn-primary")
        self.btn_run.clicked.connect(self.start_process)
        layout.addWidget(self.btn_run)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # Bảng lỗi
        layout.addWidget(QLabel("<b>📋 DANH SÁCH LỖI (Click đúp vào dòng để sửa):</b>"))
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Câu số", "Loại lỗi", "Chi tiết", "Trạng thái"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # KẾT NỐI SỰ KIỆN CLICK ĐÚP ĐỂ SỬA
        self.table.cellDoubleClicked.connect(self.open_editor) 
        layout.addWidget(self.table)
        
        self.lbl_result = QLabel("")
        layout.addWidget(self.lbl_result)

    def browse_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn File", "", "TeX (*.tex)")
        if f: self.txt_path.setText(f)

    def start_process(self):
        path = self.txt_path.text()
        if not os.path.exists(path): return
        
        self.btn_run.setEnabled(False)
        self.table.setRowCount(0)
        
        self.worker = CleanerWorker(path, self.ai, self.chk_ai.isChecked())
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def on_finished(self, errors, path, stats, header, questions):
        self.btn_run.setEnabled(True)
        self.progress.setValue(100)
        
        # Lưu dữ liệu vào bộ nhớ class
        self.clean_file_path = path
        self.file_header = header
        self.clean_questions = questions 
        
        msg = f"✅ Xong! File sạch: {os.path.basename(path)}\n" \
              f"- Số câu: {stats[0]} | Trùng lặp: {stats[1]} | Lỗi AI: {stats[2]}"
        self.lbl_result.setText(msg)
        
        # Hiển thị lỗi lên bảng
        self.table.setRowCount(len(errors))
        for i, err in enumerate(errors):
            # Lưu ID câu hỏi vào item để truy xuất khi click
            q_id = int(err.get('id', 0))
            
            item_id = QTableWidgetItem(str(q_id))
            item_id.setData(Qt.ItemDataRole.UserRole, q_id) # Lưu ID ẩn
            
            self.table.setItem(i, 0, item_id)
            self.table.setItem(i, 1, QTableWidgetItem(str(err.get('type'))))
            self.table.setItem(i, 2, QTableWidgetItem(str(err.get('desc'))))
            self.table.setItem(i, 3, QTableWidgetItem("⚠️ Cần sửa"))
            
        if not errors: 
            QMessageBox.information(self, "Tuyệt vời", "File sạch đẹp, không tìm thấy lỗi!")

    def open_editor(self, row, col):
        """Mở popup sửa lỗi khi click đúp vào bảng"""
        # Lấy ID câu hỏi từ cột 0
        item = self.table.item(row, 0)
        if not item: return
        
        q_idx = item.data(Qt.ItemDataRole.UserRole) - 1 # ID là 1-based, index là 0-based
        
        if 0 <= q_idx < len(self.clean_questions):
            current_content = self.clean_questions[q_idx]
            
            # Mở Dialog sửa
            dlg = QuickEditDialog(f"Sửa câu số {q_idx + 1}", current_content, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                new_content = dlg.new_content
                
                # 1. Cập nhật vào bộ nhớ
                self.clean_questions[q_idx] = new_content
                
                # 2. Ghi đè ngay lập tức xuống file
                self.save_changes_to_disk()
                
                # 3. Cập nhật trạng thái trên bảng
                self.table.setItem(row, 3, QTableWidgetItem("✅ Đã sửa"))
                self.table.item(row, 3).setForeground(QColor("green"))
                
                QMessageBox.information(self, "Đã lưu", "Đã cập nhật vào file _CLEANED.tex")

    def save_changes_to_disk(self):
        """Ghi đè nội dung mới xuống file đĩa"""
        try:
            with open(self.clean_file_path, "w", encoding="utf-8") as f:
                f.write(self.file_header)
                f.write("\n\n".join(self.clean_questions))
                f.write("\n\\end{document}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi ghi file", str(e))

# =============================================================================
# MODULE WEB SERVER FIX FINAL: CENTER, TRUE, IMAGES
# =============================================================================
import uvicorn
import subprocess
import hashlib
import re
import os
import json
import sqlite3
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PyQt6.QtCore import QThread

# --- CẤU HÌNH ---
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".bankai_cache")
IMAGE_LIB_PATH = os.path.join(os.path.dirname(DB_PATH), "image_lib.json") 
if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)

# --- 1. QUẢN LÝ ẢNH LOCAL ---
class ImageHandler:
    IMAGE_MAP = {}
    @staticmethod
    def load_library():
        try:
            if os.path.exists(IMAGE_LIB_PATH):
                with open(IMAGE_LIB_PATH, 'r', encoding='utf-8') as f:
                    ImageHandler.IMAGE_MAP = json.load(f)
        except: pass

    @staticmethod
    def get_image_path(filename):
        # Làm sạch tên file (bỏ đường dẫn nếu có, chỉ lấy tên file)
        clean_name = os.path.basename(filename).strip()
        
        # 1. Tìm trong thư viện map
        if clean_name in ImageHandler.IMAGE_MAP: 
            return ImageHandler.IMAGE_MAP[clean_name]
        
        # 2. Tìm fallback trong thư mục hiện tại hoặc data
        local_path = os.path.abspath(filename)
        if os.path.exists(local_path): return local_path
        
        return None
ImageHandler.load_library()

# --- 3. LATEX CLEANER (BỘ LÀM SẠCH MÃ LATEX) ---
# Class này chịu trách nhiệm loại bỏ nhiễu, comment trước khi xử lý
class LatexCleaner:
    @staticmethod
    def clean(text):
        if not text: return ""
        original_text = text
        
        # 1. Xóa comment (%) nhưng giữ lại \% (ký tự phần trăm thực sự)
        # Logic: Tìm ký tự % mà phía trước nó KHÔNG phải là dấu gạch chéo (\)
        text = re.sub(r'(?<!\\)%.*', '', text)
        
        # 2. Xóa các wrapper môi trường không cần thiết (như \begin{ex} ... \end{ex})
        # Chỉ xóa dòng lệnh begin/end, giữ lại nội dung bên trong
        text = re.sub(r'^\s*\\begin\s*\{[a-zA-Z0-9]+\}.*?(\[.*?\])?', '', text, flags=re.MULTILINE) 
        text = re.sub(r'\\end\s*\{[a-zA-Z0-9]+\}\s*$', '', text, flags=re.MULTILINE)
        
        # 3. Xóa các lệnh định dạng trang in (không cần thiết cho Web)
        text = text.replace(r'\noindent', '').replace(r'\newpage', '').replace(r'\clearpage', '')
        
        # Chuẩn hóa khoảng trắng
        text = text.strip()
        
        # [QUAN TRỌNG] Nếu clean xong mà mất hết chữ (ví dụ câu hỏi chỉ có hình ảnh)
        # thì trả về nguyên gốc để tránh mất nội dung.
        if not text:
            return original_text
            
        return text

# --- 2. TIKZ COMPILER (HỖ TRỢ TUYỆT ĐỐI CHO BẢNG & HÌNH) ---
class TikzCompiler:
    # Template chứa đầy đủ gói lệnh + varwidth để xử lý văn bản/bảng trong hình
    TEMPLATE = r"""
\documentclass[dvisvgm]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage[vietnamese]{babel}

% --- GÓI HỖ TRỢ BẢNG & VĂN BẢN (QUAN TRỌNG) ---
\usepackage{varwidth}     % Giúp bảng hiển thị được trong standalone
\usepackage{array, booktabs, longtable, colortbl}
\usepackage{multicol, multirow, makecell}

% --- GÓI TOÁN ---
\usepackage{amsmath,amssymb,mathrsfs,mathabx} 
\usepackage{mhchem, chemfig, siunitx, esvect}       
\usepackage{enumerate, enumitem}
\usepackage{tabvar}       % Bảng biến thiên đơn giản

% --- GÓI ĐỒ HỌA ---
\usepackage{tikz, tkz-euclide, tkz-tab}
\usepackage{tikz-3dplot, pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{venndiagram, tikz-dependency, tikzpeople}

% --- THƯ VIỆN TIKZ ---
\usetikzlibrary{arrows, calc, intersections, angles, quotes, backgrounds}
\usetikzlibrary{shapes.geometric, patterns, shadings, positioning, fadings}
\usetikzlibrary{decorations.markings, spy, bending, 3d, shadows}

% --- ĐỊNH NGHĨA LẠI ---
\def\vec{\vv}             
\def\overrightarrow{\vv}
\renewcommand{\arraystretch}{1.2} 
% [FIX] ĐỊNH NGHĨA HỆ PHƯƠNG TRÌNH (QUAN TRỌNG)
\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}
\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}
% --- CẤU HÌNH TIKZ ---
\tikzset{
    equal mark/.style={postaction={decorate, decoration={markings, mark=at position 0.5 with {\draw[line width=0.4pt] (-0.05,0.05)--(0.05,-0.05);}}}},
    edge from parent/.style={draw, thick, cyan},
    level 3/.style={yshift=5cm},
    level 4/.style={level distance=5mm}
}

\begin{document}
<<CONTENT>>
\end{document}
    """
    @staticmethod
    def compile(code):
        clean_code = LatexCleaner.clean(code)
        
        # --- LOGIC BỌC THÔNG MINH (SMART WRAPPER) ---
        # Nếu đoạn code KHÔNG PHẢI là tikzpicture (tức là bảng, hoặc công thức rời)
        # Ta sẽ bọc nó vào một node TikZ để ép dvisvgm render thành ảnh
        if "\\begin{tikzpicture}" not in clean_code:
            clean_code = (
                r"\begin{tikzpicture}"
                r"\node[inner sep=5pt, anchor=center, align=center] at (0,0) {"
                r"\begin{varwidth}{18cm}"  # varwidth giúp bảng tự co giãn theo nội dung
                + clean_code +
                r"\end{varwidth}"
                r"};"
                r"\end{tikzpicture}"
            )

        code_hash = hashlib.md5(clean_code.encode('utf-8')).hexdigest()
        svg_path = os.path.join(CACHE_DIR, f"{code_hash}.svg")
        
        if os.path.exists(svg_path):
            with open(svg_path, 'r', encoding='utf-8') as f: return f.read()
        
        try:
            tex_path = os.path.join(CACHE_DIR, f"{code_hash}.tex")
            dvi_path = os.path.join(CACHE_DIR, f"{code_hash}.dvi")
            
            full_content = TikzCompiler.TEMPLATE.replace("<<CONTENT>>", clean_code)
            
            with open(tex_path, 'w', encoding='utf-8') as f: 
                f.write(full_content)
            
            # Timeout 20s cho bảng lớn
            subprocess.run(["latex", "-interaction=nonstopmode", "-output-directory", CACHE_DIR, tex_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            
            if os.path.exists(dvi_path):
                # --no-fonts: Biến chữ thành vector (tránh lỗi font trên web)
                subprocess.run(["dvisvgm", "--no-fonts", "--scale=1.4", "-o", svg_path, dvi_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
                
                if os.path.exists(svg_path):
                    with open(svg_path, 'r', encoding='utf-8') as f: return f.read()
        except Exception as e:
            print(f"Lỗi biên dịch: {e}")
        return None

# --- 4. LATEX PARSER (PHIÊN BẢN AN TOÀN - KHÔNG BỎ SÓT CÂU HỎI) ---
# --- 4. LATEX PARSER (CHỐNG CRASH - LUÔN HIỂN THỊ) ---
class LatexParser:
    @staticmethod
    def find_closing_brace(text, open_pos):
        balance = 1; i = open_pos + 1; n = len(text)
        while i < n:
            char = text[i]
            if char == '\\' and i + 1 < n: i += 2; continue
            if char == '{': balance += 1
            elif char == '}': balance -= 1
            if balance == 0: return i
            i += 1
        return -1

    @staticmethod
    def extract_command(text, cmd_name):
        try:
            pattern = f"\\\\{cmd_name}" + r"(?:\[.*?\])?\s*\{"
            match = re.search(pattern, text)
            if not match: return None, text
            start_content = match.end() - 1
            end_content = LatexParser.find_closing_brace(text, start_content)
            if end_content != -1:
                content = text[start_content+1 : end_content]
                remain = text[:match.start()] + " " + text[end_content+1:]
                return content, remain
        except: pass # Nếu lỗi regex thì bỏ qua
        return None, text

    @staticmethod
    def extract_multiple_args(text, cmd_name):
        try:
            pattern = f"\\\\{cmd_name}" + r"(?:\[.*?\])?"
            match = re.search(pattern, text)
            if not match: return [], text
            args = []; idx = match.end(); text_before = text[:match.start()]
            while idx < len(text):
                while idx < len(text) and text[idx].isspace(): idx += 1
                if idx >= len(text) or text[idx] != '{': break 
                end = LatexParser.find_closing_brace(text, idx)
                if end == -1: break
                args.append(text[idx+1:end])
                idx = end + 1
            return args, text_before
        except: return [], text

    @staticmethod
    def parse_full(raw_tex):
        # Backup nội dung gốc để fallback nếu lỗi
        original_tex = raw_tex
        
        try:
            q = LatexCleaner.clean(raw_tex)
            
            # 1. Tách lời giải
            solution_content, q = LatexParser.extract_command(q, "loigiai")
            if not solution_content: solution_content = ""

            # 2. Xử lý Hình ảnh & TikZ
            # ... (Giữ nguyên logic TikZ của bạn)
            # TikZ
            tikz_blocks = re.findall(r'(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})', q, re.DOTALL)
            for code in tikz_blocks:
                svg = TikzCompiler.compile(code)
                if svg: q = q.replace(code, f'<div class="tikz-wrapper">{svg}</div>')
            
            # Tabular/Table (Biến bảng thành hình để không lỗi)
            table_blocks = re.findall(r'(\\begin\{tabular\}.*?\\end\{tabular\})', q, re.DOTALL)
            for code in table_blocks:
                svg = TikzCompiler.compile(code)
                if svg: q = q.replace(code, f'<div class="tikz-wrapper">{svg}</div>')

            # Ảnh
            matches = list(re.finditer(r"\\includegraphics(\[.*?\])?\{([^{}]+)\}", q))
            for m in reversed(matches):
                img_path = m.group(2).strip()
                html = f'<div class="img-wrapper"><img src="/api/image/{img_path}" loading="lazy"></div>'
                q = q[:m.start()] + html + q[m.end():]

            # Center
            q = re.sub(r'\\begin\{center\}(.*?)\\end\{center\}', r'<div style="text-align: center;">\1</div>', q, flags=re.DOTALL)

            # Immini
            if "\\immini" in q:
                match = re.search(r"\\immini(?:\[.*?\])?", q)
                if match:
                    start_parse = match.end()
                    temp_q = q[start_parse:]
                    args = []
                    curr = 0
                    for _ in range(2):
                        while curr < len(temp_q) and temp_q[curr].isspace(): curr += 1
                        if curr < len(temp_q) and temp_q[curr] == '{':
                            end = LatexParser.find_closing_brace(temp_q, curr)
                            if end != -1:
                                args.append(temp_q[curr+1:end])
                                curr = end + 1
                    if len(args) == 2:
                        html = f"""<div class="immini-box"><div class="immini-content">{args[0]}</div><div class="immini-media">{args[1]}</div></div>"""
                        q = q[:match.start()] + html + temp_q[curr:]

            # 3. Phân loại & Tách đáp án
            q_type = 3 # Mặc định là Tự luận (Type 3)
            options = []
            correct_key = "?"

            tf_opts, text_before = LatexParser.extract_multiple_args(q, "choiceTF")
            if tf_opts:
                q_type = 2; q = text_before; options = tf_opts
            else:
                ans_content, text_before = LatexParser.extract_command(q, "shortans")
                if ans_content:
                    q_type = 3; q = text_before; correct_key = ans_content
                    q = q.replace(f"\\shortans{{{ans_content}}}", "")
                else:
                    c_opts, text_before = LatexParser.extract_multiple_args(q, "choice")
                    if c_opts:
                        q_type = 1; q = text_before
                        clean_opts = []
                        for i, o in enumerate(c_opts):
                            if "\\True" in o: 
                                o = o.replace("\\True", ""); correct_key = ['A', 'B', 'C', 'D'][i]
                            clean_opts.append(o.strip())
                        options = clean_opts

            # Clean final
            q = q.replace("\\True", "")
            solution_content = solution_content.replace("\\True", "")

            # Kiểm tra cuối cùng: Nếu q rỗng -> Lấy original
            if not q.strip(): q = original_tex

            return {
                "type": q_type, 
                "content": q, 
                "options": options, 
                "solution": solution_content, 
                "correct_key": correct_key
            }

        except Exception as e:
            # [CHỐNG CRASH] Nếu lỗi bất cứ đâu, trả về nguyên văn để người dùng đọc tạm
            print(f"⚠️ Lỗi Parse: {e}. Đang dùng Fallback.")
            return {
                "type": 3, # Coi như câu hỏi tự luận
                "content": original_tex, # Hiển thị nội dung gốc
                "options": [],
                "solution": "",
                "correct_key": "?"
            }

    @staticmethod
    def split_question_parts(raw_tex):
        """
        Phân tách câu hỏi thành: Nội dung hỏi (Stem), List đáp án (Options), Lời giải (Solution)
        Hỗ trợ cấu trúc: \choice{A}{B}{C}{D}, \choiceTF, \loigiai
        """
        # 1. Làm sạch cơ bản
        clean_tex = LatexCleaner.clean(raw_tex)
        
        # 2. Tách Lời giải (\loigiai)
        solution = ""
        sol_content, text_remains = LatexParser.extract_command(clean_tex, "loigiai")
        if sol_content:
            solution = sol_content
            clean_tex = text_remains # Cập nhật nội dung sau khi cắt lời giải

        # 3. Tách các phương án (\choice hoặc \choiceTF)
        options = []
        stem = clean_tex
        
        # Thử tìm \choice (Trắc nghiệm 4 đáp án)
        choice_opts, stem_remains = LatexParser.extract_multiple_args(clean_tex, "choice")
        
        if choice_opts:
            options = choice_opts
            stem = stem_remains
        else:
            # Thử tìm \choiceTF (Đúng sai) - Nếu muốn tách ý
            tf_opts, stem_remains_tf = LatexParser.extract_multiple_args(clean_tex, "choiceTF")
            if tf_opts:
                options = tf_opts
                stem = stem_remains_tf

        # 4. Xử lý phần dư thừa trong Stem (như lệnh \choice rỗng còn sót lại)
        stem = re.sub(r'\\choice\s*$', '', stem).strip()
        stem = re.sub(r'\\choiceTF\s*$', '', stem).strip()
        
        return {
            "stem": stem,       # Nội dung câu hỏi (đã cắt đáp án và lời giải)
            "options": options, # List các đáp án thô (LaTeX)
            "solution": solution # Nội dung lời giải
        }
# --- 5. WEB UI (FIX LỖI JAVASCRIPT SPREAD SYNTAX) ---
WEB_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>HỆ THỐNG THI ONLINE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']]
      }
    };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; height: 100vh; overflow: hidden; }
        /* [NEW] Review Mode Classes */
        .user-correct { background-color: #22c55e !important; color: white !important; border-color: transparent !important; }
        .user-wrong { background-color: #ef4444 !important; color: white !important; border-color: transparent !important; }
        .system-correct { border: 2px solid #22c55e !important; color: #15803d !important; font-weight: bold; }
        .system-key { font-size: 0.75rem; font-weight: bold; margin-left: 0.5rem; }
        #login-screen { position: fixed; inset: 0; background: #fff; z-index: 50; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .login-box { width: 90%; max-width: 400px; text-align: center; }
        #exam-ui { display: flex; height: 100%; flex-direction: column; }
        @media (min-width: 768px) { #exam-ui { flex-direction: row; } }
        .left-panel { flex: 1; background: #374151; position: relative; display: none; }
        @media (min-width: 768px) { .left-panel { display: block; flex: 6; } }
        iframe { width: 100%; height: 100%; border: none; }
        .right-panel { flex: 4; display: flex; flex-direction: column; background: white; height: 100%; border-left: 1px solid #ddd; }
        .sheet-container { flex: 1; overflow-y: auto; padding: 15px; -webkit-overflow-scrolling: touch; }
        .part-title { background: #e0f2fe; color: #0369a1; padding: 8px; font-weight: bold; font-size: 14px; margin: 15px 0 10px 0; border-radius: 6px; text-transform: uppercase; }
        .q-item { background: #fff; border: 1px solid #e5e7eb; padding: 10px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .q-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .q-id { font-weight: bold; color: #374151; width: 30px; }
        .bubbles { display: flex; gap: 8px; justify-content: center; }
        .bubble { width: 35px; height: 35px; border-radius: 50%; border: 2px solid #d1d5db; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #6b7280; cursor: pointer; }
        .bubble.selected { background: #2563eb; color: white; border-color: #2563eb; transform: scale(1.1); transition: 0.2s; }
        .tf-row { display: flex; align-items: center; justify-content: space-between; background: #f9fafb; padding: 6px 10px; margin-bottom: 4px; border-radius: 4px; }
        .tf-opts { display: flex; gap: 5px; }
        .tf-btn { width: 30px; height: 30px; border: 1px solid #cbd5e1; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px; cursor: pointer; }
        .tf-btn.sel-D { background: #22c55e; color: white; border-color: #22c55e; }
        .tf-btn.sel-S { background: #ef4444; color: white; border-color: #ef4444; }
        .short-inp { width: 100%; border: 2px solid #e5e7eb; padding: 8px; border-radius: 6px; font-weight: bold; color: #1e3a8a; text-align: center; }
        .short-inp:focus { border-color: #2563eb; outline: none; }
        .mark { font-weight: bold; font-size: 14px; }
        #score-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 3000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(5px); }
        .score-box { background: white; padding: 40px; border-radius: 20px; text-align: center; width: 90%; max-width: 500px; animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        @keyframes popIn { from { transform: scale(0.5); opacity: 0; } to { transform: scale(1); opacity: 1; } }
    </style>
</head>
<body>
    <div id="login-screen">
        <div class="login-box" id="login-form">
            <div class="text-5xl mb-4">📝</div>
            <h2 class="text-2xl font-bold text-gray-800 mb-2">VÀO PHÒNG THI</h2>
            <div id="exam-title-display" class="text-blue-600 font-bold mb-6 text-sm uppercase">Đang tải thông tin đề...</div>
            
            <!-- [UPDATED] Select Roster -->
            <select id="student-select" class="w-full p-3 border-2 border-gray-200 rounded-lg mb-3 text-center font-bold outline-none focus:border-blue-500 bg-white">
                <option value="">-- Chọn tên của bạn --</option>
            </select>
            
            <!-- Fallback input (hidden by default) -->
            <input type="text" id="student-name" class="hidden w-full p-3 border-2 border-gray-200 rounded-lg mb-3 text-center font-bold outline-none focus:border-blue-500" placeholder="Hoặc nhập tên nếu không có trong danh sách">

            <input type="email" id="student-email" class="w-full p-3 border-2 border-gray-200 rounded-lg mb-6 text-center font-bold outline-none focus:border-blue-500" placeholder="Email (Tự động điền)" readonly>
            <button onclick="window.joinRoom()" class="w-full bg-blue-600 text-white p-3 rounded-lg font-bold text-lg shadow-lg active:scale-95 transition">VÀO THI NGAY</button>
        </div>
        <div class="login-box hidden" id="waiting-msg">
            <div class="text-6xl mb-4 animate-bounce">⏳</div>
            <h2 class="text-xl font-bold text-gray-800">ĐANG TẢI ĐỀ THI...</h2>
            <div class="mt-4 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg font-bold"><span id="display-name"></span></div>
        </div>
    </div>

    <div id="exam-ui" class="hidden">
        <div class="left-panel"><iframe id="pdf-frame"></iframe></div>
        <div class="right-panel">
             <div class="bg-gray-800 text-white p-3 flex justify-between items-center shadow-md z-10">
                <div><div class="text-xs opacity-70">THỜI GIAN</div><div class="text-2xl font-mono font-bold text-yellow-400" id="timer">--:--</div></div>
                <button onclick="window.submitExam()" id="btn-submit" class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-6 rounded shadow">NỘP BÀI</button>
             </div>
             <div class="sheet-container" id="sheet"></div>
        </div>
    </div>

    <div id="score-modal">
        <div class="score-box">
            <div class="text-6xl mb-4">🏆</div>
            <h2 class="text-3xl font-bold text-gray-800 mb-2">KẾT QUẢ</h2>
            <div class="text-5xl font-bold text-blue-600 my-6"><span id="final-score">0</span> điểm</div>
            <div class="text-sm text-green-600 font-bold mb-6">Đã lưu kết quả vào hệ thống!</div>
            <button onclick="enterReviewMode()" class="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded shadow">Xem lại bài làm</button>
        </div>
    </div>

    <script>
        // [UPDATED] Student Roster Injection
        const STUDENTS = __STUDENT_LIST__; // Injected by Python
        
        // Populate Dropdown
        document.addEventListener('DOMContentLoaded', () => {
            const sel = document.getElementById('student-select');
            const inpName = document.getElementById('student-name');
            const inpEmail = document.getElementById('student-email');
            
            if (STUDENTS && STUDENTS.length > 0) {
                STUDENTS.sort((a,b) => a.name.localeCompare(b.name));
                STUDENTS.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s.id;
                    opt.text = s.name;
                    opt.dataset.email = s.email;
                    sel.appendChild(opt);
                });
                
                sel.addEventListener('change', () => {
                    const opt = sel.options[sel.selectedIndex];
                    if (opt.value) {
                        inpName.value = opt.text;
                        inpEmail.value = opt.dataset.email;
                    } else {
                        inpName.value = "";
                        inpEmail.value = "";
                    }
                });
            } else {
                // No roster -> Show manual input
                sel.classList.add('hidden');
                inpName.classList.remove('hidden');
                inpEmail.removeAttribute('readonly');
            }
        });

        // Lấy ID đề thi từ URL (VD: /exam/DE_THI_123 -> examId = DE_THI_123)
        var pathParts = window.location.pathname.split('/');
        var examId = pathParts[pathParts.length - 1]; // Lấy phần cuối cùng

        var ws = null;
        var clientId = localStorage.getItem('sid') || 'u-' + Math.random().toString(36).substr(2, 6);
        localStorage.setItem('sid', clientId);
        var examData = null; var userAnswers = {}; var timeLeft = 0; var timerInt = null; var isSubmitted = false;
        var myName = "", myEmail = "";

        // Tự động kết nối để lấy tên đề thi
        window.onload = function() {
             document.getElementById('exam-title-display').innerText = "Mã đề: " + examId;
        }

        window.joinRoom = function() {
            myName = document.getElementById('student-name').value.trim();
            myEmail = document.getElementById('student-email').value.trim();
            if (!myName) return alert("Vui lòng nhập Họ Tên!");

            var btn = document.querySelector('#login-form button');
            var oldText = btn.innerText; btn.innerText = "ĐANG KẾT NỐI..."; btn.disabled = true;

            var proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            var url = proto + '//' + window.location.host + '/ws';
            
            try {
                ws = new WebSocket(url);
                ws.onopen = function() {
                    // [QUAN TRỌNG] Gửi kèm examId để Server biết cần lấy đề nào
                    ws.send(JSON.stringify({ type: "JOIN", id: clientId, name: myName, email: myEmail, exam_id: examId }));
                    document.getElementById('login-form').classList.add('hidden');
                    document.getElementById('waiting-msg').classList.remove('hidden');
                    document.getElementById('display-name').innerText = myName;
                };
                ws.onmessage = function(e) {
                    try {
                        var msg = JSON.parse(e.data);
                        if (msg.type === 'START_EXAM') startExam(msg.data);
                        if (msg.type === 'SCORE_RESULT') showResult(msg.data);
                        if (msg.type === 'ERROR') { alert(msg.message); location.reload(); }
                    } catch(err) {}
                };
                ws.onerror = function() { alert("Lỗi kết nối!"); btn.innerText = oldText; btn.disabled = false; };
            } catch (e) { alert("Lỗi Socket: " + e); btn.innerText = oldText; btn.disabled = false; }
        };

        function startExam(data) {
            examData = data;
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('exam-ui').classList.remove('hidden');
            if(data.pdf_filename) document.getElementById('pdf-frame').src = '/api/pdf/' + data.pdf_filename;
            if(data.duration) { timeLeft = parseInt(data.duration); startTimer(); }
            renderSheet(data.exam_matrix || []);
        }
        
        var savedReviewData = null;

        function closeModal() {
            document.getElementById('score-modal').style.display = 'none';
        }

        function showResult(data) {
            document.getElementById('final-score').innerText = data.score.toFixed(2);
            document.getElementById('score-modal').style.display = 'flex';
            savedReviewData = data.review_data;
        }

        function enterReviewMode() {
            closeModal();
            if (savedReviewData) renderReview(savedReviewData);
        }

        function renderReview(reviewData) {
            // Disable inputs
            document.querySelectorAll('.bubble, .tf-btn').forEach(el => el.style.pointerEvents = 'none');
            document.querySelectorAll('.short-inp').forEach(el => el.disabled = true);

            for (const [qid, info] of Object.entries(reviewData)) {
                // 1. Highlight Marker (Correct/Wrong)
                const mk = document.getElementById('m-'+qid);
                if (mk) {
                    if (info.type === 1 || info.type === 3) {
                        mk.innerHTML = info.is_correct ? '✅' : '<span class="text-red-500 font-bold">'+info.correct_answer+'</span>';
                    } else if (info.type === 2) {
                        mk.innerHTML = info.is_correct ? '✅' : '<span class="text-blue-600">Chi tiết bên dưới</span>';
                    }
                }

                // 2. Visual Feedback on Options
                if (info.type === 1) { // MCQ
                    // Highlight selected
                    if (info.user_selected) {
                        const btn = document.getElementById('btn-'+qid+'-'+info.user_selected);
                        if (btn) {
                            btn.classList.remove('selected');
                            // [CHANGED] Use classes
                            btn.classList.add(info.is_correct ? 'user-correct' : 'user-wrong');
                        }
                    }
                    // If wrong, highlight correct answer
                    if (!info.is_correct && info.correct_answer && info.correct_answer !== '?') {
                        const correctBtn = document.getElementById('btn-'+qid+'-'+info.correct_answer);
                        if (correctBtn) {
                            // [CHANGED] Use classes
                            correctBtn.classList.add('system-correct');
                        }
                    }
                } else if (info.type === 2) { // True/False
                    if (info.sub_details) {
                        for (const [sub, subInfo] of Object.entries(info.sub_details)) {
                            // Find row
                            const row = Array.from(document.querySelectorAll('#q-'+qid+' .tf-row')).find(r => r.innerText.includes(sub+')'));
                            if (row) {
                                // Show Correct Key
                                const keySpan = document.createElement('span');
                                // [CHANGED] Use specific class for key
                                keySpan.className = 'system-key ' + (subInfo.correct ? 'text-green-600' : 'text-red-500');
                                keySpan.innerText = 'Đ.Án: ' + subInfo.key;
                                row.querySelector('.tf-opts').appendChild(keySpan);

                                // Highlight User Choice
                                if (subInfo.user) {
                                    const btns = row.querySelectorAll('.tf-btn');
                                    btns.forEach(b => {
                                        if (b.innerText === subInfo.user) {
                                            // [CHANGED] Use classes
                                            b.classList.add(subInfo.correct ? 'user-correct' : 'user-wrong');
                                        }
                                    });
                                }
                            }
                        }
                    }
                } else if (info.type === 3) { // Short
                    const inp = document.querySelector('#q-'+qid+' input');
                    if (inp) {
                        // [CHANGED] Use Tailwind classes for border/bg
                        if (info.is_correct) {
                            inp.classList.add('border-green-500', 'bg-green-50');
                        } else {
                            inp.classList.add('border-red-500', 'bg-red-50');
                        }
                    }
                }

                // 3. Show Explanation if available
                if (info.explanation) {
                    const qItem = document.getElementById('q-'+qid);
                    if (qItem) {
                        const explDiv = document.createElement('div');
                        explDiv.className = 'mt-2 p-3 bg-yellow-50 border-l-4 border-yellow-400 text-sm text-gray-700';
                        explDiv.innerHTML = '<b>Lời giải:</b> ' + info.explanation;
                        qItem.appendChild(explDiv);
                    }
                }
            }
            // Trigger MathJax to render the new content
            if (window.MathJax && MathJax.typesetPromise) {
                MathJax.typesetPromise();
            }
        }

        function renderSheet(matrix) {
            var c = document.getElementById('sheet'); c.innerHTML = "";
            var p1 = matrix.filter(q => q.type == 1);
            var p2 = matrix.filter(q => q.type == 2);
            var p3 = matrix.filter(q => q.type == 3);

            if(p1.length > 0) {
                c.innerHTML += '<div class="part-title">PHẦN I: TRẮC NGHIỆM ('+(3.0/p1.length).toFixed(2)+'đ/câu)</div>';
                p1.forEach(q => {
                    var html = '<div class="q-item" id="q-'+q.id+'"><div class="q-header"><div class="q-id">'+q.id+'</div><div class="mark" id="m-'+q.id+'"></div></div><div class="bubbles">';
                    ['A','B','C','D'].forEach(opt => {
                        html += '<div class="bubble" id="btn-'+q.id+'-'+opt+'" data-type="1" data-id="'+q.id+'" data-val="'+opt+'" onclick="handleClick(this)">'+opt+'</div>';
                    });
                    c.innerHTML += html + '</div></div>';
                });
            }
            if(p2.length > 0) {
                c.innerHTML += '<div class="part-title">PHẦN II: ĐÚNG/SAI ('+(4.0/p2.length).toFixed(2)+'đ/câu)</div>';
                p2.forEach(q => {
                    var html = '<div class="q-item" id="q-'+q.id+'"><div class="q-header"><div class="q-id">'+q.id+'</div><div class="mark" id="m-'+q.id+'"></div></div><div class="tf-grid">';
                    ['a','b','c','d'].forEach(sub => {
                        html += '<div class="tf-row"><span>'+sub+')</span><div class="tf-opts"><div class="tf-btn" data-type="2" data-id="'+q.id+'" data-sub="'+sub+'" data-val="Đ" onclick="handleClick(this)">Đ</div><div class="tf-btn" data-type="2" data-id="'+q.id+'" data-sub="'+sub+'" data-val="S" onclick="handleClick(this)">S</div><span class="text-xs font-bold text-gray-400 ml-2" id="key-'+q.id+'-'+sub+'"></span></div></div>';
                    });
                    c.innerHTML += html + '</div></div>';
                });
            }
            if(p3.length > 0) {
                c.innerHTML += '<div class="part-title">PHẦN III: TRẢ LỜI NGẮN ('+(3.0/p3.length).toFixed(2)+'đ/câu)</div>';
                p3.forEach(q => {
                    c.innerHTML += '<div class="q-item" id="q-'+q.id+'"><div class="q-header"><div class="q-id">'+q.id+'</div><div class="mark" id="m-'+q.id+'"></div></div><input type="text" class="short-inp" placeholder="Nhập đáp án..." onchange="window.sel(3,'+q.id+',this.value)"></div>';
                });
            }
        }
        window.handleClick = function(el) { window.sel(parseInt(el.dataset.type), el.dataset.id, el.dataset.val, el.dataset.sub, el); };
        window.sel = function(t, i, v, s, e) {
            if(isSubmitted) return;
            if(t===1) { userAnswers[i] = v; var p = e.parentElement; for(var k=0; k<p.children.length; k++) p.children[k].classList.remove('selected'); e.classList.add('selected'); }
            else if(t===2) { if(!userAnswers[i]) userAnswers[i] = {}; userAnswers[i][s] = v; var p = e.parentElement; for(var k=0; k<p.children.length; k++) if(p.children[k].classList.contains('tf-btn')) p.children[k].className='tf-btn'; e.classList.add(v==='Đ'?'sel-D':'sel-S'); }
            else if(t===3) userAnswers[i] = v;
        };
        function startTimer() { timerInt = setInterval(function() { if(timeLeft <= 0) { clearInterval(timerInt); window.submitExam(); return; } timeLeft--; var m = Math.floor(timeLeft/60), s = timeLeft%60; document.getElementById('timer').innerText = m + ":" + (s<10?"0":"")+s; }, 1000); }

        window.submitExam = function() {
            if(!confirm("Nộp bài ngay?")) return;
            isSubmitted = true; 
            document.getElementById('btn-submit').style.display = 'none'; 
            clearInterval(timerInt);
            
            document.getElementById('final-score').innerText = "Đang chấm...";
            document.getElementById('score-modal').style.display = 'flex';

            // Gửi Answers + Variant Code về Server để chấm
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ 
                    type: "SUBMIT", 
                    exam_id: examId, 
                    variant_code: examData.variant_code || "", 
                    name: myName, 
                    email: myEmail, 
                    detail: userAnswers 
                }));
            } else {
                alert("Mất kết nối với Server! Không thể gửi bài.");
            }
        };
    </script>
</body>
</html>
"""

# =============================================================================
# CẬP NHẬT WEB SERVER THREAD (TỰ ĐỘNG TÌM PORT TRỐNG)
# =============================================================================
# --- CẬP NHẬT: WEB SERVER FIX LỖI TIẾNG VIỆT & KẾT NỐI ---
import json
import asyncio
import socket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def register(self, websocket: WebSocket, client_id: str, name: str):
        """Lưu thông tin sau khi nhận gói tin JOIN"""
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

# --- ĐẢM BẢO ĐÃ IMPORT CÁC THƯ VIỆN NÀY Ở ĐẦU FILE ---
from pyngrok import ngrok, conf
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import socket

# --- CẬP NHẬT: WEB SERVER THREAD (FIX LỖI GMAIL CÁ NHÂN) ---
class WebServerThread(QThread):
    students_changed = pyqtSignal(list)
    server_ready = pyqtSignal(str)
    result_received = pyqtSignal(str, float)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.port = 8080
        
        # [QUAN TRỌNG] Nhớ điền Token thật của bạn vào đây
        # Ví dụ: self.ngrok_auth_token = "2Alk..."
        self.ngrok_auth_token = "38b8oxhy3hT98ZoeqO7kl8RJaJP_axFQ8v4mjEtV5EvSwLzb"
        
        self.public_url = ""
        
        # [ĐÃ SỬA] Thêm lại dòng này để tránh lỗi Attribute Error
        self.ip_address = "0.0.0.0" 
        
        self.gg_sync = None 
        
        # Thư mục chứa các file đề thi riêng biệt
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
        if q_type == 1: # MCQ
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
        elif q_type == 2: # TF
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
        elif q_type == 3: # Short
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
        review_data = {} # Dictionary: question_id -> details
        
        p1 = [q for q in exam_matrix if q['type'] == 1]
        p2 = [q for q in exam_matrix if q['type'] == 2]
        p3 = [q for q in exam_matrix if q['type'] == 3]

        val_p1 = (3.0 / len(p1)) if p1 else 0
        val_p2 = (4.0 / len(p2)) if p2 else 0
        val_p3 = (3.0 / len(p3)) if p3 else 0

        for q in exam_matrix:
            qid = str(q['id'])
            ua = user_answers.get(qid)
            
            # Lấy Key và Explanation từ matrix (đã được chuẩn hóa bởi Worker)
            q_key = q.get('key')
            # Fallback nếu thiếu
            if not q_key or q_key == '?':
                content = q.get('content_tex') or q.get('content')
                q_key = self.extract_key_from_tex(content, q['type'])
            
            q_type = q['type']
            
            # Cấu trúc dữ liệu Review chi tiết
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
                        # ========================================================
                    # [BẮT ĐẦU ĐOẠN CODE CHÈN THÊM - BƯỚC 2]
                    # ========================================================
                    # ========================================================
                    # [CODE MỚI ĐÃ SỬA LỖI TIMESTAMP]
                    # ========================================================
                    try:
                        # 1. Tạo thời gian hiện tại từ Python (Thay vì để SQL tự sinh)
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # 2. Tạo dữ liệu chi tiết (Log bài làm)
                        results_log = []
                        questions_list = data.get('questions', []) 
                        
                        for q in questions_list:
                            q_id_str = str(q['id'])
                            stu_ans = user_answers.get(q_id_str, user_answers.get(int(q_id_str), ""))
                            cor_ans = q.get('correct', "")
                            is_right = str(stu_ans).strip().lower() == str(cor_ans).strip().lower()
                            
                            results_log.append({
                                "question": q.get('content', ""),
                                "student_ans": stu_ans,
                                "correct_ans": cor_ans,
                                "is_correct": is_right
                            })
                        
                        detail_json = json.dumps(results_log, ensure_ascii=False)
                        
                        # 3. Lấy thông tin học sinh
                        p_name = payload.get('student_name', 'Học sinh ẩn danh')
                        p_email = payload.get('student_email', '')
                        p_exam_id = payload.get('exam_id', 'unknown')
                        
                        # 4. Ghi vào Database (Có thêm cột timestamp)
                        with sqlite3.connect(DB_PATH) as conn:
                            cursor = conn.cursor()
                            
                            # Đảm bảo bảng tồn tại với cấu trúc mới (timestamp là TEXT)
                            cursor.execute('''CREATE TABLE IF NOT EXISTS exam_results (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                student_name TEXT, 
                                student_email TEXT, 
                                exam_id TEXT,
                                score REAL, 
                                detail_json TEXT, 
                                ai_feedback TEXT,
                                timestamp TEXT
                            )''')
                            
                            # CÂU LỆNH QUAN TRỌNG NHẤT: Thêm cột timestamp và giá trị current_time
                            cursor.execute("""
                                INSERT INTO exam_results (student_name, student_email, exam_id, score, detail_json, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (p_name, p_email, p_exam_id, score, detail_json, current_time))
                            
                            conn.commit()
                            
                        print(f"✅ [SERVER] Đã lưu kết quả lúc {current_time}: {p_name} - {score} điểm")
                        
                    except Exception as e_save:
                        print(f"❌ [SERVER ERROR] Lỗi lưu điểm: {e_save}")
                    # ========================================================
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
        """Lưu dữ liệu đề thi hiện tại vào thread để server sử dụng"""
        self.exam_data = data
        self.exam_id = data.get('examId', 'default')
        # Lưu file để persist
        if 'examId' in data:
            self.save_exam_file(self.exam_id, data)
        print(f"✅ Server loaded exam data: {self.exam_id}")

    def save_exam_file(self, exam_id, data):
        """Lưu đề thi thành file riêng biệt"""
        filepath = os.path.join(self.exam_dir, f"{exam_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"💾 Đã lưu đề thi: {exam_id}")

    def load_exam_file(self, exam_id):
        """Đọc file đề thi theo ID"""
        filepath = os.path.join(self.exam_dir, f"{exam_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def sync_score(self, exam_data, name, email, score):
        """Đồng bộ điểm lên Google Classroom (Cần dữ liệu của đúng đề đó)"""
        cid = exam_data.get('courseId')
        cwid = exam_data.get('courseWorkId')
        if not cid or not cwid: return

        if not self.gg_sync:
            try: self.gg_sync = GoogleManagerFull(); self.gg_sync.authenticate()
            except: return

        try:
            print(f"🔄 Đang đồng bộ điểm cho đề {exam_data.get('title')}...")
            service = self.gg_sync.service_class
            # ... (Giữ nguyên logic tìm HS và chấm điểm như cũ) ...
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

    def run(self):
        # 1. DIỆT SẠCH TIẾN TRÌNH NGROK CŨ
        try:
            print("🔄 Đang dọn dẹp các kết nối cũ...")
            from pyngrok import ngrok
            ngrok.kill()
            
            # [Fix] Force kill process nếu ngrok.kill() không sạch (Tránh lỗi ERR_NGROK_334)
            if sys.platform != "win32":
                os.system("pkill -9 ngrok")
            
            import time
            time.sleep(2)
        except:
            pass

        # 2. CẤU HÌNH TOKEN (ĐOẠN ĐÃ SỬA)
        # Bắt buộc nạp token để tránh lỗi ERR_NGROK_4018
        if self.ngrok_auth_token:
            conf.get_default().auth_token = self.ngrok_auth_token
            # Đặt vùng là US (Mỹ) hoặc AP (Châu Á) tùy chọn
            conf.get_default().region = "us" 
        
        app = FastAPI()
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

        # URL ĐỘNG: /exam/{exam_id} -> Trả về giao diện thi
        @app.get("/exam/{exam_id}")
        async def get_exam_ui(exam_id: str):
            # Kiểm tra xem đề có tồn tại không
            data = self.load_exam_file(exam_id)
            if data:
                # Inject Student List

                # 1. Khởi tạo danh sách học sinh
                final_students = []
            
            # 2. Cố gắng lấy danh sách từ Database (Do Classroom đồng bộ về)
            try:
                # DB_PATH là biến toàn cục chứa đường dẫn file .db của bạn
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                # Lấy tên và email từ bảng students
                cursor.execute("SELECT name, email FROM students")
                rows = cursor.fetchall()
                conn.close()
                
                if rows:
                    for r_name, r_email in rows:
                        final_students.append({"name": r_name, "email": r_email})
                    print(f"Server: Đã load {len(final_students)} học sinh từ Database.")
            except Exception as e:
                print(f"Server: Không đọc được DB Students ({e}). Dùng danh sách từ file đề.")

            # 3. Fallback: Nếu DB rỗng (chưa đồng bộ), dùng lại danh sách cũ trong file đề
            if not final_students:
                final_students = data.get('students', [])

            # 4. Chuyển đổi sang JSON để chèn vào HTML
            # ensure_ascii=False để giữ tiếng Việt không bị lỗi font
            json_students = json.dumps(final_students, ensure_ascii=False).replace("</script>", "<\\/script>")
            
            # 5. Thay thế placeholder trong HTML
            html_content = WEB_UI_TEMPLATE.replace("__STUDENT_LIST__", json_students)
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
                            
                            # [MỚI] Chọn ngẫu nhiên 1 mã đề nếu có nhiều variants
                            payload = exam_data
                            variants = exam_data.get('variants', [])
                            if variants:
                                import random
                                selected_variant = random.choice(variants)
                                # Tạo payload mới chỉ chứa variant này (để client render đúng PDF)
                                payload = exam_data.copy()
                                payload['pdf_filename'] = selected_variant['pdf_filename']
                                payload['exam_matrix'] = selected_variant['exam_matrix']
                                payload['variant_code'] = selected_variant['code']
                                
                            # [BẢO MẬT] Xóa Key trước khi gửi xuống Client
                            sanitized_payload = payload.copy()
                            if 'exam_matrix' in sanitized_payload:
                                import copy
                                sanitized_matrix = copy.deepcopy(sanitized_payload['exam_matrix'])
                                for q in sanitized_matrix:
                                    if 'key' in q: del q['key']
                                sanitized_payload['exam_matrix'] = sanitized_matrix

                            # Gửi đúng đề thi đó cho học sinh
                            await websocket.send_json({"type": "START_EXAM", "data": sanitized_payload})
                        else:
                            await websocket.send_json({"type": "ERROR", "message": "Không tìm thấy dữ liệu đề thi!"})

                    elif data.get('type') == 'SUBMIT':
                        exam_id = data.get('exam_id')
                        variant_code = data.get('variant_code')
                        user_answers = data.get('detail', {})
                        
                        exam_data = self.load_exam_file(exam_id)
                        if exam_data:
                            # 1. Xác định Matrix chấm điểm (theo mã đề)
                            target_matrix = exam_data.get('exam_matrix', [])
                            variants = exam_data.get('variants', [])
                            
                            if variants and variant_code:
                                for v in variants:
                                    if str(v['code']) == str(variant_code):
                                        target_matrix = v['exam_matrix']
                                        break
                            
                            # 2. Chấm điểm Server-side
                            final_score, review_data = self.calculate_score(target_matrix, user_answers)

                            # 3. Lưu kết quả (Lưu full review data vào DB)
                            try:
                                conn = sqlite3.connect(self.db_path)
                                conn.execute("INSERT INTO exam_results (student_name, exam_title, score, detail) VALUES (?, ?, ?, ?)",
                                    (f"{data['name']} ({data['email']})", exam_data.get('title'), final_score, json.dumps(review_data, ensure_ascii=False)))
                                conn.commit(); conn.close()
                                
                                self.result_received.emit(f"{data['name']} - {exam_data.get('title')}", float(final_score))
                                self.sync_score(exam_data, data['name'], data['email'], final_score)
                            except: pass
                            
                            # 4. Trả kết quả về cho Client
                            await websocket.send_json({
                                "type": "SCORE_RESULT", 
                                "data": {
                                    "score": final_score,
                                    "review_data": review_data
                                }
                            })

            except: pass

        # Kết nối Ngrok
        MY_DOMAIN = "oncologic-premeditative-nada.ngrok-free.dev"
        try:
            ngrok.kill()
            success = False

            # 1. Thử kết nối với Domain cố định (Nếu có)
            if MY_DOMAIN and "ngrok-free.dev" in MY_DOMAIN:
                try:
                    print(f"🔄 Connecting to custom domain: {MY_DOMAIN}")
                    import time; time.sleep(1)
                    self.public_url = ngrok.connect(self.port, domain=MY_DOMAIN).public_url
                    self.server_ready.emit(self.public_url)
                    success = True
                except Exception as e:
                    print(f"⚠️ Custom domain failed: {e}")

            # 2. Nếu thất bại, fallback sang random domain
            if not success:
                print("🔄 Falling back to random domain...")
                self.public_url = ngrok.connect(self.port).public_url
                self.server_ready.emit(self.public_url)

        except Exception as e:
            self.server_ready.emit(f"Lỗi Ngrok: {e}")
            print(f"❌ Ngrok Fatal Error: {e}")

        import uvicorn
        config = uvicorn.Config(app, host="0.0.0.0", port=self.port, log_level="critical", proxy_headers=True)
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        """Dừng server và ngrok an toàn"""
        if hasattr(self, 'server') and self.server:
            self.server.should_exit = True
        
        try:
            from pyngrok import ngrok
            ngrok.kill()
            # Force kill
            if sys.platform != "win32":
                os.system("pkill -9 ngrok")
        except:
            pass
        
        # Đợi tối đa 3 giây để luồng kết thúc, nếu không thì ép tắt
        if not self.wait(3000):
            self.terminate()
# =============================================================================
#  MODULE GOOGLE CLASSROOM & PDF (THÊM MỚI VÀO ĐÂY)
# =============================================================================

class StatisticsDashboard(QDialog):
    """Bảng Dashboard thống kê (Giao diện Nâu - Cam Luxury)"""
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.bk = backend
        self.setWindowTitle("📊 Dashboard Thống Kê Ngân Hàng Câu Hỏi")
        self.setMinimumSize(1150, 800)
        
        # Style đồng bộ với Main App
        self.setStyleSheet("""
            QDialog { background-color: #602C04; color: white; }
            
            QGroupBox { 
                background: rgba(237, 132, 13, 0.1); 
                border-radius: 12px; 
                border: 1px solid #954C04; 
                font-weight: bold; 
                margin-top: 10px; 
                color: #ED840D;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            
            QLabel.stat-number { font-size: 32px; font-weight: bold; color: #ED840D; }
            QLabel.stat-label { font-size: 14px; color: #dcdde1; font-weight: bold; text-transform: uppercase; }
            
            QTreeWidget { 
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid #954C04; 
                border-radius: 8px; 
                color: white;
                font-size: 14px;
            }
            QHeaderView::section { 
                background-color: #ae5c04; 
                padding: 8px; 
                border: none; 
                font-weight: bold; 
                color: white; 
                border-bottom: 2px solid #ED840D;
            }
            QTreeWidget::item { padding: 8px; }
            QTreeWidget::item:selected { background-color: #ED840D; color: white; }
            
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid #ED840D;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #ED840D; }
        """)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- PHẦN 1: TỔNG QUAN (CARDS) ---
        top_layout = QHBoxLayout()
        self.card_total = self.create_stat_card("📦 TỔNG CÂU HỎI", "0", "#ED840D")
        top_layout.addWidget(self.card_total)
        
        grp_ratio = QGroupBox("📈 Tỷ lệ Mức độ nhận thức")
        grp_ratio.setMinimumHeight(120)
        ratio_layout = QVBoxLayout(grp_ratio)
        ratio_layout.setContentsMargins(20, 30, 20, 20)
        
        self.bars = {}
        # Màu sắc các mức độ: NB(Xanh lá), TH(Xanh dương), VD(Cam), VDC(Đỏ)
        for code, name, color in [('N', 'Nhận biết', '#2ecc71'), ('H', 'Thông hiểu', '#3498db'), 
                                  ('V', 'Vận dụng', '#f39c12'), ('C', 'Vận dụng cao', '#e74c3c')]:
            h = QHBoxLayout()
            lbl = QLabel(f"{name}:"); lbl.setFixedWidth(100)
            bar = QProgressBar()
            bar.setStyleSheet(f"""
                QProgressBar {{ border: 1px solid #555; border-radius: 4px; text-align: center; background: rgba(0,0,0,0.3); color: white; }}
                QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}
            """)
            bar.setFixedHeight(20)
            self.bars[code] = bar
            h.addWidget(lbl); h.addWidget(bar)
            ratio_layout.addLayout(h)
            
        top_layout.addWidget(grp_ratio, 2)
        layout.addLayout(top_layout)
        
        # --- PHẦN 2: BẢNG CHI TIẾT ---
        layout.addWidget(QLabel("<b>📋 PHÂN TÍCH CHI TIẾT (Theo Khung chương trình mới)</b>"))
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Danh mục", "Tổng", "NB", "TH", "VD", "VDC"])
        self.tree.setColumnWidth(0, 500)
        for i in range(1, 6): self.tree.setColumnWidth(i, 80)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)
        
        btn_close = QPushButton("Đóng")
        btn_close.setFixedWidth(120)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def create_stat_card(self, title, value, color):
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{ 
                background: rgba(0,0,0,0.2); 
                border-radius: 12px; 
                border: 1px solid {color}; 
                border-left: 8px solid {color};
            }}
        """)
        l = QVBoxLayout(f)
        lbl_t = QLabel(title); lbl_t.setProperty("class", "stat-label")
        self.lbl_v = QLabel(value); self.lbl_v.setProperty("class", "stat-number")
        l.addWidget(lbl_t); l.addWidget(self.lbl_v)
        return f

    def load_data(self):
        # Lấy dữ liệu từ Backend
        total, level_map, details = self.bk.get_dashboard_stats()
        self.lbl_v.setText(f"{total:,}")
        
        for code, bar in self.bars.items():
            count = level_map.get(code, 0)
            percent = int((count / total * 100) if total > 0 else 0)
            bar.setValue(percent)
            bar.setFormat(f"{count} câu ({percent}%)")

        data_tree = {}
        for r in details:
            g, s, c, l, count = r
            try: g = int(g); c = int(c)
            except: continue 
            
            if s not in ['D', 'H']: continue
            
            # Lọc theo tên chương chuẩn
            if 'CHAPTER_NAMES' in globals():
                valid_chapters = CHAPTER_NAMES.get(g, {}).get(s, {})
                if c not in valid_chapters: continue 

            if g not in data_tree: data_tree[g] = {}
            if s not in data_tree[g]: data_tree[g][s] = {}
            if c not in data_tree[g][s]: data_tree[g][s][c] = {'total': 0, 'N':0, 'H':0, 'V':0, 'C':0}
            
            node = data_tree[g][s][c]
            node['total'] += count
            if l in node: node[l] += count

        self.tree.clear()
        font_bold = QFont("Arial", 10, QFont.Weight.Bold)
        
        for g in sorted(data_tree.keys()):
            g_item = QTreeWidgetItem(self.tree)
            g_item.setText(0, f"📚 Khối Lớp {g}")
            g_item.setExpanded(True)
            # Màu nền header nhóm
            g_item.setBackground(0, QColor("#602C04")) 
            g_item.setForeground(0, QColor("#ED840D"))
            g_item.setFont(0, font_bold)
            
            g_total = 0 
            
            for s in ['D', 'H']:
                if s not in data_tree[g]: continue
                
                s_name = "Đại số / Giải tích" if s == 'D' else "Hình học"
                
                s_item = QTreeWidgetItem(g_item)
                s_item.setText(0, s_name)
                s_item.setForeground(0, QColor("#f1c40f")) # Màu vàng cho môn
                s_item.setExpanded(True)
                s_item.setFont(0, font_bold)
                
                s_total = 0
                chapters_dict = data_tree[g][s]
                
                for c in sorted(chapters_dict.keys()):
                    stats = chapters_dict[c]
                    ch_title = f"Chương {c}"
                    if 'CHAPTER_NAMES' in globals():
                        full_name = CHAPTER_NAMES.get(g, {}).get(s, {}).get(c, "")
                        if full_name: ch_title = f"Chương {c}. {full_name}"
                    
                    c_item = QTreeWidgetItem(s_item)
                    c_item.setText(0, ch_title)
                    c_item.setText(1, str(stats['total']))
                    c_item.setText(2, str(stats['N'])); c_item.setText(3, str(stats['H']))
                    c_item.setText(4, str(stats['V'])); c_item.setText(5, str(stats['C']))
                    
                    for col in range(1, 6):
                        val = int(c_item.text(col))
                        if val > 0:
                            c_item.setFont(col, font_bold)
                            c_item.setForeground(col, QColor("#ffffff"))
                        else:
                            c_item.setForeground(col, QColor("#7f8c8d"))

                    s_total += stats['total']
                
                s_item.setText(1, str(s_total))
                g_total += s_total
            
            g_item.setText(1, str(g_total))

# =============================================================================
# MODULE TỰ ĐỘNG HÓA (AUTO SCHEDULER)
# =============================================================================
import json
from datetime import datetime, timedelta

class SchedulerManager:
    """Quản lý danh sách các bài tập đã lên lịch"""
    FILE_PATH = "scheduled_tasks.json"

    @staticmethod
    def load_tasks():
        if not os.path.exists(SchedulerManager.FILE_PATH): return []
        try:
            with open(SchedulerManager.FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []

    @staticmethod
    def save_tasks(tasks):
        with open(SchedulerManager.FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    @staticmethod
    def add_schedule(course_id, course_name, grade, subject, chapter, level, num_q, days, time_str):
        tasks = SchedulerManager.load_tasks()
        start_date = datetime.now()
        
        # Tạo danh sách công việc cho N ngày tới
        for i in range(days):
            run_date = start_date + timedelta(days=i)
            # Nếu giờ đặt là tối nay mà đã qua giờ rồi thì chuyển sang ngày mai (tùy chọn, ở đây ta cứ đặt đúng ngày)
            
            task = {
                "id": str(uuid.uuid4()),
                "run_date": run_date.strftime("%Y-%m-%d"),
                "run_time": time_str, # VD: "20:00"
                "course_id": course_id,
                "course_name": course_name,
                "config": {
                    "grade": grade, "subject": subject, "chapter": chapter,
                    "level": level, "num_q": num_q
                },
                "status": "pending", # pending, done, failed
                "log": ""
            }
            tasks.append(task)
        
        SchedulerManager.save_tasks(tasks)
        return len(tasks)

class AutoPostWorker(QThread):
    finished = pyqtSignal(str, str) # task_id, status

    def __init__(self, task, google_mgr): # Bỏ tham số backend truyền vào
        super().__init__()
        self.task = task
        # self.bk = backend  <-- KHÔNG DÙNG BACKEND CHUNG
        self.google = google_mgr

    def run(self):
        # [FIX] Tạo kết nối DB riêng cho luồng auto post
        local_bk = Backend()
        
        try:
            cfg = self.task['config']
            questions = []
            
            # 1. Sinh đề ngẫu nhiên (Dùng local_bk)
            for _ in range(cfg['num_q']):
                # Lấy câu hỏi ngẫu nhiên từ DB
                q = local_bk.get_rnd(
                    cfg['grade'], cfg['subject'], cfg['chapter'], 
                    0, cfg['level'], 0
                )
                if q: questions.append(q)
            
            if not questions:
                # Thử tìm lại với điều kiện lỏng hơn nếu cần
                q_backup = local_bk.get_rnd(cfg['grade'], cfg['subject'], cfg['chapter'], 0, None, 0)
                if q_backup: questions.append(q_backup)
            
            if not questions:
                raise Exception("Không tìm thấy đủ câu hỏi trong ngân hàng dữ liệu!")

            # 2. Tạo nội dung LaTeX
            content_list = []
            
            # Header
            header_text = (
                r"\begin{center}" + "\n"
                r"\textbf{\large BÀI TẬP TỰ LUYỆN - " + f"{self.task['run_date']}}}" + "\n"
                r"\\[0.2cm] \textit{(Hệ thống tự động)}" + "\n"
                r"\end{center}" + "\n"
                r"\setcounter{ex}{0}" + "\n"
            )
            content_list.append(header_text)

            for q in questions:
                # Xóa \True để không lộ đáp án
                clean_q = re.sub(r"\\True", "", q['content_tex'])
                content_list.append(clean_q)
            
            body_content = "\n".join(content_list)
            full_tex = LATEX_TEMPLATE.replace("__CONTENT__", body_content)

            # 3. Biên dịch PDF
            msg, pdf_path = PDFCompiler.compile_tex_to_pdf(full_tex, f"auto_exam_{self.task['id']}")
            
            if not pdf_path or not os.path.exists(pdf_path): 
                raise Exception(f"Lỗi biên dịch PDF: {msg}")

            # 4. Upload & Đăng bài
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
            # [QUAN TRỌNG] Đóng kết nối
            if hasattr(local_bk, 'conn'):
                local_bk.conn.close()

# Hộp thoại Lên lịch
class AutoSchedulerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ Lên lịch Tự động Đăng bài")
        self.setMinimumSize(500, 450)
        
        # [SỬA LỖI TẠI ĐÂY] Thay GoogleClassroomManager bằng GoogleManagerFull
        self.google = GoogleManagerFull() 
        
        self.setup_ui()
        # Auto login Google để lấy danh sách lớp
        QTimer.singleShot(100, self.init_google)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Chọn Lớp
        grp_cls = QGroupBox("1. Chọn Lớp học trên Google Classroom"); l1 = QVBoxLayout(grp_cls)
        self.cb_courses = QComboBox()
        l1.addWidget(self.cb_courses)
        self.lbl_status = QLabel("Đang tải danh sách lớp..."); l1.addWidget(self.lbl_status)
        layout.addWidget(grp_cls)
        
        # 2. Cấu hình kiến thức
        grp_know = QGroupBox("2. Cấu hình Kiến thức"); l2 = QGridLayout(grp_know)
        
        self.cb_grade = QComboBox(); self.cb_grade.addItems(["10", "11", "12"])
        self.cb_subject = QComboBox(); self.cb_subject.addItem("Đại số", 'D'); self.cb_subject.addItem("Hình học", 'H')
        self.cb_chapter = QComboBox() # Sẽ load động
        self.cb_level = QComboBox(); self.cb_level.addItems(["N", "H", "V", "C"])
        self.sp_num = QSpinBox(); self.sp_num.setRange(1, 50); self.sp_num.setValue(10)
        
        l2.addWidget(QLabel("Lớp:"),0,0); l2.addWidget(self.cb_grade,0,1)
        l2.addWidget(QLabel("Môn:"),0,2); l2.addWidget(self.cb_subject,0,3)
        l2.addWidget(QLabel("Chương:"),1,0); l2.addWidget(self.cb_chapter,1,1)
        l2.addWidget(QLabel("Mức độ:"),1,2); l2.addWidget(self.cb_level,1,3)
        l2.addWidget(QLabel("Số câu/đề:"),2,0); l2.addWidget(self.sp_num,2,1)
        
        # Sự kiện load chương
        self.cb_grade.currentIndexChanged.connect(self.load_chapters)
        self.cb_subject.currentIndexChanged.connect(self.load_chapters)
        
        layout.addWidget(grp_know)
        
        # 3. Cấu hình thời gian
        grp_time = QGroupBox("3. Lịch trình chạy"); l3 = QGridLayout(grp_time)
        
        self.time_edit = QTimeEdit(); self.time_edit.setDisplayFormat("HH:mm"); self.time_edit.setTime(QTime(20, 0)) # Mặc định 20h tối
        self.sp_days = QSpinBox(); self.sp_days.setRange(1, 30); self.sp_days.setValue(7)
        
        l3.addWidget(QLabel("Giờ đăng bài mỗi tối:"), 0, 0); l3.addWidget(self.time_edit, 0, 1)
        l3.addWidget(QLabel("Thực hiện trong (ngày):"), 1, 0); l3.addWidget(self.sp_days, 1, 1)
        
        layout.addWidget(grp_time)
        
        # Buttons
        btns = QHBoxLayout()
        b_save = QPushButton("💾 Lên lịch & Kích hoạt")
        b_save.setProperty("class", "btn-primary")
        b_save.clicked.connect(self.save_schedule)
        btns.addStretch(); btns.addWidget(b_save)
        layout.addLayout(btns)
        
        self.load_chapters() # Init

    def init_google(self):
        try:
            self.google.authenticate()
            courses = self.google.get_courses()
            self.cb_courses.clear()
            for c in courses:
                self.cb_courses.addItem(c['name'], c['id'])
            self.lbl_status.setText("✅ Đã kết nối Classroom.")
        except Exception as e:
            self.lbl_status.setText(f"Lỗi: {e}")

    def load_chapters(self):
        self.cb_chapter.clear()
        try:
            g = int(self.cb_grade.currentText())
            s = self.cb_subject.currentData()
            if 'CHAPTER_NAMES' in globals():
                chaps = CHAPTER_NAMES.get(g, {}).get(s, {})
                for k, v in chaps.items():
                    self.cb_chapter.addItem(f"Chương {k}. {v}", k)
            else:
                for i in range(1, 10): self.cb_chapter.addItem(f"Chương {i}", i)
        except: pass

    def save_schedule(self):
        if self.cb_courses.count() == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn lớp học!"); return

        days = self.sp_days.value()
        time_str = self.time_edit.time().toString("HH:mm")
        
        # Lưu vào file json
        SchedulerManager.add_schedule(
            course_id=self.cb_courses.currentData(),
            course_name=self.cb_courses.currentText(),
            grade=int(self.cb_grade.currentText()),
            subject=self.cb_subject.currentData(),
            chapter=self.cb_chapter.currentData(),
            level=self.cb_level.currentText(),
            num_q=self.sp_num.value(),
            days=days,
            time_str=time_str
        )
        
        QMessageBox.information(self, "Thành công", f"Đã lên lịch tự động cho {days} ngày tới!\n\nLƯU Ý: Bạn cần MỞ PHẦN MỀM vào lúc {time_str} hàng ngày để hệ thống tự động đăng bài.")
        self.accept()

# =============================================================================
# HỘP THOẠI HƯỚNG DẪN SỬ DỤNG
# =============================================================================
class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 Hướng dẫn sử dụng BankAI Pro")
        self.setMinimumSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # 1. Danh sách chủ đề (Bên trái)
        self.list_topics = QListWidget()
        self.list_topics.setFixedWidth(250)
        self.list_topics.setStyleSheet("""
            QListWidget { font-size: 14px; background: #fdfdfd; border-right: 1px solid #ddd; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #eee; }
            QListWidget::item:selected { background: #3498db; color: white; font-weight: bold; }
        """)
        self.list_topics.currentRowChanged.connect(self.display_topic)
        layout.addWidget(self.list_topics)
        
        # 2. Nội dung chi tiết (Bên phải)
        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)
        self.content_view.setStyleSheet("padding: 20px; font-size: 15px; line-height: 1.6;")
        layout.addWidget(self.content_view)
        
        # Dữ liệu hướng dẫn
        self.guides = [
            {
                "title": "1. Tổng quan & Kích hoạt",
                "content": """
                <h2>🚀 Tổng quan về BankAI Pro</h2>
                <p>BankAI Pro là phần mềm quản lý ngân hàng câu hỏi Toán THPT (2025) toàn diện, tích hợp AI và Google Classroom.</p>
                <h3>🔑 Kích hoạt bản quyền:</h3>
                <ul>
                    <li>Lần đầu mở app, hộp thoại kích hoạt sẽ xuất hiện.</li>
                    <li>Nhập Email và chọn Gói bản quyền để nhận mã QR.</li>
                    <li>Quét mã QR thanh toán qua ứng dụng ngân hàng.</li>
                    <li>Kiểm tra Email để nhận <b>License Key</b>.</li>
                    <li>Nhập Key vào phần mềm để kích hoạt vĩnh viễn.</li>
                </ul>
                <h3>🔑 Cấu hình API Key:</h3>
                <ul>
                    <li>Để dùng các tính năng AI, bạn cần có <b>Google Gemini API Key</b> (Miễn phí).</li>
                    <li>Phần mềm sẽ yêu cầu nhập Key khi khởi động lần đầu hoặc khi Key cũ hết hạn.</li>
                </ul>
                """
            },
            {
                "title": "2. Nhập dữ liệu (Import)",
                "content": """
                <h2>📥 Nhập câu hỏi từ file LaTeX</h2>
                <p>Hỗ trợ nhập liệu thông minh, tự động nhận diện ID6 và hình ảnh.</p>
                <h3>Các bước thực hiện:</h3>
                <ol>
                    <li>Bấm nút <b>"📥 NHẬP DỮ LIỆU"</b> ở Trang chủ (Dashboard).</li>
                    <li>Chọn một hoặc nhiều file <code>.tex</code> từ máy tính.</li>
                    <li>Hệ thống sẽ tự động quét:
                        <ul>
                            <li><b>Môi trường:</b> <code>ex, bt, vd</code>.</li>
                            <li><b>Hình ảnh:</b> Tự động copy và lưu đường dẫn ảnh.</li>
                            <li><b>ID6:</b> Tự động đọc ID chuẩn 2025 (ví dụ <code>[2D1N1-1]</code>).</li>
                        </ul>
                    </li>
                    <li><b>Xử lý thiếu ID:</b> Nếu câu hỏi chưa có ID, hộp thoại Gán ID sẽ hiện ra để bạn bổ sung ngay lập tức.</li>
                </ol>
                <p><i>Mẹo: Dùng công cụ "Gán ID6 Tự động" trong menu Tiện ích để AI giúp bạn gắn thẻ nhanh hơn.</i></p>
                """
            },
            {
                "title": "3. Soạn đề Thủ công",
                "content": """
                <h2>✏️ Soạn đề & Lọc câu hỏi</h2>
                <p>Tab "Soạn đề (Thủ công)" cho phép bạn chọn lựa từng câu hỏi theo ý muốn.</p>
                <h3>Hướng dẫn:</h3>
                <ul>
                    <li><b>Bộ lọc bên trái:</b> Chọn Lớp, Môn, Chương, Bài, Mức độ để tìm câu hỏi.</li>
                    <li><b>Kéo thả (Drag & Drop):</b> 
                        <ul>
                            <li>Kéo câu hỏi từ danh sách kết quả (bên trái).</li>
                            <li>Thả vào danh sách <b>"ĐỀ ĐANG SOẠN"</b> (bên phải).</li>
                        </ul>
                    </li>
                    <li><b>Menu chuột phải:</b> Tại danh sách bên phải, click chuột phải vào câu hỏi để:
                        <ul>
                            <li><b>🔄 Đổi câu khác:</b> Hệ thống sẽ tìm một câu tương đương (cùng ID6) để thay thế.</li>
                            <li><b>🗑️ Xóa câu này:</b> Loại bỏ câu hỏi khỏi đề.</li>
                        </ul>
                    </li>
                    <li><b>Lưu & Xuất:</b> Bấm <b>"💾 Lưu File TeX"</b> để tải về đề gốc hoặc bấm <b>"☁️ Đăng Classroom"</b> để tạo bài thi online.</li>
                </ul>
                """
            },
            {
                "title": "4. Tạo đề Ma trận (2025)",
                "content": """
                <h2>🎲 Tạo đề theo Ma trận 2025</h2>
                <p>Công cụ mạnh mẽ để tạo đề thi chuẩn cấu trúc Bộ GD&ĐT (3 phần: TN, Đ/S, TLN).</p>
                <h3>Quy trình:</h3>
                <ol>
                    <li>Vào tab <b>"🎲 Tạo đề (Ma trận 2025)"</b>.</li>
                    <li>Bấm nút <b>"🎛️ MỞ BẢNG ĐIỀU KHIỂN MA TRẬN"</b>.</li>
                    <li><b>Cấu hình ma trận:</b>
                        <ul>
                            <li>Chọn Khối lớp và Môn học.</li>
                            <li>Bảng ma trận sẽ hiện ra danh sách các Bài học.</li>
                            <li>Nhập số lượng câu hỏi vào các ô tương ứng (Phần I, II, III).</li>
                        </ul>
                    </li>
                    <li><b>Công cụ hỗ trợ:</b>
                        <ul>
                            <li><b>⚡ Copy dòng 1:</b> Sao chép cấu hình dòng đầu tiên cho tất cả các dòng dưới.</li>
                            <li><b>🧹 Xóa trắng:</b> Reset toàn bộ bảng.</li>
                        </ul>
                    </li>
                    <li>Bấm <b>"⏩ TRÍCH XUẤT ĐỀ THI"</b> để xem trước danh sách câu hỏi.</li>
                    <li>Cuối cùng, bấm <b>"✅ HOÀN TẤT & TẠO ĐỀ"</b> để chuyển dữ liệu sang bộ xử lý.</li>
                </ol>
                """
            },
            {
                "title": "5. Trí tuệ nhân tạo (AI)",
                "content": """
                <h2>🤖 Tạo đề thông minh với AI</h2>
                <p>Sử dụng Gemini AI để sinh ra các câu hỏi tương tự (Clone câu hỏi).</p>
                <h3>Cách dùng:</h3>
                <ol>
                    <li>Vào tab <b>"🤖 Tạo đề (AI)"</b>.</li>
                    <li><b>Load đề gốc:</b> Bấm "1. Load câu hỏi..." để lấy các câu hỏi từ đề đang soạn.</li>
                    <li><b>Cấu hình:</b> Nhập số lượng đề cần tạo (ví dụ: 3 đề tương đương).</li>
                    <li>Bấm <b>"2. CHẠY AI"</b>. Hệ thống sẽ gửi từng câu hỏi lên AI để viết lại (đổi số liệu, ngữ cảnh).</li>
                    <li>Xem kết quả ở cột bên phải. Bạn có thể xuất ra file LaTeX bằng nút <b>"3. 💾 Xuất ra Code LaTeX"</b>.</li>
                </ol>
                """
            },
            {
                "title": "6. Tổ chức Thi Online",
                "content": """
                <h2>🌍 Tổ chức Thi Trực tuyến (Web Server)</h2>
                <p>Biến máy tính của bạn thành máy chủ thi trắc nghiệm (LAN/Internet).</p>
                <h3>Hướng dẫn:</h3>
                <ol>
                    <li>Sau khi có danh sách câu hỏi (từ Soạn thủ công hoặc Ma trận), bấm nút <b>"🌍 Bật Thi Online"</b> ở góc trên bên phải.</li>
                    <li>Cấu hình tên kỳ thi và thời gian làm bài.</li>
                    <li>Màn hình <b>Giám sát (Monitor)</b> sẽ hiện ra cùng với địa chỉ IP/Link thi.</li>
                    <li><b>Học sinh:</b> Truy cập link được cung cấp, nhập tên để vào phòng chờ.</li>
                    <li><b>Giáo viên:</b> Bấm <b>"🚀 GIAO BÀI NGAY"</b> trên màn hình Monitor để bắt đầu tính giờ.</li>
                    <li>Kết quả làm bài sẽ được cập nhật realtime về máy giáo viên.</li>
                </ol>
                """
            },
            {
                "title": "7. Google Classroom",
                "content": """
                <h2>☁️ Tích hợp Google Classroom</h2>
                <p>Đăng bài tập và đề thi trực tiếp lên lớp học Google.</p>
                <h3>Các chế độ:</h3>
                <ul>
                    <li><b>📤 Đăng bài tập (PDF/Form):</b>
                        <ul>
                            <li>Tạo file PDF đề thi và upload lên Drive.</li>
                            <li>Tạo Google Forms (Quiz) tự chấm điểm.</li>
                            <li>Gán bài vào Classroom.</li>
                        </ul>
                    </li>
                    <li><b>🌍 Tổ chức Thi Online (Global):</b>
                        <ul>
                            <li>Tạo một đường link thi online (Web Server).</li>
                            <li>Gửi link này vào Classroom để học sinh truy cập.</li>
                        </ul>
                    </li>
                </ul>
                <p><i>Lưu ý: Bạn cần cấp quyền truy cập Google Drive/Classroom/Forms cho ứng dụng ở lần đầu sử dụng.</i></p>
                """
            },
            {
                "title": "8. Công cụ & Tiện ích",
                "content": """
                <h2>🛠️ Các Công cụ hỗ trợ</h2>
                <p>Nằm trong menu <b>"Tiện ích"</b> trên thanh công cụ:</p>
                <ul>
                    <li><b>🏷️ Gán ID6 Tự động:</b> Sử dụng AI để phân tích nội dung câu hỏi và điền mã ID6 chuẩn (Lớp-Môn-Chương-Bài-Mức độ) cho các câu hỏi thiếu ID trong Database.</li>
                    <li><b>🖼️ Quản lý Kho Hình ảnh:</b> Quét toàn bộ Database để liệt kê các ảnh đang dùng. Hỗ trợ thay thế hàng loạt đường dẫn ảnh (ví dụ: chuyển từ ảnh local sang ảnh online).</li>
                    <li><b>🧹 Làm sạch & Check lỗi:</b> (Đang phát triển) Dò lỗi chính tả và lỗi LaTeX.</li>
                    <li><b>⏰ Lên lịch Tự động:</b> Cài đặt lịch để phần mềm tự động sinh đề và đăng lên Classroom hàng ngày/hàng tuần.</li>
                </ul>
                """
            }
        ]
        
        # Load danh sách chủ đề
        for item in self.guides:
            self.list_topics.addItem(item["title"])
            
        # Chọn mục đầu tiên mặc định
        self.list_topics.setCurrentRow(0)

    def display_topic(self, row):
        if 0 <= row < len(self.guides):
            html = self.guides[row]["content"]
            # Thêm CSS cơ bản
            full_html = f"""
            <html><head><style>
                h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h3 {{ color: #e67e22; margin-top: 20px; }}
                li {{ margin-bottom: 8px; }}
                code {{ background: #f1f1f1; padding: 2px 5px; border-radius: 3px; color: #c0392b; font-family: monospace; }}
            </style></head><body>{html}</body></html>
            """
            self.content_view.setHtml(full_html)

class WatermarkWidget(QWidget):
    """Widget nền có chứa Watermark in chìm"""
    def __init__(self, text="BANKAI PRO", parent=None):
        super().__init__(parent)
        self.text = text
        # Cấu hình để widget này có thể chứa layout con
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Vẽ màu nền chủ đạo (Nâu Coffee)
        # Nếu muốn đổi màu nền, sửa mã màu ở đây
        bg_color = QColor("#602C04") 
        painter.fillRect(self.rect(), bg_color)

        # 2. Cấu hình Watermark
        painter.setOpacity(0.05) # Độ mờ cực thấp (5%) để không rối mắt
        
        # Thiết lập Font chữ to, đậm
        font_size = min(self.width(), self.height()) // 10 # Tự động chỉnh cỡ chữ theo màn hình
        font = QFont(".AppleSystemUIFont", font_size, QFont.Weight.Black)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff")) # Chữ màu trắng (khi mờ đi sẽ hòa vào nền nâu)

        # 3. Tính toán vị trí tâm để xoay
        cx = self.width() / 2
        cy = self.height() / 2

        painter.translate(cx, cy)
        painter.rotate(-30) # Xoay chéo 30 độ

        # 4. Vẽ chữ (Căn giữa)
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self.text)
        text_h = fm.height()
        
        # Vẽ dòng chính
        painter.drawText(int(-text_w/2), int(text_h/4), self.text)
        
        # (Tùy chọn) Vẽ thêm viền bao quanh text cho đẹp
        pen = QPen(QColor("#ffffff"), 5)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        # painter.drawRect(int(-text_w/2 - 50), int(-text_h + 50), int(text_w + 100), int(text_h))

class AdvancedExportDialog(QDialog):
    """Dialog xuất đề nâng cao: Cho phép dùng Main cá nhân và Tùy biến"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚀 Xuất đề & Biên dịch Tùy chỉnh")
        self.setMinimumSize(700, 500)
        self.template_path = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Chọn Template
        grp_temp = QGroupBox("1. Cấu trúc file Main (Template)"); ly_temp = QVBoxLayout(grp_temp)
        
        hbox = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Mặc định (Dùng template chuẩn của phần mềm)...")
        self.txt_path.setReadOnly(True)
        
        btn_browse = QPushButton("📂 Chọn Main cá nhân (.tex)")
        btn_browse.clicked.connect(self.browse_template)
        
        btn_reset = QPushButton("Mặc định")
        btn_reset.clicked.connect(lambda: (self.txt_path.clear(), setattr(self, 'template_path', '')))
        
        hbox.addWidget(self.txt_path); hbox.addWidget(btn_browse); hbox.addWidget(btn_reset)
        ly_temp.addLayout(hbox)
        
        lbl_note = QLabel("<i>Lưu ý: File main.tex cá nhân cần có dòng chữ <b>__CONTENT__</b> để phần mềm chèn câu hỏi vào đó.</i>")
        lbl_note.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        ly_temp.addWidget(lbl_note)
        layout.addWidget(grp_temp)
        
        # 2. Tùy chọn nội dung
        grp_opt = QGroupBox("2. Tùy chọn nội dung"); ly_opt = QGridLayout(grp_opt)
        
        self.chk_sol = QCheckBox("Xuất kèm Lời giải chi tiết")
        self.chk_shuffle = QCheckBox("Đảo hoán vị đáp án (A/B/C/D)")
        self.chk_key_table = QCheckBox("Tạo bảng đáp án ở cuối")
        
        self.chk_shuffle.setChecked(True)
        self.chk_key_table.setChecked(True)
        
        ly_opt.addWidget(self.chk_sol, 0, 0)
        ly_opt.addWidget(self.chk_shuffle, 0, 1)
        ly_opt.addWidget(self.chk_key_table, 1, 0)
        
        layout.addWidget(grp_opt)
        
        # 3. Hành động
        grp_act = QGroupBox("3. Xuất ra"); ly_act = QHBoxLayout(grp_act)
        
        self.rb_tex = QRadioButton("Chỉ xuất file .tex"); self.rb_tex.setChecked(True)
        self.rb_pdf = QRadioButton("Xuất .tex và biên dịch PDF ngay")
        
        ly_act.addWidget(self.rb_tex)
        ly_act.addWidget(self.rb_pdf)
        layout.addWidget(grp_act)
        
        # Footer Buttons
        btns = QHBoxLayout()
        b_ok = QPushButton("🚀 THỰC HIỆN")
        b_ok.setMinimumHeight(45)
        b_ok.setProperty("class", "btn-primary")
        b_ok.clicked.connect(self.accept)
        
        b_cancel = QPushButton("Hủy")
        b_cancel.setMinimumHeight(45)
        b_cancel.clicked.connect(self.reject)
        
        btns.addStretch(); btns.addWidget(b_ok); btns.addWidget(b_cancel)
        layout.addLayout(btns)

    def browse_template(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn file Main mẫu", "", "TeX Files (*.tex)")
        if f:
            self.template_path = f
            self.txt_path.setText(os.path.basename(f))

    def get_config(self):
        return {
            "template": self.template_path,
            "show_sol": self.chk_sol.isChecked(),
            "shuffle": self.chk_shuffle.isChecked(),
            "table": self.chk_key_table.isChecked(),
            "compile": self.rb_pdf.isChecked()
        }

class ExamConfigDialog(QDialog):
    """Hộp thoại Cấu hình & Soát Đáp Án (Đã Fix lỗi Decimal {,})"""
    def __init__(self, questions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cấu hình & Soát Đáp Án (Preview)")
        self.resize(1100, 650)
        self.questions = questions 
        self.final_questions = []
        self.tex_path = ""
        
        layout = QVBoxLayout(self)

        # --- PHẦN 1: THÔNG TIN ---
        grp_info = QGroupBox("Thông tin kỳ thi"); gl = QGridLayout(grp_info)
        gl.addWidget(QLabel("Tên kỳ thi:"), 0, 0)
        self.inp_title = QLineEdit("ĐỀ THI THỬ TRỰC TUYẾN")
        gl.addWidget(self.inp_title, 0, 1)
        gl.addWidget(QLabel("Thời gian (phút):"), 0, 2)
        self.inp_time = QSpinBox(); self.inp_time.setRange(5, 300); self.inp_time.setValue(90)
        gl.addWidget(self.inp_time, 0, 3)
        
        # [MỚI] Số lượng mã đề (GIỮ NGUYÊN DÒNG 1)
        gl.addWidget(QLabel("Số mã đề (trộn):"), 1, 0)
        self.inp_variants = QSpinBox(); self.inp_variants.setRange(1, 20); self.inp_variants.setValue(1)
        gl.addWidget(self.inp_variants, 1, 1)

        # [NEW] Chọn file TeX (SỬA THÀNH DÒNG 2)
        gl.addWidget(QLabel("File TeX riêng (nếu có):"), 2, 0) # <--- Sửa số 1 thành 2
        self.txt_tex_path = QLineEdit()
        self.txt_tex_path.setPlaceholderText("Chọn file .tex để biên dịch PDF thay vì tạo tự động...")
        self.txt_tex_path.setReadOnly(True)
        gl.addWidget(self.txt_tex_path, 2, 1, 1, 2)    # <--- Sửa số 1 thành 2
        
        btn_browse = QPushButton("Chọn File")
        btn_browse.clicked.connect(self.browse_tex)
        gl.addWidget(btn_browse, 2, 3)                 # <--- Sửa số 1 thành 2

        layout.addWidget(grp_info)

        # --- PHẦN 2: BẢNG SOÁT ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["STT", "Nội dung", "Dạng", "ĐÁP ÁN (Sửa tại đây)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(3, 180)
        layout.addWidget(self.table)

        self.load_data() 

        # --- BUTTONS ---
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept_data)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def load_data(self):
        self.table.setRowCount(len(self.questions))
        for idx, q in enumerate(self.questions):
            tex = q.get('content_tex', q.get('content', ''))
            dang = q.get('dang', 4)
            
            # 1. Auto-detect Dạng
            if dang == 4:
                if r"\choiceTF" in tex: dang = 2
                elif r"\choice" in tex: dang = 1
                elif r"\shortans" in tex: dang = 3

            # 2. Auto-detect Key
            detected_key = q.get('key')
            # Nếu chưa có key hoặc key rỗng, thử quét lại từ TeX
            if not detected_key or detected_key == '?':
                detected_key = self.extract_key_robust(tex, dang)

            # 3. FORMAT HIỂN THỊ
            display_key = str(detected_key)
            
            if dang == 2: # Đ/S
                if isinstance(detected_key, dict):
                    vals = [detected_key.get(k, '?') for k in ['a','b','c','d']]
                    display_key = "".join(vals) # VD: "ĐSĐS"
                elif isinstance(detected_key, str):
                    display_key = detected_key 

            # Render lên bảng
            self.table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.table.setItem(idx, 1, QTableWidgetItem(tex[:80].replace("\n", " ") + "..."))
            
            type_lbl = {1:"Trắc nghiệm", 2:"Đúng/Sai", 3:"Điền khuyết", 4:"Tự luận"}.get(dang, "Khác")
            self.table.setItem(idx, 2, QTableWidgetItem(type_lbl))
            
            item_key = QTableWidgetItem(display_key)
            item_key.setBackground(QColor("#e6fffa"))
            item_key.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(idx, 3, item_key)
            
            self.table.item(idx, 0).setData(Qt.ItemDataRole.UserRole, {"full_q": q, "dang": dang})

    def extract_key_robust(self, tex, dang):
        """Hàm trích xuất key cải tiến (Xử lý {,} thành ,)"""
        try:
            tex = tex.replace("\n", " ").strip()
            
            # --- DẠNG 1: TRẮC NGHIỆM ---
            if dang == 1:
                # Cách 1: Quét \choice thủ công để xử lý ngoặc lồng nhau
                idx = tex.find(r"\choice")
                if idx != -1:
                    content = tex[idx+len(r"\choice"):]
                    braces = 0; current_block = 0; block_content = ""
                    for char in content:
                        if char == '{':
                            if braces == 0: block_content = ""
                            braces += 1
                        elif char == '}':
                            braces -= 1
                            if braces == 0: # Kết thúc 1 phương án
                                if r"\True" in block_content: 
                                    return ['A', 'B', 'C', 'D'][current_block]
                                current_block += 1
                                if current_block > 3: break
                        else:
                            if braces > 0: block_content += char
                
                # Cách 2: Tìm comment [KEY: A]
                m = re.search(r"\[KEY:\s*([A-D])\]", tex, re.IGNORECASE)
                if m: return m.group(1).upper()
                return "?"

            # --- DẠNG 2: ĐÚNG SAI ---
            elif dang == 2:
                idx = tex.find(r"\choiceTF")
                if idx == -1: return {'a':'?', 'b':'?', 'c':'?', 'd':'?'}
                content = tex[idx+len(r"\choiceTF"):]
                braces = 0; current_block = 0; block_content = ""
                tf_res = {}; labels = ['a', 'b', 'c', 'd']
                for char in content:
                    if char == '{':
                        if braces == 0: block_content = ""
                        braces += 1
                    elif char == '}':
                        braces -= 1
                        if braces == 0:
                            val = 'Đ' if r"\True" in block_content else 'S'
                            if current_block < 4: tf_res[labels[current_block]] = val
                            current_block += 1
                    else:
                        if braces > 0: block_content += char
                return tf_res

            # --- DẠNG 3: TRẢ LỜI NGẮN (FIX LỖI TẠI ĐÂY) ---
            elif dang == 3:
                # Dùng parser ngoặc để lấy chính xác nội dung bên trong \shortans{...}
                idx = tex.find(r"\shortans")
                if idx != -1:
                    open_brace = tex.find("{", idx)
                    if open_brace != -1:
                        content = ""; balance = 1
                        for i in range(open_brace + 1, len(tex)):
                            if tex[i] == "{": balance += 1
                            elif tex[i] == "}": balance -= 1
                            if balance == 0: break
                            content += tex[i]
                        
                        # Xử lý nội dung lấy được
                        ans = content.strip()
                        ans = ans.replace("$", "") # Bỏ dấu toán học
                        ans = ans.replace("{,}", ",") # [FIX THEO YÊU CẦU] 0{,}5 -> 0,5
                        return ans
                return "?"
                
        except: pass
        return "?"

    def accept_data(self):
        """Xử lý khi bấm OK"""
        self.final_questions = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            data = item.data(Qt.ItemDataRole.UserRole)
            q = data['full_q']
            dang = data['dang']
            
            user_key_str = self.table.item(row, 3).text().strip()
            final_key = user_key_str
            
            # Convert ngược Đ/S từ chuỗi "ĐSĐS" -> Dict
            if dang == 2:
                user_key_str = user_key_str.upper()
                while len(user_key_str) < 4: user_key_str += "?"
                final_key = {
                    'a': user_key_str[0], 'b': user_key_str[1],
                    'c': user_key_str[2], 'd': user_key_str[3]
                }

            q['key'] = final_key 
            q['dang'] = dang
            self.final_questions.append(q)
            
        self.accept()

    def browse_tex(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn file TeX", "", "TeX Files (*.tex)")
        if f:
            self.tex_path = f
            self.txt_tex_path.setText(f)

    def get_config(self):
        return {
            "title": self.inp_title.text(),
            "time": self.inp_time.value(),
            "questions": self.final_questions,
            "external_tex": self.tex_path,
            "num_variants": self.inp_variants.value()
        }

class HistoryDialog(QDialog):
    """Hộp thoại xem Lịch sử kết quả thi"""
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.bk = backend
        self.setWindowTitle("📜 Lịch sử kết quả thi")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("<h2>DANH SÁCH BÀI THI ĐÃ NỘP</h2>"))
        h_layout.addStretch()
        
        btn_refresh = QPushButton("🔄 Làm mới")
        btn_refresh.clicked.connect(self.load_data)
        h_layout.addWidget(btn_refresh)
        
        btn_export = QPushButton("💾 Xuất Excel/CSV")
        btn_export.clicked.connect(self.export_csv)
        h_layout.addWidget(btn_export)
        
        layout.addLayout(h_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Thời gian", "Học sinh", "Đề thi", "Điểm số"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        layout.addWidget(QLabel("<i>* Click vào tiêu đề cột để sắp xếp</i>"))

    def load_data(self):
        try:
            results = self.bk.get_exam_results()
            self.table.setRowCount(0)
            
            for row_idx, row_data in enumerate(results):
                self.table.insertRow(row_idx)
                # row_data is a Row object, access by index or key
                # Schema: id, student_name, exam_title, score, detail, submitted_at
                
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data['id'])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data['submitted_at'])))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data['student_name'])))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row_data['exam_title'])))
                
                score_item = QTableWidgetItem(str(row_data['score']))
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                score_item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                
                try:
                    s = float(row_data['score'])
                    if s >= 8.0: score_item.setForeground(QColor("green"))
                    elif s < 5.0: score_item.setForeground(QColor("red"))
                    else: score_item.setForeground(QColor("blue"))
                except: pass
                
                self.table.setItem(row_idx, 4, score_item)
                
        except Exception as e:
            QMessageBox.warning(self, "Lỗi tải dữ liệu", str(e))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Xuất file CSV", "Lich_Su_Thi.csv", "CSV Files (*.csv)")
        if not path: return
        
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Thời gian", "Học sinh", "Đề thi", "Điểm số"])
                
                for r in range(self.table.rowCount()):
                    row_data = []
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Thành công", f"Đã xuất file: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất file", str(e))
class ExamMonitorDialog(QDialog):
    """Màn hình GIÁM SÁT & GIAO BÀI"""
    def __init__(self, web_thread, parent=None):
        super().__init__(parent)
        self.web_thread = web_thread
        self.setWindowTitle(f"Phòng Thi Ảo - Đang giám sát...")
        self.resize(1000, 600)
        
        layout = QVBoxLayout(self)

        # 1. HEADER: HƯỚNG DẪN KẾT NỐI
        # Hiển thị to rõ để giáo viên chiếu lên bảng hoặc đọc cho học sinh
        top_frame = QFrame(); top_frame.setStyleSheet("background-color: #e8f5e9; border-radius: 8px; padding: 10px;")
        hl = QHBoxLayout(top_frame)
        
        lbl_instruct = QLabel("HỌC SINH TRUY CẬP WIFI VÀ VÀO ĐỊA CHỈ:")
        lbl_instruct.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        url = f"http://{web_thread.ip_address}:{web_thread.port}"
        lbl_url = QLabel(url)
        lbl_url.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        lbl_url.setStyleSheet("color: #d35400;") # Màu cam nổi bật
        lbl_url.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        hl.addWidget(lbl_instruct)
        hl.addWidget(lbl_url)
        layout.addWidget(top_frame)

        # 2. BẢNG DANH SÁCH MÁY KẾT NỐI
        self.lbl_count = QLabel("Hiện có: 0 máy đang kết nối")
        layout.addWidget(self.lbl_count)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Chọn", "Tên Học Sinh", "ĐIỂM SỐ", "Trạng Thái", "ID Máy"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # 3. THANH CÔNG CỤ DƯỚI
        btn_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("Chọn tất cả")
        self.btn_select_all.clicked.connect(self.select_all)
        
        self.btn_distribute = QPushButton("🚀 GIAO BÀI NGAY")
        self.btn_distribute.setMinimumHeight(50)
        self.btn_distribute.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_distribute.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 5px;")
        self.btn_distribute.clicked.connect(self.distribute_action)

        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_distribute)
        layout.addLayout(btn_layout)

        # KẾT NỐI SIGNAL: Cập nhật bảng ngay khi có HS vào/ra
        self.web_thread.students_changed.connect(self.update_table)

    def update_table(self, students):
        """Vẽ lại bảng, giữ nguyên điểm số nếu đã có"""
        # Lưu lại điểm số hiện tại trên bảng để không bị mất khi redraw
        current_scores = {}
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 1).text()
            score_item = self.table.item(r, 2)
            if score_item and score_item.text():
                current_scores[name] = score_item.text()

        self.table.setRowCount(0)
        for row, s in enumerate(students):
            self.table.insertRow(row)
            # Cột 0: Checkbox
            chk_w = QWidget(); chk = QCheckBox(); chk.setChecked(True); 
            l = QHBoxLayout(chk_w); l.addWidget(chk); l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setContentsMargins(0,0,0,0)
            self.table.setCellWidget(row, 0, chk_w)
            
            # Cột 1: Tên
            self.table.setItem(row, 1, QTableWidgetItem(s['name']))
            
            # Cột 2: Điểm (Load lại nếu có)
            score_val = current_scores.get(s['name'], "")
            item_score = QTableWidgetItem(str(score_val))
            item_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_score.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            item_score.setForeground(QColor("red"))
            self.table.setItem(row, 2, item_score)

            # Cột 3: Trạng thái
            stt = "Đang làm bài" if s['status'] == 'doing' else "Chờ đề"
            if score_val: stt = "Đã nộp bài" # Nếu có điểm thì là đã nộp
            self.table.setItem(row, 3, QTableWidgetItem(stt))
            
            # Cột 4: ID
            self.table.setItem(row, 4, QTableWidgetItem(s['id'][:6]))

    def update_score(self, name, score):
        """Hàm cập nhật điểm trực tiếp khi nhận signal"""
        found = False
        for r in range(self.table.rowCount()):
            if self.table.item(r, 1).text() == name:
                self.table.setItem(r, 2, QTableWidgetItem(str(score)))
                self.table.setItem(r, 3, QTableWidgetItem("✅ Đã nộp"))
                found = True
                break
        
        if not found:
            # Nếu học sinh nộp bài mà chưa có trong danh sách (hiếm gặp), thêm mới
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(score)))
            self.table.setItem(row, 3, QTableWidgetItem("✅ Đã nộp"))

    def select_all(self):
        # Logic chọn tất cả checkbox
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            chk = w.findChild(QCheckBox)
            chk.setChecked(True)

    def distribute_action(self):
        """Gửi lệnh phát đề cho các máy được chọn"""
        targets = []
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            chk = w.findChild(QCheckBox)
            if chk.isChecked():
                # Lấy ID từ data ẩn
                uid = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
                targets.append(uid)
        
        if not targets:
            QMessageBox.warning(self, "Chưa chọn máy", "Vui lòng chọn ít nhất một học sinh để giao bài!")
            return

        # GỌI SERVER PHÁT ĐỀ
        self.web_thread.distribute_exam(targets)
        QMessageBox.information(self, "Thành công", f"Đã giao bài cho {len(targets)} học sinh!")

class MatrixEditorDialog(QDialog):
    """Cửa sổ soạn ma trận chuyên nghiệp & Review đề (Có Splitter & Hỗ trợ Tổng hợp 3 khối)"""
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.bk = backend
        self.setWindowTitle("🎛️ BỘ ĐIỀU KHIỂN MA TRẬN & TRÍCH XUẤT ĐỀ (TỔNG HỢP)")
        self.setWindowState(Qt.WindowState.WindowMaximized) 
        self.setStyleSheet("""
            QDialog { background-color: #fdfdfd; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; padding: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #2c3e50; }
            QTableWidget { background-color: white; gridline-color: #eee; border: 1px solid #ddd; }
            QListWidget { background-color: #fafafa; border: 1px solid #ddd; font-size: 13px; }
            QTextEdit { background-color: #fff; border: 1px solid #ccc; font-family: Consolas; }
            QSplitter::handle { background-color: #ddd; width: 5px; } 
        """)
        
        self.final_questions = [] 
        self.setup_ui()
        self.upd_mat() 

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === CỘT TRÁI: CẤU HÌNH ===
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Bộ lọc phạm vi
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
        
        # 2. Bảng nhập liệu
        self.mat_tb = QTableWidget()
        self.mat_tb.setColumnCount(10)
        self.mat_tb.setHorizontalHeaderLabels(["Nội dung", "I.NB", "I.TH", "I.VD", "II.NB", "II.TH", "II.VD", "III.NB", "III.TH", "III.VD"])
        
        # [FIX] Cấu hình cột: Cột 0 giãn, Cột 1-9 cố định kích thước (45px)
        header = self.mat_tb.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 10):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.mat_tb.setColumnWidth(i, 45)
            
        self.mat_tb.verticalHeader().setVisible(False)
        left_layout.addWidget(self.mat_tb)
        
        # 3. Thanh công cụ
        tool_frame = QFrame(); tool_layout = QVBoxLayout(tool_frame)
        tool_layout.setContentsMargins(0, 5, 0, 5)
        
        btn_row = QHBoxLayout()
        b_fill = QPushButton("⚡ Copy dòng 1"); b_fill.clicked.connect(self.quick_fill)
        b_reset = QPushButton("🧹 Xóa trắng"); b_reset.clicked.connect(self.reset_values)
        btn_row.addWidget(b_fill); btn_row.addWidget(b_reset); btn_row.addStretch()
        tool_layout.addLayout(btn_row)
        
        self.lbl_sum = QLabel("Tổng: 0 câu")
        self.lbl_sum.setStyleSheet("background: #ecf0f1; padding: 8px; border-radius: 4px; border: 1px solid #bdc3c7;")
        self.lbl_sum.setTextFormat(Qt.TextFormat.RichText)
        tool_layout.addWidget(self.lbl_sum)
        
        left_layout.addWidget(tool_frame)
        
        self.btn_extract = QPushButton("⏩ TRÍCH XUẤT ĐỀ THI >>")
        self.btn_extract.setMinimumHeight(50)
        self.btn_extract.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; font-size: 14px; border-radius: 5px;")
        self.btn_extract.clicked.connect(self.extract_exam)
        left_layout.addWidget(self.btn_extract)
        
        # === CỘT PHẢI: KẾT QUẢ ===
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        gb_res = QGroupBox("2. DANH SÁCH CÂU HỎI ĐÃ CHỌN"); gb_res_layout = QVBoxLayout(gb_res)
        
        self.res_list = QListWidget()
        self.res_list.setAlternatingRowColors(True)
        self.res_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.res_list.customContextMenuRequested.connect(self.open_context_menu)
        self.res_list.itemClicked.connect(self.preview_item)
        gb_res_layout.addWidget(self.res_list)
        
        gb_res_layout.addWidget(QLabel("<b>Xem trước Code LaTeX:</b>"))
        self.preview_txt = QTextEdit()
        self.preview_txt.setFixedHeight(150) # Fix height as requested
        self.preview_txt.setReadOnly(True)
        gb_res_layout.addWidget(self.preview_txt)
        
        right_layout.addWidget(gb_res)
        
        footer = QHBoxLayout()
        self.lbl_status = QLabel("Chưa có câu hỏi.")
        b_finish = QPushButton("✅ HOÀN TẤT & TẠO ĐỀ")
        b_finish.setMinimumHeight(50)
        b_finish.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 16px; border-radius: 5px;")
        b_finish.clicked.connect(self.accept_exam)
        
        footer.addWidget(self.lbl_status); footer.addStretch(); footer.addWidget(b_finish)
        right_layout.addLayout(footer)
        
        splitter.addWidget(left_panel); splitter.addWidget(right_panel)
        
        # Adjust Splitter Sizes (Left larger)
        splitter.setStretchFactor(0, 2) 
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)

    def _get_display_label(self, q, idx):
        """Helper visual formatting for question list item"""
        subj_map = {'D': 'Đại', 'H': 'Hình'}
        dang_map = {1: 'TN', 2: 'Đ/S', 3: 'TLN', 4: 'TL'}
        
        g = q.get('grade', '?')
        s_code = q.get('subject', '')
        s = subj_map.get(s_code, s_code)
        
        ch = q.get('chapter', '?')
        bai = q.get('bai', '?')
        lev = q.get('level', '?')
        d_code = q.get('dang', 4)
        d_str = dang_map.get(d_code, 'TL')
        
        content = q.get('content_tex', '')
        # Truncate content nicely
        content_clean = content.replace("\n", " ").strip()
        if len(content_clean) > 80:
            content_clean = content_clean[:80] + "..."
            
        return f"Câu {idx}: [{g}-{s}] [C{ch}.B{bai}] [{lev}] [{d_str}] - {content_clean}"

    # --- LOGIC MA TRẬN (ĐÃ FIX LỖI TÊN HÀM) ---
    def upd_mat(self):
        # 1. Xác định Lớp & Môn
        target_grades = []
        g_txt = self.mat_g.currentText()
        if "Tổng hợp" in g_txt: target_grades = [12, 11, 10]
        else:
            try: target_grades = [int(g_txt.split()[-1])]
            except: target_grades = [12]

        target_subjs = []
        s_txt = self.mat_s.currentText()
        if "Tất cả" in s_txt: target_subjs = ['D', 'H']
        else: target_subjs = ['D'] if 'Đại' in s_txt else ['H']

        self.mat_tb.setRowCount(0)
        self.mat_chap_filter.blockSignals(True)
        self.mat_chap_filter.clear(); self.mat_chap_filter.addItem("Hiển thị tất cả", 0)
        
        row_idx = 0
        for g in target_grades:
            for s in target_subjs:
                if g not in DATA_ID6_2025 or s not in DATA_ID6_2025[g]: continue
                
                # Header phân cách
                self.mat_tb.insertRow(row_idx)
                h_item = QTableWidgetItem(f"--- LỚP {g} - {'ĐẠI SỐ' if s=='D' else 'HÌNH HỌC'} ---")
                h_item.setBackground(QColor("#d35400")); h_item.setForeground(QColor("white"))
                h_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.mat_tb.setItem(row_idx, 0, h_item); self.mat_tb.setSpan(row_idx, 0, 1, 10)
                row_idx += 1
                
                chapters = DATA_ID6_2025[g][s]
                for ch_code, lessons in chapters.items():
                    filter_val = f"{g}_{s}_{ch_code}"
                    self.mat_chap_filter.addItem(f"[{g}{s}] Chương {ch_code}", filter_val)
                    
                    for bai_code, bai_name in lessons.items():
                        self.mat_tb.insertRow(row_idx)
                        item_name = QTableWidgetItem(f"C{ch_code}.B{bai_code}: {bai_name}")
                        # Lưu Metadata để trích xuất sau này
                        item_name.setData(Qt.ItemDataRole.UserRole, {'g':g, 's':s, 'ch':ch_code, 'bai':bai_code})
                        item_name.setToolTip(bai_name)
                        self.mat_tb.setItem(row_idx, 0, item_name)
                        
                        for c in range(1, 10):
                            sb = QSpinBox(); sb.setRange(0, 50); sb.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
                            sb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            # [FIX] Gọi đúng hàm calc_sum (không phải calc_mat_sum)
                            sb.valueChanged.connect(self.calc_sum)
                            if 1<=c<=3: sb.setStyleSheet("background:#e3f2fd; color:#1565c0;")
                            elif 4<=c<=6: sb.setStyleSheet("background:#fff3e0; color:#e65100;")
                            else: sb.setStyleSheet("background:#f3e5f5; color:#7b1fa2;")
                            self.mat_tb.setCellWidget(row_idx, c, sb)
                        row_idx += 1
        self.mat_chap_filter.blockSignals(False)
        self.calc_sum()

    def filter_mat_table(self):
        val = self.mat_chap_filter.currentData()
        for r in range(self.mat_tb.rowCount()):
            item = self.mat_tb.item(r, 0)
            if not item: self.mat_tb.setRowHidden(r, False); continue # Header luôn hiện
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data: continue # Dòng lỗi hoặc header
            row_key = f"{data['g']}_{data['s']}_{data['ch']}"
            self.mat_tb.setRowHidden(r, (val != 0 and row_key != val))

    def calc_sum(self):
        """Tính tổng số câu (Bỏ qua các dòng tiêu đề)"""
        s1 = s2 = s3 = 0
        for r in range(self.mat_tb.rowCount()):
            # Chỉ tính nếu dòng có SpinBox (không phải header)
            if self.mat_tb.cellWidget(r, 1): 
                s1 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(1, 4))
                s2 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(4, 7))
                s3 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(7, 10))
        
        total = s1 + s2 + s3
        stats_html = (
            f"<span style='font-size:16px; font-weight:bold'>TỔNG: <span style='color:red'>{total}</span> câu</span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<span style='color:#2980b9'>Phần I (TN): <b>{s1}</b></span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<span style='color:#e67e22'>Phần II (Đ/S): <b>{s2}</b></span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<span style='color:#8e44ad'>Phần III (TLN): <b>{s3}</b></span>"
        )
        self.lbl_sum.setText(stats_html)

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
        self.res_list.clear()
        self.final_questions = []
        col_map = {
            1:(1,'N'), 2:(1,'H'), 3:(1,'V'), 4:(2,'N'), 5:(2,'H'), 6:(2,'V'), 7:(3,'N'), 8:(3,'H'), 9:(3,'V')
        }
        missing = []
        
        for r in range(self.mat_tb.rowCount()):
            item = self.mat_tb.item(r, 0)
            if not item: continue
            d = item.data(Qt.ItemDataRole.UserRole)
            if not d: continue # Bỏ qua header
            
            for c in range(1, 10):
                cnt = self.mat_tb.cellWidget(r, c).value()
                if cnt > 0:
                    dang, lev = col_map[c]
                    for _ in range(cnt):
                        q = self.bk.get_rnd(d['g'], d['s'], d['ch'], d['bai'], lev, dang)
                        if q: self.add_q_to_list(q)
                        else: missing.append(f"[{d['g']}{d['s']}-C{d['ch']}.B{d['bai']}-{lev}] Dạng {dang}")

        self.lbl_status.setText(f"Đã lấy {self.res_list.count()} câu. (Thiếu {len(missing)} câu)")
        if missing:
            QMessageBox.warning(self, "Thiếu dữ liệu", f"Không tìm thấy {len(missing)} câu hỏi!\n(Xem chi tiết trong Console hoặc Log)")

    def add_q_to_list(self, q):
        self.final_questions.append(q)
        idx = self.res_list.count() + 1
        
        # Use helper for display text
        txt = self._get_display_label(q, idx)
        
        item = QListWidgetItem(txt)
        item.setData(Qt.ItemDataRole.UserRole, q)
        
        color = {1:"#27ae60", 2:"#2980b9", 3:"#e67e22"}.get(q.get('dang'), "#95a5a6")
        item.setForeground(QColor(color))
        font = QFont(); font.setBold(True); item.setFont(font)
        self.res_list.addItem(item)

    def preview_item(self, item):
        q = item.data(Qt.ItemDataRole.UserRole)
        self.preview_txt.setText(q['content_tex'])

    def open_context_menu(self, pos):
        item = self.res_list.itemAt(pos)
        if not item: return
        menu = QMenu()
        act_swap = menu.addAction("🔄 Đổi câu khác tương đương")
        action = menu.exec(self.res_list.viewport().mapToGlobal(pos))
        if action == act_swap: self.swap_question(item)

    def swap_question(self, item):
        old_q = item.data(Qt.ItemDataRole.UserRole)
        new_q = self.bk.get_rnd(
            old_q['grade'], old_q['subject'], old_q['chapter'], 
            old_q['bai'], old_q['level'], old_q['dang'], exc=old_q['id']
        )
        if new_q:
            item.setData(Qt.ItemDataRole.UserRole, new_q)
            idx = self.res_list.row(item)
            
            # Use helper to update text
            new_txt = self._get_display_label(new_q, idx + 1)
            item.setText(new_txt)
            
            self.preview_txt.setText(new_q['content_tex'])
            self.final_questions[idx] = new_q
            QMessageBox.information(self, "Xong", f"Đã đổi sang câu ID: {new_q['id']}")
        else:
            QMessageBox.warning(self, "Hết câu", "Không còn câu hỏi khác tương đương!")

    def accept_exam(self):
        if not self.final_questions:
            QMessageBox.warning(self, "Trống", "Chưa có câu hỏi nào được chọn!")
            return
        self.accept()

# --- CHÈN TRƯỚC CLASS MAINAPP ---
class GoogleClassroomManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Xác thực với Google và lấy token"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # Yêu cầu file credentials.json phải nằm cùng thư mục
                if not os.path.exists('credentials.json'):
                    print("Thiếu file credentials.json!")
                    return
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('classroom', 'v1', credentials=self.creds)

    def get_courses(self):
        """Lấy danh sách các lớp học đang hoạt động"""
        if not self.service: return []
        results = self.service.courses().list(courseStates=['ACTIVE']).execute()
        return results.get('courses', [])

    def get_students(self, course_id):
        """Lấy danh sách học sinh của một lớp: Tên, Email, ID"""
        students_list = []
        page_token = None
        while True:
            response = self.service.courses().students().list(
                courseId=course_id, pageToken=page_token).execute()
            students = response.get('students', [])
            for s in students:
                profile = s.get('profile', {})
                students_list.append({
                    'id': s.get('userId'),
                    'name': profile.get('name', {}).get('fullName'),
                    'email': profile.get('emailAddress')
                })
            page_token = response.get('nextPageToken', None)
            if not page_token: break
        return students_list

    def get_assignments(self, course_id):
        """Lấy danh sách bài tập của lớp"""
        results = self.service.courses().courseWork().list(
            courseId=course_id, orderBy="updateTime desc").execute()
        return results.get('courseWork', [])

    def push_grade(self, course_id, coursework_id, student_email, score):
        """Đẩy điểm số lên Classroom"""
        # 1. Tìm submission ID của học sinh
        subs = self.service.courses().courseWork().studentSubmissions().list(
            courseId=course_id, courseWorkId=coursework_id, userId='all').execute()
        
        target_sub = None
        for sub in subs.get('studentSubmissions', []):
            # API trả về userId, ta cần so khớp ID này với email (logic so khớp cần mapping)
            # Để đơn giản, ở đây ta giả định đã map được hoặc lấy user profile
            # Cách an toàn nhất: Lấy user profile của submission
            user_profile = self.service.userProfiles().get(userId=sub['userId']).execute()
            if user_profile.get('emailAddress') == student_email:
                target_sub = sub
                break
        
        if target_sub:
            body = {
                'assignedGrade': score,
                'draftGrade': score
            }
            self.service.courses().courseWork().studentSubmissions().patch(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=target_sub['id'],
                updateMask='assignedGrade,draftGrade',
                body=body
            ).execute()
            return True
        return False
# -----------------------------------------------------

    # --- [BƯỚC 1: HÀM KHỞI TẠO BẢNG KẾT QUẢ] ---
def create_results_table(db_path):
    """Tạo bảng lưu kết quả thi nếu chưa có"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                student_email TEXT,
                exam_id TEXT,
                score REAL,
                detail_json TEXT,
                ai_feedback TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Đã kiểm tra/tạo bảng exam_results.")
    except Exception as e:
        print(f"❌ Lỗi tạo bảng exam_results: {e}")
# ---------------------------------------------

class MainApp(QMainWindow):
    def apply_theme(self):
        """
        Giao diện BRAND LUXURY (Orange Glass Edition)
        Nền: #602C04 (Nâu) | Các khối: #ED840D (80% opacity)
        """
        theme_style = """
        /* --- TỔNG THỂ --- */
        QMainWindow, QDialog {
            background-color: #602C04; /* Nền Nâu Coffee Đậm */
            color: #ffffff;
        }
        QWidget {
            /* [FIX] Ưu tiên font hệ thống để tránh warning */
            font-family: -apple-system, Helvetica, Arial, sans-serif;
            font-size: 14px;
            color: #ffffff;
        }

        /* --- TAB WIDGET --- */
        QTabWidget::pane {
            border: 1px solid #954C04;
            background: #602C04;
            border-radius: 8px;
        }
        QTabBar::tab {
            background: rgba(237, 132, 13, 0.3); /* Cam nhạt */
            color: #eee;
            padding: 10px 20px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background: #ED840D; /* Cam 100% */
            color: white;
            border-bottom: 2px solid #ffffff;
        }

        /* --- GLASS CARD & GROUP BOX (NỀN CAM 80%) --- */
        QFrame[class="glass-panel"], QGroupBox {
            background-color: rgba(237, 132, 13, 0.8); /* [YÊU CẦU] Cam 80% */
            border: 1px solid #ffffff; /* Viền trắng cho nổi bật trên nền cam */
            border-radius: 12px;
        }
        QGroupBox {
            margin-top: 25px;
            font-weight: 700;
            color: #ffffff; /* Tiêu đề trắng */
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 5px;
        }

        /* --- INPUT FIELDS (NỀN CAM 80%) --- */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QTimeEdit, QComboBox {
            background-color: rgba(237, 132, 13, 0.8); /* [YÊU CẦU] Cam 80% */
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 8px;
            color: #ffffff;
            padding: 8px 12px;
            font-weight: 500;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 2px solid #ffffff; 
            background-color: #ED840D; /* Cam 100% khi focus */
        }
        
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background-color: #ED840D;
            color: white;
            selection-background-color: #602C04;
        }

        /* --- NÚT BẤM (NỀN CAM 80%) --- */
        QPushButton {
            background-color: rgba(237, 132, 13, 0.8); /* [YÊU CẦU] Cam 80% */
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            color: #ffffff;
            padding: 10px 20px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #ff9f43; /* Sáng hơn khi hover */
            border-color: #ffffff;
        }
        QPushButton:pressed {
            background-color: #ae5c04;
        }

        /* Các nút đặc biệt (Primary/Success) giữ nguyên hoặc điều chỉnh nhẹ */
        QPushButton[class="btn-primary"] {
            background-color: #ffffff;
            color: #ED840D; /* Đảo ngược: Nền trắng chữ cam để nổi bật */
            border: none;
        }
        QPushButton[class="btn-success"] {
            background-color: #2ecc71;
            border: none;
        }

        /* --- BẢNG DỮ LIỆU (NỀN CAM 80%) --- */
        QTableWidget, QListWidget, QTreeWidget {
            background-color: rgba(237, 132, 13, 0.8); /* [YÊU CẦU] Cam 80% */
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            gridline-color: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            alternate-background-color: rgba(237, 132, 13, 0.6);
        }
        QHeaderView::section {
            background-color: #ae5c04; /* Nâu cam đậm */
            border: none;
            border-bottom: 2px solid #ffffff;
            color: #ffffff;
            padding: 8px;
            font-weight: bold;
        }
        QTableWidget::item:selected {
            background-color: #ffffff;
            color: #ED840D; /* Chọn màu trắng chữ cam */
        }
        
        /* SCROLLBAR */
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
        }
        QScrollBar::handle:vertical {
            background: rgba(255,255,255,0.5);
            border-radius: 5px;
        }
        
        /* MENU */
        QMenu {
            background-color: #ED840D;
            color: white;
            border: 1px solid white;
        }
        QMenu::item:selected {
            background-color: #602C04;
        }
        """
        self.setStyleSheet(theme_style)

    def create_big_card(self, title, desc, icon, callback):
        """Tạo thẻ chức năng lớn - Đã Fix lỗi & Đổi màu Cam"""
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumHeight(180)
        
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 48px; background: transparent; border: none; color: white;")
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Chữ tiêu đề màu Trắng (trên nền cam đậm)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 900; color: #ffffff; background: transparent; border: none; text-transform: uppercase;")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 13px; color: #f0f0f0; background: transparent; border: none;")
        
        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        
        btn.clicked.connect(callback)
        
        # [FIX] Xóa dòng transform, Đổi background sang Cam 80%
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(237, 132, 13, 0.8); /* [YÊU CẦU] Cam 80% */
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 16px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ED840D; /* Hover: Cam 100% */
                border: 2px solid #ffffff;
            }
            QPushButton:pressed {
                background-color: #ae5c04;
            }
        """)
        
        return btn
    
    def create_dashboard_card(self, title, desc, icon, btn_text, callback, color="#ED840D"):
        """Hàm hỗ trợ tạo thẻ Dashboard theo phong cách Brand Luxury"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 0.25);
                border: 1px solid #954C04;
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
                background-color: rgba(0, 0, 0, 0.35);
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(10)
        
        # Icon & Header
        h_layout = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"font-size: 32px; background: transparent; border: none;")
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color}; background: transparent; border: none;")
        
        h_layout.addWidget(lbl_icon)
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        # Description
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #dcdde1; font-size: 13px; background: transparent; border: none; margin-bottom: 10px;")
        layout.addWidget(lbl_desc)
        
        # Action Button
        btn = QPushButton(btn_text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #ff9f43;
            }}
        """)
        layout.addWidget(btn)
        
        return card

    def __init__(self, api_key):
        super().__init__()
        self.bk = Backend()
        self.ai = AIEngine(api_key)
        self.gc_manager = GoogleClassroomManager()
        self.current_students = []
        # Dọn dẹp cache ngầm
        self.cleanup_worker = CacheCleanupWorker()
        self.cleanup_worker.start()
        
        self.current_exam = []
        self.generated_exams = {}
        self.setWindowTitle("BankAI Pro - 2025 Matrix Edition")
        
        # [OPTIMIZATION] Auto-fit screen
        screen = QApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * 0.9)
        h = int(screen.height() * 0.9)
        # Ensure minimum size but not larger than screen
        w = max(1000, min(w, 1600))
        h = max(700, min(h, 1200))
        
        # Center window
        x = (screen.width() - w) // 2
        y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)
        
        self.setStyleSheet(APP_STYLE)
        
        w = QWidget(); self.setCentralWidget(w); 
        main_layout = QHBoxLayout(w)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        
        # 1. SIDEBAR (LEFT)
        self.sidebar = ModernSidebar()
        main_layout.addWidget(self.sidebar)
        
        # 2. CONTENT AREA (RIGHT)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0,0,0,0)
        content_layout.setSpacing(0)
        
        content_layout.addWidget(self.create_toolbar())
        
        # Stacked Widget
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_home_tab())   # Index 0
        self.stack.addWidget(self.create_manual_tab()) # Index 1
        self.stack.addWidget(self.create_matrix_tab()) # Index 2
        self.stack.addWidget(self.create_ai_tab())     # Index 3
        self.stack.addWidget(self.create_classroom_tab()) # Index 4
        # Chèn vào MainApp.__init__
        
        # Tạo tab Dashboard (Truyền DB_PATH và self.ai vào)
        self.dashboard_tab = AnalysisTab(DB_PATH, self.ai)
        self.stack.addWidget(self.dashboard_tab) # Index tương ứng là 5 (nếu bạn đã thêm Classroom là 4)
        
        # Kết nối sự kiện nút bấm
        self.sidebar.btn_dashboard.clicked.connect(lambda: self.stack.setCurrentIndex(5))

        content_layout.addWidget(self.stack)
        
        self.lbl_stat = QLabel(" Ready"); 
        self.lbl_stat.setStyleSheet("background: #f0f0f0; padding: 5px; color: #555;")
        content_layout.addWidget(self.lbl_stat)
        
        main_layout.addWidget(content_widget)

        # Connect Sidebar Signals
        self.sidebar.btn_group.buttonClicked.connect(self.switch_page)
        self.sidebar.btn_dashboard.setChecked(True) # Default
        
        QTimer.singleShot(100, self.load_stats)

        # --- THÊM TIMER SCHEDULER ---
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self.check_scheduled_tasks)
        self.scheduler_timer.start(60000) # Kiểm tra mỗi 60 giây
        
        # Kiểm tra ngay khi mở app (xử lý các job bị lỡ)
        QTimer.singleShot(5000, self.check_scheduled_tasks)

    def switch_page(self, btn):
        id = self.sidebar.btn_group.id(btn)
        if id >= 0:
            self.stack.setCurrentIndex(id)

    def check_scheduled_tasks(self):
        """Kiểm tra xem có bài tập nào cần đăng không"""
        tasks = SchedulerManager.load_tasks()
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time_obj = now.time()
        
        has_update = False
        
        for t in tasks:
            if t['status'] == 'pending':
                # Check ngày
                if t['run_date'] == current_date:
                    # Check giờ (Nếu đã qua giờ hẹn trong ngày thì chạy luôn)
                    sched_time = datetime.strptime(t['run_time'], "%H:%M").time()
                    if current_time_obj >= sched_time:
                        print(f"⏰ Đang chạy tác vụ tự động: {t['id']}")
                        t['status'] = 'running'
                        has_update = True
                        
                        # Khởi chạy Worker
                        google_mgr = GoogleManagerFull()
                        
                        # [SỬA LỖI TẠI ĐÂY] Bỏ self.bk ra khỏi tham số
                        worker = AutoPostWorker(t, google_mgr) 
                        
                        worker.finished.connect(self.on_auto_post_finished)
                        worker.start()
                        
                        if not hasattr(self, 'auto_workers'): self.auto_workers = []
                        self.auto_workers.append(worker)

        if has_update:
            SchedulerManager.save_tasks(tasks)

    def on_auto_post_finished(self, task_id, msg):
        """Xử lý khi worker chạy xong"""
        print(f"Auto Post Result: {msg}")
        tasks = SchedulerManager.load_tasks()
        for t in tasks:
            if t['id'] == task_id:
                t['status'] = 'done' if 'Success' in msg else 'failed'
                t['log'] = msg
                break
        SchedulerManager.save_tasks(tasks)
        
        # Thông báo nhỏ ở góc (Tray notification nếu có, hoặc log)
        self.statusBar().showMessage(f"🤖 Tự động hóa: {msg}", 10000)

    def create_toolbar(self):
        container = QWidget()
        # [STYLE MỚI] Gradient Cam + Bóng đổ + Viền dưới sáng
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ED840D, stop:1 #d35400);
                border-bottom: 2px solid #ffaf40;
            }
        """)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10) 
        
        # --- TRÁI: LOGO ---
        brand_box = QHBoxLayout()
        lbl_logo = QLabel("🏛️") 
        lbl_logo.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        
        lbl_text = QLabel("BANKAI PRO 2025")
        lbl_text.setStyleSheet("""
            font-size: 20px; font-weight: 900; color: #ffffff; letter-spacing: 1px; 
            background: transparent; border: none; font-family: Arial, sans-serif;
        """)
        brand_box.addWidget(lbl_logo); brand_box.addWidget(lbl_text)
        layout.addLayout(brand_box)
        
        layout.addStretch()
        
        # --- PHẢI: CÁC NÚT CHỨC NĂNG ---
        
        # 1. Nút Bật Web Server (MỚI THÊM)
        self.btn_web = QPushButton("🌍 Bật Thi Online")
        self.btn_web.setCheckable(True) # Chế độ bật/tắt
        self.btn_web.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_web.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2); 
                border: 1px solid rgba(255, 255, 255, 0.5);
                color: #ffffff; padding: 8px 15px; border-radius: 6px; font-weight: 700;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); }
            QPushButton:checked { 
                background-color: #2ecc71; /* Màu xanh lá khi đang bật */
                border-color: #27ae60; 
                color: white;
            }
        """)
        self.btn_web.clicked.connect(self.toggle_web_server)
        layout.addWidget(self.btn_web)

        # 2. Menu Tiện ích (Giữ nguyên)
        btn_tools = QPushButton("🛠️  Tiện ích  ▼")
        btn_tools.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_tools.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.5);
                color: #ffffff; padding: 8px 25px; border-radius: 6px; font-weight: 700;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); }
            QPushButton::menu-indicator { image: none; }
        """)
        
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #fff; border-radius: 4px; padding: 5px; } QMenu::item { padding: 8px 25px; color: #333; } QMenu::item:selected { background-color: #ED840D; color: white; }")
        
        menu.addAction("📖  Hướng dẫn sử dụng", self.open_help)
        menu.addSeparator()
        menu.addAction("📜  Lịch sử Thi Online", self.open_history)
        menu.addAction("🏷️  Gán ID6 Tự động", self.show_id6)
        menu.addAction("🖼️  Quản lý Kho Hình ảnh", self.open_image_manager)
        menu.addAction("🧹  Làm sạch & Check Lỗi", self.open_file_cleaner)
        menu.addSeparator()
        menu.addAction("⏰  Lên lịch Tự động", lambda: AutoSchedulerDialog(self).exec())
        menu.addAction("💾  Xuất Database ra TeX", self.export_exam)
        menu.addSeparator()
        menu.addAction("❌  Thoát phần mềm", self.close)
        
        btn_tools.setMenu(menu)
        layout.addWidget(btn_tools)

        return container

    # THÊM CÁC HÀM NÀY VÀO CLASS MainApp

    def filter_mat_table(self):
        """Ẩn/Hiện các dòng theo Chương đã chọn (Hỗ trợ lọc đa lớp)"""
        filter_val = self.mat_chap_filter.currentData() # Dạng "g_s_ch" hoặc 0
        
        for r in range(self.mat_tb.rowCount()):
            item = self.mat_tb.item(r, 0)
            if not item: 
                # Dòng Header phân cách -> Luôn hiện nếu show all, hoặc ẩn theo logic riêng (ở đây ta cứ hiện cho đẹp)
                self.mat_tb.setRowHidden(r, False)
                continue
                
            row_data = item.data(Qt.ItemDataRole.UserRole)
            if not row_data: continue

            if filter_val == 0:
                self.mat_tb.setRowHidden(r, False)
            else:
                # Tạo key từ row hiện tại để so sánh
                row_key = f"{row_data['g']}_{row_data['s']}_{row_data['ch']}"
                if row_key == filter_val:
                    self.mat_tb.setRowHidden(r, False)
                else:
                    self.mat_tb.setRowHidden(r, True)

    def calc_mat_sum(self):
        """Tính tổng số câu (Bỏ qua các dòng tiêu đề không có Spinbox)"""
        s1 = s2 = s3 = 0
        for r in range(self.mat_tb.rowCount()):
            # Kiểm tra xem dòng này có widget nhập liệu ở cột 1 không
            # Nếu không có (là dòng Header phân cách), thì bỏ qua
            if not self.mat_tb.cellWidget(r, 1):
                continue

            s1 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(1, 4))
            s2 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(4, 7))
            s3 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(7, 10))
            
        self.mat_sum.setText(f"<b>TỔNG SỐ CÂU:</b> "
                             f"P1: <span style='color:blue; font-size:16px'>{s1}</span> | "
                             f"P2: <span style='color:orange; font-size:16px'>{s2}</span> | "
                             f"P3: <span style='color:purple; font-size:16px'>{s3}</span>")

    def quick_fill_matrix(self):
        """Copy dòng đầu tiên có dữ liệu xuống các dòng dưới"""
        first_visible_row = -1
        values = {}
        
        # 1. Tìm dòng mẫu (dòng CÓ WIDGET đầu tiên đang hiện)
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and self.mat_tb.cellWidget(r, 1):
                first_visible_row = r
                for c in range(1, 10):
                    values[c] = self.mat_tb.cellWidget(r, c).value()
                break
        
        if first_visible_row == -1: return

        # 2. Áp dụng
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and r != first_visible_row and self.mat_tb.cellWidget(r, 1):
                for c in range(1, 10):
                    self.mat_tb.cellWidget(r, c).setValue(values[c])
        
        QMessageBox.information(self, "Xong", "Đã sao chép cấu hình!")

    def reset_matrix_values(self):
        """Xóa trắng (Bỏ qua header)"""
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and self.mat_tb.cellWidget(r, 1):
                for c in range(1, 10):
                    self.mat_tb.cellWidget(r, c).setValue(0)

    def open_stats_dashboard(self):
        """Mở cửa sổ thống kê chi tiết"""
        dlg = StatisticsDashboard(self.bk, self)
        dlg.exec()
        self.load_stats() # Cập nhật lại số liệu nhỏ ở trang chủ sau khi đóng

    def quick_fill_matrix(self):
        """Copy giá trị của dòng dữ liệu đầu tiên xuống các dòng dưới (Bỏ qua header)"""
        first_visible_row = -1
        values = {}
        
        # 1. Tìm dòng mẫu (dòng có dữ liệu đầu tiên đang hiện)
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and self.mat_tb.cellWidget(r, 1):
                first_visible_row = r
                for c in range(1, 10):
                    values[c] = self.mat_tb.cellWidget(r, c).value()
                break
        
        if first_visible_row == -1: return

        # 2. Áp dụng cho các dòng còn lại
        for r in range(self.mat_tb.rowCount()):
            # Chỉ điền nếu dòng hiện và CÓ WIDGET (không phải header)
            if not self.mat_tb.isRowHidden(r) and r != first_visible_row and self.mat_tb.cellWidget(r, 1):
                for c in range(1, 10):
                    self.mat_tb.cellWidget(r, c).setValue(values[c])
        
        QMessageBox.information(self, "Xong", "Đã sao chép cấu hình cho các bài trong danh sách!")

    def reset_matrix_values(self):
        """Đặt tất cả về 0 (Bỏ qua header)"""
        for r in range(self.mat_tb.rowCount()):
            if not self.mat_tb.isRowHidden(r) and self.mat_tb.cellWidget(r, 1):
                for c in range(1, 10):
                    self.mat_tb.cellWidget(r, c).setValue(0)

    # --- HÀM SLOT MỞ HỘP THOẠI ---
    def open_image_manager(self):
        dlg = ImageManagerDialog(self)
        dlg.exec()

    # --- [MỚI] HÀM MỞ CỬA SỔ SOẠN BÀI ---
    def open_lesson_planner(self):
        # Kiểm tra xem DB_PATH có tồn tại không trước khi mở
        if not os.path.exists(DB_PATH):
             QMessageBox.critical(self, "Lỗi", "Chưa tìm thấy Database!")
             return

        # Khởi tạo cửa sổ LessonPlannerWidget
        # Lưu ý: self.planner_window phải được gán vào self để không bị garbage collector thu hồi
        self.planner_window = LessonPlannerWidget(DB_PATH)
        self.planner_window.resize(1100, 700) # Kích thước cửa sổ to cho dễ nhìn
        self.planner_window.setWindowTitle("Công cụ Soạn Giảng & Lọc Đề - BankAI Pro")
        self.planner_window.show()

    # ... (Giữ nguyên các hàm create_home_tab, create_manual_tab, create_matrix_tab, create_ai_tab ...)
    # Lưu ý: Copy lại các hàm đó vào đây nếu bạn xóa nhầm, hoặc chỉ cần paste đoạn code bên dưới vào cuối class MainApp
    
    def create_home_tab(self):
        """Trang chủ: Dashboard với nền Watermark"""
        # [THAY ĐỔI] Sử dụng WatermarkWidget thay vì QWidget thường
        w = WatermarkWidget("BANKAI PRO 2025") 
        
        main_layout = QVBoxLayout(w)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(30)

        # 1. Header (Giữ nguyên)
        header_box = QVBoxLayout()
        lbl_welcome = QLabel("TRUNG TÂM ĐIỀU KHIỂN")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Bỏ background-color của label để hiện watermark bên dưới
        lbl_welcome.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff; background: transparent;")
        
        self.stat_lbl = QLabel("Hệ thống sẵn sàng...") 
        self.stat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stat_lbl.setStyleSheet("font-size: 14px; color: #a4b0be; background: transparent;")
        
        header_box.addWidget(lbl_welcome)
        header_box.addWidget(self.stat_lbl)
        main_layout.addLayout(header_box)

        # 2. Grid Chức năng (Giữ nguyên logic cũ)
        grid = QGridLayout()
        grid.setSpacing(25)
        
        # Các Card chức năng (Vẫn dùng create_big_card cũ)
        card_import = self.create_big_card("NHẬP DỮ LIỆU", "Import câu hỏi LaTeX & Phân loại.", "📥", self.import_files)
        card_planner = self.create_big_card("SOẠN BÀI GIẢNG", "Soạn chuyên đề & Lọc ma trận.", "📝", self.open_lesson_planner)
        card_mix = self.create_big_card("TRỘN ĐỀ THI", "Đảo đề hoán vị & Xuất PDF/TeX.", "🔀", self.mix_and_export)
        # Đổi callback từ self.open_classroom_dialog sang self.show_classroom_menu
        card_class = self.create_big_card(
            "GOOGLE CLASSROOM", 
            "Đăng bài tập & Tổ chức Thi Online (Global).", 
            "☁️", 
            self.show_classroom_menu
        )

        grid.addWidget(card_import, 0, 0)
        grid.addWidget(card_planner, 0, 1)
        grid.addWidget(card_mix, 1, 0)
        grid.addWidget(card_class, 1, 1)
        
        grid.setRowStretch(0, 1); grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)

        main_layout.addLayout(grid)
        
        # Footer (Background transparent để thấy watermark)
        footer = QLabel(f"BankAI Pro v{APP_VERSION} © 2025 Matrix Edition")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: rgba(255,255,255,0.3); margin-top: 20px; background: transparent;")
        main_layout.addWidget(footer)

        return w

    def quick_save_manual_exam(self):
        """Lưu nhanh danh sách câu hỏi hiện tại ra file TeX (Cấu trúc chuẩn như Classroom)"""
        # 1. Lấy dữ liệu từ Tree Widget
        questions = self.exam_lst.get_all_questions()
        
        if not questions:
            QMessageBox.warning(self, "Trống", "Danh sách câu hỏi trống!")
            return

        # 2. Chọn nơi lưu
        path, _ = QFileDialog.getSaveFileName(self, "Lưu Đề Gốc", "De_Goc.tex", "TeX Files (*.tex)")
        if not path: return

        try:
            # --- LOGIC MỚI: SẮP XẾP VÀ CHIA PHẦN ---
            
            # 1. Sắp xếp theo Dạng (1->2->3->4)
            sanitized_qs = []
            for q in questions:
                # Đảm bảo 'dang' luôn tồn tại, mặc định là 4 (Tự luận)
                if 'dang' not in q: q['dang'] = 4
                sanitized_qs.append(q)
            
            sanitized_qs.sort(key=lambda x: x['dang'])

            # 2. Chuẩn bị nội dung Body
            body_content = [
                r"\begin{center}\textbf{\Large ĐỀ THI ĐƯỢC CHỌN TỪ NGÂN HÀNG}\end{center}",
                r"\setcounter{ex}{0}"
            ]
            
            current_dang = None
            section_titles = {
                1: r"\section*{PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.} \textbf{\textit{Thí sinh trả lời các câu sau. Mỗi câu hỏi thí sinh chỉ lựa chọn một phương án.}}",
                2: r"\section*{PHẦN II. Câu trắc nghiệm đúng sai.} \textbf{\textit{Thí sinh trả lời các câu sau. Trong mỗi ý {\bfseries a)}, {\bfseries b)}, {\bfseries c)}, {\bfseries d)} ở mỗi câu, thí sinh chọn đúng hoặc sai.}}",
                3: r"\section*{PHẦN III. Câu trắc nghiệm trả lời ngắn.} \textbf{\textit{Thí sinh trả lời các câu sau.}}",
                4: r"\section*{PHẦN IV. Tự luận / Khác}"
            }

            for q in sanitized_qs:
                dang = q['dang']
                # Nếu chuyển sang dạng mới -> Thêm tiêu đề phần
                if dang != current_dang:
                    if dang in section_titles:
                        body_content.append(r"\vspace{0.5cm}")
                        body_content.append(section_titles[dang])
                        body_content.append(r"\vspace{0.2cm}")
                    current_dang = dang
                
                body_content.append(q.get('content_tex', ''))

            # 3. Ghép vào Template
            tex_body = "\n".join(body_content)
            # LATEX_TEMPLATE có placeholder __CONTENT__
            final_tex = LATEX_TEMPLATE.replace("__CONTENT__", tex_body)

            # 4. Ghi file
            with open(path, "w", encoding="utf-8") as f:
                f.write(final_tex)
            
            QMessageBox.information(self, "Thành công", f"Đã lưu file đề gốc (Format chuẩn) tại:\n{path}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi lưu file", str(e))

    def create_manual_tab(self):
        w = QWidget(); l = QHBoxLayout(w)
        
        # --- CỘT TRÁI: KHO CÂU HỎI ---
        lw = QWidget(); ll = QVBoxLayout(lw)
        
        # Bộ lọc
        # Copy lại đoạn bộ lọc từ code cũ của bạn vào đây
        grp = QGroupBox("🔍 Bộ lọc câu hỏi"); gl = QGridLayout(grp)
        self.man_g = QComboBox(); self.man_g.addItems(["All","10","11","12"])
        self.man_s = QComboBox(); self.man_s.addItems(["All","Đại số","Hình học"])
        self.man_c = QComboBox(); self.man_c.addItem("Tất cả", 0) 
        self.man_b = QComboBox(); self.man_b.addItem("Tất cả", 0) 
        self.man_l = QComboBox(); self.man_l.addItems(["All","NB","TH","VD","VDC"])
        self.man_d = QComboBox(); self.man_d.addItem("All",0)
        if 'DANH_MUC_DANG' in globals():
            for k,v in DANH_MUC_DANG.items(): self.man_d.addItem(v,k)
        
        self.man_g.currentTextChanged.connect(self.upd_man_ch)
        self.man_s.currentTextChanged.connect(self.upd_man_ch)
        self.man_c.currentIndexChanged.connect(self.upd_man_bai) 
        
        gl.addWidget(QLabel("Lớp"),0,0); gl.addWidget(self.man_g,0,1)
        gl.addWidget(QLabel("Môn"),0,2); gl.addWidget(self.man_s,0,3)
        gl.addWidget(QLabel("Chương"),1,0); gl.addWidget(self.man_c,1,1)
        gl.addWidget(QLabel("Bài"),1,2); gl.addWidget(self.man_b,1,3) 
        gl.addWidget(QLabel("Mức độ"),2,0); gl.addWidget(self.man_l,2,1)
        gl.addWidget(QLabel("Dạng"),2,2); gl.addWidget(self.man_d,2,3)
        b_s = QPushButton("🔎 Tìm kiếm"); b_s.setProperty("class","btn-primary"); b_s.clicked.connect(self.filter_manual)
        gl.addWidget(b_s,3,0,1,4); ll.addWidget(grp)
        
        self.man_lst = DragDropListWidget()
        self.man_lst.itemClicked.connect(lambda i: self.man_prev.setText(i.data(Qt.ItemDataRole.UserRole)['content_tex']))
        ll.addWidget(QLabel("<b>Kết quả tìm kiếm (Kéo sang phải để chọn):</b>"))
        ll.addWidget(self.man_lst)
        self.man_prev = QTextEdit(); self.man_prev.setMaximumHeight(100); self.man_prev.setReadOnly(True)
        ll.addWidget(self.man_prev)
        
        # --- CỘT PHẢI: ĐỀ ĐANG SOẠN (CẬP NHẬT MỚI) ---
        rw = QWidget(); rl = QVBoxLayout(rw)
        
        # Thống kê
        self.lbl_exam_stats = QLabel("Đề đang soạn: 0 câu")
        self.lbl_exam_stats.setStyleSheet("font-size: 14px; font-weight: bold; color: #d35400; padding: 5px; border-bottom: 2px solid #d35400;")
        rl.addWidget(self.lbl_exam_stats)
        
        # [THAY ĐỔI] Sử dụng DropZoneTreeWidget thay vì List
        self.exam_lst = DropZoneTreeWidget(self.bk)
        self.exam_lst.items_changed.connect(self.update_exam_stats)
        rl.addWidget(self.exam_lst)
        
        # Toolbar
        bh = QHBoxLayout()
        
        b_clear = QPushButton("🗑️ Xóa hết")
        b_clear.setProperty("class","btn-danger")
        b_clear.clicked.connect(self.exam_lst.clear_all)
        
        # Nút 1: Lưu file TeX (Đơn giản như ban đầu)
        b_save = QPushButton("💾 Lưu File TeX (Gốc)") 
        b_save.setProperty("class","btn-primary") # Màu xanh dương
        b_save.clicked.connect(self.quick_save_manual_exam) # <--- Gọi hàm lưu nhanh mới
        
        # Nút 2: Đăng Classroom (Giữ nguyên theo yêu cầu trước)
        b_class = QPushButton("☁️ Đăng Classroom")
        b_class.setProperty("class","btn-success") # Màu xanh lá
        b_class.clicked.connect(self.upload_from_manual_tab)
        
        bh.addWidget(b_clear)
        bh.addWidget(b_save)
        bh.addWidget(b_class)
        
        rl.addLayout(bh)
        
        l.addWidget(lw, 4); l.addWidget(rw, 4)
        return w

    # Thêm hàm này vào trong class MainApp
    # Tìm và thay thế hàm này trong class MainApp
    def upload_from_manual_tab(self):
        """
        Đồng bộ chức năng: Hiển thị Menu chọn (Upload PDF hoặc Thi Online)
        Lấy dữ liệu trực tiếp từ danh sách đang soạn (TreeWidget).
        """
        # 1. Lấy dữ liệu từ danh sách đang soạn
        questions = []
        if hasattr(self.exam_lst, 'get_all_questions'):
            questions = self.exam_lst.get_all_questions()
        
        if not questions:
            QMessageBox.warning(self, "Danh sách trống", "Vui lòng chọn ít nhất 1 câu hỏi trước khi đăng!")
            return

        # 2. Tạo Menu chọn chế độ (Giống nút trang chủ)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { font-size: 14px; padding: 5px; background-color: white; border: 1px solid #ccc; } 
            QMenu::item { padding: 10px 20px; }
            QMenu::item:selected { background-color: #3498db; color: white; }
        """)
        
        act_upload = menu.addAction("📤 Đăng bài tập (PDF/Form)")
        act_exam = menu.addAction("🌍 Tổ chức Thi Online (Global)")
        
        # Hiện menu ngay tại vị trí con trỏ chuột
        action = menu.exec(QCursor.pos())
        
        if action == act_upload:
            # Chế độ 1: Đăng file PDF/Form (Logic cũ)
            dlg = ClassroomDialog(questions, self)
            dlg.exec()
            
        elif action == act_exam:
            # Chế độ 2: Tổ chức thi Online (Logic mới - Ngrok)
            # Hàm create_online_classroom_exam sẽ tự động gọi get_current_exam_questions
            # Vì ta đang ở Tab 1 (Soạn thủ công), nó sẽ tự động lấy câu hỏi từ exam_lst
            self.create_online_classroom_exam()

# Thay thế hàm create_matrix_tab trong class MainApp
    def create_matrix_tab(self):
        """Tab tạo đề Ma trận - Giao diện Launchpad"""
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(50, 50, 50, 50)
        l.setSpacing(20)
        
        # Header
        lbl_title = QLabel("CÔNG CỤ TẠO ĐỀ MA TRẬN 2025")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #d35400;")
        l.addWidget(lbl_title)
        
        lbl_desc = QLabel("Hệ thống ma trận 3 chiều (Lớp - Chương - Bài) hỗ trợ trích xuất đề thi chính xác.\n"
                          "Bấm nút bên dưới để mở Bảng điều khiển Ma trận.")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("font-size: 14px; color: #555; margin-bottom: 20px;")
        l.addWidget(lbl_desc)
        
        # Big Button
        btn_open = QPushButton("🎛️ MỞ BẢNG ĐIỀU KHIỂN MA TRẬN")
        btn_open.setMinimumHeight(80)
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white; 
                font-size: 18px; font-weight: bold; border-radius: 10px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        btn_open.clicked.connect(self.open_matrix_window)
        l.addWidget(btn_open)
        
        # Info area
        self.lbl_matrix_status = QLabel("Trạng thái: Chưa có đề nào được tạo.")
        self.lbl_matrix_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.lbl_matrix_status)
        
        l.addStretch()
        return w

    def open_matrix_window(self):
        """Mở cửa sổ Ma trận riêng biệt"""
        dlg = MatrixEditorDialog(self.bk, self)
        
        # Nếu người dùng bấm "Hoàn tất & Tạo đề" (Accept)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            questions = dlg.final_questions
            
            if questions:
                # 1. Lưu vào biến toàn cục của MainApp
                self.current_exam = questions
                
                # 2. Cập nhật thông báo
                self.lbl_matrix_status.setText(f"✅ Đã tạo thành công đề thi gồm {len(questions)} câu.\n"
                                               "Bạn có thể bấm nút 'Bật Thi Online' hoặc chuyển sang tab 'Soạn đề' để chỉnh sửa thêm.")
                
                # 3. (Tùy chọn) Chuyển sang tab Soạn đề và hiển thị lên đó
                # Xóa cũ
                self.exam_lst.clear_all()
                # Thêm mới (Cần convert format câu hỏi sang format của TreeWidget)
                root_map = self.exam_lst.roots
                for q in questions:
                    # Tạo item cho TreeWidget
                    dang = q.get('dang', 4)
                    root = root_map.get(dang, root_map[4])
                    
                    content_preview = q['content_tex'][:60].replace("\n", " ")
                    item = QTreeWidgetItem([f"[ID:{q['id']}] {q.get('level','?')} | {content_preview}..."])
                    item.setData(0, Qt.ItemDataRole.UserRole, q)
                    item.setToolTip(0, q['content_tex'])
                    root.addChild(item)
                
                # Chuyển tab để user thấy kết quả
                self.stack.setCurrentIndex(1) # Tab Index 1 là Soạn thủ công
                QMessageBox.information(self, "Thành công", f"Đã chuyển {len(questions)} câu hỏi sang danh sách 'Đề đang soạn'.")

    # =========================================================================
    # 2. HÀM MỞ THƯ VIỆN (Thêm mới ngay bên dưới hàm trên)
    # =========================================================================
    # Tìm hàm open_template_lib cũ và thay thế bằng hàm này:
    def open_template_lib(self):
        """Mở dialog thư viện mẫu và tự động điền ma trận"""
        # Kiểm tra xem người dùng đã chọn chương nào chưa
        row_count = self.mat_tb.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Chưa chọn chương", "Vui lòng chọn Lớp và Môn học để hiện danh sách các chương trước khi áp dụng mẫu.")
            return

        dlg = TemplateLibraryDialog(self)
        if dlg.exec():
            matrix_data = dlg.get_selected_template()
            if matrix_data:
                # Logic chia đều số câu hỏi cho các chương đang hiển thị
                # matrix_data dạng: {1: 4, 2: 4...} (Tổng số câu mong muốn mỗi cột)
                
                # Reset bảng về 0
                for r in range(row_count):
                    for c in range(1, 10):
                        self.mat_tb.cellWidget(r, c).setValue(0)
                
                # Phân phối câu hỏi
                for col_idx, total_needed in matrix_data.items():
                    if total_needed == 0: continue
                    
                    # Chia đều
                    base_per_row = total_needed // row_count
                    remainder = total_needed % row_count
                    
                    for r in range(row_count):
                        val = base_per_row
                        if remainder > 0:
                            val += 1
                            remainder -= 1
                        
                        # Set giá trị vào ô SpinBox
                        self.mat_tb.cellWidget(r, col_idx).setValue(val)
                
                self.calc_mat_sum() # Tính lại tổng
                QMessageBox.information(self, "Thành công", "Đã áp dụng mẫu cấu trúc đề thi!\nSố lượng câu hỏi đã được chia đều cho các chương.")

    def create_ai_tab(self):
        w = QWidget(); l = QHBoxLayout(w)
        
        # --- Cột trái: List câu hỏi gốc ---
        lw = QWidget(); ll = QVBoxLayout(lw)
        ll.addWidget(QLabel("<b>ĐỀ GỐC (Chọn câu hỏi để AI nhân bản)</b>"))
        self.ai_lst = QListWidget()
        self.ai_lst.setAlternatingRowColors(True)
        ll.addWidget(self.ai_lst)
        
        # Group cấu hình
        g = QGroupBox("Cấu hình AI")
        gl = QGridLayout(g)
        self.ai_n = QSpinBox(); self.ai_n.setValue(3); self.ai_n.setSuffix(" đề")
        self.ai_c = QSpinBox(); self.ai_c.setRange(100,999); self.ai_c.setValue(101)
        gl.addWidget(QLabel("Số lượng đề:"),0,0); gl.addWidget(self.ai_n,0,1)
        gl.addWidget(QLabel("Mã đề bắt đầu:"),1,0); gl.addWidget(self.ai_c,1,1)
        ll.addWidget(g)
        
        # Các nút bấm điều khiển
        btn_box = QVBoxLayout()
        b_load = QPushButton("1. Load câu hỏi từ đề đang soạn")
        b_load.clicked.connect(self.load_ai)
        btn_box.addWidget(b_load)
        
        b_run = QPushButton("2. CHẠY AI (Tạo đề tương tự)")
        b_run.setProperty("class","btn-success") # Màu xanh lá
        b_run.clicked.connect(self.run_ai)
        btn_box.addWidget(b_run)

        # === [NÚT MỚI] XUẤT CODE LATEX ===
        b_export = QPushButton("3. 💾 Xuất ra Code LaTeX (.tex)")
        b_export.setProperty("class", "btn-warning") # Màu cam
        b_export.clicked.connect(self.export_ai_results) # Gọi hàm xuất file
        btn_box.addWidget(b_export)
        # =================================
        
        ll.addLayout(btn_box)
        
        # --- Cột phải: Xem trước kết quả ---
        rw = QWidget(); rl = QVBoxLayout(rw)
        rl.addWidget(QLabel("<b>KẾT QUẢ TỪ AI</b>"))
        self.ai_tr = QTreeWidget()
        self.ai_tr.setHeaderHidden(True)
        self.ai_tr.itemClicked.connect(self.on_ai_tree_click)
        rl.addWidget(self.ai_tr)
        
        self.ai_prv = QTextEdit()
        self.ai_prv.setPlaceholderText("Nội dung code LaTeX của câu hỏi sẽ hiện ở đây...")
        self.ai_prv.setMaximumHeight(200)
        self.ai_prv.setReadOnly(True)
        rl.addWidget(self.ai_prv)
        
        l.addWidget(lw, 1); l.addWidget(rw, 2)
        return w

    # --- [CHÈN HÀM MỚI VÀO ĐÂY] ---
    def create_classroom_tab(self):
        """Tạo giao diện Tab Google Classroom"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Tiêu đề
        lbl_title = QLabel("QUẢN LÝ LỚP HỌC & ĐỒNG BỘ")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: 900; color: #ED840D; letter-spacing: 1px;")
        layout.addWidget(lbl_title)

        # --- Group 1: Kết nối & Đồng bộ ---
        gb_sync = QGroupBox("1. KẾT NỐI DANH SÁCH LỚP")
        gb_layout = QVBoxLayout(gb_sync)
        gb_layout.setSpacing(15)
        
        hbox1 = QHBoxLayout()
        self.cb_courses = QComboBox()
        self.cb_courses.setMinimumHeight(45)
        self.btn_load_courses = QPushButton("🔄 Danh Sách Lớp")
        self.btn_load_courses.setFixedSize(160, 45)
        self.btn_load_courses.clicked.connect(self.load_classroom_courses)
        
        hbox1.addWidget(QLabel("Chọn lớp học:"))
        hbox1.addWidget(self.cb_courses, 1)
        hbox1.addWidget(self.btn_load_courses)
        
        btn_sync = QPushButton("⬇️  Đồng bộ Học sinh vào Hệ thống Thi Online")
        btn_sync.setProperty("class", "btn-primary") # Style cam nổi bật
        btn_sync.setMinimumHeight(50)
        btn_sync.setStyleSheet("font-size: 16px; font-weight: bold;")
        btn_sync.clicked.connect(self.sync_students_to_db)
        
        gb_layout.addLayout(hbox1)
        gb_layout.addWidget(btn_sync)
        layout.addWidget(gb_sync)

        # --- Group 2: Trả điểm ---
        gb_grade = QGroupBox("2. LIÊN KẾT BÀI TẬP (ĐỂ TRẢ ĐIỂM)")
        gb_grade_layout = QVBoxLayout(gb_grade)
        
        hbox2 = QHBoxLayout()
        self.cb_assignments = QComboBox()
        self.cb_assignments.setMinimumHeight(45)
        self.btn_load_assign = QPushButton("📂 Tải Bài Tập")
        self.btn_load_assign.setFixedSize(160, 45)
        self.btn_load_assign.clicked.connect(self.load_classroom_assignments)
        
        hbox2.addWidget(QLabel("Gán vào bài tập:"))
        hbox2.addWidget(self.cb_assignments, 1)
        hbox2.addWidget(self.btn_load_assign)
        
        gb_grade_layout.addLayout(hbox2)
        
        note_lbl = QLabel("ℹ️ Lưu ý: Hãy chọn đúng bài tập tương ứng trên Classroom. Khi học sinh nộp bài thi, điểm sẽ được gửi vào bài tập này.")
        note_lbl.setStyleSheet("color: #ccc; font-style: italic; margin-top: 10px;")
        gb_grade_layout.addWidget(note_lbl)
        
        layout.addWidget(gb_grade)
        layout.addStretch()
        
        return widget
    # ------------------------------

    def export_ai_results(self):
        """Xuất toàn bộ các đề đã được AI tạo ra file .tex chuẩn"""
        # 1. Kiểm tra dữ liệu
        if not hasattr(self, 'gen_res') or not self.gen_res:
            QMessageBox.warning(self, "Chưa có dữ liệu", "Vui lòng bấm 'CHẠY AI' để tạo đề trước khi xuất file.")
            return

        # 2. Hộp thoại lưu file
        path, _ = QFileDialog.getSaveFileName(self, "Lưu Code LaTeX", "De_Thi_AI.tex", "TeX Files (*.tex)")
        if not path: return

        # 3. Tạo nội dung file LaTeX
        # LATEX_TEMPLATE là biến toàn cục đã khai báo ở đầu file
        content = [LATEX_TEMPLATE] 
        
        all_keys = {} # Lưu đáp án để làm bảng tổng hợp cuối file

        # Duyệt qua từng mã đề (Exam Code)
        for code, questions in self.gen_res.items():
            content.append(f"\\newpage")
            content.append(f"\\begin{{center}}\\textbf{{MÃ ĐỀ THI: {code}}}\\end{{center}}")
            content.append(f"\\setcounter{{ex}}{{0}}") # Reset số thứ tự câu về 1
            
            exam_keys = []
            
            for q in questions:
                # Thêm nội dung câu hỏi (Code LaTeX)
                content.append(q['content'])
                # Lưu đáp án (VD: 1.A)
                exam_keys.append(f"{q['idx']}.{q['key']}")
            
            all_keys[code] = exam_keys

        # 4. Tạo bảng đáp án tổng hợp (Phụ lục)
        content.append("\\newpage")
        content.append("\\begin{center}\\textbf{BẢNG ĐÁP ÁN THAM KHẢO}\\end{center}")
        content.append("\\begin{multicols}{2}") # Chia 2 cột nếu nhiều mã đề
        
        for code, keys in all_keys.items():
            content.append(f"\\noindent\\textbf{{Mã đề {code}:}}")
            # Tạo bảng đáp án dạng lưới hoặc dòng
            content.append("\\begin{center}")
            content.append("\\begin{tabular}{|" + "c|" * 5 + "} \\hline") # 5 cột mỗi dòng
            
            # Xử lý hiển thị đáp án đẹp hơn trong bảng
            row = []
            for i, k in enumerate(keys):
                row.append(k)
                if len(row) == 5: # Đủ 5 câu thì xuống dòng
                    content.append(" & ".join(row) + " \\\\ \\hline")
                    row = []
            if row: # In nốt các câu còn lẻ
                 content.append(" & ".join(row) + " \\\\ \\hline")

            content.append("\\end{tabular}")
            content.append("\\end{center}\\vspace{0.5cm}")
            
        content.append("\\end{multicols}")
        content.append("\\end{document}")

        # 5. Ghi file
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            QMessageBox.information(self, "Thành công", f"Đã xuất file LaTeX tại:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi ghi file", str(e))

    def on_ai_tree_click(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data: return
        if data['t'] == 'q':
            c = data['c']; i = data['i']
            try: self.ai_prv.setText(f"{self.gen_res[c][i]['content']}\n\nKEY: {self.gen_res[c][i]['key']}")
            except: self.ai_prv.setText("Lỗi hiển thị dữ liệu")
        elif data['t'] == 'e': self.ai_prv.setText(f"Đề thi mã: {data['c']}")

    def upd_man_ch(self):
        self.man_c.clear(); self.man_c.addItem("Tất cả", 0)
        g_txt = self.man_g.currentText(); s_txt = self.man_s.currentText()
        if "All" in g_txt or "All" in s_txt: return
        
        g = int(g_txt); s = 'D' if 'Đại' in s_txt else 'H'
        
        # Lấy chương từ DATA_ID6_2025
        chapters = DATA_ID6_2025.get(g, {}).get(s, {})
        for k in chapters.keys(): # Chỉ lấy key chương
            # Lấy tên bài đầu tiên để làm tên chương tượng trưng (hoặc chỉ hiện số chương)
            # Vì cấu trúc mới là Chương -> Bài -> Tên, ta sẽ hiển thị "Chương X"
            self.man_c.addItem(f"Chương {k}", k)
        self.upd_man_bai()

    def upd_man_bai(self):
        self.man_b.clear(); self.man_b.addItem("Tất cả", 0)
        try:
            g = int(self.man_g.currentText())
            s = 'D' if 'Đại' in self.man_s.currentText() else 'H'
            c = self.man_c.currentData()
            
            if c and c != 0:
                lessons = DATA_ID6_2025.get(g, {}).get(s, {}).get(c, {})
                for k, v in lessons.items():
                    self.man_b.addItem(f"Bài {k}: {v}", k)
        except: pass

    def filter_manual(self):
        self.man_lst.clear()
        
        # Lấy bộ lọc
        g_txt = self.man_g.currentText()
        g = int(g_txt) if "All" not in g_txt else None
        
        s_txt = self.man_s.currentText()
        s = ('D' if 'Đại' in s_txt else 'H') if "All" not in s_txt else None
        
        c = self.man_c.currentData() # Chương
        b = self.man_b.currentData() # Bài
        
        l_map = {'NB':'N','TH':'H','VD':'V','VDC':'C'}
        l_txt = self.man_l.currentText()
        l = l_map.get(l_txt) if "All" not in l_txt else None
        
        d = self.man_d.currentData() # Dạng
        
        # Query DB
        qs = self.bk.get_all_filtered(g, s, c, b, l, d, limit=500)
        
        # Map Icon và Màu sắc cho Dạng
        type_style = {
            1: ("🟢 TN", "#2ecc71"),   # Trắc nghiệm - Xanh lá
            2: ("🔵 Đ/S", "#3498db"),  # Đúng sai - Xanh dương
            3: ("🟠 TLN", "#e67e22"),  # Trả lời ngắn - Cam
            4: ("🟣 TL", "#9b59b6")    # Tự luận - Tím
        }
        
        for q in qs:
            dang_code = q.get('dang', 4)
            icon_text, color = type_style.get(dang_code, ("⚪ Khác", "#7f8c8d"))
            
            # Tạo hiển thị đẹp: [Dạng] [Mức độ] Nội dung rút gọn
            display_text = f"{icon_text} [{q['level']}] ID:{q['id']} | C{q['chapter']}.B{q['bai']}"
            
            it = QListWidgetItem(display_text)
            it.setToolTip(q['content_tex'][:200]) # Tooltip xem trước nội dung
            it.setData(Qt.ItemDataRole.UserRole, q)
            
            # Set màu chữ
            it.setForeground(QColor(color))
            # Set font đậm cho phần đầu
            font = QFont(); font.setBold(True)
            it.setFont(font)
            
            self.man_lst.addItem(it)
            
        self.man_prev.setText(f"Đã tìm thấy {len(qs)} câu hỏi phù hợp.")

    def save_exam(self):
        self.current_exam = [self.exam_lst.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.exam_lst.count())]
        QMessageBox.information(self,"OK",f"Lưu {len(self.current_exam)} câu")

    # Thay thế hàm upd_mat
    def upd_mat(self):
        # 1. Xác định Danh sách Lớp & Môn cần hiển thị
        target_grades = []
        g_txt = self.mat_g.currentText()
        if "Tổng hợp" in g_txt:
            target_grades = [12, 11, 10] # Ưu tiên lớp 12 lên đầu
        else:
            try: target_grades = [int(g_txt.split()[-1])]
            except: target_grades = [12]

        target_subjs = []
        s_txt = self.mat_s.currentText()
        if "Tất cả" in s_txt:
            target_subjs = ['D', 'H']
        else:
            target_subjs = ['D'] if 'Đại' in s_txt else ['H']

        # 2. Reset bảng & Dropdown chương
        self.mat_tb.setRowCount(0)
        self.mat_chap_filter.blockSignals(True)
        self.mat_chap_filter.clear()
        self.mat_chap_filter.addItem("Hiển thị tất cả", 0)
        
        row_idx = 0
        
        # 3. Duyệt qua từng Lớp -> Từng Môn -> Từng Chương
        for g in target_grades:
            for s in target_subjs:
                if g not in DATA_ID6_2025 or s not in DATA_ID6_2025[g]: continue
                
                chapters = DATA_ID6_2025[g][s]
                subj_name = "Đại" if s == 'D' else "Hình"
                
                # Thêm header phân cách trong bảng cho dễ nhìn
                header_row = self.mat_tb.rowCount()
                self.mat_tb.insertRow(header_row)
                header_item = QTableWidgetItem(f"--- LỚP {g} - {subj_name.upper()} ---")
                header_item.setBackground(QColor("#d35400")) # Màu nền cam đậm
                header_item.setForeground(QColor("white"))
                header_item.setFlags(Qt.ItemFlag.NoItemFlags) # Không cho sửa
                self.mat_tb.setItem(header_row, 0, header_item)
                self.mat_tb.setSpan(header_row, 0, 1, 10) # Merge cells
                row_idx += 1

                for ch_code, lessons in chapters.items():
                    # Thêm chương vào bộ lọc (có prefix lớp để phân biệt)
                    # Value của combobox sẽ là chuỗi "g_s_ch" để lọc chính xác
                    filter_val = f"{g}_{s}_{ch_code}"
                    self.mat_chap_filter.addItem(f"[{g}-{subj_name}] Chương {ch_code}", filter_val)
                    
                    for bai_code, bai_name in lessons.items():
                        self.mat_tb.insertRow(row_idx)
                        
                        # Cột Tên bài: [12D] C1.B1: Tên bài
                        display_name = f"[{g}{s}] C{ch_code}.B{bai_code}: {bai_name}"
                        item_name = QTableWidgetItem(display_name)
                        
                        # [QUAN TRỌNG] Lưu đầy đủ thông tin Lớp/Môn vào metadata của dòng
                        item_data = {'g': g, 's': s, 'ch': ch_code, 'bai': bai_code}
                        item_name.setData(Qt.ItemDataRole.UserRole, item_data)
                        item_name.setToolTip(bai_name)
                        self.mat_tb.setItem(row_idx, 0, item_name)
                        
                        # Các cột nhập liệu (SpinBox)
                        for c in range(1, 10):
                            sb = QSpinBox()
                            sb.setRange(0, 50)
                            sb.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
                            sb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            sb.valueChanged.connect(self.calc_mat_sum)
                            
                            # Màu nền phân biệt
                            if 1 <= c <= 3: sb.setStyleSheet("background-color: #e3f2fd; color: #1565c0;")
                            elif 4 <= c <= 6: sb.setStyleSheet("background-color: #fff3e0; color: #e65100;")
                            else: sb.setStyleSheet("background-color: #f3e5f5; color: #7b1fa2;")
                            
                            self.mat_tb.setCellWidget(row_idx, c, sb)
                        
                        row_idx += 1
        
        self.mat_chap_filter.blockSignals(False)
        self.calc_mat_sum()

    def calc_mat_sum(self):
        """Tính tổng số câu (Bỏ qua các dòng tiêu đề không có Spinbox)"""
        s1 = s2 = s3 = 0
        for r in range(self.mat_tb.rowCount()):
            # Kiểm tra xem dòng này có widget nhập liệu ở cột 1 không
            # Nếu không có (là dòng Header phân cách), thì bỏ qua
            if not self.mat_tb.cellWidget(r, 1):
                continue

            s1 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(1, 4))
            s2 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(4, 7))
            s3 += sum(self.mat_tb.cellWidget(r, c).value() for c in range(7, 10))
            
        self.mat_sum.setText(f"<b>TỔNG SỐ CÂU:</b> "
                             f"P1: <span style='color:blue; font-size:16px'>{s1}</span> | "
                             f"P2: <span style='color:orange; font-size:16px'>{s2}</span> | "
                             f"P3: <span style='color:purple; font-size:16px'>{s3}</span>")

    # Cập nhật hàm gen_mat
    def gen_mat(self):
        self.current_exam = []; self.mat_res.clear()
        
        # Map cột: Cột -> (Dạng, Mức độ)
        col_map = {
            1: (1, 'N'), 2: (1, 'H'), 3: (1, 'V'), # Phần 1 (TN)
            4: (2, 'N'), 5: (2, 'H'), 6: (2, 'V'), # Phần 2 (Đ/S)
            7: (3, 'N'), 8: (3, 'H'), 9: (3, 'V')  # Phần 3 (TLN)
        }
        
        total_qs = 0
        missing = []

        # Duyệt qua TOÀN BỘ dòng trong bảng
        for r in range(self.mat_tb.rowCount()):
            item = self.mat_tb.item(r, 0)
            
            # Bỏ qua dòng Header phân cách (không có metadata)
            if not item: continue
            row_data = item.data(Qt.ItemDataRole.UserRole)
            if not row_data: continue 
            
            # [CẬP NHẬT] Lấy Lớp và Môn từ chính dòng đó
            g = row_data['g']
            s = row_data['s']
            ch = row_data['ch']
            bai = row_data['bai']
            
            for c in range(1, 10):
                # Lấy widget Spinbox
                widget = self.mat_tb.cellWidget(r, c)
                if not widget: continue 
                
                cnt = widget.value()
                if cnt > 0:
                    dang, lev = col_map[c]
                    for _ in range(cnt):
                        # Gọi hàm lấy câu hỏi ngẫu nhiên với đúng thông số của dòng
                        q = self.bk.get_rnd(g, s, ch, bai, lev, dang)
                        
                        if q:
                            self.current_exam.append(q)
                            self.mat_res.addItem(f"Câu {len(self.current_exam)}: [{g}{s}-C{ch}.B{bai}-{lev}] ID:{q['id']}")
                            total_qs += 1
                        else:
                            # Ghi log thiếu
                            missing_info = f"[{g}{s}-C{ch}.B{bai}-{lev}] Dạng {dang}"
                            missing.append(missing_info)
                            self.mat_res.addItem(f"⚠️ THIẾU: {missing_info}")
                            
        if missing:
            QMessageBox.warning(self, "Cảnh báo thiếu câu hỏi", 
                                f"Đã tạo được {total_qs} câu.\nTuy nhiên thiếu {len(missing)} câu so với yêu cầu.\nVui lòng kiểm tra danh sách bên dưới.")
        else:
            QMessageBox.information(self, "Thành công", f"Đã tạo đề hoàn chỉnh gồm {total_qs} câu (Tổng hợp)!")

    def load_ai(self):
        self.ai_lst.clear()
        for i,q in enumerate(self.current_exam):
            it = QListWidgetItem(f"Câu {i+1}: ID:{q['id']}")
            if 'content_tex' not in q: q['content_tex'] = q.get('content', "")
            it.setData(Qt.ItemDataRole.UserRole, q); self.ai_lst.addItem(it)

    def run_ai(self):
        if self.ai_lst.count()==0: return
        self.pd = QProgressDialog("AI Running...", "Cancel", 0, 100, self); self.pd.setWindowModality(Qt.WindowModality.WindowModal)
        base = [self.ai_lst.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.ai_lst.count())]
        self.wk = BatchAIWorker(self.ai, base, self.ai_n.value(), self.ai_c.value())
        self.wk.progress.connect(lambda v,m: (self.pd.setValue(v), self.pd.setLabelText(m)))
        self.wk.finished.connect(self.ai_done); self.wk.start()

    def ai_done(self, res):
        self.pd.close(); self.gen_res = res; self.ai_tr.clear()
        for c, qs in res.items():
            rt = QTreeWidgetItem([f"Đề {c}"]); rt.setData(0, Qt.ItemDataRole.UserRole, {'t':'e','c':c})
            for q in qs:
                ch = QTreeWidgetItem([f"Câu {q['idx']}"]); ch.setData(0, Qt.ItemDataRole.UserRole, {'t':'q','c':c,'i':q['idx']-1})
                rt.addChild(ch)
            self.ai_tr.addTopLevelItem(rt); self.ai_tr.expandAll()

# Tìm và thay thế hàm import_files cũ bằng đoạn này
    # Tìm đến hàm import_files cũ và thay thế bằng hàm này:
    # Sửa trong MainApp
    def import_files(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "Chọn file TeX", "", "TeX (*.tex)")
        if not fs: return

        self.pd_import = QProgressDialog("Đang đọc và phân tích...", "Hủy", 0, 100, self)
        self.pd_import.setWindowModality(Qt.WindowModality.WindowModal)
        self.pd_import.show()

        # Dùng Worker mới
        self.import_worker = ImportWorker(fs)
        self.import_worker.progress.connect(lambda v, m: (self.pd_import.setValue(v), self.pd_import.setLabelText(m)))
        # Kết nối tới hàm xử lý logic mới
        self.import_worker.analysis_done.connect(self.on_analysis_finished)
        self.import_worker.error.connect(lambda err: QMessageBox.warning(self, "Lỗi", err))
        self.import_worker.start()

    def on_analysis_finished(self, questions, images):
        self.pd_import.close()
        
        # 1. Lọc ra các câu thiếu ID6
        missing_id_qs = [q for q in questions if not q.get('id6')]
        
        # 2. Nếu có câu thiếu ID -> Hiện Dialog yêu cầu nhập
        if missing_id_qs:
            msg = f"Phát hiện {len(missing_id_qs)} câu hỏi chưa có ID6 trong file.\nBạn có muốn gán ID ngay bây giờ trước khi nhập kho không?"
            reply = QMessageBox.question(self, "Kiểm tra dữ liệu", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                # Mở Dialog Gán ID với chế độ 'local' và chỉ truyền các câu bị thiếu
                # Lưu ý: Vì missing_id_qs chứa tham chiếu đến các dict trong questions,
                # nên sửa trong Dialog sẽ cập nhật luôn vào questions.
                dlg = ID6AssignDialog(self.bk, self, mode='local', data_list=missing_id_qs)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    # Nếu người dùng bấm Hủy/Đóng dialog mà không bấm "Hoàn tất"
                    if QMessageBox.question(self, "Hủy nhập?", "Bạn đã hủy quá trình gán ID. Bạn có muốn HỦY luôn việc nhập dữ liệu không?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                        return # Hủy toàn bộ
        
        # 3. Tiến hành Nhập vào Database (Lúc này questions đã được điền ID nếu user chịu sửa)
        self.pd_import.setLabelText("Đang lưu vào Cơ sở dữ liệu...")
        self.pd_import.show()
        
        try:
            # Cập nhật thư viện ảnh trước
            self.on_import_finished(0, 0, images) # Tận dụng hàm cũ để lưu ảnh
            
            # Lưu câu hỏi
            added, skipped = self.bk.insert_questions_list(questions)
            
            self.pd_import.close()
            self.load_stats()
            QMessageBox.information(self, "Hoàn tất", f"✅ Đã nhập thành công!\n- Thêm mới: {added}\n- Trùng lặp: {skipped}")
            
        except Exception as e:
            self.pd_import.close()
            QMessageBox.critical(self, "Lỗi Lưu DB", str(e))

    def open_image_manager(self):
        """Mở dialog quản lý hình ảnh"""
        dlg = ImageManagerDialog(self.bk, self)
        dlg.exec()

    # Thêm hàm xử lý khi nhập xong (ngay bên dưới import_files)
    # Sửa lại hàm này trong class MainApp
    def on_import_finished(self, added, skipped, detected_images):
        self.pd_import.close()
        self.load_stats()
        
        # --- LOGIC MỚI: CẬP NHẬT THƯ VIỆN ẢNH ---
        if detected_images:
            lib_path = os.path.join(os.path.dirname(DB_PATH), "image_lib.json")
            current_lib = {}
            
            # 1. Đọc thư viện cũ (nếu có)
            if os.path.exists(lib_path):
                try:
                    with open(lib_path, 'r', encoding='utf-8') as f:
                        current_lib = json.load(f)
                except: pass
            
            # 2. Gộp ảnh mới tìm được vào thư viện (Ưu tiên ảnh mới hoặc giữ cũ tùy bạn)
            # Ở đây ta chỉ cập nhật nếu trong thư viện CHƯA CÓ hoặc link cũ bị hỏng
            count_new_img = 0
            for name, path in detected_images.items():
                # Nếu ảnh chưa có trong thư viện -> Thêm vào
                if name not in current_lib:
                    current_lib[name] = path
                    count_new_img += 1
                # (Tùy chọn) Nếu đã có nhưng là link online thì giữ nguyên, 
                # nếu là path cục bộ khác thì có thể update. Ở đây ta ưu tiên giữ cái cũ.

            # 3. Lưu lại file json
            if count_new_img > 0:
                try:
                    with open(lib_path, 'w', encoding='utf-8') as f:
                        json.dump(current_lib, f, indent=2, ensure_ascii=False)
                    print(f"📸 Đã tự động thêm {count_new_img} đường dẫn ảnh vào thư viện.")
                except Exception as e:
                    print(f"Lỗi lưu thư viện ảnh: {e}")
        # ----------------------------------------

        msg = f"✅ Đã nhập xong!\n\n- Thêm mới: {added} câu\n- Trùng/Bỏ qua: {skipped} câu"
        if detected_images:
            msg += f"\n- Đã phát hiện và lưu vị trí của {len(detected_images)} hình ảnh."
            
        QMessageBox.information(self, "Kết quả Import", msg)

    def load_stats(self):
        """Cập nhật số liệu thống kê nhanh trên màn hình chính"""
        try:
            total, _, _ = self.bk.get_dashboard_stats()
            # Cập nhật Label ở trang chủ (self.stat_lbl)
            if hasattr(self, 'stat_lbl'):
                self.stat_lbl.setText(f"{total:,} câu hỏi")
            
            # Cập nhật Label ở thanh trạng thái dưới cùng (self.lbl_stat)
            if hasattr(self, 'lbl_stat'):
                self.lbl_stat.setText(f"Database: {total:,} questions")
        except Exception as e:
            print(f"Lỗi load stats: {e}")

    def show_id6(self): ID6AssignDialog(self.bk, self).exec(); self.load_stats()
    
    def export_exam(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", "", "TeX (*.tex)")
        if not path: return
        c = []
        if self.generated_exams:
            for k, qs in self.generated_exams.items():
                c.append(f"\\begin{{center}}\\textbf{{MÃ ĐỀ: {k}}}\\end{{center}}")
                for q in qs: c.append(q['content'])
                c.append("\\newpage")
        else:
            c.append("\\begin{center}\\textbf{ĐỀ THI GỐC}\\end{center}")
            for q in self.current_exam: c.append(q['content_tex'])
        with open(path, "w", encoding="utf-8") as f: f.write(LATEX_TEMPLATE + "\n".join(c) + "\n\\end{document}")
        QMessageBox.information(self,"OK","Exported")

    # --- SỬA LỖI: CÁC HÀM NÀY PHẢI NẰM TRONG CLASS MainApp ---
    # --- Dán vào trong class MainApp ---
    
    def mix_and_export(self):
        """Hàm gọi dialog cấu hình và thực hiện trộn đề"""
        # Nếu chưa có câu hỏi nào trong danh sách "Đề đang soạn", thử lấy từ tab Ma trận hoặc list hiện tại
        if not self.current_exam:
            # [FIX] Thử lấy từ Tree Widget (Soạn thủ công) nếu danh sách hiện tại trống
            questions = self.exam_lst.get_all_questions()
            
            if questions:
                self.current_exam = questions
            else:
                 QMessageBox.warning(self, "Trống", "Danh sách câu hỏi trống! Vui lòng soạn hoặc chọn câu hỏi trước.")
                 return

        dialog = MixConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            mixer = ExamMixer()
            try:
                # Gọi trộn đề
                self.generated_exams = mixer.mix_exam(self.current_exam, data['num'], data['start'])
                
                if QMessageBox.question(self, "Thành công", 
                    f"Đã trộn xong {data['num']} mã đề.\nXuất file TeX ngay?") == QMessageBox.StandardButton.Yes:
                    self.export_mixed_tex()
            except Exception as e:
                import traceback
                traceback.print_exc() 
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi trộn: {str(e)}")    

    def export_mixed_tex(self):
        """Xuất các đề đã trộn ra file TeX kèm bảng đáp án"""
        if not hasattr(self, 'generated_exams') or not self.generated_exams:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Lưu Đề Trộn", "De_Tron.tex", "TeX Files (*.tex)")
        if not path: return
        
        full_content = [LATEX_TEMPLATE]
        all_keys = {} # Lưu đáp án tất cả mã đề

        for code, questions in self.generated_exams.items():
            full_content.append(f"\\newpage")
            full_content.append(f"\\begin{{center}}\\textbf{{MÃ ĐỀ: {code}}}\\end{{center}}")
            full_content.append(f"\\setcounter{{ex}}{{0}}") 
            
            exam_keys = []
            for idx, q in enumerate(questions):
                full_content.append(q['content_tex'])
                # Lấy key đã trộn (nếu có), nếu không có thì lấy mặc định
                k = q.get('final_key', '?')
                exam_keys.append(f"{idx+1}.{k}")
            
            all_keys[code] = exam_keys
        
        # --- Tạo bảng đáp án tổng hợp cuối file ---
        full_content.append("\\newpage")
        full_content.append("\\begin{center}\\textbf{BẢNG ĐÁP ÁN CÁC MÃ ĐỀ}\\end{center}")
        
        for code, keys in all_keys.items():
            full_content.append(f"\\noindent\\textbf{{Mã {code}:}} " + " | ".join(keys) + "\\\\[0.5cm]")

        full_content.append("\\end{document}")
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(full_content))
            QMessageBox.information(self, "Xong", f"Đã xuất file tại: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi file", str(e))

    def open_file_cleaner(self):
        """Mở công cụ làm sạch file và check lỗi"""
        dlg = FileCleanerDialog(self.ai, self)
        dlg.exec()

    # Trong class MainApp
    def resolve_external_images(self, questions, tex_path):
        """Hàm helper: Quét và map lại đường dẫn ảnh cho file TeX ngoài"""
        all_imgs = set()
        for q in questions:
            content = q.get('content_tex', '')
            # Regex tìm \includegraphics{...} hoặc \includegraphics[...]{...}
            matches = re.findall(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}", content)
            for m in matches:
                all_imgs.add(m.strip())
        
        if not all_imgs: return questions

        # Mở Dialog để user confirm (luôn mở nếu có ảnh để đảm bảo tính đúng đắn)
        tex_dir = os.path.dirname(tex_path)
        dlg = ImageMappingDialog(list(all_imgs), tex_dir, self)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            final_map = dlg.mapping
            # Update questions
            for q in questions:
                # Chỉ update những câu có chứa ảnh đã được map
                # (Duyệt qua map để replace)
                content = q.get('content_tex', '')
                for img_name, abs_path in final_map.items():
                    # Pattern: \includegraphics[...]{img_name} hoặc \includegraphics{img_name}
                    pattern = r"(\\includegraphics(?:\[.*?\])?)\{" + re.escape(img_name) + r"\}"
                    if re.search(pattern, content):
                        content = re.sub(pattern, r"\1{" + abs_path + "}", content)
                q['content_tex'] = content
        
        return questions

    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        # Không chạy cleanup_cache đồng bộ nữa để tránh treo
        
        if hasattr(self, 'web_thread') and self.web_thread.isRunning():
            # Stop thread với timeout (đã xử lý trong WebServerThread.stop)
            self.web_thread.stop()
            
        event.accept()

    def toggle_web_server(self):
        """Bật/Tắt Web Server - Fix lỗi tự chạy khi chưa bấm OK"""
        if self.btn_web.isChecked():
            # TẠO MENU LỰA CHỌN NGUỒN ĐỀ
            menu = QMenu(self)
            menu.setStyleSheet("QMenu { font-size: 14px; padding: 5px; } QMenu::item { padding: 10px 20px; }")
            
            act_sys = menu.addAction("1. Lấy đề từ hệ thống (Tab hiện tại)")
            act_ext = menu.addAction("2. Lấy đề từ bên ngoài (File TeX)")
            
            # Hiển thị menu ngay dưới nút bấm
            action = menu.exec(self.btn_web.mapToGlobal(QPoint(0, self.btn_web.height())))
            
            questions = []
            
            if action == act_sys:
                # 1. LẤY DỮ LIỆU TỪ TAB ĐANG MỞ
                questions, src = self.get_current_exam_questions()
                if not questions:
                    self.btn_web.setChecked(False)
                    QMessageBox.warning(self, "Chưa có câu hỏi", 
                        f"Tab '{src}' chưa có dữ liệu.\nVui lòng tạo đề trước khi bật thi Online.")
                    return

            elif action == act_ext:
                # 2. LẤY TỪ FILE BÊN NGOÀI
                path, _ = QFileDialog.getOpenFileName(self, "Chọn file TeX đề thi", "", "TeX Files (*.tex)")
                if path:
                    # Parse file để lấy câu hỏi và đáp án
                    try:
                        parsed_qs, _ = self.bk.analyze_tex_file(path)
                        if parsed_qs:
                            # [MỚI] Xử lý link ảnh
                            questions = self.resolve_external_images(parsed_qs, path)
                            QMessageBox.information(self, "Đã đọc file", f"Đã tìm thấy {len(questions)} câu hỏi từ file.")
                        else:
                            self.btn_web.setChecked(False)
                            QMessageBox.warning(self, "Lỗi", "Không tìm thấy câu hỏi nào trong file (cần có môi trường ex/bt)!")
                            return
                    except Exception as e:
                        self.btn_web.setChecked(False)
                        QMessageBox.critical(self, "Lỗi đọc file", str(e))
                        return
                else:
                    self.btn_web.setChecked(False)
                    return
            else:
                # Hủy bỏ (click ra ngoài)
                self.btn_web.setChecked(False)
                return

            # [FIX QUAN TRỌNG] CHỈ CHẠY TIẾP KHI NGƯỜI DÙNG BẤM OK
            dlg = ExamConfigDialog(questions, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                # Lấy cấu hình đã chốt
                config = dlg.get_config()
                final_qs = config['questions']
                title = config['title']
                duration = config['time']
                ext_tex = config.get('external_tex')

                # KHỞI ĐỘNG SERVER (NẾU CHƯA)
                if not hasattr(self, 'web_thread'):
                    self.web_thread = WebServerThread(DB_PATH)
                
                if not self.web_thread.isRunning():
                    self.web_thread.start()
                    QThread.msleep(200)

                # CHẠY WORKER VỚI DỮ LIỆU ĐÃ DUYỆT
                self.pd_prep = QProgressDialog("Đang khởi tạo phòng thi ảo...", "Hủy", 0, 0, self)
                self.pd_prep.setWindowModality(Qt.WindowModality.WindowModal)
                self.pd_prep.show()

                self.prep_worker = ExamPreparerWorker(final_qs, title, duration, ext_tex, num_variants=config.get('num_variants', 1))
                self.prep_worker.progress.connect(lambda s: self.pd_prep.setLabelText(s))
                self.prep_worker.finished.connect(self.on_exam_prepared)
                self.prep_worker.start()
            
            else:
                # Nếu bấm Cancel/Đóng -> Hủy toàn bộ, nhả nút
                self.btn_web.setChecked(False)
                return

        else:
            # Tắt Server
            if hasattr(self, 'web_thread') and self.web_thread.isRunning():
                self.web_thread.stop()
            
            self.btn_web.setText("🌍 Bật Thi Online")
            self.btn_web.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); color: white;")
            QMessageBox.information(self, "Đã tắt", "Đã đóng phòng thi ảo.")

    def on_exam_prepared(self, success, data):
        self.pd_prep.close()
        
        if success:
            # 1. Nạp dữ liệu vào Server (Chưa phát vội)
            self.web_thread.set_exam_data(data)
            
            # 2. Mở màn hình GIÁM SÁT
            # (Lưu ý: dùng self.monitor_dlg để giữ reference, tránh bị garbage collector xóa)
            self.monitor_dlg = ExamMonitorDialog(self.web_thread, self)
            self.monitor_dlg.show() 

            # 3. Đổi màu nút trên App để biết Server đang chạy
            port = self.web_thread.port
            ip = self.web_thread.ip_address
            self.btn_web.setText(f"📡 {ip}:{port}")
            self.btn_web.setStyleSheet("background-color: #2ecc71; color: white;")
            
        else:
            self.btn_web.setChecked(False)
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo đề: {data.get('error')}")

    def open_classroom_dialog(self):
        """Mở dialog đăng bài lên Classroom (Hỗ trợ Google Forms)"""
        # 1. Lấy danh sách câu hỏi ĐẦY ĐỦ (Object) thay vì text gộp
        questions_objs = []
        if self.generated_exams:
            # Nếu đã trộn đề, lấy mã đề đầu tiên để làm mẫu upload
            first_code = list(self.generated_exams.keys())[0]
            questions_objs = self.generated_exams[first_code]
        elif self.current_exam:
            # Nếu chưa trộn, lấy đề gốc đang soạn
            questions_objs = self.current_exam
        else:
            QMessageBox.warning(self, "Trống", "Chưa có đề thi nào được chọn!")
            return

        # 2. Mở Dialog (Truyền list object vào - QUAN TRỌNG)
        # Class ClassroomDialog mới sẽ nhận danh sách này để xử lý từng câu
        dlg = ClassroomDialog(questions_objs, self) 
        dlg.exec()

    def open_history(self):
        """Mở lịch sử thi"""
        dlg = HistoryDialog(self.bk, self)
        dlg.exec()

    def open_help(self):
        """Mở bảng hướng dẫn sử dụng"""
        dlg = HelpDialog(self)
        dlg.exec()

    # [MỚI] Cập nhật thống kê số lượng câu hỏi trong đề đang soạn
    def update_exam_stats(self):
        """Cập nhật thống kê dựa trên dữ liệu trong Tree"""
        # Lấy toàn bộ câu hỏi từ hàm tiện ích của Tree
        questions = self.exam_lst.get_all_questions()
        count = len(questions)
        
        types = {1: 0, 2: 0, 3: 0, 4: 0}
        for q in questions:
            d = q.get('dang', 4)
            types[d] = types.get(d, 0) + 1
            
        stats_text = f"TỔNG: {count} câu | P1(TN): {types[1]} | P2(Đ/S): {types[2]} | P3(TLN): {types[3]}"
        self.lbl_exam_stats.setText(stats_text)

    # [MỚI] Mở hộp thoại xuất đề nâng cao
    def open_advanced_export(self):
        # [FIX] Sử dụng get_all_questions() thay vì count() vì exam_lst giờ là Tree
        questions = self.exam_lst.get_all_questions()
        
        if not questions:
            QMessageBox.warning(self, "Trống", "Danh sách câu hỏi trống!")
            return
            
        dlg = AdvancedExportDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            config = dlg.get_config()
            self.process_advanced_export(config)

    # [MỚI] Xử lý logic xuất file và biên dịch
    def process_advanced_export(self, config):
        # 1. Lấy danh sách câu hỏi
        questions = self.exam_lst.get_all_questions()

        if not questions:
            QMessageBox.warning(self, "Lỗi", "Chưa có câu hỏi nào!")
            return
        
        # 2. Xử lý nội dung (Đảo đáp án nếu cần)
        final_content = []
        mixer = ExamMixer()
        keys_list = []
        
        for idx, q in enumerate(questions):
            tex = q.get('content_tex', '')
            key = "?"
            # Logic đảo đề...
            if config['shuffle'] and q.get('dang') == 1:
                tex, key = mixer.permute_content(tex)
            else:
                match = re.search(r"\[KEY:\s*([A-D])\]", tex)
                if match: key = match.group(1)
            
            keys_list.append(f"{idx+1}.{key}")
            
            if not config['show_sol']:
                tex = re.sub(r"\\loigiai\{.*?\}", "", tex, flags=re.DOTALL)
            
            final_content.append(tex)

        # 3. Chuẩn bị Template
        main_content = LATEX_TEMPLATE # Mặc định
        if config['template'] and os.path.exists(config['template']):
            try:
                with open(config['template'], 'r', encoding='utf-8') as f:
                    main_content = f.read()
            except Exception as e:
                QMessageBox.warning(self, "Lỗi đọc Template", f"Không đọc được file main. Dùng mặc định.\nLỗi: {e}")

        # 4. Ghép nội dung
        body = "\n".join(final_content)
        
        # Thêm bảng đáp án nếu cần
        if config['table']:
            key_table = "\n\\newpage\n\\begin{center}\\textbf{BẢNG ĐÁP ÁN}\\end{center}\n"
            key_table += "\\begin{center}\\begin{tabular}{|" + "c|"*10 + "} \\hline\n"
            
            row = []
            for k in keys_list:
                row.append(k)
                if len(row) == 10:
                    key_table += " & ".join(row) + " \\\\ \\hline\n"
                    row = []
            if row:
                key_table += " & ".join(row) + " \\\\ \\hline\n"
            
            key_table += "\\end{tabular}\\end{center}"
            body += key_table

        # Template và Save file (Code cũ)
        main_content = LATEX_TEMPLATE
        if config['template'] and os.path.exists(config['template']):
            try:
                with open(config['template'], 'r', encoding='utf-8') as f: main_content = f.read()
            except: pass

        full_tex = main_content.replace("__CONTENT__", body) if "__CONTENT__" in main_content else main_content + "\n" + body
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file", "De_Thi.tex", "TeX Files (*.tex)")
        if not save_path: return
        
        try:
            with open(save_path, "w", encoding="utf-8") as f: f.write(full_tex)
            if config['compile']:
                msg, pdf_path = PDFCompiler.compile_tex_to_pdf(full_tex, os.path.basename(save_path).replace(".tex",""))
                if pdf_path and os.path.exists(pdf_path):
                    final_pdf = save_path.replace(".tex", ".pdf")
                    shutil.move(pdf_path, final_pdf)
                    open_file_or_url(final_pdf)
                else:
                    QMessageBox.warning(self, "Lỗi biên dịch", msg)
            else:
                QMessageBox.information(self, "Thành công", f"Đã xuất file: {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # Thêm vào trong class MainApp
    def show_classroom_menu(self):
        """Mở Bảng điều khiển Google Classroom (Thay thế Menu cũ)"""
        # Instantiate Control Panel
        panel = ClassroomControlPanel(
            self, 
            callback_exam=self.create_online_classroom_exam, 
            callback_homework=self.open_classroom_dialog
        )
        panel.exec()

    def create_online_classroom_exam(self):
        # TẠO MENU LỰA CHỌN NGUỒN ĐỀ
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { font-size: 14px; padding: 5px; } QMenu::item { padding: 10px 20px; }")
        
        act_sys = menu.addAction("1. Lấy đề từ hệ thống (Tab hiện tại)")
        act_ext = menu.addAction("2. Lấy đề từ bên ngoài (File TeX)")
        
        # Hiển thị menu ngay tại vị trí con trỏ chuột
        action = menu.exec(QCursor.pos())
        
        questions = []
        
        if action == act_sys:
            # 1. LẤY DỮ LIỆU TỪ TAB ĐANG MỞ
            questions, src = self.get_current_exam_questions()
            if not questions:
                return QMessageBox.warning(self, "Chưa có câu hỏi", 
                    f"Tab '{src}' chưa có dữ liệu.\nVui lòng tạo đề trước khi bật thi Online.")

        elif action == act_ext:
            # 2. LẤY TỪ FILE BÊN NGOÀI
            path, _ = QFileDialog.getOpenFileName(self, "Chọn file TeX đề thi", "", "TeX Files (*.tex)")
            if path:
                # Parse file để lấy câu hỏi và đáp án
                try:
                    parsed_qs, _ = self.bk.analyze_tex_file(path)
                    if parsed_qs:
                        # [MỚI] Xử lý link ảnh
                        parsed_qs = self.resolve_external_images(parsed_qs, path)
                        
                        # Preprocess: Loại bỏ trích dẫn nguồn đề sau số câu
                        # Regex tìm: \begin{ex}[...] -> \begin{ex}
                        import re
                        for q in parsed_qs:
                            if 'content_tex' in q:
                                # Xóa optional argument của ex/bt/vd
                                q['content_tex'] = re.sub(r"(\\begin\s*\{(?:ex|bt|vd)\})\s*\[.*?\]", r"\1", q['content_tex'], flags=re.DOTALL)
                        
                        questions = parsed_qs
                        QMessageBox.information(self, "Đã đọc file", f"Đã tìm thấy {len(questions)} câu hỏi từ file.\n(Đã tự động ẩn trích dẫn nguồn đề)")
                    else:
                        QMessageBox.warning(self, "Lỗi", "Không tìm thấy câu hỏi nào trong file (cần có môi trường ex/bt)!")
                        return
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi đọc file", str(e))
                    return
            else:
                return
        else:
            # Hủy bỏ (click ra ngoài)
            return

        # 2. Hộp thoại Cấu hình thi (Thời gian, Tiêu đề)
        dlg = ExamConfigDialog(questions, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            config = dlg.get_config()
            
            # 3. Hộp thoại Đăng Classroom
            cls_dlg = ClassroomDialog([], self)
            cls_dlg.btn_upload.setVisible(True); cls_dlg.btn_upload.setText("🚀 BẮT ĐẦU TỔ CHỨC THI")
            
            # Ngắt kết nối cũ để tránh lỗi click nhiều lần
            try: cls_dlg.btn_upload.clicked.disconnect()
            except: pass
            
            # Sự kiện nút bấm
            cls_dlg.btn_upload.clicked.connect(lambda: cls_dlg.accept() if cls_dlg.txt_title.text().strip() else QMessageBox.warning(cls_dlg, "Thiếu", "Nhập tên bài!"))
            
            if cls_dlg.exec() == QDialog.DialogCode.Accepted:
                course_id = cls_dlg.cb_courses.currentData()
                # Ưu tiên lấy tên bài từ hộp thoại Classroom, nếu không thì lấy từ cấu hình thi
                exam_title = cls_dlg.txt_title.text().strip() or config['title']
                
                # Hiển thị thanh tiến trình
                self.pd_prep = QProgressDialog("Đang khởi tạo Server...", "Hủy", 0, 0, self)
                self.pd_prep.setWindowModality(Qt.WindowModality.WindowModal)
                self.pd_prep.show()
                
                # Khởi tạo Server nếu chưa có
                if not hasattr(self, 'web_thread'): self.web_thread = WebServerThread(DB_PATH)
                
                # Chạy Worker biên dịch PDF (Không truyền external_tex để dùng Main hệ thống)
                self.prep_worker = ExamPreparerWorker(config['questions'], exam_title, config['time'], num_variants=config.get('num_variants', 1))
                
                # --- HÀM XỬ LÝ KHI PDF ĐÃ SẴN SÀNG ---
                def on_pdf_ready(success, data):
                    if not success:
                        self.pd_prep.close()
                        QMessageBox.critical(self, "Lỗi tạo đề", data.get('error', 'Lỗi không xác định'))
                        return

                    # Lưu thông tin lớp học vào data để dùng cho việc chấm điểm sau này
                    data['courseId'] = course_id
                    
                    # [MỚI] Fetch danh sách học sinh để inject vào Web UI
                    try:
                        gg = GoogleManagerFull(); gg.authenticate()
                        data['students'] = gg.get_students(course_id)
                        print(f"Đã tải {len(data['students'])} học sinh vào đề thi.")
                    except Exception as e:
                        print(f"Lỗi tải danh sách học sinh: {e}")
                        data['students'] = []

                    # --- HÀM XỬ LÝ KHI SERVER ĐÃ ONLINE ---
                    def on_server_online(public_url):
                        if not public_url: 
                            self.pd_prep.close()
                            return

                        # 1. Tạo Mã Đề & Link Riêng
                        import time
                        exam_id = f"de-{int(time.time())}" # VD: de-1706...
                        exam_url = f"{public_url}/exam/{exam_id}"
                        
                        self.pd_prep.setLabelText(f"Server OK!\nLink: {exam_url}\nĐang gửi vào Classroom...")
                        
                        try:
                            # 2. Đăng bài lên Google Classroom
                            gg = GoogleManagerFull(); gg.authenticate()
                            
                            link_share = {'link': {'url': exam_url, 'title': f"🔴 BÀI THI: {exam_title}"}}
                            body = {
                                'title': exam_title,
                                'description': f"Link bài thi: {exam_url}\nThời gian: {config['time']} phút.",
                                'workType': 'ASSIGNMENT', 'state': 'PUBLISHED', 'maxPoints': 10, 
                                'materials': [link_share]
                            }
                            # Gửi API tạo bài tập
                            res = gg.service_class.courses().courseWork().create(courseId=course_id, body=body).execute()
                            
                            # 3. Cập nhật ID bài tập và Lưu File
                            data['courseWorkId'] = res['id']
                            data['examId'] = exam_id
                            
                            # [QUAN TRỌNG] Lưu file riêng thay vì biến chung
                            self.web_thread.save_exam_file(exam_id, data)

                            self.pd_prep.close()
                            QMessageBox.information(self, "Thành công", f"Đã tạo bài thi!\nLink vĩnh viễn: {exam_url}")
                            
                            # Mở màn hình giám sát
                            self.monitor_dlg = ExamMonitorDialog(self.web_thread, self)
                            self.monitor_dlg.show()
                            
                        except Exception as e:
                            self.pd_prep.close()
                            QMessageBox.critical(self, "Lỗi Classroom", str(e))

                    # Kết nối tín hiệu Server
                    try: self.web_thread.server_ready.disconnect()
                    except: pass
                    self.web_thread.server_ready.connect(on_server_online)
                    
                    # Kết nối tín hiệu chấm điểm
                    try: self.web_thread.result_received.disconnect()
                    except: pass
                    self.web_thread.result_received.connect(self.on_student_submit)

                    # Bật Server (Nếu chưa chạy)
                    if not self.web_thread.isRunning():
                        self.web_thread.start()
                    else:
                        # Nếu đang chạy, tái sử dụng URL cũ
                        if self.web_thread.public_url:
                            on_server_online(self.web_thread.public_url)

                # Kết nối Worker
                self.prep_worker.finished.connect(on_pdf_ready)
                self.prep_worker.start()

    # --- THÊM HÀM NÀY VÀO CLASS MainApp ---
    def get_current_exam_questions(self):
        """
        Lấy danh sách câu hỏi hiện tại dựa trên Tab đang mở.
        Trả về: (list_questions, source_type)
        """
        current_idx = self.stack.currentIndex()
        questions = []
        source = ""

        # Trường hợp 1: Đang ở Tab "Soạn đề thủ công" (Index 1)
        if current_idx == 1: 
            # Lấy từ TreeWidget (danh sách bên phải)
            if hasattr(self.exam_lst, 'get_all_questions'):
                questions = self.exam_lst.get_all_questions()
            source = "manual"
        
        # Trường hợp 2: Đang ở Tab "Ma trận" (Index 2) hoặc có biến lưu tạm
        elif hasattr(self, 'current_exam') and self.current_exam:
            questions = self.current_exam
            source = "matrix"

        # Trường hợp 3: Đang ở Tab "AI" (Index 3)
        elif current_idx == 3:
            if hasattr(self, 'gen_res') and self.gen_res:
                # Lấy mã đề đầu tiên
                first_code = list(self.gen_res.keys())[0]
                ai_qs = self.gen_res[first_code]
                converted = []
                for q in ai_qs:
                    converted.append({
                        'id': q['idx'],
                        'content_tex': q['content'],
                        'key': q['key'],
                        'dang': q.get('dang', 4)
                    })
                questions = converted
                source = "ai_generated"
            
        # Nếu không tìm thấy ở tab hiện tại nhưng danh sách soạn thảo có dữ liệu
        if not questions and hasattr(self.exam_lst, 'get_all_questions'):
            # Fallback: Lấy từ tab soạn đề nếu các chỗ khác rỗng
            temp = self.exam_lst.get_all_questions()
            if temp:
                questions = temp
                source = "manual_fallback"

        return questions, source
    
    # --- CẬP NHẬT HÀM on_student_submit TRONG MainApp ---
    def on_student_submit(self, data):
        """Xử lý khi học sinh nộp bài"""
        # data thường có dạng: {'name': 'Nguyen Van A', 'score': 8.5, 'detail': ...}
        name = data.get('name', 'Unknown')
        score = float(data.get('score', 0))
        
        # 1. Logic cũ: Hiển thị thông báo/Cập nhật bảng điểm
        msg = f"📩 {name} vừa nộp bài! Điểm: {score}"
        self.statusBar().showMessage(msg, 5000)
        
        # 2. [MỚI] Logic Sync Google Classroom
        # Kiểm tra xem người dùng có đang chọn lớp/bài tập để đồng bộ không
        if hasattr(self, 'tab_classroom') and self.cb_courses.currentData() and self.cb_assignments.currentData():
            
            # Tìm email của học sinh này (vì Classroom cần Email, nhưng Web trả về Tên)
            student_email = None
            
            # Cách 1: Nếu Web trả về email (Tốt nhất)
            if 'email' in data and data['email']:
                student_email = data['email']
            
            # Cách 2: Tìm trong danh sách lớp đang load (Fallback)
            elif self.current_students:
                for s in self.current_students:
                    if s['name'] == name:
                        student_email = s['email']
                        break
            
            # Tiến hành đẩy điểm
            if student_email:
                print(f"🔄 Đang đồng bộ điểm cho {student_email}...")
                
                # Chạy trong thread riêng để không đơ App
                import threading
                def run_sync():
                    try:
                        course_id = self.cb_courses.currentData()
                        assign_id = self.cb_assignments.currentData()
                        self.gc_manager.push_grade(course_id, assign_id, student_email, score)
                        print(f"✅ Đã đồng bộ điểm lên Classroom: {name} - {score}")
                    except Exception as e:
                        print(f"❌ Lỗi đồng bộ Classroom: {e}")
                        
                threading.Thread(target=run_sync, daemon=True).start()
            else:
                print(f"⚠️ Không tìm thấy Email cho học sinh {name}, bỏ qua đồng bộ.")
    # -----------------------------------------------------

# --- CHÈN VÀO CUỐI CLASS MAINAPP ---
    
    def load_classroom_courses(self):
        try:
            courses = self.gc_manager.get_courses()
            self.cb_courses.clear()
            for c in courses:
                # Lưu ID vào data của item combo box
                self.cb_courses.addItem(c['name'], userData=c['id'])
            QMessageBox.information(self, "Thành công", f"Đã tải {len(courses)} lớp học.")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải lớp: {str(e)}")

    def sync_students_to_db(self):
        """Lấy danh sách HS từ Classroom và lưu vào biến toàn cục/DB để dùng khi thi"""
        course_id = self.cb_courses.currentData()
        if not course_id: return

        try:
            students = self.gc_manager.get_students(course_id)
            self.current_students = students # Lưu vào biến class
            
            # CẬP NHẬT DATABASE HOẶC FILE CẤU HÌNH
            # Giả sử bạn đang dùng SQLite table 'students' (nếu chưa có thì tạo)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS students (email TEXT PRIMARY KEY, name TEXT, uid TEXT)")
            cursor.execute("DELETE FROM students") # Xóa danh sách cũ (làm mới theo lớp)
            
            count = 0
            for s in students:
                cursor.execute("INSERT OR REPLACE INTO students (email, name, uid) VALUES (?, ?, ?)", 
                               (s['email'], s['name'], s['id']))
                count += 1
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Đồng bộ xong", 
                                    f"Đã cập nhật {count} học sinh.\n"
                                    "Khi mở Server thi, danh sách này sẽ được dùng.")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Lỗi đồng bộ: {str(e)}")

    def load_classroom_assignments(self):
        course_id = self.cb_courses.currentData()
        if not course_id: return
        try:
            assigns = self.gc_manager.get_assignments(course_id)
            self.cb_assignments.clear()
            for a in assigns:
                self.cb_assignments.addItem(a['title'], userData=a['id'])
        except Exception as e: pass
    # -----------------------------------

    # --- [CHÈN VÀO TRƯỚC CLASS MAINAPP] ---
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import threading

class AnalysisTab(QWidget):
    # Signals for thread communication
    ai_finished = pyqtSignal(str)
    ai_error = pyqtSignal(str)

    def __init__(self, db_path, ai_engine):
        super().__init__()
        self.db_path = db_path
        self.ai_engine = ai_engine
        self.current_id = None

        # Connect signals
        self.ai_finished.connect(self.on_ai_finished)
        self.ai_error.connect(self.on_ai_error)

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- CỘT TRÁI: DANH SÁCH & BIỂU ĐỒ ---
        left_layout = QVBoxLayout()
        
        # Bảng danh sách
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Học sinh", "Điểm", "Ngày nộp", "ID"])
        self.table.hideColumn(3) # Ẩn cột ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.cellClicked.connect(self.on_row_click)
        
        btn_load = QPushButton("🔄 Tải dữ liệu mới nhất")
        btn_load.clicked.connect(self.load_data)
        
        # Biểu đồ
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        left_layout.addWidget(QLabel("<b>📋 Danh sách bài thi</b>"))
        left_layout.addWidget(self.table, 2)
        left_layout.addWidget(btn_load)
        left_layout.addWidget(QLabel("<b>📊 Phổ điểm</b>"))
        left_layout.addWidget(self.canvas, 1)
        
        # --- CỘT PHẢI: AI PHÂN TÍCH ---
        right_layout = QVBoxLayout()
        group_ai = QGroupBox("🤖 Trợ lý AI Phân Tích & Gợi ý")
        ai_inner = QVBoxLayout(group_ai)
        
        self.lbl_status = QLabel("Chọn học sinh để xem chi tiết...")
        self.lbl_status.setStyleSheet("color: #d35400; font-weight: bold;")
        
        self.txt_feedback = QTextEdit()
        self.txt_feedback.setPlaceholderText("AI sẽ phân tích lỗ hổng kiến thức tại đây...")
        self.txt_feedback.setReadOnly(True)
        
        self.btn_ai = QPushButton("✨ Phân tích lỗi sai với AI")
        self.btn_ai.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 8px;")
        self.btn_ai.setEnabled(False)
        self.btn_ai.clicked.connect(self.run_ai)
        
        ai_inner.addWidget(self.lbl_status)
        ai_inner.addWidget(self.txt_feedback)
        ai_inner.addWidget(self.btn_ai)
        
        right_layout.addWidget(group_ai)
        
        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 6)
        
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            # [FIX] Rename timestamp -> submitted_at, detail_json -> detail
            cur.execute("SELECT id, student_name, score, submitted_at, detail, ai_feedback FROM exam_results ORDER BY id DESC LIMIT 100")
            self.rows = cur.fetchall()
            conn.close()
            
            self.table.setRowCount(0)
            scores = []
            for r in self.rows:
                idx = self.table.rowCount()
                self.table.insertRow(idx)
                self.table.setItem(idx, 0, QTableWidgetItem(str(r[1])))
                self.table.setItem(idx, 1, QTableWidgetItem(str(r[2])))
                self.table.setItem(idx, 2, QTableWidgetItem(str(r[3])))
                self.table.setItem(idx, 3, QTableWidgetItem(str(r[0])))
                scores.append(r[2])
            
            # Vẽ biểu đồ
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            if scores:
                ax.hist(scores, bins=[0,2,4,6,8,10], rwidth=0.9, color='#3498db')
                ax.set_title(f"Trung bình: {sum(scores)/len(scores):.1f} điểm")
            self.canvas.draw()
            
        except Exception as e:
            print(f"Load error: {e}")

    def on_row_click(self, row, col):
        id_item = self.table.item(row, 3)
        if not id_item: return
        self.current_id = int(id_item.text())
        
        # Tìm data trong cache
        record = next((r for r in self.rows if r[0] == self.current_id), None)
        if record:
            self.lbl_status.setText(f"Đang xem: {record[1]} ({record[2]} điểm)")
            self.btn_ai.setEnabled(True)
            self.current_json = record[4]
            # Nếu có feedback cũ thì hiện luôn
            if record[5]: self.txt_feedback.setText(record[5])
            else: self.txt_feedback.clear()

    def on_ai_finished(self, msg):
        """Update UI when AI finishes"""
        self.txt_feedback.setText(msg)
        self.btn_ai.setText("✨ Phân tích xong")
        self.btn_ai.setEnabled(True)

    def on_ai_error(self, err):
        """Handle AI error"""
        self.txt_feedback.setText(f"Lỗi: {err}")
        self.btn_ai.setEnabled(True)

    def run_ai(self):
        self.btn_ai.setEnabled(False)
        self.btn_ai.setText("⏳ Đang phân tích...")
        
        # Chạy luồng riêng
        t = threading.Thread(target=self._ai_worker)
        t.daemon = True
        t.start()

    def _ai_worker(self):
        try:
            details = json.loads(self.current_json)
            wrong = [d for d in details if not d['is_correct']]
            
            if not wrong:
                msg = "Học sinh làm đúng 100%. Không có lỗi sai!"
            else:
                prompt = f"Học sinh làm sai các câu sau: {json.dumps(wrong, ensure_ascii=False)}. Hãy phân tích lỗ hổng kiến thức và đưa ra lời khuyên ôn tập ngắn gọn."
                # Gọi engine AI của bạn
                if hasattr(self.ai_engine, 'generate_content'):
                    msg = self.ai_engine.generate_content(prompt).text
                else:
                    msg = "Lỗi: Không tìm thấy AI Engine."
            
            # Update DB
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE exam_results SET ai_feedback = ? WHERE id = ?", (msg, self.current_id))
            conn.commit()
            conn.close()
            
            # Emit signal to update UI safely
            self.ai_finished.emit(msg)
            
        except Exception as e:
            self.ai_error.emit(str(e))
# ----------------------------------------------
# =============================================================================
# AI CLONER - ĐÃ TÁCH RA KHỎI MAINAPP
# =============================================================================
class AIClonerDialog(QDialog):
    """Dialog tạo biến thể câu hỏi bằng AI"""
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
        header = QLabel("🤖 AI TẠO BIẾN THỂ CÂU HỎI")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #8e44ad; padding: 10px;")
        layout.addWidget(header)
        
        group_original = QGroupBox("📝 Câu hỏi gốc:")
        original_layout = QVBoxLayout(group_original)
        self.original_text = QTextEdit()
        self.original_text.setPlainText(self.base_question.get('content_tex', ''))
        self.original_text.setMaximumHeight(150)
        self.original_text.setReadOnly(True)
        original_layout.addWidget(self.original_text)
        layout.addWidget(group_original)
        
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Số lượng biến thể:"))
        self.num_spin = QSpinBox()
        self.num_spin.setRange(1, 10)
        self.num_spin.setValue(5)
        control_layout.addWidget(self.num_spin)
        
        self.btn_generate = QPushButton("🤖 Tạo biến thể")
        self.btn_generate.clicked.connect(self.generate_variants)
        self.btn_generate.setStyleSheet("background-color: #8e44ad; color: white; padding: 10px;")
        control_layout.addWidget(self.btn_generate)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        group_results = QGroupBox("📋 Kết quả:")
        results_layout = QVBoxLayout(group_results)
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_variant_selected)
        results_layout.addWidget(self.results_list)
        
        self.variant_preview = QTextEdit()
        self.variant_preview.setMaximumHeight(200)
        self.variant_preview.setReadOnly(True)
        results_layout.addWidget(QLabel("Xem trước:"))
        results_layout.addWidget(self.variant_preview)
        layout.addWidget(group_results)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Lưu vào ngân hàng")
        btn_save.clicked.connect(self.save_to_bank)
        btn_save.setStyleSheet("background-color: #27ae60;")
        
        btn_use = QPushButton("➡️ Dùng trong đề")
        btn_use.clicked.connect(self.use_in_exam)
        btn_use.setStyleSheet("background-color: #3498db;")
        
        btn_close = QPushButton("❌ Đóng")
        btn_close.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_use)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
    
    def generate_variants(self):
        if not self.ai_engine.is_ready:
            QMessageBox.warning(self, "Lỗi", "AI Engine chưa sẵn sàng!")
            return
        num = self.num_spin.value()
        content = self.base_question.get('content_tex', '')
        progress = QProgressDialog("Đang tạo biến thể...", "Hủy", 0, num, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        self.results_list.clear()
        self.variants = []
        
        for i in range(num):
            if progress.wasCanceled(): break
            progress.setValue(i)
            progress.setLabelText(f"Đang tạo biến thể {i+1}/{num}...")
            variant = self._generate_single_variant(content)
            if variant:
                self.variants.append(variant)
                item = QListWidgetItem(f"Biến thể {i+1}")
                self.results_list.addItem(item)
        progress.setValue(num)
        
        if self.variants:
            QMessageBox.information(self, "Thành công", f"Đã tạo {len(self.variants)} biến thể!")
        else:
            QMessageBox.warning(self, "Lỗi", "Không tạo được biến thể nào. Vui lòng thử lại.")
    
    def _generate_single_variant(self, content):
        prompt = f"""
        Bạn là giáo viên Toán THPT chuyên nghiệp.
        NHIỆM VỤ: Tạo 1 câu hỏi TƯƠNG TỰ với câu sau:
        {content}
        YÊU CẦU BẮT BUỘC:
        1. Giữ NGUYÊN dạng toán và độ khó
        2. THAY ĐỔI số liệu hoặc ngữ cảnh
        3. Giữ NGUYÊN cấu trúc LaTeX (\\begin{{ex}}...\\end{{ex}})
        4. Giữ NGUYÊN format \\choice{{A}}{{B}}{{C}}{{D}}
        5. Đánh dấu đáp án đúng bằng \\True
        6. Viết lời giải trong \\loigiai{{}}
        OUTPUT: Chỉ trả về code LaTeX, không giải thích.
        """
        try:
            response = self.ai_engine.model.generate_content(prompt)
            if response.text:
                text = response.text.strip()
                text = text.replace("```latex", "").replace("```", "")
                return text
        except Exception as e:
            print(f"AI Error: {e}")
        return None
    
    def on_variant_selected(self, item):
        idx = self.results_list.row(item)
        if 0 <= idx < len(self.variants):
            self.variant_preview.setPlainText(self.variants[idx])
    
    def save_to_bank(self):
        QMessageBox.information(self, "Tính năng", "Tính năng lưu vào ngân hàng đang phát triển...")
    
    def use_in_exam(self):
        QMessageBox.information(self, "Tính năng", "Tính năng dùng trong đề đang phát triển...")
class APIKeyDialog(QDialog):
    def __init__(self, current_key="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Cấu hình API Key Gemini")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setup_ui(current_key)

    def setup_ui(self, current_key):
        layout = QVBoxLayout(self)

        # Tiêu đề
        title = QLabel("🔑 NHẬP API KEY GEMINI ĐỂ SỬ DỤNG TÍNH NĂNG AI")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2980b9; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Hướng dẫn lấy API Key
        guide = QTextEdit()
        guide.setReadOnly(True)
        guide.setMaximumHeight(220)
        guide.setStyleSheet("background-color: #f8f9fa; border: 1px solid #bdc3c7; border-radius: 6px; padding: 10px;")
        guide.setHtml("""
        <h3 style='color:#27ae60;'>📋 HƯỚNG DẪN LẤY API KEY GEMINI (MIỄN PHÍ)</h3>
        <ol><p style='color:#e74c3c;'>
            <li>Truy cập: <b><a href='https://aistudio.google.com/app/apikey'>https://aistudio.google.com/app/apikey</a></b></li>
            <li>Đăng nhập bằng tài khoản Google của bạn</li>
            <li>Nhấn nút <b>"Create API key"</b></li>
            <li>Chọn project (hoặc tạo mới nếu chưa có)</li>
            <li>Sao chép chuỗi key dài (bắt đầu bằng AIz...)</li>
            <li>Dán vào ô bên dưới và nhấn <b>Lưu & Tiếp tục</b></li>
        </ol>
        <p style='color:#e74c3c;'><b>Lưu ý:</b> 
        <ul>
            <li>API Key này hoàn toàn miễn phí (Gemini 1.5 Flash có hạn mức rất cao)</li>
            <li>Không chia sẻ key công khai</li>
            <li>Key sẽ được lưu an toàn trên máy bạn</li>
        </ul>
        </p>
        """)
        guide.viewport().setAutoFillBackground(False)
        layout.addWidget(QLabel("<b>Hướng dẫn lấy API Key:</b>"))
        layout.addWidget(guide)

        # Ô nhập API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("<b>API Key:</b>"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Dán API Key Gemini vào đây...")
        self.key_input.setText(current_key)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)  # Ẩn key
        key_layout.addWidget(self.key_input)

        self.btn_show = QPushButton("👁")
        self.btn_show.setCheckable(True)
        self.btn_show.setFixedWidth(40)
        self.btn_show.clicked.connect(lambda checked: self.key_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
        key_layout.addWidget(self.btn_show)

        layout.addLayout(key_layout)

        # Nút điều khiển
        btn_layout = QHBoxLayout()
        btn_guide = QPushButton("🌐 Mở trang lấy API Key")
        btn_guide.clicked.connect(lambda: open_file_or_url("https://aistudio.google.com/app/apikey"))
        btn_guide.setProperty("class", "btn-primary")

        btn_save = QPushButton("💾 Lưu & Tiếp tục")
        btn_save.setProperty("class", "btn-success")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_guide)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def get_key(self):
        return self.key_input.text().strip()
# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
# --- [SỬA LẠI HÀM NÀY Ở CUỐI FILE ngan_hang.py] ---
def check_and_fix_db():
    print("🛠 Đang kiểm tra cấu trúc Database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Tạo bảng nếu chưa có (Chuẩn hóa theo Backend: detail, submitted_at)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                student_email TEXT,
                exam_id TEXT,
                score REAL,
                detail TEXT,
                ai_feedback TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Kiểm tra và Migrating cột
        cursor.execute("PRAGMA table_info(exam_results)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # [MIGRATION] timestamp -> submitted_at
        if 'submitted_at' not in columns:
            if 'timestamp' in columns:
                print("⚠️ Migrating: timestamp -> submitted_at")
                try:
                    cursor.execute("ALTER TABLE exam_results RENAME COLUMN timestamp TO submitted_at")
                    conn.commit()
                except:
                    # Fallback cho SQLite cũ
                    cursor.execute("ALTER TABLE exam_results ADD COLUMN submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    cursor.execute("UPDATE exam_results SET submitted_at = timestamp")
                    conn.commit()
            else:
                print("⚠️ Adding: submitted_at")
                cursor.execute("ALTER TABLE exam_results ADD COLUMN submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()

        # [MIGRATION] detail_json -> detail
        if 'detail' not in columns:
            if 'detail_json' in columns:
                print("⚠️ Migrating: detail_json -> detail")
                try:
                    cursor.execute("ALTER TABLE exam_results RENAME COLUMN detail_json TO detail")
                    conn.commit()
                except:
                    cursor.execute("ALTER TABLE exam_results ADD COLUMN detail TEXT")
                    cursor.execute("UPDATE exam_results SET detail = detail_json")
                    conn.commit()
            else:
                cursor.execute("ALTER TABLE exam_results ADD COLUMN detail TEXT")
                conn.commit()
            
        if 'ai_feedback' not in columns:
            print("⚠️ Adding: ai_feedback")
            cursor.execute("ALTER TABLE exam_results ADD COLUMN ai_feedback TEXT")
            conn.commit()
            
        conn.close()
    except Exception as e:
        print(f"❌ Lỗi kiểm tra DB: {e}")

if __name__ == "__main__":
    check_and_fix_db()
    create_results_table(DB_PATH)

    import sys
    import platform
    from PyQt6.QtGui import QFont

    # 1. Cấu hình High DPI (Màn hình độ phân giải cao/Retina)
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # 2. Khởi tạo App
    app = QApplication(sys.argv)

    # --- [BƯỚC 1] KIỂM TRA BẢN QUYỀN (CHẶN NGAY TỪ ĐẦU) ---
    # Nếu hàm này trả về False (chưa kích hoạt/hết hạn) -> Thoát App
    if not check_license_system():
        sys.exit(0)

    # --- [BƯỚC 2] CẤU HÌNH FONT CHỮ (FIX LỖI WARNING) ---
    system_name = platform.system()
    if system_name == "Darwin": # macOS
        # Font hệ thống chuẩn của Apple
        font = QFont(".AppleSystemUIFont", 10) 
    elif system_name == "Windows":
        # Font chuẩn Windows 10/11
        font = QFont(".AppleSystemUIFont", 9) 
    else:
        font = QFont(".AppleSystemUIFont", 10)
    app.setFont(font)

    # --- [BƯỚC 3] KIỂM TRA & NÂNG CẤP DATABASE ---
    # Kiểm tra file DB có tồn tại không
    if not os.path.exists(DB_PATH):
        # Nếu muốn tự động tạo DB mới khi chưa có, hãy bỏ comment dòng dưới
        # create_new_database(DB_PATH) 
        QMessageBox.warning(None, "Cảnh báo", f"Chưa tìm thấy file dữ liệu tại:\n{DB_PATH}\nVui lòng import dữ liệu sau khi vào App.")
    
    # [QUAN TRỌNG] Gọi hàm Migration để thêm cột ID6, Lesson, q_type nếu thiếu
    try:
        DatabaseManager.migrate_db(DB_PATH)
    except Exception as e:
        print(f"Lỗi khi nâng cấp DB: {e}")

    # --- [BƯỚC 4] SPLASH SCREEN & API KEY ---
    # Tạo màn hình chờ (Splash Screen)
    splash = QSplashScreen()
    splash.showMessage("Đang khởi động hệ thống...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
    splash.show()
    app.processEvents()

    # Logic lấy API Key
    saved_key = load_api_key()
    final_api_key = ""

    if not saved_key:
        splash.hide() # Ẩn splash để hiện hộp thoại nhập liệu
        key, ok = QInputDialog.getText(None, "Cấu hình", "Nhập Google Script API Key:", QLineEdit.EchoMode.Normal)
        if ok and key:
            final_api_key = key.strip()
            save_api_key(final_api_key)
            splash.show() # Hiện lại splash
        else:
            sys.exit(0)
    else:
        final_api_key = saved_key

    # --- [BƯỚC 5] KHỞI CHẠY MAIN WINDOW ---
    try:
        window = MainApp(final_api_key)
        window.show()
        splash.finish(window) # Đóng Splash khi cửa sổ chính hiện lên
        sys.exit(app.exec())
    except Exception as e:
        splash.hide()
        import traceback
        traceback.print_exc() # In lỗi ra console để debug
        QMessageBox.critical(None, "Lỗi Critical", f"Không thể khởi chạy ứng dụng:\n{str(e)}")
        sys.exit(1)