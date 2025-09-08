import os
import sys
import typer
import subprocess
import importlib
import time
import webbrowser

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..core.config import AppConfig
from ..core.preflight import PreflightChecker
from ..core.debugger import BulletProofExporter
from ..core.builder import BuildEngine
from ..gui.main import ModernGUI

APP_VERSION = "2.0.0"

app = typer.Typer(help="HTML2EXE Pro Premium - Convert HTML to Professional Desktop Apps")

@app.command()
def build(
    src: str = typer.Option(..., "--src", "-s", help="Source folder or URL"),
    name: str = typer.Option("MyHTMLApp", "--name", "-n", help="Application name"),
    icon: str = typer.Option("", "--icon", "-i", help="Icon file path (.ico, .png)"),
    onefile: bool = typer.Option(True, "--onefile/--no-onefile", help="Create single file executable"),
    offline: bool = typer.Option(False, "--offline", help="Enable offline mode"),
    kiosk: bool = typer.Option(False, "--kiosk", help="Enable kiosk mode"),
    width: int = typer.Option(1200, "--width", help="Window width"),
    height: int = typer.Option(800, "--height", help="Window height"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    output: str = typer.Option("dist", "--output", "-o", help="Output directory"),
    bullet_proof: bool = typer.Option(True, "--bullet-proof/--no-bullet-proof", help="Use bullet-proof export with auto-debug and recovery"),
    upx: bool = typer.Option(False, "--upx/--no-upx", help="Enable UPX compression (requires UPX in PATH)"),
    skip_preflight: bool = typer.Option(False, "--skip-preflight", help="Skip pre-flight checks"),
):
    """Build HTML application to executable."""
    print(f"HTML2EXE Pro Premium v{APP_VERSION}")
    print(f"Building application: {name}")

    source_type = "url" if src.startswith(("http://", "https://")) else "folder"

    if not skip_preflight:
        # Run pre-flight checks
        print("✈️  Running pre-flight checks...")
        report = PreflightChecker.run_all_checks(src, source_type)

        if report["errors"]:
            print("❌ Pre-flight checks failed with critical errors:")
            for error in report["errors"]:
                print(f"  - {error}")
            raise typer.Exit(1)

        if report["warnings"]:
            print("⚠️ Pre-flight checks found warnings:")
            for warning in report["warnings"]:
                print(f"  - {warning}")
            if not typer.confirm("Do you want to continue with the build?"):
                raise typer.Exit()
    else:
        report = {}

    # Create configuration
    config = AppConfig()
    config.metadata.name = name
    config.build.source_path = src
    config.build.source_type = source_type
    config.build.icon_path = icon
    config.build.onefile = onefile
    config.build.offline_mode = offline
    config.build.debug = debug
    config.build.output_dir = output
    config.build.upx_compress = upx
    config.window.kiosk = kiosk
    config.window.width = width
    config.window.height = height

    # Apply recommended settings
    PreflightChecker.apply_recommended_settings(config, report)

    # Always use bullet-proof export
    print("🛡️ Using bullet-proof export with auto-debug and recovery...")
    try:
        exporter = BulletProofExporter(config)
        if debug:
            exporter.debugger.enable_debug_mode()

        result = exporter.export_with_auto_debug()

        if result["success"]:
            print("✅ Bullet-proof export completed successfully!")
            print(f"📁 Output: {result['exe_path']}")
            print(f"📊 Size: {result['exe_size']}")
            print(f"⏱️ Time: {result['build_time']}")
            print(f"🎯 Strategy: {result.get('strategy', 'Standard Export')}")
        else:
            print(f"❌ Bullet-proof export failed: {result['error']}")
            if 'debug_report' in result:
                print(f"📋 Debug report saved: {result['debug_report']}")
            if 'recommendations' in result:
                print("\n💡 Recommendations:")
                for rec in result['recommendations']:
                    print(f"  • {rec}")
            raise typer.Exit(1)

    except Exception as e:
        print(f"❌ Bullet-proof export error: {e}")
        raise typer.Exit(1)

@app.command()
def serve(
    src: str = typer.Option(".", "--src", "-s", help="Source folder to serve"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser automatically")
):
    """Serve HTML folder for development and testing."""
    print(f"HTML2EXE Pro Development Server")
    print(f"Serving: {src}")
    print(f"Port: {port}")

    if not os.path.exists(src):
        print("Error: Source folder does not exist")
        raise typer.Exit(1)

    try:
        import http.server
        import socketserver

        Handler = http.server.SimpleHTTPRequestHandler

        os.chdir(src)
        with socketserver.TCPServer(("", port), Handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"🚀 Server running at: {url}")
            if open_browser:
                webbrowser.open(url)

            print("Press Ctrl+C to stop the server")
            httpd.serve_forever()

    except Exception as e:
        print(f"Server error: {e}")
        raise typer.Exit(1)

@app.command()
def doctor():
    """Check system requirements and dependencies."""
    print(f"HTML2EXE Pro System Diagnostics")

    checks = []

    # Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        checks.append(("✅", f"Python {python_version.major}.{python_version.minor}", "OK"))
    else:
        checks.append(("❌", f"Python {python_version.major}.{python_version.minor}", "Requires Python 3.8+"))

    # PyInstaller
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            checks.append(("✅", "PyInstaller", result.stdout.strip()))
        else:
            checks.append(("❌", "PyInstaller", "Not installed"))
    except:
        checks.append(("❌", "PyInstaller", "Not found"))

    # Dependencies
    for package in ["flask", "pywebview", "pillow", "requests", "rich", "typer", "beautifulsoup4"]:
        try:
            module = importlib.import_module(package.replace('pywebview', 'webview').replace('beautifulsoup4', 'bs4'))
            version = getattr(module, '__version__', 'Unknown')
            checks.append(("✅", package, version))
        except ImportError:
            checks.append(("❌", package, "Not installed"))

    # UPX check
    try:
        result = subprocess.run(["upx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            checks.append(("✅", "UPX", version_line))
        else:
            checks.append(("⚠️", "UPX", "Not in PATH (optional for compression)"))
    except:
        checks.append(("⚠️", "UPX", "Not installed (optional for compression)"))

    # WebView2 runtime check (Windows)
    if sys.platform == "win32":
        try:
            import shutil
            if shutil.which("msedgewebview2.exe") or os.environ.get("WEBVIEW2_RUNTIME"):
                checks.append(("✅", "WebView2", "Available"))
            else:
                checks.append(("⚠️", "WebView2", "Not found (will prompt to install)"))
        except:
            checks.append(("⚠️", "WebView2", "Check failed"))

    # System info
    checks.append(("ℹ️", "Platform", f"{sys.platform}"))
    checks.append(("ℹ️", "Architecture", f"{sys.maxsize > 2**32 and '64-bit' or '32-bit'}"))

    # Display results
    print("\n--- System Check Results ---")
    for status, component, version in checks:
        print(f"{status} {component:<15} {version}")

    # Recommendations
    issues = [check for check in checks if check[0] == "❌"]
    if issues:
        print("\nIssues Found:")
        for status, component, issue in issues:
            print(f"  • {component}: {issue}")

        print("\nRecommended Actions:")
        print("  1. Update Python to 3.8+ if needed")
        print("  2. Install missing packages using pip")
        print("  3. Restart the application after installing dependencies")
    else:
        print("\n🎉 All checks passed! Your system is ready.")

@app.command()
def doctor(
    src: str = typer.Option(..., "--src", "-s", help="Source folder or URL to analyze")
):
    """Run pre-flight checks on the source and system."""
    print(f"HTML2EXE Pro Premium - Pre-flight Check")
    print(f"Analyzing: {src}")
    print()

    source_type = "url" if src.startswith(("http://", "https://")) else "folder"
    report = PreflightChecker.run_all_checks(src, source_type)

    print("✈️  Pre-flight Check Report:")
    print("=" * 50)

    if report["errors"]:
        print("\n❌ Errors:")
        for error in report["errors"]:
            print(f"  - {error}")

    if report["warnings"]:
        print("\n⚠️ Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if report["suggestions"]:
        print("\n💡 Suggestions:")
        for suggestion in report["suggestions"]:
            print(f"  - {suggestion}")

    print("\n" + "="*50)
    if report["errors"]:
        print("🔴 Pre-flight failed. Please fix the errors before building.")
        raise typer.Exit(1)
    else:
        print("🟢 Pre-flight checks passed. Ready to build.")

@app.command()
def gui():
    """Launch the graphical user interface."""
    print(f"Launching HTML2EXE Pro Premium GUI...")

    try:
        gui_app = ModernGUI()
        gui_app.run()
    except Exception as e:
        print(f"GUI Error: {e}")
        raise typer.Exit(1)
