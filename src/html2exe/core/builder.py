import os
import sys
import json
import shutil
import subprocess
import time
from typing import Dict, Any, List, Callable
from datetime import datetime

from .config import AppConfig
from .icon_generator import IconGenerator

class BuildEngine:
    """Advanced PyInstaller build engine with optimization."""

    def __init__(self, config: AppConfig, progress_callback: Callable = None):
        self.config = config
        self.progress_callback = progress_callback or (lambda x: None)
        self.build_dir = os.path.join(config.build.output_dir, "build")
        self.dist_dir = os.path.join(config.build.output_dir, "dist")

    def prepare_build(self) -> str:
        """Prepare build environment and assets."""
        self.progress_callback("Preparing build environment...")

        # Create build directories
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)

        # Copy source files if folder mode
        if self.config.build.source_type == "folder":
            source_build_dir = os.path.join(self.build_dir, "html_assets")
            if os.path.exists(source_build_dir):
                shutil.rmtree(source_build_dir)
            shutil.copytree(self.config.build.source_path, source_build_dir)

        # Generate application icon
        icon_path = self.config.build.icon_path
        if not icon_path or not os.path.exists(icon_path):
            icon_path = os.path.join(self.build_dir, "app_icon.ico")
            IconGenerator.generate_icon(self.config.metadata.name[:2].upper(), icon_path)
            self.config.build.icon_path = icon_path

        # Create main application script
        main_script = self._create_main_script()
        main_script_path = os.path.join(self.build_dir, "main.py")
        with open(main_script_path, 'w', encoding='utf-8') as f:
            f.write(main_script)

        return main_script_path

    def _create_main_script(self) -> str:
        """Create the main application script."""
        script_template = '''
import sys
import os
import webview
import threading
import time
from flask import Flask, send_from_directory, jsonify

# Configuration embedded at build time
CONFIG = %(config_json)s

def create_app():
    app = Flask(__name__)

    # Block external URLs if configured
    @app.before_request
    def block_external_urls():
        if CONFIG["security"].get("block_external_urls", False):
            from flask import request
            if request.endpoint == 'serve_static':
                # Allow static files
                return None
            # Block any external requests
            if request.headers.get('Referer') and not request.headers.get('Referer').startswith('http://127.0.0.1'):
                return "External requests blocked", 403

    @app.route('/')
    def index():
        if CONFIG["build"]["source_type"] == "url":
            # Set CSP headers for URL mode based on security settings
            from flask import Response
            from urllib.parse import urlparse

            # Determine CSP policy based on block_external_urls setting
            # Note: External subresources (images, scripts, styles) of the framed site
            # are governed by the framed site's own CSP, not this Flask server's CSP
            if CONFIG["security"].get("block_external_urls", False):
                # Restrict to target origin only
                parsed_url = urlparse(CONFIG["build"]["source_path"])
                target_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
                csp_policy = f"frame-src {target_origin}; child-src {target_origin}; default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: {target_origin};"
            else:
                # Permissive CSP for external iframes
                csp_policy = "frame-src *; child-src *; default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: *;"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{CONFIG["metadata"]["name"]}</title>
            </head>
            <body style="margin:0;">
                <iframe src="{CONFIG["build"]["source_path"]}"
                        style="width:100%%;height:100vh;border:none;"
                        allow="fullscreen; microphone; camera; geolocation">
                </iframe>
            </body>
            </html>
            """
            response = Response(html_content)
            response.headers['Content-Security-Policy'] = csp_policy
            return response
        else:
            try:
                resource_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                html_dir = os.path.join(resource_path, 'html_assets')
                with open(os.path.join(html_dir, 'index.html'), 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return f"<h1>Welcome to {CONFIG['metadata']['name']}</h1>"

    @app.route('/<path:filename>')
    def serve_static(filename):
        resource_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        html_dir = os.path.join(resource_path, 'html_assets')
        return send_from_directory(html_dir, filename)

    return app

def _pick_port(preferred=5000, tries=10):
    """Pick an available port, starting with preferred port."""
    import socket
    import random

    for i in range(tries):
        port = preferred if i == 0 else random.randint(49152, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 5000  # fallback

def _bind_single_instance(port=53691):
    """Bind to a port to ensure single instance."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        s.listen(1)
        return s  # keep handle alive
    except OSError:
        sys.exit(0)  # another instance is running

def run_flask_app():
    # Single instance check
    if CONFIG["build"].get("single_instance", True):
        _si_guard = _bind_single_instance()

    app = create_app()

    # Pick an available port
    flask_port = _pick_port()

    # Start Flask server
    def run_server():
        app.run(host='127.0.0.1', port=flask_port, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server more time to start

    # WebView2 runtime check (Windows)
    if sys.platform == "win32":
        import shutil
        if not shutil.which("msedgewebview2.exe") and not os.environ.get("WEBVIEW2_RUNTIME"):
            import webbrowser
            print("WebView2 runtime not found. Opening download page...")
            webbrowser.open("https://developer.microsoft.com/microsoft-edge/webview2/#download-section")
            time.sleep(3)

    # Create webview window with the same port
    window = webview.create_window(
        title=CONFIG["metadata"]["name"],
        url=f"http://127.0.0.1:{flask_port}",
        width=CONFIG["window"]["width"],
        height=CONFIG["window"]["height"],
        resizable=CONFIG["window"]["resizable"],
        fullscreen=CONFIG["window"]["fullscreen"]
    )

    # Honor config flags
    debug_mode = CONFIG["build"].get("debug", False) and CONFIG["security"].get("allow_devtools", False)
    webview.start(debug=debug_mode)

if __name__ == '__main__':
    run_flask_app()
'''
        return script_template % {
            "config_json": json.dumps(self.config.model_dump(), indent=2)
        }

    def build(self, extra_hidden_imports: List[str] = None) -> Dict[str, Any]:
        """Execute the build process."""
        start_time = time.time()

        # Validate configuration before building
        self._validate_build_config()

        # Prepare build
        main_script_path = self.prepare_build()

        # Build PyInstaller command
        cmd = self._build_pyinstaller_command(main_script_path, extra_hidden_imports=extra_hidden_imports)

        self.progress_callback("Building executable...")

        try:
            # Execute build with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)  # 20 minutes
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Build timed out after 20 minutes",
                "build_time": f"{time.time() - start_time:.2f}s"
            }

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown build error"
            raise Exception(f"Build failed: {error_msg}")

        # Post-process
        self._post_process()

        build_time = time.time() - start_time

        # Generate build report
        exe_path = self._get_exe_path()
        if not os.path.exists(exe_path):
            raise Exception("Executable was not created successfully")

        report = {
            "success": True,
            "exe_path": exe_path,
            "build_time": f"{build_time:.2f}s",
            "exe_size": f"{os.path.getsize(exe_path) / (1024*1024):.2f} MB",
            "config": self.config.model_dump(),
            "timestamp": datetime.now().isoformat(),
            "pyinstaller_stdout": result.stdout,
            "pyinstaller_stderr": result.stderr,
            "port_used": "dynamic",  # Will be set at runtime
            "build_strategy": "standard"
        }

        # Save build report
        report_path = os.path.join(self.dist_dir, "build_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Also save PyInstaller logs separately for debugging
        with open(os.path.join(self.dist_dir, "pyinstaller_stdout.txt"), 'w') as f:
            f.write(result.stdout)
        with open(os.path.join(self.dist_dir, "pyinstaller_stderr.txt"), 'w') as f:
            f.write(result.stderr)

        return report

    def _validate_build_config(self):
        """Validate build configuration before starting."""
        if not self.config.build.source_path:
            raise Exception("Source path is required")

        if self.config.build.source_type == "folder":
            if not os.path.exists(self.config.build.source_path):
                raise Exception(f"Source folder does not exist: {self.config.build.source_path}")
        elif self.config.build.source_type == "url":
            # Validate URL reachability
            try:
                import urllib.request
                import urllib.error
                req = urllib.request.Request(self.config.build.source_path, method='HEAD')
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status >= 400:
                        raise Exception(f"URL returned error {response.status}: {self.config.build.source_path}")
            except urllib.error.URLError as e:
                raise Exception(f"URL is not reachable: {self.config.build.source_path} - {e}")
            except Exception as e:
                raise Exception(f"Failed to validate URL: {self.config.build.source_path} - {e}")

        if not self.config.metadata.name.strip():
            raise Exception("Application name is required")

        # Check for problematic characters in name
        invalid_chars = '<>:"/\\|?*'
        if any(char in self.config.metadata.name for char in invalid_chars):
            raise Exception(f"Application name contains invalid characters: {invalid_chars}")

        # Check available disk space
        try:
            import shutil
            free_space = shutil.disk_usage(self.config.build.output_dir).free
            if free_space < 500 * 1024 * 1024:  # 500MB
                raise Exception("Insufficient disk space (need at least 500MB)")
        except:
            pass  # Skip disk space check if it fails

    def _build_pyinstaller_command(self, main_script_path: str, extra_hidden_imports: List[str] = None) -> List[str]:
        """Build PyInstaller command with all options."""
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            f"--name={self.config.metadata.name}",
            f"--distpath={self.dist_dir}",
            f"--workpath={os.path.join(self.build_dir, 'work')}",
            f"--specpath={self.build_dir}"
        ]

        if self.config.build.onefile:
            cmd.append("--onefile")

        if not self.config.build.console:
            cmd.append("--windowed")

        if self.config.build.icon_path and os.path.exists(self.config.build.icon_path):
            cmd.append(f"--icon={self.config.build.icon_path}")

        # Add data files for folder mode
        if self.config.build.source_type == "folder":
            html_assets = os.path.abspath(os.path.join(self.build_dir, "html_assets"))
            if os.path.exists(html_assets):
                # Use platform-appropriate separator
                separator = ";" if sys.platform == "win32" else ":"
                cmd.append(f"--add-data={html_assets}{separator}html_assets")

        # Hidden imports
        hidden_imports = [
            "flask", "webview", "threading", "json", "os", "sys", "time",
            "importlib.metadata", "importlib.util", "pathlib", "pkgutil",
            "platform", "socket", "urllib.parse", "urllib.request", "urllib.error"
        ]
        if extra_hidden_imports:
            hidden_imports.extend(extra_hidden_imports)

        for imp in hidden_imports:
            cmd.append(f"--hidden-import={imp}")

        # Version file for Windows properties
        if sys.platform == "win32" and self.config.metadata.company:
            version_info = f"""
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{self.config.metadata.company}'),
         StringStruct(u'FileDescription', u'{self.config.metadata.description}'),
         StringStruct(u'FileVersion', u'{self.config.metadata.version}'),
         StringStruct(u'InternalName', u'{self.config.metadata.name}'),
         StringStruct(u'LegalCopyright', u'Copyright (C) {self.config.metadata.author}'),
         StringStruct(u'OriginalFilename', u'{self.config.metadata.name}.exe'),
         StringStruct(u'ProductName', u'{self.config.metadata.name}'),
         StringStruct(u'ProductVersion', u'{self.config.metadata.version}')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
            version_file = os.path.join(self.build_dir, "version_info.txt")
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(version_info)
            cmd.append(f"--version-file={version_file}")

        # UPX compression
        if self.config.build.upx_compress:
            cmd.append("--upx-dir=upx")

        # Debug options
        if self.config.build.debug:
            cmd.append("--debug=all")
        else:
            cmd.append("--strip")

        cmd.append(main_script_path)
        return cmd

    def _get_exe_path(self) -> str:
        """Get the path to the built executable."""
        exe_name = self.config.metadata.name
        if sys.platform == "win32":
            exe_name += ".exe"

        if self.config.build.onefile:
            return os.path.join(self.dist_dir, exe_name)
        else:
            return os.path.join(self.dist_dir, self.config.metadata.name, exe_name)

    def _post_process(self):
        """Post-process the built executable."""
        self.progress_callback("Post-processing...")

        exe_path = self._get_exe_path()
        if os.path.exists(exe_path):
            # Set file metadata (this would require additional tools in production)
            pass
