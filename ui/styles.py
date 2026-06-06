"""
QSS 样式集中管理:深色现代风,贴合课堂演示场景。
"""

STYLE_GLOBAL = """
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #E6EAF2;
}

QToolTip {
    background: #2A2F3A;
    color: #E6EAF2;
    border: 1px solid #4A5160;
    padding: 4px 8px;
    border-radius: 4px;
}
"""

STYLE_BUTTON_ITEM = """
QPushButton {
    background: qradialgradient(cx:0.5, cy:0.4, radius:0.7,
        fx:0.5, fy:0.35,
        stop:0 rgba(255,255,255,180),
        stop:0.6 rgba(74,144,226,220),
        stop:1 rgba(40,90,180,240));
    border: 1px solid rgba(255,255,255,220);
    border-radius: 27px;
    color: white;
    font-size: 18px;
    font-weight: bold;
}
QPushButton:hover {
    background: qradialgradient(cx:0.5, cy:0.4, radius:0.7,
        fx:0.5, fy:0.35,
        stop:0 rgba(255,255,255,230),
        stop:0.6 rgba(100,170,255,240),
        stop:1 rgba(60,120,220,255));
    border: 1px solid #FFFFFF;
}
QPushButton:pressed {
    background: #1F4E96;
}
"""

STYLE_PLACEHOLDER = """
/* "+" 占位按钮:绿色 + 虚线边框,与真实按钮视觉区分 */
QPushButton {
    background: qradialgradient(cx:0.5, cy:0.4, radius:0.7,
        fx:0.5, fy:0.35,
        stop:0 rgba(255,255,255,220),
        stop:0.6 rgba(76,175,80,240),
        stop:1 rgba(40,140,60,255));
    border: 2px dashed rgba(255,255,255,240);
    border-radius: 27px;
    color: white;
    font-size: 20px;
    font-weight: bold;
}
QPushButton:hover {
    background: qradialgradient(cx:0.5, cy:0.4, radius:0.7,
        fx:0.5, fy:0.35,
        stop:0 rgba(255,255,255,255),
        stop:0.6 rgba(110,210,110,255),
        stop:1 rgba(70,180,90,255));
    border: 2px dashed #FFFFFF;
}
QPushButton:pressed {
    background: #2E7D32;
}
"""

STYLE_MENU = """
QMenu {
    background: #1F242E;
    border: 1px solid #3A4250;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: #4A90E2;
    color: white;
}
QMenu::separator {
    height: 1px;
    background: #3A4250;
    margin: 4px 8px;
}
"""

STYLE_DIALOG = """
QDialog {
    background: #1A1E26;
}

QGroupBox {
    border: 1px solid #3A4250;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 8px;
    font-weight: bold;
    color: #E8EEF8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #FFFFFF;
}

QPushButton {
    background: #2A3140;
    color: #F0F4FB;
    border: 1px solid #3F4858;
    border-radius: 4px;
    padding: 6px 14px;
    min-width: 60px;
}
QPushButton:hover { background: #353D4F; }
QPushButton:pressed { background: #1F2632; }
QPushButton:disabled { background: #232934; color: #6B7280; }

QPushButton#primaryBtn {
    background: #4A90E2;
    color: white;
    border: none;
}
QPushButton#primaryBtn:hover { background: #5AA0F2; }
QPushButton#primaryBtn:pressed { background: #3A80D2; }

QPushButton#dangerBtn {
    background: #E74C3C;
    color: white;
    border: none;
}
QPushButton#dangerBtn:hover { background: #F25C4C; }

QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #0F131A;
    color: #F0F4FB;
    border: 1px solid #3A4250;
    border-radius: 4px;
    padding: 6px 8px;
    selection-background-color: #4A90E2;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #4A90E2;
}

QListWidget {
    background: #0F131A;
    border: 1px solid #3A4250;
    border-radius: 4px;
    padding: 4px;
    color: #E8EEF8;
}
QListWidget::item {
    padding: 8px;
    border-radius: 4px;
    color: #E8EEF8;
}
QListWidget::item:selected {
    background: #2A3F66;
    color: #FFFFFF;
}
QListWidget::item:hover { background: #1F2A3E; }

QLabel { color: #E8EEF8; }
QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #FFFFFF;
}

QCheckBox { color: #E8EEF8; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #3A4250;
    border-radius: 3px;
    background: #0F131A;
}
QCheckBox::indicator:checked {
    background: #4A90E2;
    border: 1px solid #4A90E2;
}

QTabWidget::pane {
    border: 1px solid #3A4250;
    border-radius: 4px;
    background: #1A1E26;
}
QTabBar::tab {
    background: #1F242E;
    color: #E8EEF8;
    padding: 8px 18px;
    border: 1px solid #3A4250;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #2A3140;
    color: #FFFFFF;
}

QSlider::groove:horizontal {
    height: 4px;
    background: #2A3140;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #4A90E2;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
"""
