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
                box-shadow: 0 4px 6px rgba(237, 132, 13, 0.3);
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
