"""
PyInstaller runtime hook: 在主脚本运行前,确保 shiboken6 能找到 PySide6 子模块。

PyInstaller 默认的 pyi_rth_pyside6.py 只设置 QT_PLUGIN_PATH 和 qt.conf,
但没解决 shiboken6 C 扩展加载器在 frozen 模式下找不到 PySide6.*.pyd 的问题。

原因:
- 在普通 Python 安装里,PySide6/ 和 shiboken6/ 都在 site-packages/ 同级,
  .pyd 加载时 Windows 自动在同目录找 shiboken6.abi3.dll
- 在 PyInstaller onedir 模式里:
  _internal/PySide6/QtWebEngineCore.pyd
  _internal/shiboken6/shiboken6.abi3.dll
  两个在不同目录,Windows 找不到 shiboken6.abi3.dll

修复:在 PySide6 任何子模块被 import 之前,先 import shiboken6,
这会触发 PySide6 的 __init__.py 中的 os.add_dll_directory() 调用。
"""
import os
import sys


def _pyi_rthook():
    if not getattr(sys, "frozen", False):
        return

    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return

    # 把 shiboken6 目录加到 DLL 搜索路径(Windows 3.8+)
    shiboken_dir = os.path.join(meipass, "shiboken6")
    if os.path.isdir(shiboken_dir):
        try:
            os.add_dll_directory(shiboken_dir)
        except (AttributeError, OSError):
            pass
        # 旧版兼容:也加到 PATH
        os.environ["PATH"] = shiboken_dir + os.pathsep + os.environ.get("PATH", "")

    # 把 PySide6 目录也加进去(可能它有依赖 pyside6.abi3.dll,需要确保 pyside6 目录)
    pyside_dir = os.path.join(meipass, "PySide6")
    if os.path.isdir(pyside_dir):
        try:
            os.add_dll_directory(pyside_dir)
        except (AttributeError, OSError):
            pass

    # 提前 import shiboken6 和 PySide6 主包,
    # 这样 PySide6.__init__ 的 os.add_dll_directory() 和 Shiboken import 都会执行
    try:
        import shiboken6  # noqa: F401
    except Exception:
        pass
    try:
        import PySide6  # noqa: F401
    except Exception:
        pass


_pyi_rthook()
del _pyi_rthook
