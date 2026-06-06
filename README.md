# 课件悬浮球工具

> 一颗蓝色的小圆球,静静地浮在你的课件窗口之上。点一下,周围弹出你常用的快捷键 —— 一键打开 HTML 课件、网址、互动小工具。再点一下,全屏置顶播放,**不影响**希沃白板、PPT、国家智慧中小学的运行。

为中学教师课堂演示量身设计。Windows 系统。

---

## 这是什么

悬浮球课件工具是一个常驻桌面的小工具,核心解决两个问题:

- **课件切换太麻烦** — 讲课时要在多个 HTML 课件、网页工具、互动小游戏之间切来切去,翻文件夹、找文件、按 ESC,一节课下来打断无数次思路。
- **悬浮球/批注工具容易误触** — 鼠标动一下就被吸附,PPT 放映时格外碍眼。

这颗悬浮球默认是**鼠标穿透**的 —— 你感受不到它的存在,直到你主动点它。展开的快捷键按你常用的顺序排列,一键直达。

---

## 主要功能

- 🔵 **始终置顶的悬浮球** — 拖到屏幕任意角落,自动记住位置
- 🎯 **单击展开径向菜单** — 周围弹出你自定义的快捷按钮(可加 1~N 个)
- ⛶ **一键全屏播放 HTML** — 网址 / HTML 代码 / HTML 文件,都可以挂成按钮
- 🖱️ **默认鼠标穿透** — 移动到悬浮球上才可点击,完全不影响 PPT 放映
- ⚙️ **右键菜单** — 添加按钮 / 设置 / 打开配置目录 / 退出
- 🚀 **开机自启** — 勾上后,开机即用,无需每次手动启动
- 💾 **配置自动保存** — 按钮、位置、参数,关掉再开还是你的样子

---

## 快速开始

### 老师用户(直接用)

1. 打开右侧 **Releases** 页面
2. 下载最新版的 `XuanFuQiu_*_Setup.exe`
3. 双击安装(无需管理员权限)
4. 桌面 / 开始菜单双击「悬浮球」即可启动
5. **右键悬浮球 → 添加按钮**,把常用的课件挂上去

### 开发者(从源码运行)

需要 Python 3.10+。

```bash
git clone https://github.com/tanghua-git/xuanfuqiu.git
cd xuanfuqiu
pip install -r requirements.txt
python main.py
```

打包成安装包:

```bash
pip install -r requirements.txt
python build.py                # 只生成 onedir 目录(可直接运行)
python build.py --installer    # 再用 Inno Setup 打成单个 Setup.exe
```

> 打包用的是 `onedir` 模式(生成目录,不是单 exe),这是 PySide6 + QtWebEngine 的官方推荐方案 —— 单 exe 模式下 `QCoreApplication::applicationDirPath()` 指向错误的目录,WebEngine 在别的机器上会启动失败。

---

## 使用方法

启动后,屏幕角落出现一个蓝色圆球。

| 操作 | 效果 |
|---|---|
| **左键拖动** | 移动悬浮球,松手自动保存位置 |
| **单击** | 展开周围按钮(几乎不移动时) |
| **再次单击** | 折叠按钮 |
| **单击周围按钮** | 全屏打开对应的 HTML 课件 / 网址 |
| **ESC** 或 鼠标移到屏幕顶部 | 退出 HTML 播放,焦点回到原应用 |
| **右键** | 弹出菜单:添加按钮 / 设置 / 打开配置目录 / 退出 |

> 💡 第一次打开 HTML 课件时,Chromium 引擎需要几秒钟初始化,之后切换会很快。

---

## 添加按钮

**右键悬浮球 → 添加按钮**,会弹出编辑窗口,可选三种内容类型:

1. **网址(URL)** — 填一个 https:// 链接,点按钮直接打开
2. **HTML 代码** — 粘贴一段 HTML(含 `<html>` 标签),工具会写到临时文件并打开
3. **HTML 文件** — 选本机一个 .html 文件

按钮顺序、位置、配置都自动保存到 `%APPDATA%\XuanFuQiu\config.json`,下次启动还是你的样子。

---

## 配置文件位置

| 场景 | 路径 |
|---|---|
| 开发期 | 项目根目录下的 `config.json` |
| 打包后 | `%APPDATA%\XuanFuQiu\config.json` |
| 临时 HTML | `%APPDATA%\XuanFuQiu\tmp\` |

> 想把配置同步到另一台电脑?直接复制 `config.json` 过去即可。

---

## 常见问题

**Q:点击按钮后 HTML 没有全屏?**
A:检查是否打开了两个悬浮球实例。任务栏右键退出旧的。

**Q:HTML 课件挡住了 PPT 怎么办?**
A:按 **ESC** 关闭播放窗,焦点自动回到 PPT。

**Q:悬浮球挡住了内容?**
A:把它拖到屏幕角落,下次启动会记住位置。

**Q:怎么关掉鼠标穿透?**
A:右键 → 设置 → 通用设置 → 取消「启用鼠标穿透」。

**Q:HTML 代码按钮没反应?**
A:确认代码是合法 HTML(包含 `<html>` 标签)。代码会被写到临时文件,路径在 `%APPDATA%\XuanFuQiu\tmp\`,可以打开看看具体写进去的内容。

**Q:打包后到其他机器运行,显示「QtWebEngine 未能加载」?**
A:这是 PyInstaller 单文件模式的已知问题。**请用项目自带的 `build.py` 重新打包**(`onedir` 模式即可)。如果诊断界面列出了具体缺失文件,通常补回去就行。

---

## 技术栈

| 用途 | 技术 |
|---|---|
| GUI | PySide6 (Qt for Python) |
| HTML 渲染 | QtWebEngineWidgets(Chromium 内核) |
| 打包 | PyInstaller + Inno Setup |

---

## 项目结构

```
课件悬浮球工具/
├── main.py                  # 入口
├── build.py                 # 打包脚本
├── build_lite.py            # 精简版打包脚本
├── requirements.txt
├── installer.iss            # Inno Setup 脚本
├── core/                    # 核心模块
│   ├── config.py            # 配置管理(JSON + 原子写)
│   └── paths.py             # 路径工具
├── ui/                      # 界面
│   ├── floating_ball.py     # 悬浮球主控件
│   ├── radial_menu.py       # 径向菜单
│   ├── button_item.py       # 单个按钮
│   ├── button_edit.py       # 添加/编辑按钮对话框
│   ├── settings_dialog.py   # 设置主窗口
│   ├── player_window.py     # HTML 全屏播放窗
│   └── styles.py            # QSS 样式
├── runtime/                 # 运行时
│   ├── html_runner.py       # HTML 统一执行器
│   └── auto_start.py        # 开机自启(注册表)
├── lite/                    # 精简版实验代码
└── resources/               # 图标等
```

---

## 许可

仅供教学使用。作者不承担因软件问题导致课堂中断的责任。

如果你用了觉得好,欢迎给个 ⭐ —— 这是对中学老师最大的鼓励。
