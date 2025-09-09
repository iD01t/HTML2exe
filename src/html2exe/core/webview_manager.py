import os
import sys
import time
import threading
import hashlib
from datetime import datetime

import webview
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console

from .config import AppConfig
from .builder import _create_flask_app

console = Console()


class LiveReloadHandler(FileSystemEventHandler):
    """Enhanced file system handler with debouncing."""

    def __init__(self, webview_window, debounce_ms: int = 500):
        self.webview_window = webview_window
        self.debounce_ms = debounce_ms
        self.pending_reload = False

    def on_modified(self, event):
        """Handle file modifications with debouncing."""
        if not event.is_directory and self._should_reload(event.src_path):
            if not self.pending_reload:
                self.pending_reload = True
                threading.Timer(self.debounce_ms / 1000, self._reload).start()

    def _should_reload(self, filepath: str) -> bool:
        """Check if file change should trigger reload."""
        reload_extensions = {'.html', '.css', '.js', '.json', '.xml'}
        return any(filepath.lower().endswith(ext) for ext in reload_extensions)

    def _reload(self):
        """Perform the actual reload."""
        try:
            if self.webview_window:
                self.webview_window.evaluate_js('window.location.reload()')
        except Exception as e:
            console.print(f"[yellow]Reload failed: {e}[/yellow]")
        finally:
            self.pending_reload = False


class WebViewManager:
    """Enhanced WebView manager with premium features."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.window = None
        self.flask_app = None
        self.server_thread = None
        self.observer = None
        self.server_port = None

    def start_server(self, source_path: str, port: int = 5000):
        """Start enhanced Flask development server."""
        self.server_port = port
        self.flask_app = _create_flask_app(self.config)

        def run_server():
            try:
                self.flask_app.run(
                    host='127.0.0.1',
                    port=port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                console.print(f"[red]Server error:[/red] {e}")

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(2)

        try:
            response = requests.get(f"http://127.0.0.1:{port}/api/health", timeout=5)
            if response.status_code == 200:
                console.print(f"[green]✅ Server started successfully on port {port}[/green]")
            else:
                console.print(f"[yellow]⚠️ Server responded with status {response.status_code}[/yellow]")
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Server health check failed:[/red] {e}")

    def create_window(self, url: str = None):
        """Create enhanced webview window with premium features."""
        if url is None:
            url = f"http://127.0.0.1:{self.server_port or 5000}"

        window_config = {
            'width': self.config.window.width,
            'height': self.config.window.height,
            'min_size': (self.config.window.min_width, self.config.window.min_height),
            'resizable': self.config.window.resizable,
            'fullscreen': self.config.window.fullscreen,
            'on_top': self.config.window.always_on_top,
        }

        if self.config.window.kiosk:
            window_config.update({'fullscreen': True, 'resizable': False, 'on_top': True})
        if self.config.window.frameless:
            window_config['frameless'] = True

        self.window = webview.create_window(title=self.config.metadata.name, url=url, **window_config)
        self._setup_window_events()
        return self.window

    def _setup_window_events(self):
        """Setup window event handlers."""
        if not self.window:
            return
        if self.config.build.single_instance:
            self._enforce_single_instance()

    def _enforce_single_instance(self):
        """Enforce single instance using mutex."""
        try:
            import win32event
            import win32api
            import winerror

            mutex_name = f"HTML2EXE_Pro_{self.config.metadata.name}"
            mutex = win32event.CreateMutex(None, False, mutex_name)

            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                console.print("[yellow]Application is already running[/yellow]")
                sys.exit(0)

        except ImportError:
            pass

    def setup_live_reload(self, source_path: str):
        """Setup enhanced file watching for live reload."""
        if os.path.isdir(source_path):
            handler = LiveReloadHandler(self.window, debounce_ms=300)
            self.observer = Observer()
            self.observer.schedule(handler, source_path, recursive=True)
            self.observer.start()
            console.print(f"[green]📁 Live reload enabled for: {source_path}[/green]")

    def start(self, source_path: str = None, url: str = None, dev_mode: bool = False):
        """Start the enhanced webview application."""
        try:
            if source_path:
                port = 5000
                self.start_server(source_path, port)
                target_url = f"http://127.0.0.1:{port}"
                if dev_mode:
                    self.setup_live_reload(source_path)
            else:
                target_url = url

            window = self.create_window(target_url)
            console.print(f"[green]🚀 Starting application: {self.config.metadata.name}[/green]")
            console.print(f"[blue]🌐 URL: {target_url}[/blue]")
            webview.start(debug=self.config.build.debug)

        except Exception as e:
            console.print(f"[red]❌ Application start error:[/red] {e}")
            raise
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()


class SystemIntegration:
    """System integration utilities for Windows."""

    @staticmethod
    def register_protocol(protocol: str, executable_path: str):
        """Register custom protocol handler in Windows registry."""
        try:
            import winreg
            protocol_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, protocol)
            winreg.SetValueEx(protocol_key, "", 0, winreg.REG_SZ, f"URL:{protocol} Protocol")
            winreg.SetValueEx(protocol_key, "URL Protocol", 0, winreg.REG_SZ, "")
            command_key = winreg.CreateKey(protocol_key, r"shell\\open\\command")
            winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'"{executable_path}" "%1"')
            winreg.CloseKey(command_key)
            winreg.CloseKey(protocol_key)
            return True
        except Exception as e:
            console.print(f"[red]Protocol registration failed:[/red] {e}")
            return False

    @staticmethod
    def add_to_startup(app_name: str, executable_path: str):
        """Add application to Windows startup."""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                               0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, executable_path)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            console.print(f"[red]Startup registration failed:[/red] {e}")
            return False


class Analytics:
    """Anonymous analytics and telemetry."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.enabled = config.advanced.analytics

    def track_event(self, event_name: str, properties: dict = None):
        """Track anonymous event."""
        if not self.enabled:
            return
        try:
            event_data = {
                "event": event_name,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "app_version": "2.0.0", # Replace with dynamic version
                "properties": properties or {}
            }
            console.print(f"[dim]📊 Analytics: {event_name}[/dim]")
        except Exception:
            pass

    def track_build(self, success: bool, build_time: float, config: AppConfig):
        """Track build event."""
        self.track_event("build_completed", {
            "success": success,
            "build_time": build_time,
            "source_type": config.build.source_type,
            "onefile": config.build.onefile,
            "window_size": f"{config.window.width}x{config.window.height}"
        })
