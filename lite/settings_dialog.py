"""
lite 设置对话框:tk.Toplevel 模态,通用设置 + 按钮列表(增删改)
"""
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as mb
from core.config import Config
from lite.styles import (
    COLOR_BG, COLOR_FG, FONT_NORMAL, FONT_TITLE, FONT_BOLD,
    apply_ttk_style, COLOR_ACCENT, COLOR_CARD,
)
from lite.button_edit import ButtonEditDialog


class SettingsDialog:
    def __init__(self, parent: tk.Tk, config: Config):
        self.parent = parent
        self.config = config
        self.win = tk.Toplevel(parent)
        self.win.title("悬浮球 - 设置")
        self.win.config(bg=COLOR_BG)
        self.win.attributes("-topmost", True)
        apply_ttk_style(parent)
        w, h = 640, 480
        x = parent.winfo_screenwidth() // 2 - w // 2
        y = parent.winfo_screenheight() // 2 - h // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self.win.transient(parent)
        self.win.grab_set()

    def _build_ui(self):
        # 标题
        tk.Label(
            self.win, text="⚙️ 悬浮球设置", bg=COLOR_BG, fg=COLOR_ACCENT,
            font=FONT_TITLE,
        ).pack(pady=(16, 8), anchor="w", padx=20)
        # 通用
        ball_frame = ttk.LabelFrame(self.win, text="通用")
        ball_frame.pack(fill="x", padx=20, pady=(0, 8))
        bcfg = self.config.data["ball"]
        # 大小
        row1 = ttk.Frame(ball_frame)
        row1.pack(fill="x", padx=8, pady=4)
        ttk.Label(row1, text="浮球大小(像素):").pack(side="left")
        self.var_size = tk.IntVar(value=int(bcfg.get("size", 56)))
        ttk.Spinbox(row1, from_=32, to=128, textvariable=self.var_size, width=6).pack(side="left", padx=(4, 16))
        # 透明度
        ttk.Label(row1, text="不透明度(0.3-1.0):").pack(side="left")
        self.var_opacity = tk.DoubleVar(value=float(bcfg.get("opacity", 0.92)))
        ttk.Spinbox(row1, from_=0.3, to=1.0, increment=0.05,
                    textvariable=self.var_opacity, width=6).pack(side="left", padx=4)
        # 鼠标穿透
        self.var_through = tk.BooleanVar(value=bool(bcfg.get("click_through", True)))
        ttk.Checkbutton(
            ball_frame, text="启用鼠标穿透(光标离开浮球后,鼠标可穿透悬浮球,不挡 PPT)",
            variable=self.var_through,
        ).pack(anchor="w", padx=8, pady=(0, 6))
        # 按钮列表
        btn_frame = ttk.LabelFrame(self.win, text="按钮列表")
        btn_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        # 工具条
        toolbar = ttk.Frame(btn_frame)
        toolbar.pack(fill="x", padx=4, pady=4)
        ttk.Button(toolbar, text="➕ 添加", command=self._on_add).pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="✏️ 编辑", command=self._on_edit).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🗑️ 删除", command=self._on_delete).pack(side="left", padx=4)
        ttk.Button(toolbar, text="⬆️ 上移", command=lambda: self._on_move(-1)).pack(side="left", padx=4)
        ttk.Button(toolbar, text="⬇️ 下移", command=lambda: self._on_move(+1)).pack(side="left", padx=4)
        # 列表
        list_frame = ttk.Frame(btn_frame)
        list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 6))
        self.listbox = tk.Listbox(
            list_frame, bg=COLOR_CARD, fg=COLOR_FG,
            selectbackground=COLOR_ACCENT, selectforeground="#1e1e2e",
            font=FONT_NORMAL, relief="flat", highlightthickness=1,
            highlightbackground="#45475a",
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb.set)
        self._refresh_list()
        self.listbox.bind("<Double-Button-1>", lambda e: self._on_edit())
        # 底部
        bottom = ttk.Frame(self.win)
        bottom.pack(fill="x", padx=20, pady=(0, 16))
        ttk.Button(bottom, text="关闭", command=self._on_close).pack(side="right")

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        for i, b in enumerate(self.config.data.get("buttons", [])):
            t = b.get("type", "?")
            name = b.get("name", "")
            content = b.get("content", "")
            if t == "html":
                preview = content[:30] + ("..." if len(content) > 30 else "")
            else:
                preview = content[:50] + ("..." if len(content) > 50 else "")
            self.listbox.insert("end", f"{i+1}. [{t}] {name}  —  {preview}")

    def _selected_index(self) -> int:
        sel = self.listbox.curselection()
        if not sel:
            return -1
        return sel[0]

    def _on_add(self):
        # 临时释放 grab,让 add 对话框能 grab
        self.win.grab_release()
        dlg = ButtonEditDialog(self.parent, self.config)
        result = dlg.show_modal()
        self.win.grab_set()
        if result is not None:
            self._refresh_list()

    def _on_edit(self):
        i = self._selected_index()
        if i < 0:
            mb.showinfo("提示", "请先选中一个按钮。", parent=self.win)
            return
        self.win.grab_release()
        dlg = ButtonEditDialog(self.parent, self.config, edit_index=i)
        result = dlg.show_modal()
        self.win.grab_set()
        if result is not None:
            self._refresh_list()

    def _on_delete(self):
        i = self._selected_index()
        if i < 0:
            mb.showinfo("提示", "请先选中一个按钮。", parent=self.win)
            return
        btns = self.config.data.get("buttons", [])
        if 0 <= i < len(btns):
            name = btns[i].get("name", "")
            if mb.askyesno("确认", f"删除按钮 '{name}'?", parent=self.win):
                del btns[i]
                self.config.data["buttons"] = btns
                self.config.save()
                self._refresh_list()

    def _on_move(self, delta: int):
        i = self._selected_index()
        if i < 0:
            return
        btns = self.config.data.get("buttons", [])
        j = i + delta
        if not (0 <= j < len(btns)):
            return
        btns[i], btns[j] = btns[j], btns[i]
        self.config.data["buttons"] = btns
        self.config.save()
        self._refresh_list()
        self.listbox.selection_set(j)

    def _on_close(self):
        # 保存通用设置
        ball = self.config.data["ball"]
        ball["size"] = int(self.var_size.get())
        ball["opacity"] = float(self.var_opacity.get())
        ball["click_through"] = bool(self.var_through.get())
        self.config.save()
        try:
            self.win.grab_release()
        except Exception:
            pass
        self.win.destroy()

    def show_modal(self):
        self.win.wait_window()
