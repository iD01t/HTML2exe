import sys
import os
import subprocess
import importlib
import time
import tkinter as tk
from tkinter import ttk, messagebox

APP_NAME = "HTML2EXE Pro Premium"

def get_required_packages():
    """Reads the requirements from requirements.in"""
    # Note: This assumes the script is run from the root of the project
    try:
        with open('requirements.in', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        # Fallback if running from a different directory
        # This is not ideal, but makes it more robust for development
        return [
            "typer>=0.12.0", "rich>=13.7.0", "pydantic>=2.7.0", "appdirs>=1.4.0",
            "watchdog>=4.0.0", "flask>=3.0.0", "pywebview>=5.0.0", "requests>=2.32.0",
            "pillow>=10.4.0", "pyinstaller>=6.8.0", "psutil>=5.9.0", "packaging>=23.0",
            "pywin32>=306; sys_platform == 'win32'"
        ]

def show_splash():
    """Show splash screen during dependency installation."""
    splash = tk.Tk()
    splash.title(f"{APP_NAME}")
    splash.geometry("500x300")
    splash.configure(bg='#1a1a1a')
    splash.resizable(False, False)
    splash.eval('tk::PlaceWindow . center')

    title_frame = tk.Frame(splash, bg='#1a1a1a')
    title_frame.pack(pady=40)

    title_label = tk.Label(title_frame, text="HTML2EXE", font=('Arial', 24, 'bold'), fg='#00D4AA', bg='#1a1a1a')
    title_label.pack()
    subtitle_label = tk.Label(title_frame, text="Pro Premium", font=('Arial', 14), fg='#ffffff', bg='#1a1a1a')
    subtitle_label.pack()

    status_frame = tk.Frame(splash, bg='#1a1a1a')
    status_frame.pack(pady=20)
    status_label = tk.Label(status_frame, text="Initializing...", font=('Arial', 11), fg='#cccccc', bg='#1a1a1a')
    status_label.pack()

    progress = ttk.Progressbar(splash, length=300, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()

    splash.update()
    return splash, status_label


def check_and_install_dependencies():
    """Check for required packages and install if missing with modern UI."""
    required_packages = get_required_packages()
    missing_packages = []
    for package in required_packages:
        # handle platform specific packages
        if ";" in package:
            package_name, condition = package.split(";")
            if not eval(condition.strip().replace("sys_platform", f"'{sys.platform}'")):
                continue
        else:
            package_name = package

        package_name = package_name.split(">=")[0].split("==")[0].replace("-", "_")

        try:
            importlib.import_module(package_name)
        except ImportError:
            missing_packages.append(package)

    if not missing_packages:
        return

    splash, status_label = show_splash()
    for i, package in enumerate(missing_packages):
        status_label.config(text=f"Installing {package}... ({i + 1}/{len(missing_packages)})")
        splash.update()

        for attempt in range(3): # Retry up to 3 times
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break # Success
            except subprocess.CalledProcessError as e:
                if attempt == 2: # Last attempt failed
                    splash.destroy()
                    messagebox.showerror("Installation Error",
                                       f"Failed to install {package}.\nPlease run: pip install {' '.join(missing_packages)}")
                    sys.exit(1)
                time.sleep(2) # Wait before retrying

    status_label.config(text="Installation complete! Restarting...")
    splash.update()
    time.sleep(1)
    splash.destroy()
    os.execv(sys.executable, [sys.executable] + sys.argv)
