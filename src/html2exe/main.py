import sys
import os

APP_NAME = "HTML2EXE Pro Premium"
APP_VERSION = "2.0.1"

def main():
    """Main entry point - CLI or GUI based on arguments."""
    # It's better to handle dependencies inside the utils module
    from .utils.dependencies import check_and_install_dependencies
    check_and_install_dependencies()

    from rich.console import Console
    from .cli.main import app as cli_app
    from .gui.main import ModernGUI

    console = Console()
    try:
        if len(sys.argv) == 1 or 'gui' in sys.argv:
            console.print(f"[bold cyan]{APP_NAME} v{APP_VERSION}[/bold cyan]")
            console.print("[dim]No command line arguments provided, launching GUI...[/dim]")
            gui_app = ModernGUI()
            gui_app.run()
        else:
            cli_app()

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
