import os
import sys
import json
import shutil
import time
import subprocess
from datetime import datetime
from typing import Any, Callable, Dict, List

from flask import Flask, send_from_directory, jsonify
from rich.console import Console

from .config import AppConfig
from .icon_generator import IconGenerator
from .preflight import run_preflight_checks

console = Console()


def _generate_default_html(config: AppConfig) -> str:
    """Generate default HTML template when no index.html is found."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.metadata.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; height: 100vh; display: flex; align-items: center; justify-content: center;
        }}
        .container {{ text-align: center; max-width: 600px; padding: 2rem; }}
        h1 {{ font-size: 3rem; margin-bottom: 1rem; }}
        p {{ font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }}
        .info {{ background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 10px; backdrop-filter: blur(10px); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 {config.metadata.name}</h1>
        <p>{config.metadata.description}</p>
        <div class="info">
            <p><strong>Version:</strong> {config.metadata.version}</p>
            <p><strong>Company:</strong> {config.metadata.company}</p>
            <p><strong>Built with HTML2EXE Pro Premium</strong></p>
        </div>
    </div>
</body>
</html>
"""


def _create_flask_app(config: AppConfig) -> Flask:
    """Create enhanced Flask application with premium features."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        if config.security.csp_enabled:
            response.headers.add('Content-Security-Policy', config.security.csp_policy)
        return response

    source_path = config.build.source_path

    @app.route('/')
    def index():
        """Serve the main HTML file."""
        if config.build.source_type == "url":
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{config.metadata.name}</title>
                <style>
                    body {{ margin: 0; padding: 0; height: 100vh; }}
                    iframe {{ width: 100%; height: 100%; border: none; }}
                </style>
            </head>
            <body>
                <iframe src="{source_path}" sandbox="allow-scripts allow-same-origin allow-forms allow-popups"></iframe>
            </body>
            </html>
            """
        else:
            index_file = os.path.join(source_path, 'index.html')
            if os.path.exists(index_file):
                return send_from_directory(source_path, 'index.html')
            else:
                return _generate_default_html(config), 200

    @app.route('/<path:filename>')
    def serve_file(filename):
        """Serve static files with caching."""
        try:
            response = send_from_directory(source_path, filename)
            if filename.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                response.cache_control.max_age = 3600
            return response
        except FileNotFoundError:
            return "File not found", 404

    @app.route('/api/health')
    def health():
        """Enhanced health check endpoint."""
        return jsonify({
            "status": "ok",
            "app": config.metadata.name,
            "version": config.metadata.version,
            "offline_mode": config.build.offline_mode,
            "timestamp": datetime.now().isoformat()
        })

    @app.route('/api/reload')
    def reload():
        """Trigger reload endpoint."""
        return jsonify({"reload": True})

    return app


class BuildEngine:
    """Advanced PyInstaller build engine with optimization."""

    def __init__(self, config: AppConfig, progress_callback: Callable = None):
        self.config = config
        self.progress_callback = progress_callback or (lambda x: None)
        self.build_dir = os.path.join(config.build.output_dir, "build")
        self.dist_dir = config.build.output_dir

    def prepare_build(self) -> str:
        """Prepare build environment and assets."""
        self.progress_callback("Preparing build environment...")

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
        """Create the main application script."""
        script_template = '''
import sys
import os
import webview
import threading
import time
import socket
from flask import Flask, send_from_directory, jsonify

# Configuration embedded at build time
CONFIG = {config_json}

def get_random_port():
    """Get a random available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        if CONFIG["build"]["source_type"] == "url":
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>{{CONFIG["metadata"]["name"]}}</title></head>
            <body style="margin:0;">
                <iframe src="{{CONFIG["build"]["source_path"]}}"
                        style="width:100%;height:100vh;border:none;">
                </iframe>
            </body>
            </html>
            """
        else:
            try:
                resource_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                html_dir = os.path.join(resource_path, 'html_assets')
                with open(os.path.join(html_dir, 'index.html'), 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return "<h1>Welcome to {{}}</h1>".format(CONFIG["metadata"]["name"])

    @app.route('/<path:filename>')
    def serve_static(filename):
        resource_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        html_dir = os.path.join(resource_path, 'html_assets')
        return send_from_directory(html_dir, filename)

    return app

def main():
    if '--self-test' in sys.argv:
        print("Running self-test...")
        # In a real self-test, you might check for window creation, etc.
        # For now, we'll just create a file to signal success.
        import tempfile
        with open(os.path.join(tempfile.gettempdir(), 'self_test_success.txt'), 'w') as f:
            f.write('success')
        time.sleep(2) # Give it time to be detected
        sys.exit(0)

    app = create_app()
    port = get_random_port()

    def run_server():
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1) # Give server time to start

    # Create webview window
    window = webview.create_window(
        title=CONFIG["metadata"]["name"],
        url=f"http://127.0.0.1:{{port}}",
        width=CONFIG["window"]["width"],
        height=CONFIG["window"]["height"],
        resizable=CONFIG["window"]["resizable"],
        fullscreen=CONFIG["window"]["fullscreen"]
    )

    webview.start(debug={debug_mode})

if __name__ == '__main__':
    main()
'''
        return script_template.format(
            config_json=json.dumps(self.config.dict(), indent=2),
            debug_mode=str(self.config.build.debug).lower()
        )

    def build(self) -> Dict[str, Any]:
        """Execute the build process with error recovery."""
        start_time = time.time()

        # Pre-flight checks
        self.progress_callback("Running pre-flight checks...")
        errors = run_preflight_checks(self.config)
        if errors:
            return {"success": False, "error": "\n".join(errors), "build_time": f"{time.time() - start_time:.2f}s"}

        # Prepare for build once
        main_script_path = self.prepare_build()

        # Create logs directory
        logs_dir = os.path.join(self.dist_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # Build attempts with fallback configurations
        build_configs = [
            self.config.build,  # Initial config
            self.config.build.copy(update={'onefile': False}),  # Fallback 1: one-dir mode
            self.config.build.copy(update={'console': True}), # Fallback 2: with console
            self.config.build.copy(update={'upx_compress': False, 'strip_debug': False}) # Fallback 3
        ]

        last_error = ""
        for i, build_config in enumerate(build_configs):
            original_build_config = self.config.build
            self.config.build = build_config

            try:
                self.progress_callback(f"Attempting build {i+1}/{len(build_configs)}...")
                if self.config.build.debug:
                    console.log(f"Build config: {build_config.dict()}")

                cmd = self._build_pyinstaller_command(main_script_path)
                if self.config.build.debug:
                    console.log(f"PyInstaller command: {' '.join(cmd)}")

                log_path = os.path.join(logs_dir, f"build_{i+1}.log")
                with open(log_path, 'w') as log_file:
                    result = subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT, text=True, cwd=self.build_dir, check=False)

                if result.returncode == 0:
                    self._post_process()
                    build_time = time.time() - start_time
                    exe_path = self._get_exe_path()
                    self_test_passed = self.run_self_test(exe_path)
                    report = {
                        "success": True,
                        "exe_path": exe_path,
                        "build_time": f"{build_time:.2f}s",
                        "exe_size": f"{os.path.getsize(exe_path) / (1024*1024):.2f} MB" if os.path.exists(exe_path) else "Unknown",
                        "config": self.config.dict(),
                        "timestamp": datetime.now().isoformat(),
                        "self_test_passed": self_test_passed
                    }
                    report_path = os.path.join(self.dist_dir, "build_report.json")
                    with open(report_path, 'w') as f:
                        json.dump(report, f, indent=2)

                    self.config.build = original_build_config # Restore original config
                    return report

                last_error = result.stderr or "Unknown build error."
                self.progress_callback(f"Build attempt {i+1} failed. Trying fallback...")

            except Exception as e:
                last_error = str(e)

            finally:
                self.config.build = original_build_config # Ensure config is restored

        return {"success": False, "error": last_error, "build_time": f"{time.time() - start_time:.2f}s"}

    def run_self_test(self, exe_path: str) -> bool:
        """Run a self-test on the built executable."""
        self.progress_callback("Running post-build self-test...")
        import psutil

        try:
            proc = subprocess.Popen([exe_path, "--self-test"])
            time.sleep(2) # Give the process time to start

            p = psutil.Process(proc.pid)
            if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
                self.progress_callback("Self-test failed: Process did not start correctly.")
                return False

            time.sleep(3) # Let it run for a bit

            if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                proc.terminate()
                return True
            else:
                self.progress_callback("Self-test failed: Process crashed.")
                return False

        except Exception as e:
            console.print(f"[red]Self-test failed with exception: {e}[/red]")
            return False

    def _build_pyinstaller_command(self, main_script_path: str) -> List[str]:
        """Build PyInstaller command with all options."""
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            f"--name={self.config.metadata.name}",
            f"--distpath={self.dist_dir}",
            f"--workpath={os.path.join(self.build_dir, 'work')}"
        ]

        if self.config.build.onefile:
            cmd.append("--onefile")

        if not self.config.build.console:
            cmd.append("--windowed")

        if self.config.build.icon_path and os.path.exists(self.config.build.icon_path):
            cmd.append(f"--icon={self.config.build.icon_path}")

        if self.config.build.source_type == "folder":
            html_assets = os.path.join(self.build_dir, "html_assets")
            cmd.append(f"--add-data={html_assets}{os.pathsep}html_assets")

        hidden_imports = [
            "flask", "webview", "threading", "json", "os", "sys", "time"
        ]
        for imp in hidden_imports:
            cmd.append(f"--hidden-import={imp}")

        if self.config.build.upx_compress:
            cmd.append("--upx-dir=upx")

        if self.config.build.debug:
            cmd.append("--debug=all")
        else:
            if self.config.build.strip_debug:
                cmd.append("--strip")

        cmd.append(main_script_path)
        return cmd

    def _get_exe_path(self) -> str:
        """Get the path to the built executable."""
        if self.config.build.onefile:
            return os.path.join(self.dist_dir, f"{self.config.metadata.name}.exe")
        else:
            return os.path.join(self.dist_dir, self.config.metadata.name, f"{self.config.metadata.name}.exe")

    def _post_process(self):
        """Post-process the built executable."""
        self.progress_callback("Post-processing...")
        # Placeholder for future post-processing steps
        pass
