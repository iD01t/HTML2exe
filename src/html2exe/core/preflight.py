import sys
import os
import subprocess
import shutil
from typing import List

from .config import AppConfig


def check_python_version() -> List[str]:
    """Check if Python version is sufficient."""
    errors = []
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10 or newer is required. You are using {sys.version.split(' ')[0]}.")
    return errors


def check_pyinstaller() -> List[str]:
    """Check if PyInstaller is installed and accessible."""
    errors = []
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                                capture_output=True, text=True, check=False)
        if result.returncode != 0:
            errors.append("PyInstaller is not installed or not in PATH. Please run 'pip install pyinstaller'.")
    except FileNotFoundError:
        errors.append("PyInstaller is not installed or not in PATH. Please run 'pip install pyinstaller'.")
    return errors


def check_vc_redist() -> List[str]:
    """Check for Visual C++ Redistributable on Windows."""
    errors = []
    if sys.platform == "win32":
        try:
            import winreg
            # This is a common key for the VC++ 2015-2022 redistributable
            key_path = r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
            try:
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            except FileNotFoundError:
                errors.append("Microsoft Visual C++ Redistributable is not found. It is recommended for some packages. Please install it.")
        except ImportError:
            # Should not happen on Windows if pywin32 is installed
            pass
    return errors


def check_upx(config: AppConfig) -> List[str]:
    """Check for UPX if compression is enabled."""
    errors = []
    if config.build.upx_compress:
        if not shutil.which("upx"):
            errors.append("UPX compression is enabled, but UPX is not found in your system's PATH.")
    return errors


def check_project_files(config: AppConfig) -> List[str]:
    """Check for necessary project files."""
    errors = []
    if config.build.source_type == "folder":
        if not os.path.exists(config.build.source_path):
            errors.append(f"Source folder not found: {config.build.source_path}")
        elif not os.path.exists(os.path.join(config.build.source_path, "index.html")):
            errors.append(f"index.html not found in source folder: {config.build.source_path}")
    if config.build.icon_path and not os.path.exists(config.build.icon_path):
        errors.append(f"Icon file not found: {config.build.icon_path}")
    return errors


def find_iscc() -> str:
    """Find the Inno Setup compiler."""
    if sys.platform != "win32":
        return None

    program_files = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    program_files_64 = os.environ.get("ProgramW6432", "C:\\Program Files")

    possible_paths = [
        os.path.join(program_files, "Inno Setup 6", "iscc.exe"),
        os.path.join(program_files_64, "Inno Setup 6", "iscc.exe")
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    if shutil.which("iscc"):
        return "iscc"

    return None

def check_inno_setup() -> List[str]:
    """Check for Inno Setup compiler."""
    errors = []
    if sys.platform == "win32" and not find_iscc():
        errors.append("Inno Setup is not installed or not in PATH. Installer creation will be disabled.")
    return errors

def run_preflight_checks(config: AppConfig, check_installer=False) -> List[str]:
    """Run all pre-flight checks."""
    errors = []
    errors.extend(check_python_version())
    errors.extend(check_pyinstaller())
    errors.extend(check_vc_redist())
    errors.extend(check_upx(config))
    errors.extend(check_project_files(config))
    if check_installer:
        errors.extend(check_inno_setup())
    return errors
