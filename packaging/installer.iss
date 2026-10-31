#define MyAppName "GitHub Command Center"
#ifndef MyAppVersion
  #define MyAppVersion "3.47.0"
#endif
#define MyAppExeName "GitHubCommandCenter.exe"

[Setup]
AppId={{65015D7E-8274-4F5D-BE91-474D69EFAF0D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\GitHub Command Center
DefaultGroupName={#MyAppName}
OutputDir=dist\installer
OutputBaseFilename=GitHubCommandCenterSetup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern

[Files]
Source: "dist\GitHubCommandCenter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "USER_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
