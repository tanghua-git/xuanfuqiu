"""
打包脚本:在 Windows 下生成单目录 exe(可被 Inno Setup 打成安装包)。

为什么不用 --onefile?
    PyInstaller --onefile 启动时把所有文件解压到 %TEMP%\_MEIxxxxx 临时目录,
    但 QtWebEngine 内部用 QCoreApplication::applicationDirPath() 定位
    QtWebEngineProcess.exe 和资源文件 — 该 API 返回的是 *原始 exe 所在目录*,
    不是解压后的临时目录,导致 WebEngine 找不到资源、初始化失败。
    官方推荐的稳定方案是 --onedir:exe 和所有 DLL 在同一文件夹里,绝对路径正常。
    配合 Inno Setup 打成安装包后,用户拿到的仍然是单个 Setup.exe,体验不变。

用法:
    python build.py             # 仅生成 onedir 目录
    python build.py --installer # 同步生成 Inno Setup 安装包(需本机有 Inno Setup 6)
    python build.py --onefile   # (不推荐) 强行打单文件,WebEngine 在其他机器上会失败

输出:
    dist/悬浮球/悬浮球.exe + DLL们     单目录版(配合安装包使用)
    dist/悬浮球.exe                    单文件版(可选,WebEngine 在其他机器大概率坏)
    dist/Output/XuanFuQiu_..._Setup.exe  Inno Setup 生成的安装程序(可选)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Windows cmd 默认 GBK,emoji/中文会炸。强制 UTF-8 输出
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


APP_NAME = "悬浮球"
ENTRY = "main.py"
ICON_PATH = "resources/icon.ico"


def make_icon() -> Path:
    """用 PySide6 渲染一个简单的图标,转成 .ico 写入 resources/。

    优先用 PySide6 渲染,失败则回退到 PIL/None(无图标也能打包)。"""
    root = Path(__file__).resolve().parent
    out = root / ICON_PATH
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QIcon
        from PySide6.QtCore import Qt

        app = QApplication.instance() or QApplication(sys.argv)
        # 渲染多尺寸 png,再合并成 ico
        sizes = [16, 24, 32, 48, 64, 128, 256]
        pngs = []
        for sz in sizes:
            pm = QPixmap(sz, sz)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            # 蓝色渐变球
            from PySide6.QtGui import QRadialGradient
            grad = QRadialGradient(sz * 0.4, sz * 0.35, sz * 0.7)
            grad.setColorAt(0, QColor(255, 255, 255, 230))
            grad.setColorAt(0.55, QColor(120, 180, 255, 240))
            grad.setColorAt(1, QColor(40, 90, 180, 255))
            p.setBrush(QBrush(grad))
            p.setPen(QPen(QColor(255, 255, 255, 220), max(1, sz // 28)))
            r = sz // 2 - 2
            p.drawEllipse(sz // 2 - r, sz // 2 - r, 2 * r, 2 * r)
            # 中心图标 📚
            p.setPen(QColor(255, 255, 255))
            f = p.font()
            f.setPointSize(int(sz * 0.42))
            f.setBold(True)
            p.setFont(f)
            p.drawText(pm.rect(), Qt.AlignCenter, "📚")
            p.end()
            tmp = out.with_suffix(f".{sz}.png")
            pm.save(str(tmp), "PNG")
            pngs.append(tmp)

        # 用 Pillow 合成 ico(若可用)
        try:
            from PIL import Image
            imgs = [Image.open(str(p), "r") for p in pngs]
            imgs[0].save(
                str(out),
                format="ICO",
                sizes=[(i.width, i.height) for i in imgs],
                append_images=imgs[1:],
            )
            print(f"  ✓ 图标已生成: {out}")
        except ImportError:
            # Pillow 不可用,直接把 256 png 改名为 ico(Qt 仍能加载)
            shutil.copyfile(pngs[-1], out)
            print(f"  ! Pillow 未安装,使用 256x256 png 代替 ico")
        finally:
            for p in pngs:
                try:
                    p.unlink()
                except OSError:
                    pass
        return out if out.exists() else Path()
    except Exception as e:
        print(f"  ! 图标生成失败: {e}")
        return Path()


def build_exe(root: Path) -> Path:
    """调用 PyInstaller 生成产物,返回主 exe 路径。

    默认走 --onedir(WebEngine 兼容),加 --onefile 才会用单文件模式。
    """
    entry_path = root / ENTRY
    if not entry_path.exists():
        print(f"找不到入口: {entry_path}")
        sys.exit(1)

    # 清理旧文件
    for d in (root / "build", root / "dist"):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    use_onefile = "--onefile" in sys.argv

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", APP_NAME,
    ]

    if use_onefile:
        # 单文件模式:WebEngine 在其他机器上大概率会坏,仅作 fallback
        cmd += ["--onefile", "--windowed"]
        print("⚠️  --onefile 模式:QtWebEngine 在解压到 %TEMP% 后可能找不到资源,推荐用 --onedir")
    else:
        # 单目录模式:WebEngine 友好,推荐方案
        cmd += ["--onedir", "--windowed"]

    # ----- WebEngine 资源收集(关键!)-----
    # 显式 --collect-all 子模块,确保 WebEngine 全套运行时都被 PyInstaller 看到
    cmd += [
        "--collect-all", "PySide6",
        "--collect-all", "PySide6.QtWebEngineWidgets",
        "--collect-all", "PySide6.QtWebEngineCore",
        "--collect-all", "PySide6.QtWebEngineQuick",
        "--collect-all", "shiboken6",
        # 显式 hidden-import 兜底
        "--hidden-import", "PySide6.QtWebEngineWidgets",
        "--hidden-import", "PySide6.QtWebEngineCore",
        "--hidden-import", "PySide6.QtWebEngineQuick",
    ]

    # 排除不需要的大模块,减小体积
    # ⚠️ 重要:不能排除 QtWebChannel —— QtWebEngineCore 通过它做进程间 IPC,
    # 排除后 import 报 "libshiboken: could not import module 'PySide6.QtWebChannel'"
    cmd += [
        "--exclude-module", "PySide6.Qt3DCore",
        "--exclude-module", "PySide6.Qt3DRender",
        "--exclude-module", "PySide6.QtCharts",
        "--exclude-module", "PySide6.QtDataVisualization",
        "--exclude-module", "PySide6.QtPdf",
        "--exclude-module", "PySide6.QtQuick3D",
        "--exclude-module", "PySide6.QtScxml",
        "--exclude-module", "PySide6.QtSensors",
        "--exclude-module", "PySide6.QtSerialPort",
        "--exclude-module", "PySide6.QtTest",
        "--exclude-module", "PySide6.QtTextToSpeech",
        # QtWebChannel 和 QtWebSockets 是 QtWebEngine 的依赖,绝对不能排除
        # "--exclude-module", "PySide6.QtWebChannel",
        # "--exclude-module", "PySide6.QtWebSockets",
        # Multimedia 大部分用户用不上,WebEngine 已自包含 ffmpeg 不依赖此模块
        "--exclude-module", "PySide6.QtMultimedia",
        "--exclude-module", "PySide6.QtMultimediaWidgets",
    ]

    icon = root / ICON_PATH
    if icon.exists():
        cmd += [f"--icon={icon}"]

    # 关键:runtime hook — 在主脚本前手动 add_dll_directory + 预 import shiboken6/PySide6,
    # 绕过 frozen 模式下 shiboken6 C 加载器找不到 PySide6 子模块 .pyd 的问题
    rthook = root / "rthook_pyside6_shim.py"
    if rthook.exists():
        cmd += [f"--runtime-hook={rthook}"]

    cmd += [str(entry_path)]

    print("执行 PyInstaller:")
    print("  " + " ".join(cmd))
    code = subprocess.call(cmd, cwd=root)
    if code != 0:
        print(f"\n打包失败,退出码: {code}")
        sys.exit(code)

    # 定位产物
    if use_onefile:
        out = root / "dist" / (APP_NAME + ".exe")
    else:
        out = root / "dist" / APP_NAME / (APP_NAME + ".exe")
    if not out.exists():
        print(f"未找到输出: {out}")
        sys.exit(1)

    # 统计整个目录大小
    if use_onefile:
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"\n✅ exe 已生成: {out}  ({size_mb:.1f} MB)")
    else:
        out_dir = out.parent
        total = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
        size_mb = total / 1024 / 1024
        # 数一下关键文件
        n_dll = len(list(out_dir.rglob("*.dll")))
        n_pak = len(list(out_dir.rglob("*.pak")))
        print(f"\n✅ 单目录已生成: {out_dir}  (共 {size_mb:.1f} MB,{n_dll} 个 DLL,{n_pak} 个 .pak)")
        print(f"   入口: {out}")
    return out


def build_installer(root: Path, exe: Path) -> Path | None:
    """如果系统装了 Inno Setup 6(ISCC.exe),就用它生成安装包。

    找不到 ISCC 就跳过,只输出 onedir 目录也足够分发(打成 zip 给老师即可)。

    ISCC 候选路径(按优先级):
      1) 环境变量 INNO_SETUP(用户可指向自定义位置)
      2) 标准安装路径 Program Files / Program Files (x86)
      3) C:\\InnoSetup6(便携式解压位置)
      4) PATH
    """
    candidates = []
    env = os.environ.get("INNO_SETUP")
    if env:
        candidates.append(env)
    candidates += [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\InnoSetup6\ISCC.exe",
    ]
    iscc = None
    for c in candidates:
        if c and Path(c).exists():
            iscc = c
            break
    if not iscc:
        found = shutil.which("ISCC") or shutil.which("ISCC.exe")
        if found:
            iscc = found
    if not iscc:
        print("\n未检测到 Inno Setup 6(ISCC.exe),跳过安装包生成。")
        print("如需生成 .exe 安装器,有两种方式:")
        print("  A) 安装 Inno Setup 6:https://jrsoftware.org/isinfo.php  (标准方式)")
        print("  B) 用 /EXTRACT 模式解压到 C:\\InnoSetup6 即可便携使用(无需安装):")
        print("     innosetup-6.5.3.exe /SP- /SILENT /EXTRACT=C:\\InnoSetup6 /NORESTART")
        return None

    iss = root / "installer.iss"
    if not iss.exists():
        print(f"未找到 {iss},跳过安装包生成。")
        return None

    out_dir = root / "dist"
    print(f"\n用 {iscc} 生成安装包...")
    code = subprocess.call([iscc, str(iss)], cwd=root)
    if code != 0:
        print(f"安装包生成失败,退出码: {code}")
        return None

    # Inno Setup 默认输出到 dist/Output/...
    out = out_dir / "Output" / (APP_NAME + "_Setup.exe")
    if not out.exists():
        # 兜底:扫描 dist
        for p in out_dir.rglob("*.exe"):
            if "Setup" in p.name or "setup" in p.name:
                out = p
                break
    if out.exists():
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"\n✅ 安装包已生成: {out}  ({size_mb:.1f} MB)")
        return out
    return None


def main():
    root = Path(__file__).resolve().parent
    print(f"项目目录: {root}\n")

    print("[1/2] 生成图标...")
    icon = make_icon()

    print("\n[2/2] 打包 exe...")
    exe = build_exe(root)

    if "--installer" in sys.argv:
        print("\n[3/3] 生成安装包...")
        build_installer(root, exe)

    print("\n分发方式:")
    if "--onefile" in sys.argv:
        print(f"  • 单文件版:  {exe}    (双击即用,⚠️ WebEngine 在其他机器上可能坏)")
    else:
        out_dir = exe.parent
        print(f"  • 单目录版:  {out_dir}    (推荐,WebEngine 兼容)")
        print(f"  • 直接分发:  把整个 {out_dir.name}/ 目录打成 zip 发给老师,解压到任意位置即可")
    if "--installer" in sys.argv:
        print("  • 安装包:    dist/Output/XuanFuQiu_..._Setup.exe  (带开始菜单/卸载)")


if __name__ == "__main__":
    main()
