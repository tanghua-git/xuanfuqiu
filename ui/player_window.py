"""
HTML 全屏播放窗:置顶、Frameless、ESC 退出、不主动抢焦点以免打断 PPT。

使用 PySide6.QtWebView(走系统 WebView2,Win10+ 自带)替代 QtWebEngine(自带 Chromium 200MB+),
让打包后的安装包能从 160MB 降到 < 50MB。API 与 QWebEngineView 完全兼容(setUrl/load)。
"""
import sys
import os
import traceback
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QApplication, QVBoxLayout
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QShortcut, QKeySequence

# 优先用 QtWebView(走系统 WebView2,极小),如果导入失败再 fallback
_WEBVIEW_IMPORT_ERROR: str = ""
try:
    from PySide6.QtWebView import QWebView
    HAS_WEBVIEW = True
except Exception as _e:
    HAS_WEBVIEW = False
    QWebView = None
    _WEBVIEW_IMPORT_ERROR = f"{type(_e).__name__}: {_e}"


def _diagnose_webview() -> str:
    """在 WebView 不可用时,生成诊断信息。"""
    lines = []
    lines.append("QtWebView 未能加载(将无法显示 HTML 课件)。")
    lines.append("")
    lines.append(f"导入错误: {_WEBVIEW_IMPORT_ERROR}")
    lines.append("")
    lines.append("WebView 走系统 WebView2(Win10 1809+ / Win11 自带),")
    lines.append("旧版 Windows(Win7/Win8)需手动安装:")
    lines.append("  https://developer.microsoft.com/microsoft-edge/webview2/")
    return "\n".join(lines)


class PlayerWindow(QWidget):
    """全屏 HTML 播放窗。

    关键设计:
    - WindowStaysOnTopHint:置顶,叠在 PPT 放映之上
    - 不主动 activateWindow:不抢焦点,不影响 PPT 内部逻辑
    - ESC / 右上角 X 关闭,关闭后焦点自然回到原应用
    """

    def __init__(self, url: str, title: str = "", html_content: str = "", parent=None):
        """
        Args:
            url: 显示用的 URL(title 展示 / baseUrl 解析)
            title: 窗口标题
            html_content: 如果非空,用 loadHtml() 加载(不走 file:// 协议,避免 WebView2 403);
                         为空则用 setUrl(url) 加载(用于 https:// 类型的网页)
            parent: 父窗口
        """
        super().__init__(parent)
        self.url = url
        self.title = title
        self._html_content = html_content
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(self.title or "课件播放")
        # 关键:Tool + StaysOnTopHint + 不显示任务栏
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #000000;")

        # 顶栏 — 常驻显示(关键:WebView2 嵌入到 QWidget 后会吃掉鼠标事件,
        # 主窗口的 mouseMoveEvent 收不到,自动隐藏逻辑不可靠,
        # 所以改成顶栏一直显示,32px 半透明,占空间小但 ✕ 永远能找到)
        self._topbar = QWidget(self)
        self._topbar.setFixedHeight(32)
        self._topbar.setStyleSheet(
            "background-color: rgba(20,22,28,210);"
        )
        top_layout = QHBoxLayout(self._topbar)
        top_layout.setContentsMargins(10, 0, 6, 0)
        top_layout.setSpacing(4)
        self._title_label = QLabel(self.title or "课件播放")
        self._title_label.setStyleSheet("color: #E6EAF2; font-size: 12px;")
        top_layout.addWidget(self._title_label)
        top_layout.addStretch()

        # ESC/F11 提示(让用户知道快捷键)
        self._hint_label = QLabel("ESC 关闭  ·  F11 全屏")
        self._hint_label.setStyleSheet(
            "color: #8A93A6; font-size: 11px; padding-right: 4px;"
        )
        top_layout.addWidget(self._hint_label)

        self._btn_full = QPushButton("⛶")
        self._btn_full.setFixedSize(26, 26)
        self._btn_full.setStyleSheet(
            "QPushButton{background:transparent;color:#E6EAF2;border:none;"
            "border-radius:3px;}"
            "QPushButton:hover{background:#3A4250;}"
        )
        self._btn_full.setToolTip("切换全屏(F11)")
        self._btn_full.clicked.connect(self._toggle_full)
        top_layout.addWidget(self._btn_full)

        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(26, 26)
        self._btn_close.setStyleSheet(
            "QPushButton{background:transparent;color:#E6EAF2;border:none;"
            "border-radius:3px;font-size:14px;}"
            "QPushButton:hover{background:#E74C3C;color:#FFFFFF;}"
        )
        self._btn_close.setToolTip("关闭(ESC)")
        self._btn_close.clicked.connect(self.close)
        top_layout.addWidget(self._btn_close)

        # WebView(QtWebView 走系统 WebView2,小;失败时显示诊断信息)
        # 注意:QWebView 继承自 QWindow,不是 QWidget,不能直接放进 QVBoxLayout。
        # 必须用 QWidget.createWindowContainer() 包一层才能嵌入到 QWidget 里。
        # 关键:优先用 loadHtml() 加载(避免 WebView2 走 file:// 协议返回 403)
        if HAS_WEBVIEW:
            self._webview_raw = QWebView()
            if self._html_content:
                # loadHtml(content, baseUrl) — 直接传 HTML 字符串,不依赖 file://
                # baseUrl 用于解析 HTML 里的相对路径(file:// 类型 → 子资源走 file:// 同目录)
                self._webview_raw.loadHtml(self._html_content, QUrl(self.url))
            else:
                # https:// 类型,WebView2 走 https,不会 403
                self._webview_raw.setUrl(QUrl(self.url))
            self.browser = QWidget.createWindowContainer(self._webview_raw, self)
        else:
            diag = _diagnose_webview()
            self.browser = QLabel(diag, self)
            self.browser.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.browser.setWordWrap(True)
            self.browser.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.browser.setStyleSheet(
                "color:#E6AF72; font-family: Consolas, 'Courier New', monospace;"
                " font-size: 12px; padding: 18px; line-height: 1.5;"
                " background-color: #1A1D24;"
            )

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._topbar)
        layout.addWidget(self.browser, 1)

        # 顶栏始终在 WebView 之上(WebView2 嵌入后用 raise_ 确保不被覆盖)
        self._topbar.raise_()

        # 全局快捷键:ESC 关闭 / F11 切全屏
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)
        QShortcut(QKeySequence("F11"), self, self._toggle_full)

        # 顶栏一直显示,不自动隐藏
        self._topbar.show()

    # ---- 全屏控制 ----
    def showEvent(self, e):
        super().showEvent(e)
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.showFullScreen()

    def _toggle_full(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ---- 顶栏自动隐藏(已禁用)----
    # 顶栏改成常驻显示,不再自动隐藏。
    # 原逻辑:鼠标移动 → 显示顶栏 → 2.5s 不动就隐藏
    # 新逻辑:顶栏一直显示(WebView2 嵌入后 mouseMoveEvent 收不到,自动隐藏不可靠)
    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)

    def closeEvent(self, e):
        try:
            if HAS_WEBVIEW and hasattr(self, "_webview_raw"):
                self._webview_raw.stop()
        except Exception:
            pass
        super().closeEvent(e)
