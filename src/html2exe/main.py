import sys
import os
import traceback

def entry_point():
    """Main entry point - CLI or GUI based on arguments."""
    from .cli.main import app as cli_app
    from .gui.main import ModernGUI

    try:
        if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == 'gui'):
             if len(sys.argv) > 1 and sys.argv[1] == 'gui':
                # remove 'gui' argument so it doesn't interfere
                sys.argv.pop(1)
             print("HTML2EXE Pro Premium v2.0.0")
             print("No command line arguments provided or 'gui' command used, launching GUI...")
             gui_app = ModernGUI()
             gui_app.run()
        else:
            print("HTML2EXE Pro Premium v2.0.0")
            print("Command line arguments provided, using CLI...")
            cli_app()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    entry_point()
