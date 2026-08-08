#define AppName "EREBUS"
#define AppVersion "1.0"
#define AppPublisher "Noah Joseph Mateo Almagro"
#define AppExecutableName "EREBUS v1.0.exe"
#define AppId "{{7DF0826D-1C36-48A2-9C70-F17D4CA90D14}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}

DefaultDirName={autopf}\EREBUS
DefaultGroupName=EREBUS

DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

OutputDir=..\release
OutputBaseFilename=EREBUS_v1.0_Setup

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

LicenseFile=LICENSE.txt

UninstallDisplayName=EREBUS v1.0
UninstallDisplayIcon={app}\{#AppExecutableName}

VersionInfoVersion=1.0.0.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Instalador de EREBUS v1.0
VersionInfoProductName=EREBUS
VersionInfoProductVersion=1.0

CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Types]
Name: "full"; Description: "Instalación completa"
Name: "compact"; Description: "Solo EREBUS"
Name: "custom"; Description: "Instalación personalizada"; Flags: iscustom

[Components]
Name: "erebus"; Description: "EREBUS v1.0"; Types: full compact custom; Flags: fixed
Name: "nmap"; Description: "Instalar Nmap"; Types: full custom
[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "startmenuicon"; Description: "Crear acceso directo en el menú Inicio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\EREBUS v1.0\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: erebus

Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "NOTICE.txt"; DestDir: "{app}"; Flags: ignoreversion

Source: "dependencies\nmap-setup.exe"; DestDir: "{tmp}\EREBUS"; DestName: "nmap-setup.exe"; Flags: deleteafterinstall; Components: nmap

[Icons]
Name: "{group}\EREBUS v1.0"; Filename: "{app}\{#AppExecutableName}"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{autodesktop}\EREBUS v1.0"; Filename: "{app}\{#AppExecutableName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{tmp}\EREBUS\nmap-setup.exe"; Description: "Instalar Nmap"; StatusMsg: "Iniciando el instalador de Nmap..."; Flags: waituntilterminated; Components: nmap

Filename: "{app}\{#AppExecutableName}"; Description: "Ejecutar EREBUS v1.0"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent; Components: erebus

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
