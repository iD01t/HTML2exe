import os
import sys
import subprocess
import importlib
import shutil
import time
import webbrowser

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

import json
from ..core.config import AppConfig
from ..core.builder import BuildEngine
from ..core.packager import create_installer
from ..gui.main import ModernGUI
from ..main import APP_VERSION

console = Console()
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
    output: str = typer.Option("dist", "--output", "-o", help="Output directory")
):
    """Build HTML application to executable."""
    console.print(f"[bold green]HTML2EXE Pro Premium v{APP_VERSION}[/bold green]")
    console.print(f"Building application: [bold]{name}[/bold]")

    config = AppConfig()
    config.metadata.name = name
    config.build.source_path = src
    config.build.source_type = "url" if src.startswith(("http://", "https://")) else "folder"
    config.build.icon_path = icon
    config.build.onefile = onefile
    config.build.offline_mode = offline
    config.build.debug = debug
    config.build.output_dir = output
    config.window.kiosk = kiosk
    config.window.width = width
    config.window.height = height

    if config.build.source_type == "folder" and not os.path.exists(src):
        console.print("[red]Error: Source folder does not exist[/red]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True
    ) as progress:
        task = progress.add_task("Building...", total=100)

        def progress_callback(message):
            progress.update(task, description=message)
            progress.advance(task, 10)

        try:
            engine = BuildEngine(config, progress_callback)
            result = engine.build()

            if result["success"]:
                console.print("[green]✅ Build completed successfully![/green]")
                console.print(f"[blue]📁 Output:[/blue] {result['exe_path']}")
                console.print(f"[blue]📊 Size:[/blue] {result['exe_size']}")
                console.print(f"[blue]⏱️ Time:[/blue] {result['build_time']}")
            else:
                console.print(f"[red]❌ Build failed:[/red] {result['error']}")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]❌ Build error:[/red] {e}")
            raise typer.Exit(1)


@app.command()
def serve(
    src: str = typer.Option(".", "--src", "-s", help="Source folder to serve"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser automatically")
):
    """Serve HTML folder for development and testing."""
    console.print(f"[bold blue]HTML2EXE Pro Development Server[/bold blue]")
    console.print(f"Serving: [bold]{src}[/bold]")
    console.print(f"Port: [bold]{port}[/bold]")

    if not os.path.exists(src):
        console.print("[red]Error: Source folder does not exist[/red]")
        raise typer.Exit(1)

    try:
        from ..core.webview_manager import WebViewManager
        config = AppConfig()
        config.build.source_path = src
        config.build.source_type = "folder"

        webview_manager = WebViewManager(config)
        webview_manager.start_server(src, port)

        url = f"http://localhost:{port}"
        console.print(f"[green]🚀 Server running at:[/green] {url}")

        if open_browser:
            webbrowser.open(url)

        console.print("Press [bold]Ctrl+C[/bold] to stop the server")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")

    except Exception as e:
        console.print(f"[red]Server error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def doctor():
    """Check system requirements and dependencies."""
    console.print(f"[bold blue]HTML2EXE Pro System Diagnostics[/bold blue]")

    checks = []

    python_version = sys.version_info
    if python_version >= (3, 10):
        checks.append(("✅", f"Python {python_version.major}.{python_version.minor}", "OK"))
    else:
        checks.append(("❌", f"Python {python_version.major}.{python_version.minor}", "Requires Python 3.10+"))

    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            checks.append(("✅", "PyInstaller", result.stdout.strip()))
        else:
            checks.append(("❌", "PyInstaller", "Not installed"))
    except FileNotFoundError:
        checks.append(("❌", "PyInstaller", "Not found"))

    for package in ["flask", "pywebview", "pillow", "requests", "rich", "typer"]:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'Unknown')
            checks.append(("✅", package, version))
        except ImportError:
            checks.append(("❌", package, "Not installed"))

    checks.append(("ℹ️", "Platform", f"{sys.platform}"))
    checks.append(("ℹ️", "Architecture", f"{'64-bit' if sys.maxsize > 2**32 else '32-bit'}"))

    table = Table(title="System Check Results")
    table.add_column("Status", style="bold")
    table.add_column("Component", style="cyan")
    table.add_column("Version/Status", style="green")

    for status, component, version in checks:
        table.add_row(status, component, version)

    console.print(table)

    issues = [check for check in checks if check[0] == "❌"]
    if issues:
        console.print("\n[bold red]Issues Found:[/bold red]")
        for status, component, issue in issues:
            console.print(f"  • {component}: {issue}")

        console.print("\n[bold yellow]Recommended Actions:[/bold yellow]")
        console.print("  1. Update Python to 3.10+ if needed")
        console.print("  2. Install missing packages: pip install -r requirements.txt")
        console.print("  3. Restart the application after installing dependencies")
    else:
        console.print("\n[bold green]🎉 All checks passed! Your system is ready.[/bold green]")


@app.command()
def clean():
    """Clean build artifacts and temporary files."""
    console.print("[bold blue]Cleaning build artifacts...[/bold blue]")

    cleaned = []
    build_dirs = ["build", "dist", "__pycache__", "*.egg-info"]

    for pattern in build_dirs:
        import glob
        for path in glob.glob(pattern, recursive=True):
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    cleaned.append(f"📁 {path}")
                else:
                    os.remove(path)
                    cleaned.append(f"📄 {path}")

    temp_patterns = ["*.pyc", "*.pyo", "*.tmp", "*.log"]
    for pattern in temp_patterns:
        for path in glob.glob(f"**/{pattern}", recursive=True):
            try:
                os.remove(path)
                cleaned.append(f"🗑️ {path}")
            except OSError:
                pass

    if cleaned:
        console.print(f"[green]✅ Cleaned {len(cleaned)} items:[/green]")
        for item in cleaned[:10]:
            console.print(f"  {item}")
        if len(cleaned) > 10:
            console.print(f"  ... and {len(cleaned) - 10} more items")
    else:
        console.print("[yellow]No build artifacts found to clean[/yellow]")


@app.command()
def gui():
    """Launch the graphical user interface."""
    console.print(f"[bold green]Launching HTML2EXE Pro Premium GUI...[/bold green]")

    try:
        gui_app = ModernGUI()
        gui_app.run()
    except Exception as e:
        console.print(f"[red]GUI Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def package(
    report_path: str = typer.Option("dist/build_report.json", "--report", "-r", help="Path to the build_report.json file")
):
    """Package the application into a Windows installer."""
    console.print(f"[bold green]Creating installer...[/bold green]")

    if not os.path.exists(report_path):
        console.print(f"[red]Error: Build report not found at {report_path}[/red]")
        raise typer.Exit(1)

    with open(report_path, 'r') as f:
        report = json.load(f)

    config = AppConfig(**report['config'])
    exe_path = report['exe_path']

    try:
        installer_path = create_installer(config, exe_path)
        console.print(f"[green]✅ Installer created successfully![/green]")
        console.print(f"[blue]📁 Output:[/blue] {installer_path}")
    except Exception as e:
        console.print(f"[red]❌ Installer creation failed:[/red] {e}")
        raise typer.Exit(1)
