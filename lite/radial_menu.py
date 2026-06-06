"""
lite 径向菜单:一个透明 tk.Toplevel 容器,canvas 画圆环,
周围放若干圆形按钮(占位 "➕" 永远在顶部,其他按钮均匀分布)。
"""
import math
import tkinter as tk
from typing import List
from lite.styles import COLOR_BG, COLOR_FG, FONT_NORMAL


class RadialMenu:
    """径向菜单容器。"""

    BTN_SIZE = 48
    RING_RADIUS = 80

    def __init__(self, root: tk.Tk, anchor, buttons_cfg: List[dict]):
        self.root = root
        self.anchor = anchor
        self.button_widgets: List[tk.Frame] = []
        self._ring_radius = self.RING_RADIUS
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.config(bg=COLOR_BG)
        # 画布
        self.canvas = tk.Canvas(self.win, bg=COLOR_BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        # 关闭时清理
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)
        # 初始隐藏
        self.win.withdraw()
        self._build(buttons_cfg)

    def _build(self, buttons_cfg: List[dict]):
        for w in self.button_widgets:
            w.destroy()
        self.button_widgets.clear()
        # "➕" 占位按钮永远在 index 0(顶部)
        plus = self._make_plus_button()
        self.button_widgets.append(plus)
        for cfg in buttons_cfg:
            item = self._make_button_widget(cfg)
            self.button_widgets.append(item)
        # 重新布局
        self._relayout()

    def _make_plus_button(self):
        f = tk.Frame(self.win, width=self.BTN_SIZE, height=self.BTN_SIZE, bg=COLOR_BG)
        b = tk.Label(
            f, text="➕", bg=COLOR_BG, fg="#a6e3a1",
            font=("Segoe UI Emoji", 22, "bold"),
            cursor="hand2", width=2, height=1,
        )
        b.place(relx=0.5, rely=0.5, anchor="center")
        b.bind("<Button-1>", lambda e: self._on_plus_click())
        b.bind("<Button-3>", lambda e: self.anchor._show_context_menu(
            e.x_root + self.win.winfo_x(), e.y_root + self.win.winfo_y()))
        return f

    def _make_button_widget(self, cfg):
        f = tk.Frame(self.win, width=self.BTN_SIZE, height=self.BTN_SIZE, bg=COLOR_BG)
        label_text = cfg.get("name") or cfg.get("content", "")[:2] or "📘"
        # 用首字符当图标
        if isinstance(label_text, str) and len(label_text) > 0:
            icon = label_text[0]
        else:
            icon = "📘"
        b = tk.Label(
            f, text=icon, bg=COLOR_BG, fg="#cdd6f4",
            font=("Microsoft YaHei UI", 16, "bold"),
            cursor="hand2", width=2, height=1, relief="flat",
        )
        b.place(relx=0.5, rely=0.5, anchor="center")
        tip = cfg.get("name", "")
        if tip:
            b.bind("<Enter>", lambda e, t=tip: self._show_tooltip(t))
            b.bind("<Leave>", lambda e: self._hide_tooltip())
        b.bind("<Button-1>", lambda e, c=cfg: self.anchor.on_button_triggered(c))
        b.bind("<Button-3>", lambda e: self.anchor._show_context_menu(
            e.x_root + self.win.winfo_x(), e.y_root + self.win.winfo_y()))
        f._cfg = cfg
        f._label = b
        return f

    def _show_tooltip(self, text):
        # 简化:不画 tooltip,留给以后扩展
        pass

    def _hide_tooltip(self):
        pass

    def _on_plus_click(self):
        # 8 秒点击锁
        import time
        self.anchor._click_lock_until_ms = int(time.time() * 1000) + 5000
        if hasattr(self.anchor, "_on_add_button"):
            self.anchor._on_add_button()

    def _relayout(self):
        n = len(self.button_widgets)
        if n == 0:
            return
        # 容器尺寸 = 球 + (半径+按钮)*2
        ax, ay = self.anchor.win.winfo_x(), self.anchor.win.winfo_y()
        asize = self.anchor.size
        cont = asize + (self._ring_radius + self.BTN_SIZE) * 2
        self.canvas.config(width=cont, height=cont)
        # 中心对齐悬浮球
        cx_screen = ax + asize // 2
        cy_screen = ay + asize // 2
        # 屏幕边缘保护
        from lite import win32
        sw, sh = win32.get_screen_size()
        left = cx_screen - cont // 2
        top = cy_screen - cont // 2
        if left < 0: left = 0
        if top < 0: top = 0
        if left + cont > sw: left = sw - cont
        if top + cont > sh: top = sh - cont
        self.win.geometry(f"{cont}x{cont}+{left}+{top}")
        # 画圆环
        self.canvas.delete("ring")
        cx = cont // 2
        cy = cont // 2
        self.canvas.create_oval(
            cx - self._ring_radius, cy - self._ring_radius,
            cx + self._ring_radius, cy + self._ring_radius,
            outline="#89b4fa", dash=(3, 3), width=1, tags="ring"
        )
        # 摆按钮
        for i, item in enumerate(self.button_widgets):
            angle = self._angle_for(i, n)
            rad = math.radians(angle)
            bx = int(cx + math.cos(rad) * self._ring_radius - self.BTN_SIZE / 2)
            by = int(cy + math.sin(rad) * self._ring_radius - self.BTN_SIZE / 2)
            # 解除之前的管理
            try:
                item.place_forget()
            except Exception:
                pass
            item.place(x=bx, y=by, width=self.BTN_SIZE, height=self.BTN_SIZE)

    @staticmethod
    def _angle_for(i: int, n: int) -> float:
        if n == 1:
            return -90
        return -90 + i * (360 / n)

    # ---- 显示/隐藏 ----
    def show_around(self, anchor):
        self._relayout()
        self.win.deiconify()
        self.win.lift()
        from lite import win32
        win32.set_topmost(self.win, True)

    def hide(self):
        self.win.withdraw()

    def update_buttons(self, buttons_cfg: List[dict]):
        self._build(buttons_cfg)

    def is_visible(self) -> bool:
        try:
            return bool(self.win.winfo_viewable())
        except Exception:
            return False

    def position(self):
        return self.win.winfo_x(), self.win.winfo_y()

    def size(self):
        return self.canvas.winfo_width()
