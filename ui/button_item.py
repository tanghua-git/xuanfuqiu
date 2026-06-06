"""
单个快捷按钮:圆形,带图标,点击触发信号。
"""
from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QColor, QFont
from ui.styles import STYLE_BUTTON_ITEM


class ButtonItem(QPushButton):
    """悬浮球周围的一个快捷按钮。"""

    triggered = Signal(dict)  # 发射按钮配置

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setFixedSize(56, 56)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(self._tooltip_text())
        self.setStyleSheet(STYLE_BUTTON_ITEM)

        # 文本 = 图标(emoji 或图片路径)
        icon = cfg.get("icon", "📌")
        self.setText(icon)
        f = self.font()
        f.setPointSize(16)
        self.setFont(f)

        # 阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        # 入场缩放动画
        self._scale_anim = QPropertyAnimation(self, b"geometry")
        self._scale_anim.setDuration(220)
        self._scale_anim.setEasingCurve(QEasingCurve.OutBack)

        self.clicked.connect(lambda: self.triggered.emit(self.cfg))

    def _tooltip_text(self) -> str:
        name = self.cfg.get("name", "未命名")
        t = self.cfg.get("type", "")
        type_map = {"url": "网址", "html": "HTML代码", "file": "HTML文件"}
        return f"{name}\n类型:{type_map.get(t, t)}"

    def animate_in(self, target_rect):
        self._scale_anim.stop()
        start = target_rect
        # 从中心点极小开始放大
        cx, cy = target_rect.center().x(), target_rect.center().y()
        tiny = target_rect
        tiny.setSize(QSize(1, 1))
        tiny.moveCenter(target_rect.center())
        self._scale_anim.setStartValue(tiny)
        self._scale_anim.setEndValue(target_rect)
        self.setGeometry(tiny)
        self.show()
        self._scale_anim.start()
