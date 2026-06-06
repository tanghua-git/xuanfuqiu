"""
Win32 API 小工具 — 鼠标穿透、窗口置顶、获取窗口尺寸等
"""
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

# 窗口样式
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008

# SetWindowPos 标志
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010


def get_hwnd(window):
    """从 tkinter 窗口获取底层 HWND(Windows)"""
    return int(window.frame(), 16)


def set_click_through(window, enable: bool):
    """切换窗口的鼠标穿透。enable=True 时鼠标点不到该窗口。"""
    try:
        hwnd = get_hwnd(window)
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enable:
            new_style = style | WS_EX_TRANSPARENT | WS_EX_LAYERED
        else:
            new_style = style & ~WS_EX_TRANSPARENT
            new_style |= WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
    except Exception:
        pass


def set_topmost(window, topmost: bool = True):
    """把窗口设为/取消置顶"""
    try:
        hwnd = get_hwnd(window)
        flags = SWP_NOMOVE | SWP_NOSIZE | (0 if topmost else SWP_NOACTIVATE)
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST if topmost else 0,
            0, 0, 0, 0,
            flags
        )
    except Exception:
        pass


def get_screen_size():
    """获取主屏幕大小(像素)"""
    try:
        user32.GetSystemMetrics.restype = wintypes.INT
        SM_CXSCREEN, SM_CYSCREEN = 0, 1
        return user32.GetSystemMetrics(SM_CXSCREEN), user32.GetSystemMetrics(SM_CYSCREEN)
    except Exception:
        return 1920, 1080


def get_cursor_pos():
    """获取当前鼠标位置(屏幕坐标)"""
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y
