"""
悬浮球主控件:
- 圆球绘制
- 5px 阈值区分点击/拖拽
- 鼠标穿透 + hover 取消穿透
- 单击展开/折叠径向菜单
- 右键菜单(添加按钮/设置/退出)
- 位置持久化
"""
from PySide6.QtWidgets import QWidget, QMenu, QApplication, QSystemTrayIcon
from PySide6.QtCore import Qt, QTimer, QPoint, QDateTime
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QCursor, QIcon, QPixmap, QPainterPath

from core.config import Config
from ui.radial_menu import RadialMenu
from ui.settings_dialog import SettingsDialog
from ui.styles import STYLE_MENU
from runtime.html_runner import HtmlRunner


class FloatingBall(QWidget):
    """悬浮球本体。"""

    DRAG_THRESHOLD = 5  # 像素:大于此值视为拖拽,小于视为点击

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._drag_pos: QPoint | None = None
        self._expanded = False
        self._radial: RadialMenu | None = None
        self._runner = HtmlRunner(self)
        self._tray: QSystemTrayIcon | None = None
        self._is_click_through = False  # 当前是否处于穿透模式
        self._modal_dialog_open = False  # 模态对话框(添加/编辑)是否正在打开,用于阻止 _check_hover_state 自动折叠

        self._setup_window()
        self._setup_tray()
        self._restore_geometry()
        self._restore_click_through()
        self._restore_startup_state()

        # 关键:用定时器轮询鼠标位置来切换穿透模式
        # (因为 WindowTransparentForInput 窗口不会触发 enterEvent)
        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(120)
        self._hover_timer.timeout.connect(self._check_hover_state)
        self._hover_timer.start()

    # ---------- 窗口 ----------
    def _setup_window(self):
        b = self.config.data["ball"]
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        size = int(b.get("size", 56))
        self.resize(size, size)
        self.setWindowOpacity(float(b.get("opacity", 0.92)))
        self.setMouseTracking(True)

    def _restore_geometry(self):
        pos = self.config.data["ball"].get("position", {"x": 100, "y": 100})
        # 边界保护:确保悬浮球不会跑到所有屏幕之外
        screens = QApplication.screens()
        valid = False
        for s in screens:
            geo = s.availableGeometry()
            if geo.contains(QPoint(pos["x"] + 20, pos["y"] + 20)):
                valid = True; break
        if not valid:
            primary = QApplication.primaryScreen()
            if primary:
                geo = primary.availableGeometry()
                pos = {
                    "x": geo.right() - 100,
                    "y": geo.bottom() - 100,
                }
        self.move(pos["x"], pos["y"])
        self.config.data["ball"]["position"] = pos

    def _restore_click_through(self):
        if self.config.data["ball"].get("click_through", True):
            self._set_click_through(True)
        else:
            self._set_click_through(False)

    def _restore_startup_state(self):
        if self.config.data["ball"].get("start_expanded", False):
            QTimer.singleShot(300, self._expand)

    # ---------- 托盘 ----------
    def _setup_tray(self):
        # 不强依赖托盘;若系统不支持则跳过
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(self)
        icon = self._build_tray_icon()
        self._tray.setIcon(icon)
        self._tray.setToolTip("悬浮球课件工具")
        menu = QMenu()
        menu.addAction("⚙️ 打开设置", self._open_settings)
        menu.addSeparator()
        menu.addAction("❌ 退出", QApplication.quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _build_tray_icon(self) -> QIcon:
        pm = QPixmap(32, 32)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor("#4A90E2")))
        p.setPen(QPen(QColor(255, 255, 255, 200), 1))
        p.drawEllipse(2, 2, 28, 28)
        p.setPen(QColor(255, 255, 255))
        f = p.font(); f.setPointSize(14); p.setFont(f)
        p.drawText(pm.rect(), Qt.AlignCenter, "📚")
        p.end()
        return QIcon(pm)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._open_settings()

    # ---------- 绘制 ----------
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)

        # 球体(径向渐变,模拟 3D)
        from PySide6.QtGui import QRadialGradient
        grad = QRadialGradient(
            rect.topLeft().x() + rect.width() * 0.4,
            rect.topLeft().y() + rect.height() * 0.35,
            rect.width() * 0.7,
        )
        color = self.config.data["ball"].get("color", "#4A90E2")
        grad.setColorAt(0, QColor(255, 255, 255, 230))
        grad.setColorAt(0.55, QColor(self._lighten(color, 0.2)))
        grad.setColorAt(1, QColor(self._darken(color, 0.2)))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(255, 255, 255, 220), 2))
        p.drawEllipse(rect)

        # 中心图标
        icon_text = self.config.data["ball"].get("icon", "📚")
        p.setPen(QColor(255, 255, 255))
        f = p.font()
        f.setPointSize(int(self.width() * 0.36))
        f.setBold(True)
        p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, icon_text)

    @staticmethod
    def _lighten(hex_color: str, ratio: float) -> QColor:
        c = QColor(hex_color)
        return QColor(
            min(255, c.red() + int((255 - c.red()) * ratio)),
            min(255, c.green() + int((255 - c.green()) * ratio)),
            min(255, c.blue() + int((255 - c.blue()) * ratio)),
        )

    @staticmethod
    def _darken(hex_color: str, ratio: float) -> QColor:
        c = QColor(hex_color)
        return QColor(
            int(c.red() * (1 - ratio)),
            int(c.green() * (1 - ratio)),
            int(c.blue() * (1 - ratio)),
        )

    # ---------- 鼠标事件 ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            # 记录按下时的全局坐标,用于后续判断位移
            self._press_global = e.globalPosition().toPoint()
            self._drag_pos = self._press_global - self.frameGeometry().topLeft()
            # 点击后 1 秒内,即使鼠标光标轻微抖动出界,也不恢复穿透
            self._click_lock_until_ms = QDateTime.currentMSecsSinceEpoch() + 1000
        elif e.button() == Qt.RightButton:
            self.contextMenuEvent(None)

    def mouseMoveEvent(self, e):
        if (e.buttons() & Qt.LeftButton) and self._drag_pos is not None:
            cur = e.globalPosition().toPoint()
            # 用按下时的全局坐标计算真实位移(关键:之前用 - self.pos() 永远为 0)
            moved = (cur - self._press_global).manhattanLength()
            if moved > self.DRAG_THRESHOLD:
                self.move(cur - self._drag_pos)
                e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._press_global is not None:
            moved = (e.globalPosition().toPoint() - self._press_global).manhattanLength()
            if moved < self.DRAG_THRESHOLD:
                self._toggle_expand()
            else:
                self._save_position()
            self._press_global = None
            self._drag_pos = None

    def enterEvent(self, e):
        # 仅作为快速路径;主要靠 _check_hover_state 定时器
        if self.config.data["ball"].get("click_through", True):
            self._set_click_through(False)

    def leaveEvent(self, e):
        # 不用主动恢复,由 _check_hover_state 定时器统一处理
        pass

    # ---------- 鼠标穿透 ----------
    def _set_click_through(self, enable: bool):
        """切换穿透模式。带状态跟踪,避免重复 setWindowFlags 导致闪烁。"""
        if self._is_click_through == enable:
            return
        flags = self.windowFlags()
        if enable:
            flags = flags | Qt.WindowTransparentForInput
        else:
            flags = flags & ~Qt.WindowTransparentForInput
        self.setWindowFlags(flags)
        self._is_click_through = enable
        # show() 让新 flag 生效
        self.show()
        self.raise_()

    def _check_hover_state(self):
        """每 120ms 轮询鼠标位置,自动切换穿透模式。
        这是核心机制:WindowsTransparentForInput 窗口收不到 enterEvent,
        所以必须主动检测鼠标位置。"""
        # 如果用户关掉了穿透,确保关闭
        if not self.config.data["ball"].get("click_through", True):
            if self._is_click_through:
                self._set_click_through(False)
            return

        # 1 秒防抖期:刚点击过,即使鼠标短暂离开也保持可点击
        if QDateTime.currentMSecsSinceEpoch() < getattr(self, "_click_lock_until_ms", 0):
            return

        # 模态对话框正在打开时(添加/编辑/设置),绝对不要自动折叠菜单
        # 之前的问题:用户点 "+" → 对话框弹出 → 鼠标在对话框上 → 120ms 后菜单被自动折叠
        # → 用户点 OK 后,虽然 update_buttons 重建了菜单,但瞬间又被折叠,新 "+" 看不到
        # → 用户以为"添加失败"或"无法继续添加"
        if getattr(self, "_modal_dialog_open", False) and self._expanded:
            return

        cursor_pos = QCursor.pos()
        # 命中区比可视球大 6px,让光标更易"踩上"
        ball_rect = self.frameGeometry().adjusted(-6, -6, 6, 6)
        is_over_ball = ball_rect.contains(cursor_pos)

        is_over_radial = False
        if self._radial is not None and self._radial.isVisible():
            radial_rect = self._radial.frameGeometry().adjusted(-6, -6, 6, 6)
            is_over_radial = radial_rect.contains(cursor_pos)

        should_clickable = is_over_ball or is_over_radial

        if should_clickable and self._is_click_through:
            self._set_click_through(False)
        elif not should_clickable and not self._is_click_through:
            self._set_click_through(True)
            # 鼠标离开,自动折叠
            if self._expanded:
                self._collapse()

    # ---------- 展开/折叠 ----------
    def _toggle_expand(self):
        # 一律展开/折叠,0 按钮时菜单里会显示一个 "+" 提示按钮
        if self._expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        if self._expanded:
            return
        self._expanded = True
        if self._radial is None:
            self._radial = RadialMenu(self, self.config.data.get("buttons", []))
        else:
            self._radial.update_buttons(self.config.data.get("buttons", []))
        self._radial.show_around(self)

    def _collapse(self):
        if not self._expanded:
            return
        self._expanded = False
        if self._radial:
            self._radial.hide_animated()

    # ---------- 按钮触发 ----------
    def on_button_triggered(self, btn_cfg: dict):
        self._runner.run(btn_cfg)
        # 触发后自动折叠
        QTimer.singleShot(100, self._collapse)

    # ---------- 右键菜单 ----------
    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.setStyleSheet(STYLE_MENU)
        menu.addAction("➕ 添加按钮", self._on_add_button)
        menu.addAction("⚙️ 设置", self._open_settings)
        menu.addSeparator()
        menu.addAction("📂 打开配置目录", self._open_config_dir)
        menu.addSeparator()
        menu.addAction("❌ 退出", QApplication.quit)
        menu.exec(QCursor.pos())

    def _on_add_button(self):
        from ui.button_edit import ButtonEditDialog
        from PySide6.QtWidgets import QDialog
        # 关键修复:用 self 当 parent,exec() 会自己处理 show/raise/activate。
        # 之前用 parent=None + 显式 show + exec() 的写法在 Windows 上有副作用:
        # 1) 旧 dialog 没法被 parent 回收,会泄露并干扰后续焦点
        # 2) show() + exec() 同时调用,模态状态在第二次打开时可能错乱,导致 OK 看似点了但其实没接受
        dlg = ButtonEditDialog(parent=self)
        # 标记"模态对话框正在打开",让 _check_hover_state 不要在这期间自动折叠菜单
        self._modal_dialog_open = True
        # 显式居中(避免副屏/被遮挡)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            dlg.move(
                geo.center().x() - dlg.width() // 2,
                geo.center().y() - dlg.height() // 2,
            )
        result = dlg.exec()
        # 不管 accept/reject,都要在 dlg 销毁前拿配置
        cfg = None
        if result == QDialog.Accepted:
            cfg = dlg.get_config()
        dlg.deleteLater()
        # 用 try/finally 保证 _modal_dialog_open 一定被复位
        try:
            if cfg is not None:
                # 1) 立即写 config + 落盘
                self.config.add_button(cfg)
                # 2) 用 QTimer.singleShot(0, ...) 把菜单更新推迟到下一个事件循环
                #    关键修复:之前直接在 dlg.exec() 返回后立刻操作 _radial,有时 dialog 还没完全销毁
                #    (WA_DeleteOnClose 的 deleteLater 还在 pending),就触发对旧 widget 集合的访问,
                #    导致 update_buttons 走异常路径、新按钮实际没创建出来
                QTimer.singleShot(0, self._apply_added_button)
                # 续 8 秒点击锁,给用户充足时间
                self._click_lock_until_ms = QDateTime.currentMSecsSinceEpoch() + 8000
        finally:
            self._modal_dialog_open = False

    def _apply_added_button(self):
        """在 dlg 完全销毁后的下一个事件循环里,重建/刷新菜单并显示。"""
        try:
            btns = self.config.data.get("buttons", [])
            if self._radial is None:
                self._radial = RadialMenu(self, btns)
            else:
                self._radial.update_buttons(btns)
            self._expanded = True
            self._radial.show_around(self)
        except Exception as exc:
            import traceback
            traceback.print_exc()

    def _open_settings(self):
        dlg = SettingsDialog(self.config, parent=None)
        dlg.config_changed.connect(self._on_config_changed)
        dlg.exec()

    def _on_config_changed(self):
        # 重新加载某些属性
        b = self.config.data["ball"]
        size = int(b.get("size", 56))
        if size != self.width():
            self.resize(size, size)
        self.setWindowOpacity(float(b.get("opacity", 0.92)))

        # 关键:无论 _radial 是否存在,都刷新菜单
        # 场景:用户在设置窗里加按钮 → 关闭设置窗 → 期望看到新按钮
        # 之前 _radial 为 None 时什么都不做,用户看不到反馈
        btns = self.config.data.get("buttons", [])
        if self._radial is None and btns:
            self._radial = RadialMenu(self, btns)
        elif self._radial is not None:
            self._radial.update_buttons(btns)

        # 有按钮 + 当前未展开 → 自动展开,让用户立即看到效果
        if btns and not self._expanded:
            self._expand()
        elif self._radial is not None and self._expanded:
            self._radial.show_around(self)

        self.update()  # 触发重绘
        # 重新应用穿透
        self._set_click_through(b.get("click_through", True))

    def _open_config_dir(self):
        import os
        from core.paths import app_data_dir
        os.startfile(str(app_data_dir()))

    def _save_position(self):
        self.config.data["ball"]["position"] = {"x": self.x(), "y": self.y()}
        self.config.save()

    def moveEvent(self, e):
        # 拖动过程中不频繁写盘,仅在 mouseRelease 中写一次
        super().moveEvent(e)
