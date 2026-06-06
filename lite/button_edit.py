"""
lite 添加/编辑按钮对话框:tk.Toplevel 模态,字段:名称、类型(url/file/html)、内容
"""
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
from core.config import Config
from lite.styles import (
    COLOR_BG, COLOR_FG, FONT_NORMAL, FONT_TITLE, FONT_BOLD,
    apply_ttk_style, COLOR_ACCENT, COLOR_CARD,
)


class ButtonEditDialog:
    def __init__(self, parent: tk.Tk, config: Config, edit_index: int = -1):
        self.parent = parent
        self.config = config
        self.edit_index = edit_index
        self.result: dict | None = None

        # 预填(编辑模式下)
        if edit_index >= 0:
            btns = self.config.data.get("buttons", [])
            if 0 <= edit_index < len(btns):
                self._initial = dict(btns[edit_index])
            else:
                self._initial = {"name": "", "type": "url", "content": ""}
        else:
            self._initial = {"name": "", "type": "url", "content": ""}

        self.win = tk.Toplevel(parent)
        self.win.title("添加按钮" if edit_index < 0 else "编辑按钮")
        self.win.config(bg=COLOR_BG)
        self.win.attributes("-topmost", True)
        apply_ttk_style(parent)

        # 窗口尺寸
        w, h = 460, 360
        x = parent.winfo_screenwidth() // 2 - w // 2
        y = parent.winfo_screenheight() // 2 - h // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_ui()
        self._fill_initial()
        # 模态
        self.win.transient(parent)
        self.win.grab_set()
        self.win.focus_force()

    def _build_ui(self):
        # 标题
        tk.Label(
            self.win, text="➕ 添加按钮", bg=COLOR_BG, fg=COLOR_ACCENT,
            font=FONT_TITLE,
        ).pack(pady=(16, 4), anchor="w", padx=20)
        # 名称
        frm_name = ttk.Frame(self.win, style="TLabelframe")
        frm_name.pack(fill="x", padx=20, pady=(8, 4))
        ttk.Label(frm_name, text="名称(显示在悬浮球周围):").pack(anchor="w", padx=4, pady=(4, 0))
        self.var_name = tk.StringVar()
        ttk.Entry(frm_name, textvariable=self.var_name).pack(fill="x", padx=4, pady=4)
        # 类型
        frm_type = ttk.Frame(self.win)
        frm_type.pack(fill="x", padx=20, pady=(8, 4))
        ttk.Label(frm_type, text="类型:").pack(anchor="w", padx=4, pady=(4, 0))
        self.var_type = tk.StringVar(value="url")
        rb_frame = ttk.Frame(frm_type)
        rb_frame.pack(fill="x", padx=4, pady=4)
        ttk.Radiobutton(rb_frame, text="网址(URL)", variable=self.var_type,
                        value="url", command=self._on_type_change).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(rb_frame, text="HTML 文件", variable=self.var_type,
                        value="file", command=self._on_type_change).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(rb_frame, text="HTML 代码", variable=self.var_type,
                        value="html", command=self._on_type_change).pack(side="left", padx=(0, 12))
        # 内容
        frm_content = ttk.Frame(self.win)
        frm_content.pack(fill="both", expand=True, padx=20, pady=(8, 4))
        ttk.Label(frm_content, text="内容:").pack(anchor="w", padx=4, pady=(4, 0))
        content_inner = ttk.Frame(frm_content)
        content_inner.pack(fill="both", expand=True, padx=4, pady=4)
        self.text_content = tk.Text(
            content_inner, height=6, bg=COLOR_CARD, fg=COLOR_FG,
            insertbackground=COLOR_FG, font=FONT_NORMAL,
            relief="flat", wrap="word",
        )
        self.text_content.pack(side="left", fill="both", expand=True)
        self.btn_browse = ttk.Button(
            content_inner, text="📂 浏览", command=self._on_browse, width=10,
        )
        self.btn_browse.pack(side="right", padx=(4, 0))
        # 提示
        self.lbl_hint = ttk.Label(frm_content, text="", style="Hint.TLabel")
        self.lbl_hint.pack(anchor="w", padx=4, pady=(2, 0))
        # 按钮区
        btn_frame = ttk.Frame(self.win)
        btn_frame.pack(fill="x", padx=20, pady=(12, 16))
        ttk.Button(btn_frame, text="取消", command=self._on_cancel).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="保存", style="Accent.TButton",
                   command=self._on_save).pack(side="right")

    def _fill_initial(self):
        self.var_name.set(self._initial.get("name", ""))
        self.var_type.set(self._initial.get("type", "url"))
        self.text_content.insert("1.0", self._initial.get("content", ""))
        self._on_type_change()

    def _on_type_change(self):
        t = self.var_type.get()
        if t == "url":
            self.lbl_hint.config(text="提示:输入完整网址,例如 https://example.com (可省略 https://)")
            self.btn_browse.state(["disabled"])
        elif t == "file":
            self.lbl_hint.config(text="提示:选择本地 HTML 文件")
            self.btn_browse.state(["!disabled"])
        else:  # html
            self.lbl_hint.config(text="提示:粘贴 HTML 代码,会写入临时文件并用 WebView2 渲染")
            self.btn_browse.state(["disabled"])

    def _on_browse(self):
        if self.var_type.get() != "file":
            return
        path = fd.askopenfilename(
            title="选择 HTML 文件",
            filetypes=[("HTML 文件", "*.html *.htm"), ("所有文件", "*.*")],
        )
        if path:
            self.text_content.delete("1.0", "end")
            self.text_content.insert("1.0", path)

    def _on_save(self):
        name = self.var_name.get().strip()
        t = self.var_type.get()
        content = self.text_content.get("1.0", "end").strip()
        if not name:
            mb.showwarning("提示", "请填写名称。", parent=self.win)
            return
        if not content:
            mb.showwarning("提示", "请填写内容。", parent=self.win)
            return
        # URL 补全协议
        if t == "url" and content and not content.startswith(("http://", "https://", "file://")):
            content = "https://" + content
        self.result = {"name": name, "type": t, "content": content}
        self.win.grab_release()
        self.win.destroy()

    def _on_cancel(self):
        self.result = None
        try:
            self.win.grab_release()
        except Exception:
            pass
        self.win.destroy()

    def show_modal(self) -> dict | None:
        self.win.wait_window()
        if self.result is None:
            return None
        # 写入 config
        if self.edit_index >= 0:
            btns = self.config.data.get("buttons", [])
            if 0 <= self.edit_index < len(btns):
                btns[self.edit_index] = self.result
            else:
                btns.append(self.result)
        else:
            self.config.add_button(self.result)
        self.config.save()
        return self.result
