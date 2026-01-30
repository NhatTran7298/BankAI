import sys
import os
import shutil
import platform
import traceback
import json
import uuid
import hashlib
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QDialog, QComboBox, QSpinBox,
                             QStackedWidget, QSplashScreen, QInputDialog, QMenu)
from PyQt6.QtGui import QFont, QIcon, QAction, QColor, QCursor
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread

# Imports from modules
from config import (
    API_URL, APP_VERSION, DB_PATH, CACHE_DIR, APP_STYLE,
    load_api_key, save_api_key, LATEX_TEMPLATE
)
from utils import get_hwid, open_file_or_url
from database import Backend, DatabaseManager
from integrations import AIEngine
from workers import (
    CacheCleanupWorker, ImportWorker, ExamPreparerWorker, WebServerThread,
    BatchAIWorker, AutoPostWorker
)
from ui_components import (
    ModernSidebar, WatermarkWidget, DragDropListWidget, DropZoneTreeWidget,
    ActivationDialog, ClassroomControlPanel, ID6AssignDialog, LessonPlannerWidget,
    ImageManagerDialog, MatrixEditorDialog, AIClonerDialog, APIKeyDialog,
    StatisticsDashboard, MixConfigDialog, TemplateLibraryDialog, ClassroomDialog,
    ExamConfigDialog, HistoryDialog, ExamMonitorDialog, HelpDialog,
    AdvancedExportDialog, FileCleanerDialog, ImageMappingDialog, AutoSchedulerDialog,
    check_license_system
)

# =============================================================================
# MAIN APPLICATION
# =============================================================================

class MainApp(QMainWindow):
    def __init__(self, api_key):
        super().__init__()
        self.bk = Backend()
        self.ai = AIEngine(api_key)

        self.cleanup_worker = CacheCleanupWorker()
        self.cleanup_worker.start()

        self.current_exam = []
        self.generated_exams = {}
        self.setWindowTitle("BankAI Pro - 2025 Matrix Edition")

        screen = QApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * 0.9)
        h = int(screen.height() * 0.9)
        w = max(1000, min(w, 1600))
        h = max(700, min(h, 1200))
        x = (screen.width() - w) // 2
        y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

        self.setStyleSheet(APP_STYLE)

        w = QWidget(); self.setCentralWidget(w);
        main_layout = QHBoxLayout(w)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        self.sidebar = ModernSidebar()
        main_layout.addWidget(self.sidebar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0,0,0,0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self.create_toolbar())

        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_home_tab())
        self.stack.addWidget(self.create_manual_tab())
        self.stack.addWidget(self.create_matrix_tab())
        self.stack.addWidget(self.create_ai_tab())

        content_layout.addWidget(self.stack)

        self.lbl_stat = QLabel(" Ready");
        self.lbl_stat.setStyleSheet("background: #f0f0f0; padding: 5px; color: #555;")
        content_layout.addWidget(self.lbl_stat)

        main_layout.addWidget(content_widget)

        self.sidebar.btn_group.buttonClicked.connect(self.switch_page)
        self.sidebar.btn_dashboard.setChecked(True)

        QTimer.singleShot(100, self.load_stats)

    def switch_page(self, btn):
        id = self.sidebar.btn_group.id(btn)
        if id >= 0: self.stack.setCurrentIndex(id)

    def create_toolbar(self):
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ED840D, stop:1 #d35400);
                border-bottom: 2px solid #ffaf40;
            }
        """)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10)

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

        self.btn_web = QPushButton("🌍 Bật Thi Online")
        self.btn_web.setCheckable(True)
        self.btn_web.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_web.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
                color: #ffffff; padding: 8px 15px; border-radius: 6px; font-weight: 700;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); }
            QPushButton:checked {
                background-color: #2ecc71;
                border-color: #27ae60;
                color: white;
            }
        """)
        self.btn_web.clicked.connect(self.toggle_web_server)
        layout.addWidget(self.btn_web)

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

    def create_big_card(self, title, desc, icon, callback):
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
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 900; color: #ffffff; background: transparent; border: none; text-transform: uppercase;")

        lbl_desc = QLabel(desc)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 13px; color: #f0f0f0; background: transparent; border: none;")

        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)

        btn.clicked.connect(callback)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(237, 132, 13, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 16px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ED840D;
                border: 2px solid #ffffff;
            }
            QPushButton:pressed {
                background-color: #ae5c04;
            }
        """)
        return btn

    def create_home_tab(self):
        w = WatermarkWidget("BANKAI PRO 2025")
        main_layout = QVBoxLayout(w)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(30)

        header_box = QVBoxLayout()
        lbl_welcome = QLabel("TRUNG TÂM ĐIỀU KHIỂN")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_welcome.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff; background: transparent;")

        self.stat_lbl = QLabel("Hệ thống sẵn sàng...")
        self.stat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stat_lbl.setStyleSheet("font-size: 14px; color: #a4b0be; background: transparent;")

        header_box.addWidget(lbl_welcome)
        header_box.addWidget(self.stat_lbl)
        main_layout.addLayout(header_box)

        grid = QGridLayout()
        grid.setSpacing(25)

        card_import = self.create_big_card("NHẬP DỮ LIỆU", "Import câu hỏi LaTeX & Phân loại.", "📥", self.import_files)
        card_planner = self.create_big_card("SOẠN BÀI GIẢNG", "Soạn chuyên đề & Lọc ma trận.", "📝", self.open_lesson_planner)
        card_mix = self.create_big_card("TRỘN ĐỀ THI", "Đảo đề hoán vị & Xuất PDF/TeX.", "🔀", self.mix_and_export)
        card_class = self.create_big_card("GOOGLE CLASSROOM", "Đăng bài tập & Tổ chức Thi Online.", "☁️", self.show_classroom_menu)

        grid.addWidget(card_import, 0, 0)
        grid.addWidget(card_planner, 0, 1)
        grid.addWidget(card_mix, 1, 0)
        grid.addWidget(card_class, 1, 1)

        grid.setRowStretch(0, 1); grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)

        main_layout.addLayout(grid)

        footer = QLabel(f"BankAI Pro v{APP_VERSION} © 2025 Matrix Edition")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: rgba(255,255,255,0.3); margin-top: 20px; background: transparent;")
        main_layout.addWidget(footer)

        return w

    def create_manual_tab(self):
        w = QWidget(); l = QHBoxLayout(w)

        lw = QWidget(); ll = QVBoxLayout(lw)

        grp = QGroupBox("🔍 Bộ lọc câu hỏi"); gl = QGridLayout(grp)
        self.man_g = QComboBox(); self.man_g.addItems(["All","10","11","12"])
        self.man_s = QComboBox(); self.man_s.addItems(["All","Đại số","Hình học"])
        self.man_c = QComboBox(); self.man_c.addItem("Tất cả", 0)
        self.man_b = QComboBox(); self.man_b.addItem("Tất cả", 0)
        self.man_l = QComboBox(); self.man_l.addItems(["All","NB","TH","VD","VDC"])
        self.man_d = QComboBox(); self.man_d.addItem("All",0)

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

        rw = QWidget(); rl = QVBoxLayout(rw)

        self.lbl_exam_stats = QLabel("Đề đang soạn: 0 câu")
        self.lbl_exam_stats.setStyleSheet("font-size: 14px; font-weight: bold; color: #d35400; padding: 5px; border-bottom: 2px solid #d35400;")
        rl.addWidget(self.lbl_exam_stats)

        self.exam_lst = DropZoneTreeWidget(self.bk)
        self.exam_lst.items_changed.connect(self.update_exam_stats)
        rl.addWidget(self.exam_lst)

        bh = QHBoxLayout()
        b_clear = QPushButton("🗑️ Xóa hết"); b_clear.setProperty("class","btn-danger"); b_clear.clicked.connect(self.exam_lst.clear_all)
        b_save = QPushButton("💾 Lưu File TeX"); b_save.setProperty("class","btn-primary"); b_save.clicked.connect(self.quick_save_manual_exam)
        b_class = QPushButton("☁️ Đăng Classroom"); b_class.setProperty("class","btn-success"); b_class.clicked.connect(self.upload_from_manual_tab)

        bh.addWidget(b_clear); bh.addWidget(b_save); bh.addWidget(b_class)
        rl.addLayout(bh)
        l.addWidget(lw, 4); l.addWidget(rw, 4)
        return w

    def create_matrix_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(50, 50, 50, 50); l.setSpacing(20)
        lbl_title = QLabel("CÔNG CỤ TẠO ĐỀ MA TRẬN 2025")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #d35400;")
        l.addWidget(lbl_title)

        btn_open = QPushButton("🎛️ MỞ BẢNG ĐIỀU KHIỂN MA TRẬN")
        btn_open.setMinimumHeight(80)
        btn_open.setStyleSheet("QPushButton { background-color: #e67e22; color: white; font-size: 18px; font-weight: bold; border-radius: 10px; }")
        btn_open.clicked.connect(self.open_matrix_window)
        l.addWidget(btn_open)

        self.lbl_matrix_status = QLabel("Trạng thái: Chưa có đề nào được tạo.")
        self.lbl_matrix_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.lbl_matrix_status)
        l.addStretch()
        return w

    def create_ai_tab(self):
        w = QWidget(); l = QHBoxLayout(w)
        lw = QWidget(); ll = QVBoxLayout(lw)
        ll.addWidget(QLabel("<b>ĐỀ GỐC (Chọn câu hỏi để AI nhân bản)</b>"))
        self.ai_lst = QListWidget(); self.ai_lst.setAlternatingRowColors(True)
        ll.addWidget(self.ai_lst)

        g = QGroupBox("Cấu hình AI"); gl = QGridLayout(g)
        self.ai_n = QSpinBox(); self.ai_n.setValue(3); self.ai_n.setSuffix(" đề")
        self.ai_c = QSpinBox(); self.ai_c.setRange(100,999); self.ai_c.setValue(101)
        gl.addWidget(QLabel("Số lượng đề:"),0,0); gl.addWidget(self.ai_n,0,1)
        gl.addWidget(QLabel("Mã đề bắt đầu:"),1,0); gl.addWidget(self.ai_c,1,1)
        ll.addWidget(g)

        btn_box = QVBoxLayout()
        b_load = QPushButton("1. Load câu hỏi từ đề đang soạn"); b_load.clicked.connect(self.load_ai)
        btn_box.addWidget(b_load)
        b_run = QPushButton("2. CHẠY AI"); b_run.setProperty("class","btn-success"); b_run.clicked.connect(self.run_ai)
        btn_box.addWidget(b_run)
        b_export = QPushButton("3. 💾 Xuất ra Code LaTeX"); b_export.setProperty("class", "btn-warning"); b_export.clicked.connect(self.export_ai_results)
        btn_box.addWidget(b_export)
        ll.addLayout(btn_box)

        rw = QWidget(); rl = QVBoxLayout(rw)
        rl.addWidget(QLabel("<b>KẾT QUẢ TỪ AI</b>"))
        self.ai_tr = QTreeWidget(); self.ai_tr.setHeaderHidden(True); self.ai_tr.itemClicked.connect(self.on_ai_tree_click)
        rl.addWidget(self.ai_tr)
        self.ai_prv = QTextEdit(); self.ai_prv.setMaximumHeight(200); self.ai_prv.setReadOnly(True)
        rl.addWidget(self.ai_prv)

        l.addWidget(lw, 1); l.addWidget(rw, 2)
        return w

    def open_lesson_planner(self):
        if not os.path.exists(DB_PATH): QMessageBox.critical(self, "Lỗi", "Chưa tìm thấy Database!"); return
        self.planner_window = LessonPlannerWidget(DB_PATH)
        self.planner_window.resize(1100, 700)
        self.planner_window.setWindowTitle("Công cụ Soạn Giảng & Lọc Đề - BankAI Pro")
        self.planner_window.show()

    def load_stats(self):
        try:
            total, _, _ = self.bk.get_dashboard_stats()
            if hasattr(self, 'stat_lbl'): self.stat_lbl.setText(f"{total:,} câu hỏi")
            if hasattr(self, 'lbl_stat'): self.lbl_stat.setText(f"Database: {total:,} questions")
        except Exception as e: print(f"Lỗi load stats: {e}")

    def import_files(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "Chọn file TeX", "", "TeX (*.tex)")
        if not fs: return
        self.pd_import = QProgressDialog("Đang đọc và phân tích...", "Hủy", 0, 100, self)
        self.pd_import.setWindowModality(Qt.WindowModality.WindowModal)
        self.pd_import.show()
        self.import_worker = ImportWorker(fs)
        self.import_worker.progress.connect(lambda v, m: (self.pd_import.setValue(v), self.pd_import.setLabelText(m)))
        self.import_worker.analysis_done.connect(self.on_import_finished)
        self.import_worker.start()

    def on_import_finished(self, questions, images):
        self.pd_import.close()
        missing_id_qs = [q for q in questions if not q.get('id6')]
        if missing_id_qs:
            reply = QMessageBox.question(self, "Kiểm tra dữ liệu", f"Phát hiện {len(missing_id_qs)} câu thiếu ID6. Gán ngay?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                dlg = ID6AssignDialog(self.bk, self, mode='local', data_list=missing_id_qs)
                if dlg.exec() != QDialog.DialogCode.Accepted: return

        self.pd_import.setLabelText("Đang lưu vào DB..."); self.pd_import.show()
        try:
            added, skipped = self.bk.insert_questions_list(questions)
            self.pd_import.close(); self.load_stats()
            QMessageBox.information(self, "Hoàn tất", f"✅ Đã nhập thành công!\n- Thêm mới: {added}\n- Trùng lặp: {skipped}")
        except Exception as e:
            self.pd_import.close()
            QMessageBox.critical(self, "Lỗi Lưu DB", str(e))

    def mix_and_export(self):
        if not self.current_exam:
            questions = self.exam_lst.get_all_questions()
            if questions: self.current_exam = questions
            else: QMessageBox.warning(self, "Trống", "Danh sách câu hỏi trống!"); return

        dialog = MixConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                from utils import ExamMixer
                mixer = ExamMixer()
                self.generated_exams = mixer.mix_exam(self.current_exam, data['num'], data['start'])
                if QMessageBox.question(self, "Thành công", f"Đã trộn xong {data['num']} mã đề. Xuất file TeX?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    self.export_mixed_tex()
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))

    def export_mixed_tex(self):
        if not self.generated_exams: return
        path, _ = QFileDialog.getSaveFileName(self, "Lưu Đề Trộn", "De_Tron.tex", "TeX Files (*.tex)")
        if not path: return
        full_content = [LATEX_TEMPLATE]
        for code, questions in self.generated_exams.items():
            full_content.append(f"\\newpage\n\\begin{{center}}\\textbf{{MÃ ĐỀ: {code}}}\\end{{center}}\n\\setcounter{{ex}}{{0}}")
            for idx, q in enumerate(questions): full_content.append(q['content_tex'])
        full_content.append("\\end{document}")
        with open(path, "w", encoding="utf-8") as f: f.write("\n".join(full_content))
        QMessageBox.information(self, "Xong", f"Đã xuất file: {path}")

    def show_classroom_menu(self):
        ClassroomControlPanel(self, callback_exam=self.create_online_classroom_exam, callback_homework=self.open_classroom_dialog).exec()

    def open_classroom_dialog(self):
        questions_objs = self.current_exam or self.exam_lst.get_all_questions()
        if not questions_objs: QMessageBox.warning(self, "Trống", "Chưa có đề thi!"); return
        ClassroomDialog(questions_objs, self).exec()

    def create_online_classroom_exam(self):
        questions, src = self.get_current_exam_questions()
        if not questions: QMessageBox.warning(self, "Chưa có câu hỏi", "Danh sách trống!"); return

        dlg = ExamConfigDialog(questions, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            config = dlg.get_config()
            if not hasattr(self, 'web_thread'): self.web_thread = WebServerThread(DB_PATH)
            if not self.web_thread.isRunning(): self.web_thread.start()

            self.prep_worker = ExamPreparerWorker(config['questions'], config['title'], config['time'], num_variants=config.get('num_variants', 1))
            self.prep_worker.finished.connect(lambda s, d: self.on_exam_prepared(s, d) if s else QMessageBox.critical(self, "Lỗi", d.get('error')))
            self.prep_worker.start()

    def on_exam_prepared(self, success, data):
        if success:
            self.web_thread.set_exam_data(data)
            self.monitor_dlg = ExamMonitorDialog(self.web_thread, self)
            self.monitor_dlg.show()
            self.btn_web.setStyleSheet("background-color: #2ecc71; color: white;")
            self.btn_web.setText(f"📡 Online")

    def get_current_exam_questions(self):
        idx = self.stack.currentIndex()
        if idx == 1: return self.exam_lst.get_all_questions(), "manual"
        elif idx == 3 and self.gen_res: return self.gen_res[list(self.gen_res.keys())[0]], "ai"
        elif self.current_exam: return self.current_exam, "matrix"
        return [], ""

    def toggle_web_server(self):
        if self.btn_web.isChecked(): self.create_online_classroom_exam()
        else:
            if hasattr(self, 'web_thread'): self.web_thread.stop()
            self.btn_web.setStyleSheet("background-color: rgba(255,255,255,0.2);")
            self.btn_web.setText("🌍 Bật Thi Online")

    def quick_save_manual_exam(self):
        questions = self.exam_lst.get_all_questions()
        if not questions: return
        path, _ = QFileDialog.getSaveFileName(self, "Lưu Đề", "De_Goc.tex", "TeX Files (*.tex)")
        if path:
            content = [q['content_tex'] for q in questions]
            with open(path, "w", encoding="utf-8") as f: f.write(LATEX_TEMPLATE.replace("__CONTENT__", "\n".join(content)))

    def open_matrix_window(self):
        dlg = MatrixEditorDialog(self.bk, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.current_exam = dlg.final_questions
            self.exam_lst.clear_all() # Optional: sync to manual tab
            self.lbl_matrix_status.setText(f"✅ Đã tạo {len(self.current_exam)} câu.")

    def update_exam_stats(self):
        qs = self.exam_lst.get_all_questions()
        self.lbl_exam_stats.setText(f"Đề đang soạn: {len(qs)} câu")

    def upd_man_ch(self):
        self.man_c.clear(); self.man_c.addItem("Tất cả", 0)
        try:
            g = int(self.man_g.currentText())
            s = 'D' if 'Đại' in self.man_s.currentText() else 'H'
            if g in DATA_ID6_2025:
                for k in DATA_ID6_2025[g][s]: self.man_c.addItem(f"Chương {k}", k)
        except: pass
        self.upd_man_bai()

    def upd_man_bai(self):
        self.man_b.clear(); self.man_b.addItem("Tất cả", 0)
        try:
            g = int(self.man_g.currentText())
            s = 'D' if 'Đại' in self.man_s.currentText() else 'H'
            c = self.man_c.currentData()
            if c:
                for k, v in DATA_ID6_2025[g][s][c].items(): self.man_b.addItem(f"Bài {k}: {v}", k)
        except: pass

    def filter_manual(self):
        self.man_lst.clear()
        lvl = self.man_l.currentText(); l = lvl if lvl != "All" else None
        d = self.man_d.currentData()
        try:
            g = int(self.man_g.currentText()) if "All" not in self.man_g.currentText() else None
            s = ('D' if 'Đại' in self.man_s.currentText() else 'H') if "All" not in self.man_s.currentText() else None
            c = self.man_c.currentData(); b = self.man_b.currentData()
            qs = self.bk.get_all_filtered(g, s, c, b, l, d, limit=200)
            for q in qs:
                it = QListWidgetItem(f"ID:{q['id']} | {q['content_tex'][:50]}...")
                it.setData(Qt.ItemDataRole.UserRole, q)
                self.man_lst.addItem(it)
        except: pass

    def upload_from_manual_tab(self):
        self.current_exam = self.exam_lst.get_all_questions()
        self.show_classroom_menu()

    def load_ai(self):
        qs, _ = self.get_current_exam_questions()
        self.ai_lst.clear()
        for q in qs:
            it = QListWidgetItem(f"ID:{q.get('id')}..."); it.setData(Qt.ItemDataRole.UserRole, q)
            self.ai_lst.addItem(it)

    def run_ai(self):
        if self.ai_lst.count() == 0: return
        base = [self.ai_lst.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.ai_lst.count())]
        self.pd = QProgressDialog("AI Running...", "Cancel", 0, 100, self)
        self.wk = BatchAIWorker(self.ai, base, self.ai_n.value(), self.ai_c.value())
        self.wk.progress.connect(lambda v,m: (self.pd.setValue(v), self.pd.setLabelText(m)))
        self.wk.finished.connect(self.ai_done)
        self.wk.start()

    def ai_done(self, res):
        self.pd.close(); self.gen_res = res
        self.ai_tr.clear()
        for c, qs in res.items():
            rt = QTreeWidgetItem([f"Đề {c}"]); rt.setData(0, Qt.ItemDataRole.UserRole, {'t':'e','c':c})
            for q in qs:
                ch = QTreeWidgetItem([f"Câu {q['idx']}"]); ch.setData(0, Qt.ItemDataRole.UserRole, {'t':'q','c':c,'i':q['idx']-1})
                rt.addChild(ch)
            self.ai_tr.addTopLevelItem(rt)

    def on_ai_tree_click(self, item):
        d = item.data(0, Qt.ItemDataRole.UserRole)
        if d and d['t'] == 'q':
            q = self.gen_res[d['c']][d['i']]
            self.ai_prv.setText(q['content'])

    def export_ai_results(self):
        if not hasattr(self, 'gen_res'): return
        path, _ = QFileDialog.getSaveFileName(self, "Export AI", "AI_Exam.tex", "TeX Files (*.tex)")
        if path:
            c = [LATEX_TEMPLATE]
            for code, qs in self.gen_res.items():
                c.append(f"\\section*{{Đề {code}}}")
                for q in qs: c.append(q['content'])
            with open(path, "w", encoding="utf-8") as f: f.write("\n".join(c) + "\n\\end{document}")

    def export_exam(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export DB", "Database.tex", "TeX Files (*.tex)")
        if path:
            qs = self.bk.conn.execute("SELECT content_tex FROM questions").fetchall()
            with open(path, "w", encoding="utf-8") as f:
                f.write(LATEX_TEMPLATE.replace("__CONTENT__", "\n".join([q[0] for q in qs])))

    def open_help(self): HelpDialog(self).exec()
    def open_history(self): HistoryDialog(self.bk, self).exec()
    def show_id6(self): ID6AssignDialog(self.bk, self).exec()
    def open_image_manager(self): ImageManagerDialog(self.bk, self).exec()
    def open_file_cleaner(self): FileCleanerDialog(self.ai, self).exec()
    def closeEvent(self, e):
        if hasattr(self, 'web_thread'): self.web_thread.stop()
        e.accept()

if __name__ == "__main__":
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(sys.argv)

    # Check License
    if not check_license_system():
        sys.exit(0)

    # Font
    font = QFont(".AppleSystemUIFont", 10) if platform.system() == "Darwin" else QFont("Segoe UI", 9)
    app.setFont(font)

    # DB Check
    if not os.path.exists(DB_PATH):
        QMessageBox.warning(None, "Cảnh báo", f"Chưa tìm thấy DB tại: {DB_PATH}")

    try:
        DatabaseManager.migrate_db(DB_PATH)
    except: pass

    # Splash
    splash = QSplashScreen()
    splash.showMessage("Đang khởi động...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
    splash.show()
    app.processEvents()

    key = load_api_key()
    if not key:
        splash.hide()
        k, ok = QInputDialog.getText(None, "API Key", "Nhập Google Gemini API Key:")
        if ok and k:
            save_api_key(k.strip()); key = k.strip(); splash.show()
        else: sys.exit(0)

    try:
        window = MainApp(key)
        window.show()
        splash.finish(window)
        sys.exit(app.exec())
    except Exception as e:
        splash.hide()
        traceback.print_exc()
        QMessageBox.critical(None, "Error", str(e))
        sys.exit(1)
