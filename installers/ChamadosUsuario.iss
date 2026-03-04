#define MyAppName "Chamados Usuario"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TI Local"
#define MyAppExeName "ChamadosUsuario.exe"
#define MyBuildDir "..\dist\ChamadosUsuario"

[Setup]
AppId={{FC8E7D2A-CC7A-4DB6-9A53-613C12EB4C11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SistemaChamados\Usuario
DisableProgramGroupPage=yes
OutputDir=..\dist_installers
OutputBaseFilename=ChamadosUsuarioSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config.example.json"; DestDir: "{app}"; DestName: "config.json"; Flags: onlyifdoesntexist

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent
