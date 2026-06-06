"""
lite 版入口:用 tkinter + pywebview 替代 PySide6 + QtWebEngine,
目标是把打包后的安装包压到 50MB 以内(实际期望 25-30MB)。
"""
import sys
import os

if sys.platform == "win32":
    # 隐藏 Python 启动时的控制台闪烁
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

import tkinter as tk
from core.config import Config
from core.paths import config_path
from lite.styles import apply_ttk_style, COLOR_BG
from lite.floating_ball import FloatingBall


def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏 tk 默认根窗口
    root.title("悬浮球")
    root.config(bg=COLOR_BG)
    apply_ttk_style(root)

    cfg = Config(config_path())
    ball = FloatingBall(root, cfg)

    # 单实例锁(基于文件,简单实现)
    lock_path = os.path.join(os.path.dirname(config_path()), ".lock")
    if os.path.exists(lock_path):
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                old_pid = int(f.read().strip() or "0")
        except Exception:
            pass
    try:
        with open(lock_path, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    def on_close():
        try:
            os.remove(lock_path)
        except OSError:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # ESC 退出
    root.bind("<Escape>", lambda e: on_close())

    try:
        root.mainloop()
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
