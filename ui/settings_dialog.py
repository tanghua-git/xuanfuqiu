"""
设置主窗口:
- 标签页 1:按钮管理(列表 + 增/删/改/上下移)
- 标签页 2:通用设置(大小、透明度、开机自启、默认展开、鼠标穿透)
"""
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QLabel, QSpinBox,
    QSlider, QCheckBox, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication

from core.config import Config
from ui.button_edit import ButtonEditDialog
from ui.styles import STYLE_DIALOG
from runtime.auto_start import set_auto_start, is_auto_start_enabled


class SettingsDialog(QDialog):
    """设置主窗。关闭后,Config 已经被写回磁盘。"""

    config_changed = Signal()

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("悬浮球设置")
        self.resize(680, 540)
        self.setStyleSheet(STYLE_DIALOG)
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # ---- 标签页 1:按钮管理 ----
        page_btns = QWidget()
        v = QVBoxLayout(page_btns)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(self.list_widget.iconSize())
        v.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("➕ 添加")
        self.btn_edit = QPushButton("✏️ 编辑")
        self.btn_del = QPushButton("🗑️ 删除")
        self.btn_up = QPushButton("↑ 上移")
        self.btn_down = QPushButton("↓ 下移")
        for b in (self.btn_add, self.btn_edit, self.btn_del, self.btn_up, self.btn_down):
            btn_row.addWidget(b)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_del.clicked.connect(self._on_del)
        self.btn_up.clicked.connect(lambda: self._on_move(-1))
        self.btn_down.clicked.connect(lambda: self._on_move(1))

        self.tabs.addTab(page_btns, "📋 按钮管理")

        # ---- 标签页 2:通用设置 ----
        page_general = QWidget()
        form = QFormLayout(page_general)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(32, 96)
        self.size_spin.setSuffix(" px")
        form.addRow("悬浮球大小:", self.size_spin)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        form.addRow("悬浮球透明度:", self.opacity_slider)

        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(50, 200)
        self.radius_spin.setSuffix(" px")
        form.addRow("按钮距悬浮球:", self.radius_spin)

        self.chk_auto_start = QCheckBox("开机自启(写入注册表)")
        form.addRow("", self.chk_auto_start)

        self.chk_start_expanded = QCheckBox("启动时默认展开按钮")
        form.addRow("", self.chk_start_expanded)

        self.chk_click_through = QCheckBox("启用鼠标穿透(默认穿透,鼠标悬停时才可点)")
        form.addRow("", self.chk_click_through)

        # 说明
        info = QLabel(
            "提示:\n"
            "• 设置修改后立即保存,关闭此窗即生效。\n"
            "• 配置文件位于 %APPDATA%\\XuanFuQiu\\config.json"
        )
        info.setStyleSheet("color:#7A8597; font-size:12px;")
        info.setWordWrap(True)
        form.addRow(info)

        self.tabs.addTab(page_general, "⚙️ 通用设置")

        root.addWidget(self.tabs)

        # OK / Cancel
        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.button(QDialogButtonBox.Close).setText("关闭")
        box.rejected.connect(self.reject)
        box.button(QDialogButtonBox.Close).clicked.connect(self.accept)
        root.addWidget(box)

    # ---- 加载 ----
    def _load(self):
        self._refresh_list()
        b = self.config.data.get("ball", {})
        self.size_spin.setValue(int(b.get("size", 56)))
        self.opacity_slider.setValue(int(b.get("opacity", 0.92) * 100))
        self.radius_spin.setValue(int(b.get("radial_radius", 80)))
        self.chk_auto_start.setChecked(is_auto_start_enabled())
        self.chk_start_expanded.setChecked(bool(b.get("start_expanded", False)))
        self.chk_click_through.setChecked(bool(b.get("click_through", True)))

        # 信号连接(放到最后,避免填充时触发保存)
        self.size_spin.valueChanged.connect(self._on_general_changed)
        self.opacity_slider.valueChanged.connect(self._on_general_changed)
        self.radius_spin.valueChanged.connect(self._on_general_changed)
        self.chk_auto_start.stateChanged.connect(self._on_auto_start_changed)
        self.chk_start_expanded.stateChanged.connect(self._on_general_changed)
        self.chk_click_through.stateChanged.connect(self._on_general_changed)

    def _refresh_list(self):
        self.list_widget.clear()
        for b in self.config.data.get("buttons", []):
            label = f"{b.get('icon','📌')}  {b.get('name','(未命名)')}  [{b.get('type','')}]"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, b.get("id"))
            self.list_widget.addItem(item)

    # ---- 按钮管理 ----
    def _selected_id(self):
        it = self.list_widget.currentItem()
        if not it:
            return None
        return it.data(Qt.UserRole)

    def _on_add(self):
        dlg = ButtonEditDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            cfg = dlg.get_config()
            self.config.add_button(cfg)
            self._refresh_list()
            self.config_changed.emit()

    def _on_edit(self):
        bid = self._selected_id()
        if not bid:
            QMessageBox.information(self, "提示", "请先选择一个按钮")
            return
        cur = next((b for b in self.config.data["buttons"] if b.get("id") == bid), None)
        if not cur:
            return
        dlg = ButtonEditDialog(cfg=cur, parent=self)
        if dlg.exec() == QDialog.Accepted:
            new_cfg = dlg.get_config()
            self.config.update_button(bid, new_cfg)
            self._refresh_list()
            self.config_changed.emit()

    def _on_del(self):
        bid = self._selected_id()
        if not bid:
            QMessageBox.information(self, "提示", "请先选择一个按钮")
            return
        cur = next((b for b in self.config.data["buttons"] if b.get("id") == bid), None)
        if not cur:
            return
        ans = QMessageBox.question(
            self, "确认删除",
            f"确定删除按钮「{cur.get('name','')}」吗?"
        )
        if ans == QMessageBox.Yes:
            self.config.remove_button(bid)
            self._refresh_list()
            self.config_changed.emit()

    def _on_move(self, delta: int):
        bid = self._selected_id()
        if not bid:
            return
        self.config.move_button(bid, delta)
        self._refresh_list()
        # 保持选中
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(Qt.UserRole) == bid:
                self.list_widget.setCurrentRow(i)
                break
        self.config_changed.emit()

    # ---- 通用设置 ----
    def _on_general_changed(self, *_):
        self.config.update_ball(
            size=self.size_spin.value(),
            opacity=self.opacity_slider.value() / 100,
            radial_radius=self.radius_spin.value(),
            start_expanded=self.chk_start_expanded.isChecked(),
            click_through=self.chk_click_through.isChecked(),
        )
        self.config_changed.emit()

    def _on_auto_start_changed(self, state):
        enable = bool(state == Qt.Checked)
        ok, msg = set_auto_start(enable)
        if not ok:
            QMessageBox.warning(self, "开机自启", f"设置失败:{msg}")
            self.chk_auto_start.blockSignals(True)
            self.chk_auto_start.setChecked(not enable)
            self.chk_auto_start.blockSignals(False)
