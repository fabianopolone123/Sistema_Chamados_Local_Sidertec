#define MyAppName "Chamados TI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TI Local"
#define MyAppExeName "ChamadosTI.exe"
#define MyBuildDir "..\dist\ChamadosTI"

[Setup]
AppId={{1E5E708E-7A95-4EB7-A19A-4D0EA5185558}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SistemaChamados\TI
DisableProgramGroupPage=yes
OutputDir=..\dist_installers
OutputBaseFilename=ChamadosTISetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config.example.json"; DestDir: "{app}"; DestName: "config.json"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent
