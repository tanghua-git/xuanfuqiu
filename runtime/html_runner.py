"""
HTML 统一执行器:把 URL / HTML代码 / HTML文件 三种类型统一转为可加载的资源,
并启动全屏播放窗口。

关键:HTML代码 和 HTML文件 都改用 QWebView.loadHtml() 加载(不走 file:// 协议),
原因是 WebView2 (Edge) 在 sandbox 下加载 file:// 时,经常返回 403 错误。
loadHtml() 是 WebView2 最稳的"内嵌 HTML"方式,直接传内容,不依赖文件访问。

file 类型的 baseUrl 设成 file:// 原路径,这样 HTML 里的相对资源(<img src="x.png">)
仍然能正常解析(走 file:// 访问同目录下的资源,这个是允许的;只有顶层 file:// 加载会 403)。
html 类型的 baseUrl 用 about:blank(代码里一般没有相对资源)。
url 类型继续用 setUrl(https://...),WebView2 走 https 没问题。
"""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl, QObject

from ui.player_window import PlayerWindow


class HtmlRunner(QObject):
    """持有当前播放窗口引用,避免被 GC。"""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current: Optional[PlayerWindow] = None

    def run(self, btn_cfg: dict):
        url_str, html_content = self._resolve(btn_cfg)
        if not url_str and not html_content:
            return
        # 关闭旧的
        if self._current is not None:
            try:
                self._current.close()
                self._current.deleteLater()
            except Exception:
                pass
        self._current = PlayerWindow(
            url_str,
            title=btn_cfg.get("name", ""),
            html_content=html_content,
        )
        self._current.show()

    def _resolve(self, btn_cfg: dict) -> tuple[str, Optional[str]]:
        """返回 (url, html_content)。

        - url        : 用于 setUrl(url) 或 loadHtml(content, baseUrl=url)
        - html_content: 不为空时,PlayerWindow 改用 loadHtml() 加载,不走 file:// 协议
        """
        t = btn_cfg.get("type")
        c = btn_cfg.get("content", "")
        if t == "url":
            if not c:
                return "", None
            if not c.startswith(("http://", "https://", "file://")):
                c = "https://" + c
            return c, None
        if t == "file":
            p = Path(c)
            if not p.exists():
                return "", None
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return "", None
            # baseUrl = 原文件路径(file://),这样 <img src="./x.png"> 这种相对资源
            # 能继续走 file:// 解析(子资源 file:// 是允许的,只有顶层 file:// 加载会被 WebView2 拒绝)
            return QUrl.fromLocalFile(str(p.resolve())).toString(), content
        if t == "html":
            if not c:
                return "", None
            # HTML 代码:不再写临时文件,直接用 loadHtml 传内容(避免 file:// 403)
            # baseUrl 用 about:blank;用户粘贴的代码里通常只有内联 CSS / base64 图片,
            # 不会有外部相对资源
            return "about:blank", c
        return "", None
