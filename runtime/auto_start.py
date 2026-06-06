"""
Windows 开机自启:写 HKCU 注册表 Run 项。
"""
import sys
import os
from pathlib import Path


def _is_windows() -> bool:
    return sys.platform == "win32"


_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "XuanFuQiu"


def _exe_path() -> str:
    """获取当前可执行文件路径(打包后是 .exe,开发期是 python.exe + main.py)。"""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    # 开发模式:用 pythonw.exe(无控制台)启动 main.py
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe")
    runner = pyw if pyw.exists() else py
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{runner}" "{main_py}"'


def is_auto_start_enabled() -> bool:
    if not _is_windows():
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            try:
                val, _ = winreg.QueryValueEx(key, _APP_NAME)
                return bool(val)
            except FileNotFoundError:
                return False
    except Exception:
        return False


def set_auto_start(enable: bool) -> tuple[bool, str]:
    """设置开机自启。返回 (ok, msg)。"""
    if not _is_windows():
        return False, "当前平台非 Windows"
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enable:
                winreg.SetValueEx(
                    key, _APP_NAME, 0, winreg.REG_SZ, _exe_path()
                )
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                except FileNotFoundError:
                    pass
        return True, ""
    except PermissionError:
        return False, "权限不足,请以管理员身份运行"
    except Exception as e:
        return False, str(e)
