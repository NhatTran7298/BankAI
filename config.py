import os
import sys
import json
import shutil
import platform
import hashlib
import uuid
import warnings
from pathlib import Path

# --- TẮT CẢNH BÁO GOOGLE DEPRECATED ---
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# 🔥 URL API
API_URL = "https://script.google.com/macros/s/AKfycbxDJmIsjLWXHuq0aq-IY5Rk67jK1G6dLWfVPicuyk2hxMTcz2ePHs_UEmoUkUvd3fgtRA/exec"

APP_VERSION = "1.0"

# --- CẤU HÌNH THANH TOÁN ---
BANK_ID = "BIDV"           # Mã ngân hàng
BANK_ACCOUNT = "6612853484" # Số tài khoản
BANK_NAME = "TRAN NAM NHAT" # Tên chủ tài khoản

PRICE_YEAR = 400000    # 400k
PRICE_LIFE = 800000    # 800k

# [QUAN TRỌNG] Cấu hình PATH cho macOS
if sys.platform == 'darwin':
    os.environ['PATH'] += ':/usr/local/bin:/opt/homebrew/bin:/Library/TeX/texbin'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def resource_path(relative_path):
    """Lấy đường dẫn tuyệt đối của tài nguyên, dùng được cho cả dev và PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_database_path():
    db_filename = "bank_pro.db"

    # [FIX] Đổi sang thư mục ẩn tại Home Directory
    user_data_dir = os.path.join(os.path.expanduser("~"), ".bankai_data")

    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    writable_db_path = os.path.join(user_data_dir, db_filename)

    # Logic kiểm tra và copy DB mẫu
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

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

DB_PATH = get_database_path()
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".bankai_cache")
if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)

IMAGE_LIB_PATH = os.path.join(os.path.dirname(DB_PATH), "image_lib.json")

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
# DATA STRUCTURES & TEMPLATES
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

DANH_MUC_DANG = {
    1: "Trắc nghiệm (4 lựa chọn)",
    2: "Đúng/Sai",
    3: "Trả lời ngắn",
    4: "Tự luận",
}

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