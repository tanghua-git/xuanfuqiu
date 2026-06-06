; Inno Setup 6 脚本 — 把悬浮球 onedir 目录打成带开始菜单/桌面快捷方式/卸载项的安装包
; 用法:本机装好 Inno Setup 6 后,运行 "ISCC.exe installer.iss"
; 或运行 "python build.py --installer" 让 build.py 自动调 ISCC
;
; 注意:build.py 现在用的是 --onedir 模式,产物是 dist\悬浮球\ 整个目录
; (主 exe + 一堆 DLL/locales/.pak 等)。--onefile 与 QtWebEngine 有兼容性 bug
; (Chromium 子进程用 applicationDirPath() 找资源,但 --onefile 的资源在
;  %TEMP%\_MEIxxxxx,导致其他机器上 WebEngine 启动失败)。

#define MyAppName "悬浮球课件工具(精简版)"
#define MyAppNameEn "XuanFuQiu"
; PyInstaller 输出的目录名(必须和 build.py 里的 APP_NAME 一致!)
; APP_NAME = "悬浮球" → dist/悬浮球/
#define MyAppBuildDir "悬浮球"
#define MyAppVersion "1.0"
#define MyAppPublisher "XuanFuQiu"
#define MyAppURL "https://github.com/"
#define MyAppExeName "悬浮球.exe"

[Setup]
; 安装包标识(每次发布改成唯一 GUID)
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppNameEn}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 安装包输出目录(相对于当前 .iss)
OutputDir=dist\Output
; 输出文件名
; (注:全功能版如果想区分,可以加 _full 后缀,但默认保持兼容文件名)
OutputBaseFilename={#MyAppNameEn}_lite_v{#MyAppVersion}_Setup
; 安装包图标(用我们生成的 .ico)
SetupIconFile=resources\icon.ico
; 压缩算法
Compression=lzma2/ultra64
SolidCompression=yes
; 普通用户权限,不需要管理员
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Windows 10/11 风格
MinVersion=10.0
; 卸载时显示应用图标
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; 漂亮的安装界面
WizardStyle=modern
WizardSizePercent=120

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
; 注意:这个 ISCC 6.5.3 不认 "checked"/"disable" 等 flag(奇怪 bug),
; 所以全部走默认 unchecked,用户在向导里手动勾选。
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "开机自动启动(可选)"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; ---- 关键:整个 onedir 目录(主 exe + DLL + QtWebEngine 资源)一并打入 ----
; 源目录 = build.py 用 APP_NAME="悬浮球" 生成的 dist\悬浮球\(短目录名)
; 注意不要用 {#MyAppName},那是显示名 "悬浮球课件工具"
; recursesubdirs   = 递归子目录
; createallsubdirs = 自动创建子目录
; ignoreversion    = 不比较版本,每次都覆盖(开发期方便)
Source: "dist\{#MyAppBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 图标(给开始菜单快捷方式用,虽然 onedir 里的 Qt6WebEngineWidgets.dll 等文件里也有图标)
Source: "resources\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
; 安装完询问是否启动
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; 可选的"开机自启"任务
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppNameEn}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[UninstallDelete]
; 卸载时清掉用户配置(可选,默认保留,让用户重装后能恢复按钮)
; Type: filesandordirs; Name: "{userappdata}\{#MyAppNameEn}"
