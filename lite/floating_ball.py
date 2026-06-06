"""
lite 浮球:tk.Toplevel 透明球,鼠标穿透 + hover 检测,
单击展开径向菜单,右键弹出添加菜单。
"""
import os
import sys
import tkinter as tk
from tkinter import Menu
from core.config import Config
from lite.styles import COLOR_BG, COLOR_FG, FONT_NORMAL
from lite import win32
from lite.radial_menu import RadialMenu
from lite.button_edit import ButtonEditDialog
from lite.settings_dialog import SettingsDialog
from lite.player_window import open_html


def _rgba(hex_color: str, alpha: float) -> str:
    """hex 颜色 → tkinter 接受的 #RRGGBB(忽略 alpha,tkinter 不支持真 alpha)。"""
    return hex_color


class FloatingBall:
    DRAG_THRESHOLD = 5
    HOVER_POLL_MS = 120

    def __init__(self, root: tk.Tk, config: Config):
        self.root = root
        self.config = config
        self._drag_pos = None
        self._press_pos = None
        self._expanded = False
        self._radial: RadialMenu | None = None
        self._is_click_through = False
        self._modal_dialog_open = False
        self._click_lock_until_ms = 0

        ball_cfg = self.config.data["ball"]
        self.size = int(ball_cfg.get("size", 56))
        self.color = ball_cfg.get("color", "#4A90E2")
        self.icon_text = ball_cfg.get("icon", "📚")
        self.opacity = float(ball_cfg.get("opacity", 0.92))

        # 主 Toplevel
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)  # 无边框
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", self.opacity)
        self.win.config(bg=COLOR_BG)
        # 关键:用一个特殊颜色做透明 key,然后用这个颜色画所有"不可见"区域
        # 但球本身要可见 — 所以我们用 canvas 画圆
        self.canvas = tk.Canvas(
            self.win, width=self.size, height=self.size,
            bg=COLOR_BG, highlightthickness=0, bd=0,
        )
        self.canvas.pack()
        self._draw_ball()
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)

        # 位置
        pos = self._restore_geometry()
        self.win.geometry(f"{self.size}x{self.size}+{pos['x']}+{pos['y']}")
        win32.set_topmost(self.win, True)
        self._set_click_through(bool(ball_cfg.get("click_through", True)))

        # 轮询 hover
        self._hover_after_id = None
        self._schedule_hover_check()

        # 单实例已在 main.py 处理

    # ---------------- 绘制 ----------------
    def _draw_ball(self):
        c = self.canvas
        s = self.size
        # 渐变近似:外圈深 + 内圈浅
        c.delete("all")
        # 主体圆
        c.create_oval(
            2, 2, s - 2, s - 2,
            fill=self.color, outline="#FFFFFF", width=2,
            tags="ball",
        )
        # 高光小圆(伪 3D)
        c.create_oval(
            s * 0.28, s * 0.20, s * 0.55, s * 0.42,
            fill="#FFFFFF", outline="", stipple="gray25", tags="hl",
        )
        # 中心图标
        c.create_text(
            s // 2, s // 2 + 1, text=self.icon_text,
            fill="white", font=(self._emoji_font(), int(s * 0.40), "bold"),
            tags="icon",
        )

    @staticmethod
    def _emoji_font():
        # Windows 上 emoji 用 Segoe UI Emoji 比较稳
        return "Segoe UI Emoji"

    # ---------------- 鼠标事件 ----------------
    def _on_press(self, e):
        self._press_pos = (e.x_root, e.y_root)
        self._drag_pos = (e.x_root - self.win.winfo_x(),
                          e.y_root - self.win.winfo_y())
        # 1 秒防抖
        import time
        self._click_lock_until_ms = int(time.time() * 1000) + 1000

    def _on_drag(self, e):
        if self._press_pos is None:
            return
        dx = e.x_root - self._press_pos[0]
        dy = e.y_root - self._press_pos[1]
        if abs(dx) + abs(dy) > self.DRAG_THRESHOLD:
            nx = e.x_root - self._drag_pos[0]
            ny = e.y_root - self._drag_pos[1]
            self.win.geometry(f"+{nx}+{ny}")

    def _on_release(self, e):
        if self._press_pos is None:
            return
        dx = e.x_root - self._press_pos[0]
        dy = e.y_root - self._press_pos[1]
        if abs(dx) + abs(dy) < self.DRAG_THRESHOLD:
            self._toggle_expand()
        else:
            self._save_position()
        self._press_pos = None
        self._drag_pos = None

    def _on_right_click(self, e):
        self._show_context_menu(e.x_root, e.y_root)

    def _on_enter(self, e):
        if self.config.data["ball"].get("click_through", True):
            self._set_click_through(False)

    def _on_leave(self, e):
        pass  # 由 _check_hover_state 统一管理

    # ---------------- 鼠标穿透 ----------------
    def _set_click_through(self, enable: bool):
        if self._is_click_through == enable:
            return
        win32.set_click_through(self.win, enable)
        self._is_click_through = enable
        # 重新置顶(切换 flag 时可能丢失)
        win32.set_topmost(self.win, True)

    def _schedule_hover_check(self):
        self._hover_after_id = self.root.after(self.HOVER_POLL_MS, self._check_hover_state)

    def _check_hover_state(self):
        import time
        # 模态对话框开着不处理
        if self._modal_dialog_open and self._expanded:
            self._schedule_hover_check()
            return
        # 防抖
        if int(time.time() * 1000) < self._click_lock_until_ms:
            self._schedule_hover_check()
            return
        # 鼠标在球或菜单上 → 取消穿透
        cx, cy = win32.get_cursor_pos()
        ball_rect = (
            self.win.winfo_x() - 6, self.win.winfo_y() - 6,
            self.win.winfo_x() + self.size + 6, self.win.winfo_y() + self.size + 6,
        )
        over_ball = (ball_rect[0] <= cx <= ball_rect[2] and ball_rect[1] <= cy <= ball_rect[3])
        over_radial = False
        if self._radial is not None and self._radial.is_visible():
            rx, ry = self._radial.position()
            rs = self._radial.size()
            over_radial = (rx - 6 <= cx <= rx + rs + 6 and ry - 6 <= cy <= ry + rs + 6)
        if self.config.data["ball"].get("click_through", True):
            if (over_ball or over_radial) and self._is_click_through:
                self._set_click_through(False)
            elif not (over_ball or over_radial) and not self._is_click_through:
                self._set_click_through(True)
                if self._expanded:
                    self._collapse()
        else:
            if self._is_click_through:
                self._set_click_through(False)
        self._schedule_hover_check()

    # ---------------- 展开/折叠 ----------------
    def _toggle_expand(self):
        if self._expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        if self._expanded:
            return
        self._expanded = True
        btns = self.config.data.get("buttons", [])
        if self._radial is None:
            self._radial = RadialMenu(self.root, self, btns)
        else:
            self._radial.update_buttons(btns)
        self._radial.show_around(self)

    def _collapse(self):
        if not self._expanded:
            return
        self._expanded = False
        if self._radial is not None:
            self._radial.hide()

    # ---------------- 按钮触发 ----------------
    def on_button_triggered(self, btn_cfg: dict):
        # 关闭菜单后再开播放窗,避免遮挡
        self._collapse()
        self.root.after(150, lambda: open_html(btn_cfg))

    # ---------------- 右键菜单 ----------------
    def _show_context_menu(self, x_root, y_root):
        menu = Menu(self.win, tearoff=0)
        menu.add_command(label="➕ 添加按钮", command=self._on_add_button)
        menu.add_command(label="⚙️ 打开设置", command=self._open_settings)
        menu.add_separator()
        menu.add_command(label="📂 打开配置目录", command=self._open_config_dir)
        menu.add_separator()
        menu.add_command(label="❌ 退出", command=self.root.destroy)
        try:
            menu.tk_popup(x_root, y_root)
        finally:
            menu.grab_release()

    def _on_add_button(self):
        self._modal_dialog_open = True
        try:
            dlg = ButtonEditDialog(self.root, self.config)
            dlg.show_modal()
        finally:
            self._modal_dialog_open = False
        # 刷新菜单
        self._refresh_radial()
        # 8 秒点击锁,给用户操作时间
        import time
        self._click_lock_until_ms = int(time.time() * 1000) + 8000

    def _refresh_radial(self):
        btns = self.config.data.get("buttons", [])
        if self._radial is None:
            self._radial = RadialMenu(self.root, self, btns)
        else:
            self._radial.update_buttons(btns)
        if btns or True:  # 0 按钮也显示 "+" 占位
            self._expanded = True
            self._radial.show_around(self)

    def _open_settings(self):
        self._modal_dialog_open = True
        try:
            dlg = SettingsDialog(self.root, self.config)
            dlg.show_modal()
        finally:
            self._modal_dialog_open = False
        # 重新应用某些属性
        ball_cfg = self.config.data["ball"]
        new_size = int(ball_cfg.get("size", 56))
        if new_size != self.size:
            self.size = new_size
            self.canvas.config(width=new_size, height=new_size)
            self.win.geometry(f"{new_size}x{new_size}+{self.win.winfo_x()}+{self.win.winfo_y()}")
        new_opacity = float(ball_cfg.get("opacity", 0.92))
        if abs(new_opacity - self.opacity) > 0.01:
            self.opacity = new_opacity
            self.win.attributes("-alpha", new_opacity)
        self.color = ball_cfg.get("color", "#4A90E2")
        self.icon_text = ball_cfg.get("icon", "📚")
        self._draw_ball()
        # 刷新菜单
        btns = self.config.data.get("buttons", [])
        if self._radial is not None:
            self._radial.update_buttons(btns)
        if btns and not self._expanded:
            self._expand()
        self._set_click_through(bool(ball_cfg.get("click_through", True)))

    def _open_config_dir(self):
        from core.paths import app_data_dir
        path = str(app_data_dir())
        if sys.platform == "win32":
            os.startfile(path)
        else:
            os.system(f'open "{path}"' if sys.platform == "darwin" else f'xdg-open "{path}"')

    def _save_position(self):
        self.config.data["ball"]["position"] = {
            "x": self.win.winfo_x(), "y": self.win.winfo_y()
        }
        self.config.save()

    def _restore_geometry(self):
        pos = self.config.data["ball"].get("position", {"x": 100, "y": 100})
        # 边界保护
        sw, sh = win32.get_screen_size()
        if pos["x"] < 0 or pos["x"] > sw - 50 or pos["y"] < 0 or pos["y"] > sh - 50:
            pos = {"x": sw - 100, "y": sh - 100}
        self.config.data["ball"]["position"] = pos
        return pos
