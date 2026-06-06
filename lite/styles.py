"""
lite 版的样式:ttk 主题颜色
"""
# 颜色
COLOR_BG = "#1e1e2e"          # 暗色背景
COLOR_FG = "#cdd6f4"          # 浅色文字
COLOR_ACCENT = "#89b4fa"      # 蓝色
COLOR_ACCENT2 = "#f38ba8"     # 粉红
COLOR_OK = "#a6e3a1"          # 绿
COLOR_WARN = "#f9e2af"        # 黄
COLOR_CARD = "#313244"        # 卡片底
COLOR_BORDER = "#45475a"      # 边框

# 字体
FONT_FAMILY = "Microsoft YaHei UI"
FONT_SIZE = 10
FONT_BOLD = (FONT_FAMILY, FONT_SIZE, "bold")
FONT_NORMAL = (FONT_FAMILY, FONT_SIZE)
FONT_TITLE = (FONT_FAMILY, 12, "bold")
FONT_SMALL = (FONT_FAMILY, 9)

# 通用 ttk 样式
def apply_ttk_style(root):
    import tkinter.ttk as ttk
    style = ttk.Style(root)
    # 用 clam 主题作为基础(支持颜色定制)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    # LabelFrame
    style.configure("TLabelframe", background=COLOR_BG, foreground=COLOR_FG)
    style.configure("TLabelframe.Label", background=COLOR_BG, foreground=COLOR_ACCENT,
                    font=FONT_TITLE)
    # Label
    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_FG, font=FONT_NORMAL)
    style.configure("Hint.TLabel", background=COLOR_BG, foreground=COLOR_WARN, font=FONT_SMALL)
    # Button
    style.configure("TButton", background=COLOR_CARD, foreground=COLOR_FG,
                    borderwidth=1, focusthickness=0, padding=(12, 6))
    style.map("TButton",
              background=[("active", COLOR_ACCENT), ("pressed", COLOR_ACCENT2)],
              foreground=[("active", "#1e1e2e"), ("pressed", "#1e1e2e")])
    style.configure("Accent.TButton", background=COLOR_ACCENT, foreground="#1e1e2e",
                    font=FONT_BOLD, padding=(16, 8))
    style.map("Accent.TButton",
              background=[("active", "#b4befe"), ("pressed", "#74c7ec")])
    # Entry
    style.configure("TEntry", fieldbackground=COLOR_CARD, foreground=COLOR_FG,
                    insertcolor=COLOR_FG)
    # Combobox
    style.configure("TCombobox", fieldbackground=COLOR_CARD, foreground=COLOR_FG)
    style.map("TCombobox", fieldbackground=[("readonly", COLOR_CARD)])
    # Radiobutton / Checkbutton
    style.configure("TRadiobutton", background=COLOR_BG, foreground=COLOR_FG)
    style.configure("TCheckbutton", background=COLOR_BG, foreground=COLOR_FG)
