"""
lite 版打包脚本(真正的"小体积"版):保留所有 PySide6 UI 不变,
只把打包产物里的 QtWebEngine(200MB+ 的 Chromium)剔除掉,
改用 ui/player_window.py 里的 QWebView(走系统 WebView2)。

UI 和操作逻辑与原版(build.py)完全一致,只是 HTML 渲染从
内嵌 Chromium 换成系统 WebView2,打包后体积从 160MB 降到 < 30MB。

用法:
    python build_lite.py             # 只打 exe (onefile,目标 < 25MB)
    python build_lite.py --installer # 同步生成安装包(目标 < 25MB)
    python build_lite.py --onedir    # 改用 onedir 模式(更快启动)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


# 关键:用同名 APP_NAME,这样 dist/悬浮球/ 和 dist/悬浮球.exe 都和原版一致,
# 方便测试时直接对比;安装包文件名要分一下
APP_NAME = "悬浮球"
ENTRY = "main.py"
ICON_PATH = "resources/icon.ico"

# 需要从打包产物里剔除的 QtWebEngine 文件(Chromium 200MB+)
# 这些 PyInstaller hook 会自动收集进来,但我们已经不依赖了,必须手动删
WEBENGINE_FILES_TO_PRUNE = [
    # 主 DLL(最胖,196MB)
    "Qt6WebEngineCore.dll",
    "Qt6WebEngineCore.dll.debug",
    # WebEngine 衍生 DLL
    "Qt6WebEngineWidgets.dll",
    "Qt6WebEngineQuick.dll",
    "Qt6WebEngineQuickDelegatesQml.dll",
    # WebEngine 进程
    "QtWebEngineProcess.exe",
    # WebEngine 子模块 .pyd
    "QtWebEngineCore.pyd",
    "QtWebEngineWidgets.pyd",
    "QtWebEngineQuick.pyd",
]
# PySide6 自带但我们用不到的大文件
# (PyInstaller hook 默认全收,我们要主动减负)
PYQT_UNNEEDED_FILES = [
    # 软 OpenGL 兜底(Win10+ 都有硬件 GL,不需要 19.7MB 软渲染)
    "opengl32sw.dll",
    # FFmpeg(我们不播视频,不要)
    "avcodec-61.dll", "avformat-61.dll", "avutil-59.dll",
    # QML 引擎(我们不用 QML)
    "Qt6Quick.dll", "Qt6Quick3DRuntimeRender.dll", "Qt6Qml.dll",
    "Qt6QmlCompiler.dll", "Qt6QmlCore.dll", "Qt6QmlLocalStorage.dll",
    "Qt6QmlMeta.dll", "Qt6QmlModels.dll", "Qt6QmlNetwork.dll",
    "Qt6QmlWorkerScript.dll", "Qt6QmlXmlListModel.dll",
    "Qt6Quick3D.dll", "Qt6Quick3DUtils.dll", "Qt6Quick3DIblBaker.dll",
    "Qt6Quick3DParticleEffects.dll", "Qt6Quick3DPhysics.dll",
    "QtQml.pyd",
    # PDF(我们不用)
    "Qt6Pdf.dll", "Qt6PdfQuick.dll", "QtPdf.pyd",
    # Designer(运行时不需要)
    "Qt6Designer.dll", "Qt6DesignerComponents.dll", "QtDesigner.pyd",
    # ShaderTools(我们没用自定义 shader)
    "Qt6ShaderTools.dll",
    # QML language server / 工具(运行时不需要)
    "qmlls.exe", "qsb.exe", "qmlformat.exe", "qmlcachegen.exe",
    "qmlimportscanner.exe", "qmltyperegistrar.exe", "qmllint.exe",
    # Qt Linguist 工具(运行时不需要)
    "lupdate.exe", "lrelease.exe", "linguist.exe",
    # Qt 助手文档
    "assistant.exe",
    # 3D 渲染
    "Qt6OpenGLWidgetIntegration.dll", "Qt6OpenGLWidgets.dll",
    "Qt6OpenGL.dll", "QtOpenGL.pyd",  # QtOpenGL.pyd 8.3MB
    # Balsam UI 工具
    "balsam.exe", "balsamui.exe",
    # 3D/Graphs/Charts/Location(我们不用)
    "Qt63DRender.dll", "Qt63DCore.dll", "Qt63DExtras.dll",
    "Qt6Graphs.dll", "Qt6Charts.dll", "Qt6Location.dll",
    "Qt6Positioning.dll", "Qt6PositioningQuick.dll",
    "Qt6Sensors.dll", "Qt6SensorsQuick.dll",
    "Qt6Scxml.dll", "Qt6StateMachine.dll",
    "Qt6Test.dll", "Qt6TextToSpeech.dll",
    "Qt6Multimedia.dll", "Qt6MultimediaWidgets.dll",
    "Qt6MultimediaQuick.dll",
    "Qt6Sql.dll", "Qt6Svg.dll", "Qt6SvgWidgets.dll",
    "Qt6Concurrent.dll", "Qt6DBus.dll",
    "Qt6Bluetooth.dll", "Qt6Nfc.dll",
    "Qt6SerialPort.dll", "Qt6SerialBus.dll",
    "Qt6RemoteObjects.dll", "Qt6WebSockets.dll",
    "Qt6HttpServer.dll", "Qt6WebChannel.dll",
    "Qt6Xml.dll", "Qt6XmlPatterns.dll",
    "Qt6Help.dll", "Qt6QuickControls2Impl.dll",
    # Quick Controls 2 各种风格(我们用 ttk 不需要)
    "Qt6QuickControls2Imagine.dll",
    "Qt6QuickControls2Material.dll",
    "Qt6QuickControls2Basic.dll",
    "Qt6QuickControls2Universal.dll",
    "Qt6QuickControls2Fusion.dll",
    "Qt6QuickControls2Windows.dll",
    "Qt6QuickDialogs2QuickImpl.dll",
    "Qt6QuickTemplates2.dll",
    "Qt6LabsStyleKit.dll", "Qt6LabsAnimation.dll",
    "Qt6LabsFolderListModel.dll", "Qt6LabsQmlModels.dll",
    "Qt6LabsSettings.dll", "Qt6LabsWavefrontMesh.dll",
    "Qt6Quick3DParticles.dll", "Qt6Quick3DAssetUtils.dll",
    "Qt6Quick3DEffects.dll",
    # Quick 控件 Fluent 风格
    "qtquickcontrols2fluentwinui3styleplugin.dll",
    "qtquickcontrols2windowsstyleplugin.dll",
    "qtquickcontrols2fusionstyleplugin.dll",
    "qtquickcontrols2macosstyleplugin.dll",
    "qtquickcontrols2universalstyleplugin.dll",
    "qtquickcontrols2basicstyleplugin.dll",
    "qtquickcontrols2materialstyleplugin.dll",
    "qtquickcontrols2imaginestyleplugin.dll",
    "qtquickcontrols2flstyleplugin.dll",
    # OpenSSL(我们用 QLocalSocket 不用 SSL)
    "libcrypto-3-x64.dll", "libcrypto-3.dll",
    "libssl-3-x64.dll", "libssl-3.dll",
    # assimp 3D 资源
    "assimp.dll", "assimpsceneimport.dll",
    # .pyd 对应的额外 module
    "QtCharts.pyd", "QtDataVisualization.pyd",
    "QtOpenGL.pyd", "QtSvg.pyd", "QtSvgWidgets.pyd",
    "QtSql.pyd", "QtPrintSupport.pyd", "QtXml.pyd",
    # 注意:QtNetwork.pyd 必须保留(QLocalServer/QLocalSocket)
    # OpenWNN 日文输入法插件
    "qtvkbopenwnnplugin.dll", "qtvkbpinyinplugin.dll",
    "qtvkbtcimeplugin.dll", "qtvkbgrooveplugin.dll",
    "qtvkbmalayalamplugin.dll", "qtvkbthaiplugin.dll",
    "qtvkbcangjieplugin.dll", "qtvkbczechplugin.dll",
    "qtvkbhebrewplugin.dll", "qtvkbhungarianplugin.dll",
    "qtvkbitalianplugin.dll", "qtvkblatinplugin.dll",
    "qtvkblithuanianplugin.dll", "qtvkbpolishplugin.dll",
    "qtvkbportugueseplugin.dll", "qtvkbrussianplugin.dll",
    "qtvkbspanishplugin.dll",
    # 其它没在 exclude-module 列表但运行时用不上的 DLL
    "Qt6DataVisualization.dll", "Qt6DataVisualizationQml.dll",
    "Qt6Quick3DXr.dll", "swscale-8.dll",
    "Qt6SpatialAudio.dll", "Qt6UiTools.dll", "Qt6UiToolsQuick.dll",
    "Qt6Quick3DHelpers.dll", "Qt6Quick3DHelpersImpl.dll",
    "Qt6QuickParticles.dll", "Qt6CanvasPainter.dll",
    "Qt6ChartsQml.dll", "Qt63DQuickRender.dll", "Qt63DAnimation.dll",
    "Qt63DExtras.dll", "Qt63DInput.dll", "Qt63DLogic.dll",
    "Qt6VirtualKeyboard.dll", "Qt6VirtualKeyboardQuick.dll",
    "Qt6LabsWavefrontMesh.dll",
    # 数据可视化 / 图形 charts
    "Qt6DataVisualization.pyd", "QtGraphs.pyd",
    "QtGraphsWidgets.pyd", "QtChartsWidgets.pyd",
    "QtCharts.pyd", "QtLocation.pyd", "QtPositioning.pyd",
    "QtBluetooth.pyd", "QtSensors.pyd", "QtSerialPort.pyd",
    "QtNfc.pyd", "QtWebSockets.pyd", "QtScxml.pyd",
    "QtStateMachine.pyd", "QtMultimedia.pyd",
    "QtMultimediaWidgets.pyd", "QtTextToSpeech.pyd",
    "Qt3DCore.pyd", "Qt3DRender.pyd", "Qt3DExtras.pyd",
    "Qt3DAnimation.pyd", "Qt3DInput.pyd", "Qt3DLogic.pyd",
    "QtRemoteObjects.pyd", "QtPdf.pyd", "QtPdfWidgets.pyd",
    "QtSvg.pyd", "QtSvgWidgets.pyd", "QtSql.pyd",
    "QtPrintSupport.pyd", "QtXml.pyd", "QtDesigner.pyd",
    "QtTest.pyd", "QtConcurrent.pyd", "QtDBus.pyd",
    "QtHelp.pyd", "QtOpenGL.pyd", "QtAxContainer.pyd",
    "QtQml.pyd", "QtQuick.pyd", "QtQuickControls2.pyd",
    "QtQuickWidgets.pyd", "QtQuickDialogs2.pyd",
    "QtQuickTemplates2.pyd", "QtQuick3D.pyd",
    "QtWebChannel.pyd",  # WebEngine 依赖,我们不用 WebEngine
    # 注意:QtWebView.pyd 必须保留!(我们用 QWebView 渲染 HTML)
    "QtMultimediaQuick.pyd", "QtSensorsQuick.pyd",
    "QtPositioningQuick.pyd", "QtBluetoothQuick.pyd",
    "QtNfcQuick.pyd", "QtHttpServer.pyd", "QtPdfQuick.pyd",
]
# 整个剔除的目录
WEBENGINE_DIRS_TO_PRUNE = [
    "PySide6/translations/qtwebengine_locales",
    "PySide6/resources",
    "PySide6/qml/QtWebEngine",
]
# 整个剔除的其他目录(我们不用的 Qt 资源)
UNNEEDED_DIRS = [
    # 整个 QML 目录(我们用 PySide6 不是 QML)
    "PySide6/qml",
    # 整个 translations 目录(我们用中文,但用自带 locale)
    "PySide6/translations",
    # 各种用不到的 plugins
    "PySide6/plugins/audio",
    "PySide6/plugins/mediaservice",
    "PySide6/plugins/playlistformats",
    "PySide6/plugins/sensors",
    "PySide6/plugins/sqldrivers",  # 数据库驱动
    "PySide6/plugins/texttospeech",
    "PySide6/plugins/tls",  # TLS 插件
    "PySide6/plugins/canbus",
    "PySide6/plugins/gamepad",
    "PySide6/plugins/geoservices",
    "PySide6/plugins/assetimporters",  # 3D 资源
    "PySide6/plugins/sceneparsers",
    "PySide6/plugins/qmltools",  # QML 工具
    "PySide6/plugins/qml1plugins",
    "PySide6/plugins/designer",  # Designer
    "PySide6/plugins/printsupport",  # 打印
    "PySide6/plugins/platforminputcontexts",  # 输入法
    "PySide6/plugins/accessible",
    "PySide6/plugins/iconengines",
    "PySide6/plugins/renderers",  # QML/3D 渲染器
    "PySide6/plugins/qmltooling",  # QML 工具
    "PySide6/plugins/multimedia",  # 多媒体
    "PySide6/plugins/qmllint",  # QML lint
    "PySide6/plugins/position",  # 位置
    "PySide6/plugins/geometryloaders",  # 3D 几何
    "PySide6/plugins/styles",  # Qt 样式
    "PySide6/plugins/scxmldatamodel",
    "PySide6/plugins/virtualkeyboard",
    "PySide6/plugins/wayland",
    "PySide6/plugins/xcbglintegrations",
    "PySide6/plugins/eglfs",
    # 死目录(运行时用不到)
    "PySide6/metatypes",  # metatype info(15MB,运行时用不到)
    "PySide6/include",  # C++ 头文件
    "PySide6/typesystems",  # C++ binding type info
    "PySide6/lib",  # .lib 文件(linker 用,运行时不需要)
    "PySide6/glue",  # shiboken glue
    # 必须保留:
    # - PySide6/plugins/platforms/(qwindows.dll,Qt 主平台插件)
    # - PySide6/plugins/webview/(QtWebView 2 backend)
    # - PySide6/plugins/imageformats/(PNG/JPEG 加载)
    # - PySide6/plugins/generic/(qgif 等)
]


def make_icon() -> Path:
    """复用主 build.py 的图标生成(确保两个版本图标一致)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_main", Path(__file__).parent / "build.py")
    mod = importlib.util.module_from_spec(spec)
    # build.main() 启动 PyInstaller 流程,这里只想用 make_icon
    # 直接 exec 进 build.py 源但只调用 make_icon
    # 简单做法:读 build.py 源码找到 make_icon 重新执行(略),更简单 — 直接 import 然后单独调
    # 实际上 build.py 是脚本,import 会触发 main() 保护。直接 execfile
    src = (Path(__file__).parent / "build.py").read_text(encoding="utf-8")
    ns = {"__name__": "_not_main_"}
    # 截到 main 之前,只执行 make_icon
    cut = src.find("def main():")
    if cut > 0:
        exec(src[:cut], ns)
    return ns.get("make_icon", lambda: Path())()


def _prune_webengine(dist_root: Path):
    """在打包产物中删除 QtWebEngine + PySide6 用不到的文件,目标 -200MB+。

    适配 onedir(直接在 dist_root 下)布局。"""
    if not dist_root.exists():
        return
    saved = 0
    n_files = 0
    n_dirs = 0
    # 1. 删文件(全目录递归)
    for fname in WEBENGINE_FILES_TO_PRUNE + PYQT_UNNEEDED_FILES:
        for p in dist_root.rglob(fname):
            try:
                saved += p.stat().st_size
                p.unlink()
                n_files += 1
            except OSError:
                pass
    # 1.5 删所有 .pyi(Python 类型提示,运行时不需要,光 PySide6 里有几十个)
    for p in dist_root.rglob("*.pyi"):
        try:
            saved += p.stat().st_size
            p.unlink()
            n_files += 1
        except OSError:
            pass
    # 1.6 删 .lib 文件(linker 用的静态库,运行时不需要)
    for p in dist_root.rglob("*.lib"):
        try:
            saved += p.stat().st_size
            p.unlink()
            n_files += 1
        except OSError:
            pass
    # 2. 删目录(必须先清空)
    for sub in WEBENGINE_DIRS_TO_PRUNE + UNNEEDED_DIRS:
        for p in dist_root.rglob(sub):
            if p.is_dir():
                try:
                    inner_size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                    shutil.rmtree(p, ignore_errors=True)
                    saved += inner_size
                    n_dirs += 1
                except OSError:
                    pass
    print(f"  剪枝:删了 {n_files} 个文件 + {n_dirs} 个目录,共省 {saved/1024/1024:.1f} MB")
    return saved


def build_exe(root: Path) -> Path:
    """打 lite 版 exe。复用 build.py 的 PyInstaller 命令(去 WebEngine 增强)。"""
    entry_path = root / ENTRY
    if not entry_path.exists():
        print(f"找不到入口: {entry_path}")
        sys.exit(1)

    # 清理旧文件
    for d in (root / "build", root / "dist"):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    use_onedir = "--onedir" in sys.argv
    use_onefile = "--onefile" in sys.argv or not use_onedir  # 默认 onefile

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--name", APP_NAME,
    ]
    if use_onefile:
        cmd += ["--onefile", "--windowed"]
    else:
        cmd += ["--onedir", "--windowed"]

    # 关键:不要 collect WebEngine,只 collect 必要的 PySide6 模块
    cmd += [
        "--collect-all", "PySide6",  # 默认行为
        "--collect-all", "shiboken6",
        # 显式 hidden-import:QtWebView 必须有,WebEngine 必须没有
        "--hidden-import", "PySide6.QtWebView",
        # WebEngine 不再 hidden-import(否则 hook 会自动收集 DLL)
    ]

    # 排除大模块(注意:QtWebChannel 不再需要,因为不再用 WebEngine)
    cmd += [
        "--exclude-module", "PySide6.QtWebEngineCore",
        "--exclude-module", "PySide6.QtWebEngineWidgets",
        "--exclude-module", "PySide6.QtWebEngineQuick",
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
        # WebChannel 是 WebEngine 的依赖,WebEngine 没了它也不需要
        "--exclude-module", "PySide6.QtWebChannel",
        "--exclude-module", "PySide6.QtWebSockets",
        # Multimedia 相关
        "--exclude-module", "PySide6.QtMultimedia",
        "--exclude-module", "PySide6.QtMultimediaWidgets",
    ]

    icon = root / ICON_PATH
    if icon.exists():
        cmd += [f"--icon={icon}"]

    # runtime hook:不复用 rthook_pyside6_shim(那是为 WebEngine 设计的),
    # 但保留对 shiboken6 的 DLL 目录添加(Python 3.8+ add_dll_directory)
    # 这里 PySide6.__init__ 自己的机制会处理好,不需要额外 hook

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

    # ---- 关键:剪枝 — 删掉 WebEngine 的 DLL/PYD/.pak(200MB+)----
    print()
    if use_onefile:
        # onefile 是自解压,产物是单文件,无法删 _MEIPASS 里的内容;
        # 但 _MEIPASS 是临时目录,文件在 exe 内部,没法剪。
        # 因此 onefile 模式无法用此方案 — 强制提示
        print("⚠️  --onefile 模式:WebEngine 文件被压进 exe 内部,无法剪枝;")
        print("    强烈建议用 --onedir 模式,体积能从 ~250MB 降到 ~30MB。")
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"\n⚠️  exe 已生成: {out}  ({size_mb:.1f} MB) — 未剪枝,大概率 > 50MB")
    else:
        print("[剪枝] 移除 QtWebEngine DLL/PYD/.pak 资源...")
        out_dir = out.parent
        _prune_webengine(out_dir)
        total = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
        size_mb = total / 1024 / 1024
        n_dll = len(list(out_dir.rglob("*.dll")))
        n_pak = len(list(out_dir.rglob("*.pak")))
        print(f"\n✅ lite 单目录已生成: {out_dir}  (共 {size_mb:.1f} MB,{n_dll} 个 DLL,{n_pak} 个 .pak)")
        print(f"   入口: {out}")
    return out


def build_installer(root: Path, exe: Path) -> Path | None:
    """生成 lite 版安装包(共享 installer.iss,只换文件名加 _lite 后缀避免和原版冲突)。"""
    # ISCC 路径检测
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
        return None

    iss_src = root / "installer_lite.iss"
    if not iss_src.exists():
        print(f"未找到 {iss_src},跳过安装包生成。")
        return None
    # 项目本身就是精简版,installer_lite.iss 已是最终版(显示名带"精简版"、文件名带 _lite),
    # 直接拿这个文件当 ISCC 输入,无需再做替换。
    lite_iss = iss_src

    print(f"\n用 {iscc} 生成 lite 安装包...")
    code = subprocess.call([iscc, str(lite_iss)], cwd=root)
    if code != 0:
        print(f"安装包生成失败,退出码: {code}")
        return None
    out = root / "dist" / "Output" / "XuanFuQiu_lite_v1.0_Setup.exe"
    if not out.exists():
        candidates = sorted((root / "dist" / "Output").glob("*.exe"),
                            key=lambda p: p.stat().st_mtime, reverse=True)
        for c in candidates:
            if "lite" in c.name.lower():
                out = c
                break
    if out.exists():
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"\n✅ lite 安装包已生成: {out}  ({size_mb:.1f} MB)")
        return out
    return None


def main():
    root = Path(__file__).resolve().parent
    print(f"项目目录: {root}\n")

    # 1. 图标(用 build.py 的实现,确保和原版一致)
    print("[1/3] 生成图标...")
    try:
        make_icon()
    except Exception as e:
        print(f"  ! 图标生成跳过: {e}")

    # 2. 打包(强制 onedir 模式,因为 onefile 没法剪枝)
    print("\n[2/3] 打包 lite exe...")
    if "--onefile" in sys.argv:
        print("  (--onefile 模式:WebEngine 文件被压进 exe 内部无法剪,可能 > 50MB)")
    else:
        # 强制 onedir 让剪枝生效
        if "--onedir" not in sys.argv:
            sys.argv.append("--onedir")
    exe = build_exe(root)

    # 3. 安装包
    if "--installer" in sys.argv:
        print("\n[3/3] 生成 lite 安装包...")
        build_installer(root, exe)

    # 大小检查
    print("\n--- 大小检查 ---")
    if exe.is_file():
        sz = exe.stat().st_size / 1024 / 1024
        status = "✅ < 50MB 达标" if sz < 50 else f"❌ {sz:.1f}MB 超过 50MB"
        print(f"  exe:        {sz:6.1f} MB  {status}")
    if "--installer" in sys.argv:
        setup_exe = root / "dist" / "Output" / "XuanFuQiu_lite_v1.0_Setup.exe"
        if setup_exe.exists():
            sz = setup_exe.stat().st_size / 1024 / 1024
            status = "✅ < 50MB 达标" if sz < 50 else f"❌ {sz:.1f}MB 超过 50MB"
            print(f"  安装包:     {sz:6.1f} MB  {status}")

    print("\n分发方式:")
    if "--onefile" in sys.argv:
        print(f"  • lite 单文件:  {exe}    (⚠️  WebEngine 没法剪,可能 > 50MB)")
    else:
        print(f"  • lite 单目录:  {exe.parent}    (推荐,WebEngine 已剪)")
        print(f"  • 整个目录打成 zip 发给老师,解压即可双击启动")
    if "--installer" in sys.argv:
        print(f"  • lite 安装包:  dist/Output/XuanFuQiu_lite_v1.0_Setup.exe")


if __name__ == "__main__":
    main()
