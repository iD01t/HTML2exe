#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML2EXE Pro Premium - Complete Production Edition
All-in-one script for converting HTML applications to professional desktop executables.
"""

import os
import sys
import json
import shutil
import subprocess
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import webbrowser
import tempfile
import threading
from datetime import datetime
from typing import Dict, Any, List, Callable
import importlib
import re
import traceback
import urllib.request
import urllib.parse
import urllib.error
import socket

# Third-party libraries (will be checked and installed)
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
try:
    import typer
except ImportError:
    typer = None
try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
except ImportError:
    rich = None
try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel: pass
    def Field(*args, **kwargs): return None
try:
    import appdirs
except ImportError:
    appdirs = None
try:
    from flask import Flask, send_from_directory, jsonify, Response
except ImportError:
    Flask, send_from_directory, jsonify, Response = None, None, None, None
try:
    import webview
except ImportError:
    webview = None
try:
    import requests
except ImportError:
    requests = None
try:
    import psutil
except ImportError:
    psutil = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# ==================================================================================================
# Dependency Management
# ==================================================================================================
PACKAGE_TO_MODULE_MAP = {
    "typer": "typer",
    "rich": "rich",
    "pydantic": "pydantic",
    "appdirs": "appdirs",
    "flask": "flask",
    "pywebview": "webview",
    "requests": "requests",
    "pillow": "PIL",
    "pyinstaller": "PyInstaller",
    "psutil": "psutil",
    "packaging": "packaging",
    "beautifulsoup4": "bs4",
    "pywin32": "win32api"
}
REQUIRED_PACKAGES = list(PACKAGE_TO_MODULE_MAP.keys())
if sys.platform != "win32":
    REQUIRED_PACKAGES.remove("pywin32")

def check_and_install_dependencies():
    """Checks for missing packages and prompts the user to install them."""
    missing_packages = []
    for package_name in REQUIRED_PACKAGES:
        module_name = PACKAGE_TO_MODULE_MAP.get(package_name, package_name)
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print("HTML2EXE Pro Premium requires the following packages:")
        for pkg in missing_packages:
            print(f" - {pkg}")

        try:
            response = input("Would you like to install them now? (y/n): ").lower()
        except EOFError: # Non-interactive session
            response = 'n'

        if response == 'y':
            print("Installing missing packages...")
            for pkg in missing_packages:
                try:
                    print(f"Installing {pkg}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                except subprocess.CalledProcessError:
                    print(f"\nERROR: Failed to install {pkg}. Please install it manually.", file=sys.stderr)
                    print("You can do this by running: pip install " + " ".join(missing_packages), file=sys.stderr)
                    sys.exit(1)
            print("\nDependencies installed successfully. Please restart the script.")
            sys.exit(0)
        else:
            print("\nInstallation cancelled. Please install the missing packages manually and run the script again.")
            sys.exit(1)

# ==================================================================================================
# Core Module: config.py
# ==================================================================================================
APP_NAME = "HTML2EXE Pro Premium"
if appdirs:
    CONFIG_DIR = appdirs.user_config_dir(APP_NAME)
else:
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", APP_NAME)

class WindowConfig(BaseModel):
    width: int = Field(default=1200, ge=400, le=4096)
    height: int = Field(default=800, ge=300, le=2160)
    min_width: int = Field(default=400, ge=200)
    min_height: int = Field(default=300, ge=200)
    resizable: bool = True
    fullscreen: bool = False
    kiosk: bool = False
    frameless: bool = False
    dpi_aware: bool = True
    always_on_top: bool = False
    center: bool = True
    maximized: bool = False

class SecurityConfig(BaseModel):
    csp_enabled: bool = True
    csp_policy: str = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; img-src 'self' data: blob: *;"
    same_origin_only: bool = False
    allow_devtools: bool = True
    block_external_urls: bool = False
    allowed_domains: List[str] = Field(default_factory=list)
    disable_context_menu: bool = False

class AppMetadata(BaseModel):
    name: str = "MyHTMLApp"
    version: str = "1.0.0"
    company: str = "My Company"
    copyright: str = Field(default_factory=lambda: f"© {datetime.now().year} My Company")
    description: str = "HTML Desktop Application"
    author: str = "Developer"
    email: str = "developer@company.com"
    website: str = "https://company.com"
    license: str = "Proprietary"

class BuildConfig(BaseModel):
    source_type: str = Field(default="folder", pattern="^(folder|url)$")
    source_path: str = ""
    output_dir: str = "dist"
    offline_mode: bool = False
    onefile: bool = True
    console: bool = False
    debug: bool = False
    upx_compress: bool = False
    icon_path: str = ""
    splash_screen: str = ""
    custom_protocol: str = ""
    single_instance: bool = True
    tray_menu: bool = True
    auto_start: bool = False
    include_ffmpeg: bool = False
    strip_debug: bool = True

class AdvancedConfig(BaseModel):
    auto_updater: bool = False
    update_url: str = ""
    deep_links: bool = False
    file_associations: List[str] = Field(default_factory=list)
    startup_sound: str = ""
    theme: str = "auto"

class AppConfig(BaseModel):
    metadata: AppMetadata = Field(default_factory=AppMetadata)
    window: WindowConfig = Field(default_factory=WindowConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    build: BuildConfig = Field(default_factory=BuildConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)

    def save(self, path: str = None):
        if path is None:
            path = os.path.join(CONFIG_DIR, "config.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load(cls, path: str = None):
        if path is None:
            path = os.path.join(CONFIG_DIR, "config.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                return cls.model_validate(data)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
        return cls()

# ==================================================================================================
# Core Module: icon_generator.py
# ==================================================================================================
class IconGenerator:
    @staticmethod
    def generate_icon(text: str, output_path: str, size: int = 256):
        if not Image:
            print("Warning: Pillow is not installed. Cannot generate icon.")
            return None
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for y in range(size):
            r = int(102 + (116 * y / size))
            g = int(126 - (47 * y / size))
            b = int(234 - (72 * y / size))
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        margin = size // 8
        draw.ellipse([margin, margin, size - margin, size - margin], fill=(255, 255, 255, 30))
        font = None
        font_size = size // 4
        font_names = ["dejavusans.ttf", "liberationsans-regular.ttf", "arial.ttf", "calibri.ttf"]
        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except IOError:
                continue
        if not font:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 100), font=font)
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        img.save(output_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        return output_path

# ==================================================================================================
# Core Module: preflight.py
# ==================================================================================================
class PreflightChecker:
    @staticmethod
    def run_all_checks(source_path: str, source_type: str) -> Dict[str, Any]:
        report = { "recommendations": [], "warnings": [], "errors": [], "suggestions": [] }
        PreflightChecker._check_python_version(report)
        PreflightChecker._check_pyinstaller(report)
        PreflightChecker._check_memory(report)
        if source_type == "folder":
            PreflightChecker._check_folder_source(source_path, report)
        elif source_type == "url":
            PreflightChecker._check_url_source(source_path, report)
        return report

    @staticmethod
    def _check_python_version(report: Dict[str, Any]):
        if sys.version_info < (3, 8):
            report["errors"].append("Python 3.8+ is required.")

    @staticmethod
    def _check_pyinstaller(report: Dict[str, Any]):
        if not importlib.util.find_spec("PyInstaller"):
            report["errors"].append("PyInstaller is not installed.")

    @staticmethod
    def _check_memory(report: Dict[str, Any]):
        if psutil:
            available_memory = psutil.virtual_memory().available / (1024**3)
            if available_memory < 1:
                report["warnings"].append(f"Low memory detected ({available_memory:.2f}GB).")

    @staticmethod
    def _check_folder_source(source_path: str, report: Dict[str, Any]):
        if not os.path.exists(source_path):
            report["errors"].append(f"Source folder not found: {source_path}")
            return
        if not os.path.exists(os.path.join(source_path, "index.html")):
            report["warnings"].append("No 'index.html' file found in the source folder.")

    @staticmethod
    def _check_url_source(source_path: str, report: Dict[str, Any]):
        try:
            response = urllib.request.urlopen(source_path, timeout=10)
            if response.getcode() >= 400:
                report["errors"].append(f"URL returned status code {response.getcode()}.")
        except Exception as e:
            report["errors"].append(f"Could not access URL: {e}")

    @staticmethod
    def apply_recommended_settings(config: AppConfig, settings: Dict[str, Any]):
        pass

# ==================================================================================================
# Core Module: builder.py
# ==================================================================================================
class BuildEngine:
    def __init__(self, config: AppConfig, progress_callback: Callable = None):
        self.config = config
        self.progress_callback = progress_callback or (lambda x: None)
        self.build_dir = os.path.join(config.build.output_dir, "build")
        self.dist_dir = config.build.output_dir

    def prepare_build(self) -> str:
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)
        if self.config.build.source_type == "folder":
            source_build_dir = os.path.join(self.build_dir, "html_assets")
            if os.path.exists(source_build_dir):
                shutil.rmtree(source_build_dir)
            shutil.copytree(self.config.build.source_path, source_build_dir)
        icon_path = self.config.build.icon_path
        if not icon_path or not os.path.exists(icon_path):
            icon_path = os.path.join(self.build_dir, "app_icon.ico")
            IconGenerator.generate_icon(self.config.metadata.name[:2].upper(), icon_path)
            self.config.build.icon_path = icon_path
        main_script = self._create_main_script()
        main_script_path = os.path.join(self.build_dir, "main.py")
        with open(main_script_path, 'w', encoding='utf-8') as f:
            f.write(main_script)
        return main_script_path

    def _create_main_script(self) -> str:
        script_template = """
import sys, os, webview, threading, time, json
from flask import Flask, send_from_directory

CONFIG = %(config_json)s

def create_app():
    app = Flask(__name__)
    @app.route('/')
    def index():
        if CONFIG["build"]["source_type"] == "url":
            return '<html><body style="margin:0;"><iframe src="' + CONFIG["build"]["source_path"] + '" style="width:100%%;height:100vh;border:none;"></iframe></body></html>'
        else:
            # Correctly reference bundled assets
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            return send_from_directory(os.path.join(base_dir, 'html_assets'), 'index.html')

    @app.route('/<path:filename>')
    def serve_static(filename):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return send_from_directory(os.path.join(base_dir, 'html_assets'), filename)
    return app

def run_flask_app():
    app = create_app()
    # Use a random port to avoid conflicts
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()

    server_thread = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False), daemon=True)
    server_thread.start()
    time.sleep(1)

    webview.create_window(
        CONFIG["metadata"]["name"],
        f"http://127.0.0.1:{port}",
        width=CONFIG["window"]["width"],
        height=CONFIG["window"]["height"],
        resizable=CONFIG["window"]["resizable"]
    )
    webview.start(debug=CONFIG["build"]["debug"])

if __name__ == '__main__':
    run_flask_app()
"""
        return script_template % {"config_json": json.dumps(self.config.model_dump())}

    def build(self, extra_hidden_imports: List[str] = None) -> Dict[str, Any]:
        main_script_path = self.prepare_build()
        cmd = self._build_pyinstaller_command(main_script_path, extra_hidden_imports)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Build failed: {result.stderr or result.stdout}")
        exe_path = self._get_exe_path()
        return {"success": True, "exe_path": exe_path}

    def _build_pyinstaller_command(self, main_script_path: str, extra_hidden_imports: List[str] = None) -> List[str]:
        cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", f"--name={self.config.metadata.name}", f"--distpath={self.dist_dir}", f"--workpath={os.path.join(self.build_dir, 'work')}", f"--specpath={self.build_dir}"]
        if self.config.build.onefile: cmd.append("--onefile")
        if not self.config.build.console: cmd.append("--windowed")
        if self.config.build.icon_path: cmd.append(f"--icon={self.config.build.icon_path}")
        if self.config.build.source_type == "folder":
            assets_path = os.path.abspath(os.path.join(self.build_dir, "html_assets"))
            cmd.append(f"--add-data={assets_path}{os.pathsep}html_assets")
        hidden_imports = ["flask", "webview"] + (extra_hidden_imports or [])
        for imp in hidden_imports: cmd.append(f"--hidden-import={imp}")
        cmd.append(main_script_path)
        return cmd

    def _get_exe_path(self) -> str:
        exe_name = self.config.metadata.name + (".exe" if sys.platform == "win32" else "")
        return os.path.join(self.dist_dir, exe_name)

# ==================================================================================================
# Core Module: debugger.py
# ==================================================================================================
class BulletProofExporter:
    def __init__(self, config: 'AppConfig'):
        self.config = config
        self.debugger = ExportDebugger()

    def export_with_auto_debug(self) -> Dict[str, Any]:
        strategies = self._get_export_strategies()
        for strategy in strategies:
            try:
                original_config = self.config.model_copy(deep=True)
                for key, value in strategy.get("modifications", {}).items():
                    setattr(self.config.build, key, value)
                engine = BuildEngine(self.config)
                result = engine.build(extra_hidden_imports=strategy.get("extra_hidden_imports"))
                if result["success"]:
                    return result
                self.config = original_config
            except Exception as e:
                print(f"Strategy {strategy['name']} failed with exception: {e}")
                self.config = original_config
        return {"success": False, "error": "All export strategies failed"}

    def _get_export_strategies(self) -> List[Dict[str, Any]]:
        return [
            {"name": "Standard Export", "modifications": {}},
            {"name": "Directory Mode", "modifications": {"onefile": False}},
            {"name": "Add common hidden imports", "extra_hidden_imports": ["jinja2", "werkzeug"]},
        ]

class ExportDebugger:
    pass

# ==================================================================================================
# GUI Module: main.py
# ==================================================================================================
class ModernGUI:
    def __init__(self):
        self.root = None
        self.config = AppConfig.load()

    def run(self):
        self.root = tk.Tk()
        self.root.title("HTML2EXE Pro Premium")
        self.root.geometry("600x400")
        self.root.configure(bg='#1a1a1a')
        self._create_main_layout()
        self.root.mainloop()

    def _create_main_layout(self):
        main_frame = ttk.Frame(self.root, padding=20, style="Modern.TFrame")
        main_frame.pack(fill='both', expand=True)
        source_frame = ttk.LabelFrame(main_frame, text="Source (Folder or URL)", padding=10)
        source_frame.pack(fill='x', pady=10)
        self.source_path_var = tk.StringVar(value=self.config.build.source_path)
        ttk.Entry(source_frame, textvariable=self.source_path_var).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(source_frame, text="Browse...", command=self._browse_source).pack(side='right')
        name_frame = ttk.LabelFrame(main_frame, text="Application Name", padding=10)
        name_frame.pack(fill='x', pady=10)
        self.app_name_var = tk.StringVar(value=self.config.metadata.name)
        ttk.Entry(name_frame, textvariable=self.app_name_var).pack(fill='x')
        ttk.Button(main_frame, text="BUILD", command=self._start_build).pack(fill='x', pady=20)

    def _browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_path_var.set(folder)

    def _start_build(self):
        self.config.build.source_path = self.source_path_var.get()
        self.config.build.source_type = "url" if self.config.build.source_path.startswith("http") else "folder"
        self.config.metadata.name = self.app_name_var.get()
        exporter = BulletProofExporter(self.config)
        result = exporter.export_with_auto_debug()
        if result["success"]:
            messagebox.showinfo("Success", f"Build completed: {result['exe_path']}")
        else:
            messagebox.showerror("Build Failed", result['error'])

# ==================================================================================================
# CLI Module: main.py
# ==================================================================================================
if typer:
    app = typer.Typer()

    @app.command()
    def build(src: str, name: str = "MyApp"):
        config = AppConfig()
        config.build.source_path = src
        config.build.source_type = "url" if src.startswith("http") else "folder"
        config.metadata.name = name
        exporter = BulletProofExporter(config)
        result = exporter.export_with_auto_debug()
        if result["success"]:
            print(f"Build successful: {result['exe_path']}")
        else:
            print(f"Build failed: {result['error']}")

    @app.command()
    def gui():
        """Launch the graphical user interface."""
        gui_app = ModernGUI()
        gui_app.run()

# ==================================================================================================
# Main Entry Point
# ==================================================================================================
def entry_point():
    """Main entry point for the application."""
    try:
        if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == 'gui'):
            if len(sys.argv) > 1 and sys.argv[1] == 'gui':
                sys.argv.pop(1)
            print("HTML2EXE Pro Premium v2.0.0")
            print("Launching GUI...")
            gui_app = ModernGUI()
            gui_app.run()
        else:
            print("HTML2EXE Pro Premium v2.0.0")
            if typer:
                print("Command line arguments provided, using CLI...")
                app()
            else:
                print("CLI is not available because 'typer' is not installed.", file=sys.stderr)
                sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}", file=sys.stderr)
        if "--debug" in sys.argv:
            print("\n--- DEBUG TRACEBACK ---", file=sys.stderr)
            traceback.print_exc()
            print("------------------------", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    check_and_install_dependencies()
    entry_point()
