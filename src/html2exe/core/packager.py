import os
import sys
import subprocess
import shutil
from .config import AppConfig
from .preflight import find_iscc

def create_inno_script(config: AppConfig, exe_path: str, output_dir: str) -> str:
    """Generate the Inno Setup script."""
    script_template = f"""
[Setup]
AppName={config.metadata.name}
AppVersion={config.metadata.version}
AppPublisher={config.metadata.company}
AppPublisherURL={config.metadata.website}
AppSupportURL={config.metadata.website}
AppUpdatesURL={config.metadata.website}
DefaultDirName={{autopf}}\\{config.metadata.name}
DefaultGroupName={config.metadata.name}
OutputBaseFilename=setup_{config.metadata.name.lower().replace(' ', '_')}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion
; TODO: Add other files for one-dir mode

[Icons]
Name: "{{group}}\\{config.metadata.name}"; Filename: "{{app}}\\{os.path.basename(exe_path)}"
Name: "{{group}}\\{{cm:UninstallProgram,{config.metadata.name}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{config.metadata.name}"; Filename: "{{app}}\\{os.path.basename(exe_path)}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{os.path.basename(exe_path)}"; Description: "{{cm:LaunchProgram,{config.metadata.name}}}"; Flags: nowait postinstall skipifsilent
"""

    iss_path = os.path.join(output_dir, "installer.iss")
    with open(iss_path, 'w') as f:
        f.write(script_template)
    return iss_path

def create_installer(config: AppConfig, exe_path: str) -> str:
    """Create a Windows installer using Inno Setup."""
    iscc_path = find_iscc()
    if not iscc_path:
        raise FileNotFoundError("Inno Setup compiler (iscc.exe) not found. Please install Inno Setup 6.")

    output_dir = os.path.dirname(exe_path)
    iss_path = create_inno_script(config, exe_path, output_dir)

    cmd = [iscc_path, iss_path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        raise Exception(f"Inno Setup compilation failed:\n{result.stdout}\n{result.stderr}")

    # The installer is created in a 'Output' subdirectory by default
    installer_output_dir = os.path.join(output_dir, "Output")

    # Find the created setup file
    for file in os.listdir(installer_output_dir):
        if file.startswith("setup_") and file.endswith(".exe"):
            return os.path.join(installer_output_dir, file)

    raise FileNotFoundError("Could not find the created installer.")
