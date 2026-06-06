"""
lite HTML 课件播放:用 pywebview 调系统 WebView2 (Edge),全屏打开。
ESC 退出由 WebView2 内 JS 监听 keydown 实现(注入页面)。
"""
import os
import sys
import tempfile
import uuid
import threading
import time
from pathlib import Path
import webview
from core.paths import temp_dir


def _resolve_url(btn_cfg: dict) -> str | None:
    t = btn_cfg.get("type")
    c = btn_cfg.get("content", "")
    if t == "url":
        if not c:
            return None
        if not c.startswith(("http://", "https://", "file://")):
            c = "https://" + c
        return c
    if t == "file":
        p = Path(c)
        if not p.exists():
            return None
        # pywebview 在 Windows 上能直接接受本地路径
        return str(p.resolve())
    if t == "html":
        if not c:
            return None
        td = temp_dir()
        fp = td / f"snippet_{uuid.uuid4().hex[:8]}.html"
        fp.write_text(c, encoding="utf-8")
        return str(fp.resolve())
    return None


# 在 HTML 页面里注入 ESC 关闭脚本(对 url 类型无效,只对生成的临时 html 有效)
ESC_INJECTION_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;height:100%;background:#000;}</style>
</head>
<body>
<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' || e.keyCode === 27) {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.close_window();
        } else {
            window.close();
        }
    }
});
</script>
__BODY__
</body></html>
"""


def _maybe_inject_esc(local_path: str) -> str:
    """如果是临时 html 文件,就在外面包一层 ESC 监听。
    对于 URL 类型不做处理(WebView2 自带 ESC 可能无效,但不影响)。"""
    try:
        p = Path(local_path)
        if p.suffix.lower() in (".html", ".htm"):
            content = p.read_text(encoding="utf-8", errors="replace")
            # 如果内容里没有 <html> 标签,简单包一下
            if "<html" not in content.lower():
                wrapped = ESC_INJECTION_HTML.replace("__BODY__", content)
                p.write_text(wrapped, encoding="utf-8")
    except Exception:
        pass
    return local_path


def open_html(btn_cfg: dict):
    """主入口:打开 HTML 课件全屏播放。"""
    url = _resolve_url(btn_cfg)
    if not url:
        return
    # 仅对生成的临时 html 文件注入 ESC;file/url 跳过
    if btn_cfg.get("type") == "html":
        url = _maybe_inject_esc(url)
    title = btn_cfg.get("name", "课件播放")
    # 屏幕尺寸
    try:
        from lite import win32
        sw, sh = win32.get_screen_size()
    except Exception:
        sw, sh = 1366, 768

    # 用 pywebview 创建并启动
    try:
        window = webview.create_window(
            title=title,
            url=url,
            width=sw,
            height=sh,
            resizable=True,
            fullscreen=False,
            easy_drag=False,
            confirm_close=False,
        )
    except Exception as e:
        # pywebview 创建失败(没装 WebView2 等)→ 用系统浏览器兜底
        import webbrowser
        webbrowser.open(url)
        return

    # 在独立线程跑 webview.start(),主线程可继续做其他事
    def _run():
        try:
            webview.start()
        except Exception:
            pass
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    # 给 webview 一点时间初始化
    time.sleep(0.5)
