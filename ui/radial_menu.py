"""
径向菜单:在悬浮球周围圆周上等距分布若干 ButtonItem。
"""
import math
from typing import List

from PySide6.QtWidgets import QWidget, QPushButton, QMenu
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QEvent
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPolygonF, QCursor

from ui.button_item import ButtonItem
from ui.styles import STYLE_PLACEHOLDER, STYLE_MENU


class RadialMenu(QWidget):
    """承载若干 ButtonItem 的容器,绘制连接线/装饰(可选)。"""

    def __init__(self, anchor: QWidget, buttons_cfg: List[dict], parent=None):
        super().__init__(parent)
        self.anchor = anchor  # 悬浮球控件
        self.button_items: List[QPushButton] = []
        self._ring_radius = 0  # 画圆环用
        self._build(buttons_cfg)
        # 透明背景
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
            # 注意:不能加 WindowTransparentForInput,否则整个窗口(含按钮)都收不到鼠标事件
        )

    def _build(self, buttons_cfg):
        # 关键修复 1:"+" 永远在 index 0(顶部 -90°),不管有几个真实按钮都不会动
        # 这样用户永远知道 "+" 在球的正上方
        placeholder = QPushButton("➕", self)
        placeholder.setFixedSize(56, 56)
        placeholder.setStyleSheet(STYLE_PLACEHOLDER)
        placeholder.setCursor(Qt.PointingHandCursor)
        placeholder.setToolTip("点击添加新按钮(绿色虚线,在球正上方)")
        placeholder.clicked.connect(self._on_placeholder_clicked)
        self.button_items.append(placeholder)

        for cfg in buttons_cfg:
            item = ButtonItem(cfg, self)
            item.triggered.connect(self._on_item_triggered)
            self.button_items.append(item)

        # 关键修复 2:对每个子按钮安装事件过滤器
        # 这样无论右键点哪个按钮(真实按钮 / "+" / 菜单空白),都能弹出"添加"菜单
        for item in self.button_items:
            item.installEventFilter(self)

    def _on_placeholder_clicked(self):
        # 关键:点占位按钮时,立刻延长 5 秒点击锁,避免对话框打开后
        # _check_hover_state 把菜单自动折叠,导致用户点 OK 后看不到新菜单
        if hasattr(self.anchor, "_click_lock_until_ms"):
            from PySide6.QtCore import QDateTime
            self.anchor._click_lock_until_ms = QDateTime.currentMSecsSinceEpoch() + 5000
        if hasattr(self.anchor, "_on_add_button"):
            self.anchor._on_add_button()

    # 关键修复 3:事件过滤器 — 把子按钮上的右键也接管过来
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            self._show_context_menu()
            return True   # 事件已被消费,不再向下传递
        return super().eventFilter(obj, event)

    def _show_context_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(STYLE_MENU)
        menu.addAction("➕ 添加按钮", self._on_placeholder_clicked)
        if hasattr(self.anchor, "_open_settings"):
            menu.addAction("⚙️ 打开设置", self.anchor._open_settings)
        menu.exec(QCursor.pos())

    # 兜底:菜单背景的右键
    def contextMenuEvent(self, e):
        self._show_context_menu()

    def _on_item_triggered(self, cfg):
        # 转发给悬浮球,由悬浮球调用 html_runner
        if hasattr(self.anchor, "on_button_triggered"):
            self.anchor.on_button_triggered(cfg)

    # ---- 布局 ----
    def layout_around(self, radius: int = 80):
        n = len(self.button_items)
        if n == 0:
            return
        self._ring_radius = radius  # 画圆环用

        anchor_rect = self.anchor.frameGeometry()
        btn_size = 56
        # 容器尺寸 = 球 + (半径 + 按钮) * 2,留出足够边距
        size = QSize(
            anchor_rect.width() + (radius + btn_size) * 2,
            anchor_rect.height() + (radius + btn_size) * 2,
        )
        self.resize(size)

        # 容器中心对齐悬浮球中心 + 屏幕边缘保护
        cx_global = anchor_rect.center().x()
        cy_global = anchor_rect.center().y()
        container_left = cx_global - size.width() // 2
        container_top = cy_global - size.height() // 2
        container_left, container_top = self._clamp_to_screens(
            container_left, container_top, size.width(), size.height()
        )
        self.move(container_left, container_top)

        # 按钮位置(相对容器)
        btn_size = 56
        cx, cy = size.width() // 2, size.height() // 2
        for i, item in enumerate(self.button_items):
            angle_deg = self._angle_for(i, n)
            rad = math.radians(angle_deg)
            x = int(cx + math.cos(rad) * radius - btn_size / 2)
            y = int(cy + math.sin(rad) * radius - btn_size / 2)
            target = QRect(x, y, btn_size, btn_size)
            # ButtonItem 有 animate_in 入场动画;占位 QPushButton 没有,直接定位
            if hasattr(item, "animate_in"):
                item.animate_in(target)
            else:
                item.setGeometry(target)
                item.show()

    def paintEvent(self, e):
        """画两个圆环 + 球心连到每个按钮的辅助线,布局一目了然。"""
        if not self.button_items or self._ring_radius <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = self.width() // 2
        cy = self.height() // 2

        # 主圆环(虚线)— 经过每个按钮中心,直观显示布局
        pen = QPen(QColor(120, 200, 255, 140), 1, Qt.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPoint(cx, cy), self._ring_radius, self._ring_radius)

        # 球本身的小圆(指示中心位置,即使球被遮挡也能看到圆心)
        anchor_rect = self.anchor.frameGeometry()
        # 球心在容器中的位置 = 球的全局中心 - 容器的全局位置
        ball_cx_in_container = (anchor_rect.center().x() - self.x())
        ball_cy_in_container = (anchor_rect.center().y() - self.y())
        ball_r = anchor_rect.width() // 2
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPoint(ball_cx_in_container, ball_cy_in_container),
                      ball_r, ball_r)

    @staticmethod
    def _angle_for(i: int, n: int) -> float:
        """起点正上方,顺时针均布。"""
        if n == 1:
            return -90
        step = 360 / n
        return -90 + i * step

    @staticmethod
    def _clamp_to_screens(left: int, top: int, w: int, h: int):
        """多显示器边缘保护:把矩形平移到所有屏幕的并集范围内。"""
        from PySide6.QtWidgets import QApplication
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")
        for s in QApplication.screens():
            g = s.availableGeometry()
            min_x = min(min_x, g.left())
            min_y = min(min_y, g.top())
            max_x = max(max_x, g.right())
            max_y = max(max_y, g.bottom())
        cur_cx = left + w // 2
        cur_cy = top + h // 2
        # 中心点不在屏幕并集内时,把它拉回最近的可视中心
        if not (min_x <= cur_cx <= max_x) or not (min_y <= cur_cy <= max_y):
            target_cx = max(min_x, min(cur_cx, max_x))
            target_cy = max(min_y, min(cur_cy, max_y))
            left = target_cx - w // 2
            top = target_cy - h // 2
        return left, top

    @staticmethod
    def _compute_container_size(anchor_rect: QRect, radius: int) -> QSize:
        btn_size = 56
        d = anchor_rect.width() + (radius + btn_size) * 2
        return QSize(d, d)

    # ---- 显示/隐藏 ----
    def show_around(self, anchor: QWidget):
        radius = anchor.config.data.get("ball", {}).get("radial_radius", 80)
        self.layout_around(radius)
        self.show()
        self.raise_()

    def hide_animated(self, on_finished=None):
        # 简单直接隐藏;若需要可在此处做缩小动画
        self.hide()
        if on_finished:
            on_finished()

    def update_buttons(self, buttons_cfg: List[dict]):
        """刷新按钮列表(用于设置窗修改后)。"""
        for item in self.button_items:
            # 关键修复:先 hide,再 setParent(None) + deleteLater()
            # 否则 setParent(None) 会让旧按钮瞬间变成顶层窗口,
            # 虽然 Qt 默认会隐藏它,但与新按钮位置重叠,可能干扰事件分发
            item.hide()
            item.setParent(None)
            item.deleteLater()
        self.button_items.clear()
        self._build(buttons_cfg)
        # 关键:让新占位按钮立即出现在正确位置
        # (否则要等下一次 show_around,期间用户看不到 "+")
        if self._ring_radius > 0:
            self.layout_around(self._ring_radius)
