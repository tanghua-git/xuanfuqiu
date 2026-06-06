"""
悬浮球课件工具 — 入口
"""
import sys
import os

# 在 Windows 下隐藏 Python 启动时可能闪现的控制台(开发期会显示,打包后用 pythonw.exe)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

from core.paths import config_path
from core.config import Config
from ui.floating_ball import FloatingBall
from ui.styles import STYLE_GLOBAL


def main():
    # 高 DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("XuanFuQiu")
    app.setOrganizationName("XuanFuQiu")
    app.setStyleSheet(STYLE_GLOBAL)
    # 关闭所有窗口时不退出(悬浮球关闭 = 隐藏,真正退出靠托盘)
    app.setQuitOnLastWindowClosed(False)

    cfg = Config(config_path())
    ball = FloatingBall(cfg)
    ball.show()

    # 单实例锁(简易实现)
    try:
        from PySide6.QtNetwork import QLocalServer, QLocalSocket
        sock = QLocalSocket()
        sock.connectToServer("XuanFuQiu_SingleInstance")
        if sock.waitForConnected(300):
            # 已经有实例在跑,激活旧实例后退出
            sock.disconnectFromServer()
            print("悬浮球已在运行。")
            return 0
        # 自己起一个 server
        server = QLocalServer()
        QLocalServer.removeServer("XuanFuQiu_SingleInstance")
        server.listen("XuanFuQiu_SingleInstance")
        server.newConnection.connect(lambda: None)
    except Exception:
        pass

    # 异常钩子:让崩溃时也不至于直接消失(简单打印)
    def excepthook(exc_type, exc_value, tb):
        import traceback
        msg = "".join(traceback.format_exception(exc_type, exc_value, tb))
        sys.stderr.write(msg)
    sys.excepthook = excepthook

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
