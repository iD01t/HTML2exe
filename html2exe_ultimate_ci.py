#!/usr/bin/env python3
"""
HTML2EXE Pro Ultimate - CI/Headless Edition
============================================
Enterprise-grade HTML to Windows executable converter with full CLI support,
headless builds, and production hardening.

Version: 9.0.0 Ultimate CI
Author: HTML2EXE Pro Team
License: Commercial

New Features:
- Headless/CI mode with --no-gui flag
- JSON config file support
- Simulate/dry-run mode for testing
- Production-safe defaults
- Enhanced error messages
"""

import sys
import os
import subprocess
import json
import shutil
import threading
import time
import uuid
import platform
import webbrowser
import tempfile
import zipfile
import winreg
import traceback
import logging
import argparse
import socket
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import urllib.request

# Platform check with simulation support
SIMULATE_MODE = "--simulate" in sys.argv
if platform.system() != "Windows" and not SIMULATE_MODE:
    print("=" * 60)
    print("ERROR: HTML2EXE Pro targets Windows executables")
    print("This builder must run on Windows to create .exe files")
    print("Use --simulate flag to test on non-Windows systems")
    print("=" * 60)
    sys.exit(2)

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False
    if "--no-gui" not in sys.argv:
        print("ERROR: tkinter not available. Use --no-gui for headless mode.")
        sys.exit(1)

# Optional imports
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
    if TK_AVAILABLE:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
except ImportError:
    CTK_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# =============================================================================
# CONSTANTS
# =============================================================================

__version__ = "9.0.0"
__build__ = "20250117.ci"
APP_NAME = "HTML2EXE Pro Ultimate CI"
APP_ID = "com.html2exe.pro"

# Paths
DATA_DIR = Path.home() / ".html2exe_pro"
CONFIG_DIR = DATA_DIR / "config"
LOG_DIR = DATA_DIR / "logs"
PROJECTS_DIR = DATA_DIR / "projects"
TEMP_DIR = DATA_DIR / "temp"

# Create directories
for directory in [CONFIG_DIR, LOG_DIR, PROJECTS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Requirements
MIN_PYTHON = (3, 8)
WEBVIEW2_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW2_INSTALLER_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"

# Package import mapping
PACKAGE_IMPORT_MAP = {
    "pyinstaller": "PyInstaller",
    "pywebview": "webview",
    "pillow": "PIL"
}

# =============================================================================
# LAUNCHER TEMPLATE
# =============================================================================

LAUNCHER_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{app_name} - Built with HTML2EXE Pro
Version: {app_version}
"""

import sys
import os
import json
import threading
import platform
import webbrowser
import logging
import socket
import time
from pathlib import Path

# Configuration
CONFIG = {{
    "app_name": {app_name!r},
    "app_version": {app_version!r},
    "window": {{
        "title": {window_title!r},
        "width": {window_width},
        "height": {window_height},
        "min_width": {window_min_width},
        "min_height": {window_min_height},
        "resizable": {window_resizable},
        "fullscreen": {window_fullscreen},
        "frameless": {window_frameless},
        "on_top": {window_always_on_top},
        "transparent": {window_transparent}
    }},
    "features": {{
        "dev_tools": {enable_dev_tools},
        "context_menu": {enable_context_menu},
        "printing": {enable_printing}
    }},
    "security": {{
        "csp_policy": {csp_policy!r},
        "enable_cors": {enable_cors}
    }},
    "app_dir": {app_dir!r},
    "entry_file": {entry_file!r},
    "http_port": 0
}}

# Command-line argument support
if "--version" in sys.argv:
    print(f"{{CONFIG['app_name']}} {{CONFIG['app_version']}}")
    sys.exit(0)

if "--help" in sys.argv:
    print(f"{{CONFIG['app_name']}} v{{CONFIG['app_version']}}")
    print("Usage: {{sys.argv[0]}} [options]")
    print("Options:")
    print("  --version    Show version information")
    print("  --help       Show this help message")
    print("  --debug      Enable debug mode")
    sys.exit(0)

if "--debug" in sys.argv:
    CONFIG["features"]["dev_tools"] = True

def get_resource_path(relative_path):
    """Get path to bundled resource."""
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def build_url():
    """Build URL for application."""
    app_dir = get_resource_path(CONFIG["app_dir"])
    entry = CONFIG["entry_file"]
    
    if Path(app_dir).is_dir():
        try:
            from flask import Flask, send_from_directory, send_file, Response, request
        except ImportError:
            path = Path(app_dir) / entry
            return path.as_uri()
        
        app = Flask(__name__, static_folder=app_dir)
        
        @app.after_request
        def apply_security(resp):
            if CONFIG["security"]["csp_policy"]:
                resp.headers["Content-Security-Policy"] = CONFIG["security"]["csp_policy"]
            if CONFIG["security"]["enable_cors"]:
                resp.headers["Access-Control-Allow-Origin"] = "*"
                resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            resp.headers["X-Content-Type-Options"] = "nosniff"
            resp.headers["X-Frame-Options"] = "SAMEORIGIN"
            resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            return resp
        
        @app.route("/")
        def index():
            return send_file(os.path.join(app_dir, entry))
        
        @app.route("/<path:path>")
        def serve_file(path):
            return send_from_directory(app_dir, path)
        
        @app.errorhandler(404)
        def spa_fallback(e):
            return send_file(os.path.join(app_dir, entry))
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        
        def run_server():
            app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(0.5)
        
        return f"http://127.0.0.1:{{port}}/"
    
    path = Path(app_dir) / entry
    return path.as_uri()

class Api:
    def __init__(self, window=None):
        self.window = window
    
    def open_external(self, url):
        try:
            webbrowser.open(url)
            return {{"ok": True}}
        except Exception as e:
            return {{"ok": False, "error": str(e)}}
    
    def get_system_info(self):
        return {{
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": sys.version
        }}
    
    def minimize(self):
        if self.window:
            try:
                self.window.minimize()
                return {{"ok": True}}
            except Exception as e:
                return {{"ok": False, "error": str(e)}}
        return {{"ok": False, "error": "Window not available"}}
    
    def maximize(self):
        if self.window:
            try:
                self.window.maximize()
                return {{"ok": True}}
            except Exception as e:
                return {{"ok": False, "error": str(e)}}
        return {{"ok": False, "error": "Window not available"}}
    
    def close(self):
        if self.window:
            try:
                self.window.destroy()
                return {{"ok": True}}
            except Exception as e:
                return {{"ok": False, "error": str(e)}}
        return {{"ok": False, "error": "Window not available"}}
    
    def toggle_fullscreen(self):
        if self.window:
            try:
                self.window.toggle_fullscreen()
                return {{"ok": True}}
            except Exception as e:
                return {{"ok": False, "error": str(e)}}
        return {{"ok": False, "error": "Window not available"}}

def main():
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
    
    url = build_url()
    
    try:
        import webview
        
        api = Api(None)
        
        window = webview.create_window(
            title=CONFIG["window"]["title"],
            url=url,
            width=CONFIG["window"]["width"],
            height=CONFIG["window"]["height"],
            resizable=CONFIG["window"]["resizable"],
            fullscreen=CONFIG["window"]["fullscreen"],
            frameless=CONFIG["window"]["frameless"],
            on_top=CONFIG["window"]["on_top"],
            transparent=CONFIG["window"]["transparent"],
            min_size=(CONFIG["window"]["min_width"], CONFIG["window"]["min_height"]),
            js_api=api
        )
        
        api.window = window
        
        JS_BRIDGE = """
        (function() {{
            window.html2exe = {{
                version: '9.0.0',
                platform: 'windows',
                api: {{
                    openExternal: (url) => pywebview.api.open_external(url),
                    getSystemInfo: () => pywebview.api.get_system_info(),
                    minimize: () => pywebview.api.minimize(),
                    maximize: () => pywebview.api.maximize(),
                    close: () => pywebview.api.close(),
                    toggleFullscreen: () => pywebview.api.toggle_fullscreen()
                }}
            }};
            
            if (!{{CONFIG["features"]["context_menu"]}}) {{
                document.addEventListener('contextmenu', e => e.preventDefault());
            }}
        }})();
        """.format(CONFIG=CONFIG)
        
        def inject_bridge():
            try:
                window.evaluate_js(JS_BRIDGE)
            except:
                pass
        
        window.events.loaded += inject_bridge
        
        webview.start(debug=CONFIG["features"]["dev_tools"])
        
    except ImportError:
        webbrowser.open(url)
        print(f"Opened in browser: {{url}}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''

# =============================================================================
# VERSION FILE TEMPLATE
# =============================================================================

VERSION_FILE_TEMPLATE = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{company}'),
           StringStruct(u'FileDescription', u'{description}'),
           StringStruct(u'FileVersion', u'{version}'),
           StringStruct(u'InternalName', u'{name}'),
           StringStruct(u'LegalCopyright', u'{copyright}'),
           StringStruct(u'OriginalFilename', u'{name}.exe'),
           StringStruct(u'ProductName', u'{name}'),
           StringStruct(u'ProductVersion', u'{version}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''

# =============================================================================
# LOGGING
# =============================================================================

def setup_logger() -> logging.Logger:
    """Setup logger with rotation."""
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', '%H:%M:%S'))
    logger.addHandler(console)
    
    # Daily rotating file handler
    log_file = LOG_DIR / "html2exe.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

# =============================================================================
# DATA MODELS
# =============================================================================

class BuildStatus(Enum):
    IDLE = "idle"
    VALIDATING = "validating"
    PREPARING = "preparing"
    BUILDING = "building"
    PACKAGING = "packaging"
    SIGNING = "signing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BuildConfig:
    """Build configuration with production defaults."""
    # App info
    app_name: str = "MyApp"
    app_version: str = "1.0.0"
    app_description: str = "My Application"
    app_company: str = "My Company"
    app_copyright: str = ""
    
    # Source
    source_path: str = ""
    entry_file: str = "index.html"
    app_dir: str = "html_assets"
    
    # Window
    window_title: str = ""
    window_width: int = 1280
    window_height: int = 720
    window_min_width: int = 640
    window_min_height: int = 480
    window_resizable: bool = True
    window_fullscreen: bool = False
    window_frameless: bool = False
    window_always_on_top: bool = False
    window_transparent: bool = False
    
    # Build
    output_dir: str = "dist"
    one_file: bool = True
    console_mode: bool = False
    admin_required: bool = False
    icon_path: str = ""
    use_upx: bool = False
    strip_binaries: bool = True
    
    # Features (production-safe defaults)
    enable_dev_tools: bool = False
    enable_context_menu: bool = False  # Changed to False by default
    enable_printing: bool = True
    enable_cors: bool = True
    
    # Security
    csp_policy: str = "default-src 'self' http://127.0.0.1:*; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    
    # Signing
    sign_executable: bool = False
    certificate_path: str = ""
    certificate_password: str = ""
    timestamp_server: str = "http://timestamp.digicert.com"
    
    # Installer
    create_installer: bool = False
    include_webview2: bool = True
    
    # Metadata
    guid: str = field(default_factory=lambda: str(uuid.uuid4()))
    build_count: int = 0
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration."""
        errors = []
        
        if not self.app_name or not self.app_name.replace(" ", "").replace("_", "").replace("-", "").isalnum():
            errors.append("App name must contain alphanumeric characters")
        
        if not self.source_path:
            errors.append("Source path is required")
        elif not SIMULATE_MODE and not Path(self.source_path).exists():
            errors.append(f"Source path not found: {self.source_path}")
        
        if self.icon_path and not SIMULATE_MODE and not Path(self.icon_path).exists():
            errors.append(f"Icon not found: {self.icon_path}")
        
        # Validate version format
        try:
            parts = self.app_version.split('.')
            if len(parts) < 2:
                errors.append("Version must be in format X.Y or X.Y.Z")
            for part in parts:
                int(part)
        except:
            errors.append("Invalid version format")
        
        return len(errors) == 0, errors
    
    def get_version_tuple(self) -> str:
        """Get version as tuple string for version file."""
        parts = self.app_version.split('.')
        while len(parts) < 4:
            parts.append('0')
        return ', '.join(parts[:4])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BuildConfig':
        """Create from dictionary."""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config

# =============================================================================
# CONFIG HELPERS FOR CLI
# =============================================================================

def load_config_from_json(path: str) -> BuildConfig:
    """Load BuildConfig from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BuildConfig.from_dict(data)

def apply_overrides(cfg: BuildConfig, kv_pairs: List[str]) -> BuildConfig:
    """Apply key=value overrides to config."""
    if not kv_pairs:
        return cfg
        
    for pair in kv_pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k = k.strip()
        v = v.strip()
        
        if not hasattr(cfg, k):
            logger.warning(f"Unknown config field: {k}")
            continue
        
        # Type casting based on current field type
        current = getattr(cfg, k)
        try:
            if isinstance(current, bool):
                setattr(cfg, k, v.lower() in ("1", "true", "yes", "on"))
            elif isinstance(current, int):
                setattr(cfg, k, int(v))
            else:
                setattr(cfg, k, v)
            logger.info(f"Override: {k} = {v}")
        except ValueError as e:
            logger.warning(f"Failed to override {k}: {e}")
            
    return cfg

def save_config_to_json(cfg: BuildConfig, path: str):
    """Save BuildConfig to JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, indent=2, default=str)

# =============================================================================
# DEPENDENCY CHECKER
# =============================================================================

class DependencyChecker:
    """Check and manage dependencies."""
    
    @staticmethod
    def check_python() -> bool:
        """Check Python version."""
        return sys.version_info >= MIN_PYTHON
    
    @staticmethod
    def check_package(name: str) -> Tuple[bool, str]:
        """Check if package is installed."""
        import_name = PACKAGE_IMPORT_MAP.get(name, name.replace('-', '_'))
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            return True, version
        except ImportError:
            return False, ""
    
    @staticmethod
    def check_pyinstaller() -> Tuple[bool, str]:
        """Check PyInstaller availability."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, ""
        except:
            return False, ""
    
    @staticmethod
    def check_webview2() -> Tuple[bool, str]:
        """Check WebView2 runtime installation."""
        if SIMULATE_MODE:
            return True, "simulated"
            
        locations = [
            (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_GUID}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_GUID}"),
            (winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_GUID}"),
        ]
        
        for hkey, key_path in locations:
            try:
                with winreg.OpenKey(hkey, key_path) as key:
                    version, _ = winreg.QueryValueEx(key, "pv")
                    return True, version
            except:
                continue
        return False, ""

# =============================================================================
# ICON GENERATOR
# =============================================================================

class IconGenerator:
    """Generate application icons."""
    
    @staticmethod
    def generate_from_text(text: str, output_path: str) -> bool:
        """Generate icon from text."""
        if not PIL_AVAILABLE:
            return False
        
        try:
            size = 256
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Gradient background
            for i in range(size):
                color = (
                    int(20 + 50 * (1 - i/size)),
                    int(100 + 100 * (1 - i/size)),
                    int(200 + 55 * (1 - i/size)),
                    255
                )
                draw.rectangle([0, i, size, i+1], fill=color)
            
            # Draw text
            text = text[:2].upper()
            try:
                font = ImageFont.truetype("arial.ttf", size // 3)
            except:
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", size // 3)
                except:
                    font = ImageFont.load_default()
            
            # Center text
            bbox = draw.textbbox((0, 0), text, font=font)
            x = (size - (bbox[2] - bbox[0])) // 2
            y = (size - (bbox[3] - bbox[1])) // 2
            
            # Draw with shadow
            for offset in [3, 2]:
                draw.text((x+offset, y+offset), text, fill=(0, 0, 0, 100), font=font)
            draw.text((x, y), text, fill='white', font=font)
            
            # Use compatible resampling filter
            resample = getattr(Image, "Resampling", Image).LANCZOS
            
            # Save with multiple sizes
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(output_path, format='ICO', sizes=sizes)
            return True
            
        except Exception as e:
            logger.error(f"Icon generation failed: {e}")
            return False

# =============================================================================
# BUILD ENGINE
# =============================================================================

class BuildEngine:
    """Production build engine with simulation support."""
    
    def __init__(self, config: BuildConfig, simulate: bool = False):
        self.config = config
        self.status = BuildStatus.IDLE
        self.progress = 0
        self.temp_dir = TEMP_DIR / f"build_{int(time.time())}_{os.getpid()}"
        self.output_path = None
        self.cancel_event = threading.Event()
        self.process = None
        self.callbacks = {}
        self.simulate = simulate  # NEW: Simulation mode
    
    def set_callback(self, name: str, callback: Callable):
        """Set callback function."""
        self.callbacks[name] = callback
    
    def cancel(self):
        """Cancel the build."""
        self.cancel_event.set()
        if self.process:
            self.process.terminate()
    
    def build(self) -> Tuple[bool, str]:
        """Execute build process."""
        try:
            # Validate
            self._update_status(BuildStatus.VALIDATING)
            valid, errors = self.config.validate()
            if not valid:
                raise BuildError(f"Validation failed: {', '.join(errors)}")
            
            # Check dependencies (skip heavy checks in simulate mode)
            if not self.simulate:
                self._check_dependencies()
            else:
                self._update_progress("Simulate: skipping dependency checks", 5)
            
            self._check_cancelled()
            
            # Create temp directory
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Build steps up to spec creation are safe in simulate mode
            self._update_status(BuildStatus.PREPARING)
            self._prepare_resources()
            self._check_cancelled()
            
            self._generate_launcher()
            self._check_cancelled()
            
            self._generate_version_file()
            self._check_cancelled()
            
            self._create_spec()
            self._check_cancelled()
            
            if self.simulate:
                # Simulation mode - stop here and report success
                self._update_status(BuildStatus.COMPLETED)
                self._update_progress("Simulation complete", 100)
                return True, f"SIMULATE OK - Artifacts generated in {self.temp_dir}"
            
            # Real build continues...
            self._update_status(BuildStatus.BUILDING)
            self._run_pyinstaller()
            self._check_cancelled()
            
            if self.config.sign_executable:
                self._update_status(BuildStatus.SIGNING)
                self._sign_executable()
            
            if self.config.create_installer:
                self._update_status(BuildStatus.PACKAGING)
                self._create_installer()
            
            self._update_status(BuildStatus.TESTING)
            self._test_executable()
            
            # Complete
            self._update_status(BuildStatus.COMPLETED)
            self.config.build_count += 1
            
            return True, str(self.output_path)
            
        except BuildCancelled:
            self._update_status(BuildStatus.CANCELLED)
            return False, "Build cancelled"
        except BuildError as e:
            self._update_status(BuildStatus.FAILED)
            return False, str(e)
        except Exception as e:
            self._update_status(BuildStatus.FAILED)
            logger.error(f"Build failed: {e}", exc_info=True)
            return False, f"Unexpected error: {e}"
        finally:
            if not self.simulate:  # Keep artifacts in simulate mode for inspection
                self._cleanup()
    
    def _check_dependencies(self):
        """Check required dependencies with enhanced error messages."""
        self._update_progress("Checking dependencies...", 5)
        
        has_pyinstaller, version = DependencyChecker.check_pyinstaller()
        if not has_pyinstaller:
            raise BuildError(
                "PyInstaller is required but not detected.\n"
                "Install with: python -m pip install --upgrade pip && pip install pyinstaller\n"
                "Tip (Windows): ensure the Python Scripts folder is on PATH."
            )
        self._log(f"Using PyInstaller {version}")
        
        has_webview2, version = DependencyChecker.check_webview2()
        if not has_webview2:
            self._log("WebView2 runtime not detected (optional)", "WARNING")
    
    def _check_cancelled(self):
        """Check if build was cancelled."""
        if self.cancel_event.is_set():
            raise BuildCancelled()
    
    def _prepare_resources(self):
        """Prepare HTML resources."""
        self._update_progress("Preparing resources...", 10)
        
        if not self.simulate:
            html_dir = self.temp_dir / self.config.app_dir
            shutil.copytree(self.config.source_path, html_dir)
            
            # Validate entry file
            if not (html_dir / self.config.entry_file).exists():
                raise BuildError(f"Entry file not found: {self.config.entry_file}")
        else:
            # In simulate mode, just create empty structure
            html_dir = self.temp_dir / self.config.app_dir
            html_dir.mkdir(parents=True, exist_ok=True)
            (html_dir / self.config.entry_file).touch()
        
        # Generate icon if needed
        if not self.config.icon_path:
            icon_path = self.temp_dir / "app.ico"
            if IconGenerator.generate_from_text(self.config.app_name, str(icon_path)):
                self.config.icon_path = str(icon_path)
    
    def _generate_launcher(self):
        """Generate launcher script."""
        self._update_progress("Generating launcher...", 20)
        
        if not self.config.app_copyright:
            self.config.app_copyright = f"© {datetime.now().year} {self.config.app_company}"
        
        launcher_code = LAUNCHER_TEMPLATE.format(
            app_name=self.config.app_name,
            app_version=self.config.app_version,
            window_title=self.config.window_title or self.config.app_name,
            window_width=self.config.window_width,
            window_height=self.config.window_height,
            window_min_width=self.config.window_min_width,
            window_min_height=self.config.window_min_height,
            window_resizable=str(self.config.window_resizable).lower(),
            window_fullscreen=str(self.config.window_fullscreen).lower(),
            window_frameless=str(self.config.window_frameless).lower(),
            window_always_on_top=str(self.config.window_always_on_top).lower(),
            window_transparent=str(self.config.window_transparent).lower(),
            enable_dev_tools=str(self.config.enable_dev_tools).lower(),
            enable_context_menu=str(self.config.enable_context_menu).lower(),
            enable_printing=str(self.config.enable_printing).lower(),
            enable_cors=str(self.config.enable_cors).lower(),
            csp_policy=json.dumps(self.config.csp_policy),
            app_dir=json.dumps(self.config.app_dir),
            entry_file=json.dumps(self.config.entry_file)
        )
        
        launcher_path = self.temp_dir / "launcher.py"
        launcher_path.write_text(launcher_code, encoding='utf-8')
        self._log(f"Launcher generated: {launcher_path}")
    
    def _generate_version_file(self):
        """Generate version file for EXE properties."""
        self._update_progress("Generating version info...", 25)
        
        version_content = VERSION_FILE_TEMPLATE.format(
            name=self.config.app_name,
            version=self.config.app_version,
            version_tuple=self.config.get_version_tuple(),
            description=self.config.app_description,
            company=self.config.app_company,
            copyright=self.config.app_copyright
        )
        
        version_path = self.temp_dir / "version.py"
        version_path.write_text(version_content, encoding='utf-8')
        self._log("Version file generated")
        return version_path
    
    def _create_spec(self):
        """Create PyInstaller spec file."""
        self._update_progress("Creating build specification...", 30)
        
        version_file = self.temp_dir / "version.py"
        
        # Create spec with proper Tree import handling
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Import Tree with fallback
Tree = None
try:
    from PyInstaller.building.datastruct import Tree
except ImportError:
    try:
        from PyInstaller.building.build_main import Tree
    except ImportError:
        try:
            from PyInstaller.utils.hooks import Tree
        except ImportError:
            pass

a = Analysis(
    ['launcher.py'],
    pathex=['{self.temp_dir}'],
    binaries=[],
    datas=[],
    hiddenimports=['flask', 'werkzeug', 'webview', 'jinja2'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add HTML assets
if Tree:
    html_tree = Tree('{self.config.app_dir}', prefix='{self.config.app_dir}')
    a.datas += html_tree
else:
    # Fallback: add files manually
    import os, glob
    for filepath in glob.glob('{self.config.app_dir}/**/*', recursive=True):
        if os.path.isfile(filepath):
            dest_path = filepath.replace(os.sep, '/')
            a.datas.append((dest_path, filepath, 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
'''
        
        if self.config.one_file:
            spec_content += f'''
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.config.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip={str(self.config.strip_binaries).lower()},
    upx={str(self.config.use_upx).lower()},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(self.config.console_mode).lower()},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='{version_file}',
    {'icon="' + self.config.icon_path + '",' if self.config.icon_path else ''}
    uac_admin={str(self.config.admin_required).lower()},
)
'''
        else:
            spec_content += f'''
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{self.config.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip={str(self.config.strip_binaries).lower()},
    upx=False,
    console={str(self.config.console_mode).lower()},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='{version_file}',
    {'icon="' + self.config.icon_path + '",' if self.config.icon_path else ''}
    uac_admin={str(self.config.admin_required).lower()},
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip={str(self.config.strip_binaries).lower()},
    upx={str(self.config.use_upx).lower()},
    upx_exclude=[],
    name='{self.config.app_name}',
)
'''
        
        spec_path = self.temp_dir / f"{self.config.app_name}.spec"
        spec_path.write_text(spec_content)
        self._log(f"Spec file created: {spec_path}")
    
    def _run_pyinstaller(self):
        """Run PyInstaller build process."""
        self._update_progress("Building executable...", 40)
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--noconfirm',
            '--clean',
            '--distpath', str(Path(self.config.output_dir).absolute()),
            '--workpath', str(self.temp_dir / 'build'),
            str(self.temp_dir / f"{self.config.app_name}.spec")
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(self.temp_dir)
        )
        
        # Progress tracking
        progress_keywords = {
            "Building": 50,
            "Collecting": 55,
            "Processing": 60,
            "Copying": 65,
            "Appending": 70,
            "Compressing": 75
        }
        
        for line in self.process.stdout:
            if self.cancel_event.is_set():
                self.process.terminate()
                raise BuildCancelled()
            
            line = line.strip()
            if line:
                self._log(line, "DEBUG")
                
                for keyword, progress in progress_keywords.items():
                    if keyword.lower() in line.lower():
                        self._update_progress(f"{keyword}...", progress)
                        break
        
        self.process.wait()
        
        if self.process.returncode != 0:
            raise BuildError("PyInstaller build failed. Check console for details.")
        
        # Determine output path
        if self.config.one_file:
            self.output_path = Path(self.config.output_dir) / f"{self.config.app_name}.exe"
        else:
            self.output_path = Path(self.config.output_dir) / self.config.app_name / f"{self.config.app_name}.exe"
        
        if not self.output_path.exists():
            raise BuildError(f"Output not found: {self.output_path}")
        
        file_size = self.output_path.stat().st_size / (1024 * 1024)
        self._log(f"Executable created: {self.output_path} ({file_size:.2f} MB)")
    
    def _sign_executable(self):
        """Sign executable with certificate (RFC3161)."""
        self._update_progress("Signing executable...", 85)
        
        if not self.config.certificate_path:
            self._log("No certificate configured", "WARNING")
            return
        
        try:
            # Use modern RFC3161 timestamping
            cmd = [
                'signtool', 'sign',
                '/fd', 'sha256',
                '/f', self.config.certificate_path,
                '/p', self.config.certificate_password,
                '/tr', self.config.timestamp_server,
                '/td', 'sha256',
                '/v',
                str(self.output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self._log("Executable signed successfully")
            else:
                self._log(f"Signing failed: {result.stderr}", "WARNING")
                
        except subprocess.TimeoutExpired:
            self._log("Signing timed out", "WARNING")
        except FileNotFoundError:
            self._log("signtool not found. Install Windows SDK for code signing.", "WARNING")
    
    def _create_installer(self):
        """Create NSIS installer with enhanced error messages."""
        self._update_progress("Creating installer...", 90)
        
        # Check NSIS availability
        try:
            result = subprocess.run(['makensis', '/VERSION'], capture_output=True, timeout=5)
            if result.returncode != 0:
                self._log(
                    "NSIS (makensis) not found. Install from https://nsis.sourceforge.io/ "
                    "and ensure 'makensis' is on PATH.",
                    "WARNING"
                )
                return
        except Exception as e:
            self._log(
                "NSIS (makensis) not found. Install from https://nsis.sourceforge.io/ "
                "and ensure 'makensis' is on PATH.",
                "WARNING"
            )
            return
        
        # Generate NSIS script with proper admin level
        admin_level = "admin" if self.config.admin_required else "user"
        dist_path = Path(self.config.output_dir).absolute()
        
        nsis_script = f'''
!define APP_NAME "{self.config.app_name}"
!define APP_VERSION "{self.config.app_version}"
!define APP_GUID "{self.config.guid}"
!define DIST_PATH "{dist_path}"
!define ONEFILE "{str(self.config.one_file).lower()}"

Name "${{APP_NAME}}"
OutFile "${{APP_NAME}}_Setup.exe"
InstallDir "$PROGRAMFILES\\${{APP_NAME}}"

RequestExecutionLevel {admin_level}

!include "MUI2.nsh"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Main"
    SetOutPath "$INSTDIR"
    
    ; Copy files based on build type
    !if "${{ONEFILE}}" == "true"
        File "${{DIST_PATH}}\\${{APP_NAME}}.exe"
    !else
        File /r "${{DIST_PATH}}\\${{APP_NAME}}\\*.*"
    !endif
    '''
        
        # Add WebView2 installer if configured
        if self.config.include_webview2:
            nsis_script += f'''
    
    ; Check and install WebView2 if needed
    ReadRegStr $0 HKLM "SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\{WEBVIEW2_GUID}" "pv"
    StrCmp $0 "" InstallWebView2 SkipWebView2
    
    InstallWebView2:
        DetailPrint "Installing WebView2 Runtime..."
        ; Download or include WebView2 bootstrapper
        ; ExecWait '"$TEMP\\MicrosoftEdgeWebview2Setup.exe" /silent /install'
    
    SkipWebView2:
    '''
        
        nsis_script += f'''
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_GUID}}" \\
                     "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_GUID}}" \\
                     "DisplayVersion" "${{APP_VERSION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_GUID}}" \\
                     "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_GUID}}" \\
                     "InstallLocation" "$INSTDIR"
    
    ; Shortcuts
    CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_NAME}}.exe"
SectionEnd

Section "Uninstall"
    ; Remove installed files only
    !if "${{ONEFILE}}" == "true"
        Delete "$INSTDIR\\${{APP_NAME}}.exe"
    !else
        RMDir /r "$INSTDIR"
    !endif
    
    Delete "$INSTDIR\\Uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$DESKTOP\\${{APP_NAME}}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_GUID}}"
SectionEnd
'''
        
        # Save and compile NSIS script
        nsis_path = self.temp_dir / "installer.nsi"
        nsis_path.write_text(nsis_script)
        
        try:
            result = subprocess.run(
                ['makensis', str(nsis_path)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.temp_dir)
            )
            
            if result.returncode == 0:
                installer_path = self.temp_dir / f"{self.config.app_name}_Setup.exe"
                if installer_path.exists():
                    final_installer = Path(self.config.output_dir) / installer_path.name
                    shutil.move(str(installer_path), str(final_installer))
                    self._log(f"Installer created: {final_installer}")
            else:
                self._log("Installer creation failed", "WARNING")
                
        except subprocess.TimeoutExpired:
            self._log("Installer creation timed out", "WARNING")
    
    def _test_executable(self):
        """Test the generated executable."""
        self._update_progress("Testing executable...", 95)
        
        try:
            # Test with --version flag
            result = subprocess.run(
                [str(self.output_path), '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if self.config.app_version in result.stdout:
                self._log("Executable version test passed")
            else:
                self._log("Version test inconclusive", "DEBUG")
            
            # Test with --help flag
            result = subprocess.run(
                [str(self.output_path), '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if self.config.app_name in result.stdout:
                self._log("Executable help test passed")
                
        except subprocess.TimeoutExpired:
            self._log("Executable test timed out", "WARNING")
        except Exception as e:
            self._log(f"Test error: {e}", "WARNING")
    
    def _cleanup(self):
        """Clean up temporary files."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self._log("Temporary files cleaned")
        except:
            pass
    
    def _update_status(self, status: BuildStatus):
        """Update build status."""
        self.status = status
        if 'status' in self.callbacks:
            self.callbacks['status'](status)
    
    def _update_progress(self, message: str, percentage: int):
        """Update progress."""
        self.progress = percentage
        if 'progress' in self.callbacks:
            self.callbacks['progress'](message, percentage)
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message."""
        getattr(logger, level.lower())(message)
        if 'log' in self.callbacks:
            self.callbacks['log'](message, level)

class BuildError(Exception):
    """Build error."""
    pass

class BuildCancelled(Exception):
    """Build cancelled."""
    pass

# =============================================================================
# GUI APPLICATION
# =============================================================================

class HTML2EXEApp:
    """Main GUI application."""
    
    def __init__(self):
        # Setup window - prefer CTK when available
        if CTK_AVAILABLE:
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        
        self.root.title(f"{APP_NAME} v{__version__}")
        self.root.geometry("1300x800")
        self.root.minsize(1000, 600)
        
        # Initialize
        self.config = BuildConfig()
        self.build_engine = None
        self.build_thread = None
        
        # Create UI
        self.setup_ui()
        self.check_dependencies()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """Setup user interface."""
        # Main container
        if CTK_AVAILABLE:
            container = ctk.CTkFrame(self.root)
        else:
            container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        if CTK_AVAILABLE:
            self.tabs = ctk.CTkTabview(container)
            self.tabs.pack(fill='both', expand=True)
            
            self.tabs.add("Configuration")
            self.tabs.add("Build")
            self.tabs.add("Console")
            
            self.create_config_tab(self.tabs.tab("Configuration"))
            self.create_build_tab(self.tabs.tab("Build"))
            self.create_console_tab(self.tabs.tab("Console"))
        else:
            self.tabs = ttk.Notebook(container)
            self.tabs.pack(fill='both', expand=True)
            
            config_tab = ttk.Frame(self.tabs)
            build_tab = ttk.Frame(self.tabs)
            console_tab = ttk.Frame(self.tabs)
            
            self.tabs.add(config_tab, text="Configuration")
            self.tabs.add(build_tab, text="Build")
            self.tabs.add(console_tab, text="Console")
            
            self.create_config_tab(config_tab)
            self.create_build_tab(build_tab)
            self.create_console_tab(console_tab)
    
    def create_config_tab(self, parent):
        """Create configuration tab."""
        if CTK_AVAILABLE:
            # CTK version
            scroll = ctk.CTkScrollableFrame(parent)
            scroll.pack(fill='both', expand=True)
            
            # App info
            ctk.CTkLabel(scroll, text="Application Info", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=10)
            
            frame = ctk.CTkFrame(scroll)
            frame.pack(fill='x', pady=5)
            ctk.CTkLabel(frame, text="Name:", width=120).pack(side='left', padx=10)
            self.name_entry = ctk.CTkEntry(frame, width=300)
            self.name_entry.pack(side='left')
            self.name_entry.insert(0, "MyApp")
            
            frame = ctk.CTkFrame(scroll)
            frame.pack(fill='x', pady=5)
            ctk.CTkLabel(frame, text="Version:", width=120).pack(side='left', padx=10)
            self.version_entry = ctk.CTkEntry(frame, width=300)
            self.version_entry.pack(side='left')
            self.version_entry.insert(0, "1.0.0")
            
            # Source
            ctk.CTkLabel(scroll, text="Source Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=10)
            
            frame = ctk.CTkFrame(scroll)
            frame.pack(fill='x', pady=5)
            ctk.CTkLabel(frame, text="HTML Folder:", width=120).pack(side='left', padx=10)
            self.source_var = tk.StringVar()
            self.source_entry = ctk.CTkEntry(frame, textvariable=self.source_var, width=250)
            self.source_entry.pack(side='left')
            ctk.CTkButton(frame, text="Browse", command=self.browse_source, width=80).pack(side='left', padx=5)
            
            frame = ctk.CTkFrame(scroll)
            frame.pack(fill='x', pady=5)
            ctk.CTkLabel(frame, text="Entry File:", width=120).pack(side='left', padx=10)
            self.entry_var = tk.StringVar(value="index.html")
            ctk.CTkEntry(frame, textvariable=self.entry_var, width=300).pack(side='left')
        else:
            # Standard tkinter version
            canvas = tk.Canvas(parent)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scroll = ttk.Frame(canvas)
            
            scroll.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scroll, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # App info
            info_frame = ttk.LabelFrame(scroll, text="Application Information", padding=10)
            info_frame.pack(fill='x', padx=10, pady=10)
            
            ttk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky='w', pady=2)
            self.name_entry = ttk.Entry(info_frame, width=40)
            self.name_entry.grid(row=0, column=1, pady=2, padx=5)
            self.name_entry.insert(0, "MyApp")
            
            ttk.Label(info_frame, text="Version:").grid(row=1, column=0, sticky='w', pady=2)
            self.version_entry = ttk.Entry(info_frame, width=40)
            self.version_entry.grid(row=1, column=1, pady=2, padx=5)
            self.version_entry.insert(0, "1.0.0")
            
            # Source
            source_frame = ttk.LabelFrame(scroll, text="Source Configuration", padding=10)
            source_frame.pack(fill='x', padx=10, pady=10)
            
            ttk.Label(source_frame, text="HTML Folder:").grid(row=0, column=0, sticky='w', pady=2)
            self.source_var = tk.StringVar()
            self.source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=40)
            self.source_entry.grid(row=0, column=1, pady=2, padx=5)
            ttk.Button(source_frame, text="Browse", command=self.browse_source).grid(row=0, column=2, padx=5)
            
            ttk.Label(source_frame, text="Entry File:").grid(row=1, column=0, sticky='w', pady=2)
            self.entry_var = tk.StringVar(value="index.html")
            ttk.Entry(source_frame, textvariable=self.entry_var, width=40).grid(row=1, column=1, pady=2, padx=5)
            
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
    
    def create_build_tab(self, parent):
        """Create build tab."""
        if CTK_AVAILABLE:
            frame = ctk.CTkFrame(parent)
            frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Options
            ctk.CTkLabel(frame, text="Build Options", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=10)
            
            self.onefile_var = tk.BooleanVar(value=True)
            ctk.CTkCheckBox(frame, text="Single File Executable", variable=self.onefile_var).pack(anchor='w', pady=2)
            
            self.console_var = tk.BooleanVar(value=False)
            ctk.CTkCheckBox(frame, text="Console Window", variable=self.console_var).pack(anchor='w', pady=2)
            
            self.admin_var = tk.BooleanVar(value=False)
            ctk.CTkCheckBox(frame, text="Require Admin Rights", variable=self.admin_var).pack(anchor='w', pady=2)
            
            # Buttons
            button_frame = ctk.CTkFrame(frame)
            button_frame.pack(pady=20)
            
            self.build_button = ctk.CTkButton(
                button_frame,
                text="BUILD",
                command=self.start_build,
                width=150,
                height=40,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            self.build_button.pack(side='left', padx=10)
            
            self.cancel_button = ctk.CTkButton(
                button_frame,
                text="CANCEL",
                command=self.cancel_build,
                width=150,
                height=40,
                state='disabled'
            )
            self.cancel_button.pack(side='left', padx=10)
            
            # Progress
            self.progress_bar = ctk.CTkProgressBar(frame, width=500)
            self.progress_bar.pack(pady=10)
            self.progress_bar.set(0)
            
            self.status_label = ctk.CTkLabel(frame, text="Ready")
            self.status_label.pack()
        else:
            frame = ttk.Frame(parent)
            frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Options
            options_frame = ttk.LabelFrame(frame, text="Build Options", padding=10)
            options_frame.pack(fill='x', pady=10)
            
            self.onefile_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text="Single File Executable", variable=self.onefile_var).pack(anchor='w', pady=2)
            
            self.console_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(options_frame, text="Console Window", variable=self.console_var).pack(anchor='w', pady=2)
            
            self.admin_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(options_frame, text="Require Admin Rights", variable=self.admin_var).pack(anchor='w', pady=2)
            
            # Buttons
            button_frame = ttk.Frame(frame)
            button_frame.pack(pady=20)
            
            self.build_button = ttk.Button(button_frame, text="BUILD", command=self.start_build)
            self.build_button.pack(side='left', padx=10)
            
            self.cancel_button = ttk.Button(button_frame, text="CANCEL", command=self.cancel_build, state='disabled')
            self.cancel_button.pack(side='left', padx=10)
            
            # Progress
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, length=500, maximum=100)
            self.progress_bar.pack(pady=10)
            
            self.status_label = ttk.Label(frame, text="Ready")
            self.status_label.pack()
    
    def create_console_tab(self, parent):
        """Create console tab."""
        self.console_text = scrolledtext.ScrolledText(
            parent,
            wrap='word',
            height=30,
            bg='black',
            fg='white',
            font=('Consolas', 10)
        )
        self.console_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        if CTK_AVAILABLE:
            button_frame = ctk.CTkFrame(parent)
            button_frame.pack(fill='x', padx=10, pady=5)
            ctk.CTkButton(button_frame, text="Clear", command=self.clear_console, width=100).pack(side='left', padx=5)
        else:
            button_frame = ttk.Frame(parent)
            button_frame.pack(fill='x', padx=10, pady=5)
            ttk.Button(button_frame, text="Clear", command=self.clear_console).pack(side='left', padx=5)
    
    def check_dependencies(self):
        """Check system dependencies."""
        self.log("Checking dependencies...")
        
        # Python
        if DependencyChecker.check_python():
            self.log(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
        else:
            self.log(f"✗ Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required", "ERROR")
        
        # PyInstaller
        has_pyinstaller, version = DependencyChecker.check_pyinstaller()
        if has_pyinstaller:
            self.log(f"✓ PyInstaller {version}")
        else:
            self.log("✗ PyInstaller not installed", "ERROR")
        
        # WebView2
        has_webview2, version = DependencyChecker.check_webview2()
        if has_webview2:
            self.log(f"✓ WebView2 Runtime {version}")
        else:
            self.log("✗ WebView2 Runtime not installed (optional)", "WARNING")
    
    def browse_source(self):
        """Browse for source folder."""
        folder = filedialog.askdirectory(title="Select HTML Source Folder")
        if folder:
            self.source_var.set(folder)
    
    def start_build(self):
        """Start build process."""
        # Update config
        self.config.app_name = self.name_entry.get().strip().replace(" ", "_")
        self.config.app_version = self.version_entry.get().strip()
        self.config.source_path = self.source_var.get().strip()
        self.config.entry_file = self.entry_var.get().strip()
        self.config.one_file = self.onefile_var.get()
        self.config.console_mode = self.console_var.get()
        self.config.admin_required = self.admin_var.get()
        
        # Validate
        valid, errors = self.config.validate()
        if not valid:
            messagebox.showerror("Configuration Error", "\n".join(errors))
            return
        
        # Start build
        self.build_button.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        self.build_thread = threading.Thread(target=self.run_build, daemon=True)
        self.build_thread.start()
    
    def cancel_build(self):
        """Cancel build process."""
        if self.build_engine:
            self.build_engine.cancel()
            self.cancel_button.configure(state='disabled')
    
    def run_build(self):
        """Run build in thread."""
        try:
            self.build_engine = BuildEngine(self.config)
            self.build_engine.set_callback('progress', self.update_progress)
            self.build_engine.set_callback('log', self.log)
            self.build_engine.set_callback('status', self.update_status)
            
            success, result = self.build_engine.build()
            
            if success:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Build Complete",
                    f"Application built successfully!\n\nOutput: {result}"
                ))
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "Build Failed",
                    f"Build failed:\n{result}"
                ))
            
        finally:
            self.root.after(0, lambda: self.build_button.configure(state='normal'))
            self.root.after(0, lambda: self.cancel_button.configure(state='disabled'))
            self.root.after(0, lambda: self.update_progress("Ready", 0))
    
    def update_progress(self, message: str, percentage: int):
        """Update progress display."""
        def update():
            if CTK_AVAILABLE:
                self.progress_bar.set(percentage / 100)
            else:
                self.progress_var.set(percentage)
            self.status_label.configure(text=message)
        
        self.root.after(0, update)
    
    def update_status(self, status: BuildStatus):
        """Update status display."""
        self.root.after(0, lambda: self.status_label.configure(text=f"Status: {status.value}"))
    
    def log(self, message: str, level: str = "INFO"):
        """Log to console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "DEBUG": "gray",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red"
        }
        
        def write():
            self.console_text.insert('end', f"[{timestamp}] {message}\n")
            
            if level in colors:
                start = self.console_text.index('end-2l')
                end = self.console_text.index('end-1c')
                self.console_text.tag_add(level, start, end)
                self.console_text.tag_config(level, foreground=colors[level])
            
            self.console_text.see('end')
        
        self.root.after(0, write)
    
    def clear_console(self):
        """Clear console."""
        self.console_text.delete('1.0', 'end')
    
    def on_close(self):
        """Handle window close."""
        if self.build_thread and self.build_thread.is_alive():
            if messagebox.askyesno("Confirm", "Build in progress. Cancel and exit?"):
                if self.build_engine:
                    self.build_engine.cancel()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run application."""
        self.root.mainloop()

# =============================================================================
# MAIN ENTRY POINT WITH CLI SUPPORT
# =============================================================================

def main():
    """Main entry point with CLI and GUI support."""
    print(f"\n{APP_NAME} v{__version__}")
    print("=" * 60)
    print("Bulletproof Production HTML to EXE Converter\n")
    
    parser = argparse.ArgumentParser(prog="html2exe", add_help=True)
    parser.add_argument("--no-gui", action="store_true", help="Run headless (CLI mode).")
    parser.add_argument("--config", type=str, help="Path to JSON file with BuildConfig fields.")
    parser.add_argument("--set", action="append", default=[], metavar="key=value",
                        help="Override a BuildConfig field (repeatable).")
    parser.add_argument("--simulate", action="store_true",
                        help="Dry-run: validate and generate artifacts but skip PyInstaller.")
    parser.add_argument("--save-config", type=str, help="Save current config to JSON file.")
    args, unknown = parser.parse_known_args()
    
    try:
        if args.no_gui:
            # Headless/CI mode
            print("Running in headless mode...")
            
            # Load or create config
            if args.config:
                print(f"Loading config from: {args.config}")
                cfg = load_config_from_json(args.config)
            else:
                print("Using default configuration")
                cfg = BuildConfig()
            
            # Apply overrides
            if args.set:
                print("Applying overrides...")
                cfg = apply_overrides(cfg, args.set)
            
            # Save config if requested
            if args.save_config:
                save_config_to_json(cfg, args.save_config)
                print(f"Configuration saved to: {args.save_config}")
            
            # Validate configuration
            ok, errs = cfg.validate()
            if not ok:
                print("\nConfiguration errors:")
                for e in errs:
                    print(f"  - {e}")
                sys.exit(1)
            
            # Run build
            print("\nStarting build...")
            engine = BuildEngine(cfg, simulate=args.simulate)
            
            # Simple console callbacks
            engine.set_callback("progress", lambda msg, p: print(f"[{p:3d}%] {msg}"))
            engine.set_callback("log", lambda m, lvl: print(f"{lvl}: {m}"))
            engine.set_callback("status", lambda s: print(f"STATUS: {s.value}"))
            
            success, result = engine.build()
            
            if not success:
                print("\n✗ Build failed:")
                print(result)
                sys.exit(1)
            
            print("\n✓ Build complete:")
            print(result)
            sys.exit(0)
        
        # GUI mode (default)
        if not TK_AVAILABLE:
            print("ERROR: tkinter not available. Use --no-gui for headless mode.")
            sys.exit(1)
        
        app = HTML2EXEApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"\nError: {e}")
        if not args.no_gui:
            try:
                input("\nPress Enter to exit...")
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()
