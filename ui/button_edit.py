"""
添加/编辑按钮的子对话框。
支持三种类型:URL / HTML代码 / HTML文件。
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QPlainTextEdit,
    QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel,
    QDialogButtonBox, QWidget, QStackedWidget
)
from PySide6.QtCore import Qt

from ui.styles import STYLE_DIALOG


TYPE_URL = "url"
TYPE_HTML = "html"
TYPE_FILE = "file"

ICON_PRESETS = ["📚", "🎯", "📝", "📁", "🧪", "🎨", "🌐", "🎬", "📊", "🧠", "🔬", "🎵", "🖼️", "📌", "⭐", "🎮"]


class ButtonEditDialog(QDialog):
    """添加或编辑单个按钮。"""

    def __init__(self, cfg: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加按钮" if not cfg else "编辑按钮")
        self.resize(520, 460)
        # 关键:必须显式设置暗色样式,否则在 Windows 浅色主题上白字白底看不见
        self.setStyleSheet(STYLE_DIALOG)
        self._cfg = dict(cfg) if cfg else {}
        self._build_ui()
        if cfg:
            self._fill(cfg)

    def _build_ui(self):
        root = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如:古诗课件")
        form.addRow("按钮名称:", self.name_edit)

        # 图标选择(预设 + 任意文本)
        icon_row = QHBoxLayout()
        self.icon_combo = QComboBox()
        self.icon_combo.setEditable(True
        )
        self.icon_combo.addItems(ICON_PRESETS)
        self.icon_combo.setCurrentText("📚")
        icon_row.addWidget(self.icon_combo, 1)
        form.addRow("图标(emoji/文字):", self._wrap(icon_row))

        self.type_combo = QComboBox()
        self.type_combo.addItem("网址 (URL)", TYPE_URL)
        self.type_combo.addItem("HTML 代码", TYPE_HTML)
        self.type_combo.addItem("HTML 文件", TYPE_FILE)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("内容类型:", self.type_combo)

        root.addLayout(form)

        # 内容区:三种类型切换
        self.stack = QStackedWidget()

        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com/course.html")
        self.stack.addWidget(self._wrap_simple(self.url_edit))

        # HTML 代码
        self.html_edit = QPlainTextEdit()
        self.html_edit.setPlaceholderText(
            "<!DOCTYPE html><html><body>\n"
            "  <h1>Hello</h1>\n"
            "  <p>这里粘贴你的 HTML 课件代码</p>\n"
            "</body></html>"
        )
        self.stack.addWidget(self.html_edit)

        # HTML 文件
        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("C:/课件/lesson1.html")
        file_btn = QPushButton("浏览…")
        file_btn.clicked.connect(self._pick_file)
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(file_btn)
        self.stack.addWidget(self._wrap(file_row))

        root.addWidget(QLabel("内容:"))
        root.addWidget(self.stack, 1)

        # OK / Cancel
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.button(QDialogButtonBox.Ok).setObjectName("primaryBtn")
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _wrap(self, layout) -> QWidget:
        w = QWidget(); w.setLayout(layout); return w

    def _wrap_simple(self, w) -> QWidget:
        from PySide6.QtWidgets import QVBoxLayout
        wrap = QWidget()
        v = QVBoxLayout(wrap); v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(w)
        return wrap

    def _on_type_changed(self, idx: int):
        self.stack.setCurrentIndex(idx)

    def _pick_file(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, "选择 HTML 文件", "",
            "HTML 文件 (*.html *.htm);;所有文件 (*.*)"
        )
        if fp:
            self.file_edit.setText(fp)

    def _fill(self, cfg: dict):
        self.name_edit.setText(cfg.get("name", ""))
        self.icon_combo.setCurrentText(cfg.get("icon", "📚"))
        t = cfg.get("type", TYPE_URL)
        idx = max(0, [TYPE_URL, TYPE_HTML, TYPE_FILE].index(t))
        self.type_combo.setCurrentIndex(idx)
        self.stack.setCurrentIndex(idx)
        c = cfg.get("content", "")
        if t == TYPE_URL:
            self.url_edit.setText(c)
        elif t == TYPE_HTML:
            self.html_edit.setPlainText(c)
        elif t == TYPE_FILE:
            self.file_edit.setText(c)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        t = self.type_combo.currentData()
        if t == TYPE_URL and not self.url_edit.text().strip():
            self.url_edit.setFocus(); return
        if t == TYPE_HTML and not self.html_edit.toPlainText().strip():
            self.html_edit.setFocus(); return
        if t == TYPE_FILE:
            p = Path(self.file_edit.text().strip())
            if not p.exists():
                self.file_edit.setFocus(); return
        self.accept()

    def get_config(self) -> dict:
        t = self.type_combo.currentData()
        if t == TYPE_URL:
            content = self.url_edit.text().strip()
        elif t == TYPE_HTML:
            content = self.html_edit.toPlainText()
        else:
            content = self.file_edit.text().strip()
        return {
            "id": self._cfg.get("id", ""),
            "name": self.name_edit.text().strip(),
            "icon": self.icon_combo.currentText().strip() or "📌",
            "type": t,
            "content": content,
        }
