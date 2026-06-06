"""
路径工具:定位配置文件、资源、临时文件等。
"""
import os
import sys
from pathlib import Path


def app_data_dir() -> Path:
    """获取 %APPDATA%\\XuanFuQiu 目录,不存在则创建。"""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    else:
        base = Path.home() / ".config"
    p = base / "XuanFuQiu"
    p.mkdir(parents=True, exist_ok=True)
    return p


def config_path() -> Path:
    return app_data_dir() / "config.json"


def temp_dir() -> Path:
    """HTML 代码类型按钮的临时文件目录。"""
    p = app_data_dir() / "tmp"
    p.mkdir(parents=True, exist_ok=True)
    return p


def resource_dir() -> Path:
    """打包后的资源目录(_MEIPASS)或开发期当前目录。"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent
