"""HTML to EXE conversion logic."""

import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def validate_input(input_path: Path) -> Path:
    """Validate and normalize input path."""
    if not input_path.exists():
        raise ValueError(f"Input path does not exist: {input_path}")

    if input_path.is_file():
        if input_path.suffix.lower() != ".html":
            raise ValueError(f"Input file must be HTML: {input_path}")
        return input_path
    elif input_path.is_dir():
        index_html = input_path / "index.html"
        if not index_html.exists():
            raise ValueError(f"Directory must contain index.html: {input_path}")
        return index_html
    else:
        raise ValueError(f"Invalid input path: {input_path}")


def prepare_assets(input_path: Path, temp_dir: Path) -> Path:
    """Prepare HTML assets in temporary directory."""
    assets_dir = temp_dir / "html_assets"
    assets_dir.mkdir(exist_ok=True)

    if input_path.is_file():
        # Single HTML file
        shutil.copy2(input_path, assets_dir / "index.html")

        # Copy any assets in the same directory
        parent_dir = input_path.parent
        for item in parent_dir.iterdir():
            if item.is_file() and item != input_path:
                if item.suffix.lower() in {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"}:
                    shutil.copy2(item, assets_dir / item.name)
            elif item.is_dir() and item.name in {"css", "js", "images", "img", "assets", "static"}:
                shutil.copytree(item, assets_dir / item.name, dirs_exist_ok=True)
    else:
        # Directory with index.html
        shutil.copytree(input_path, assets_dir, dirs_exist_ok=True)

    return assets_dir


def create_viewer_script(temp_dir: Path, title: Optional[str], width: int, height: int) -> Path:
    """Create the pywebview viewer script."""
    viewer_script = temp_dir / "viewer.py"

    script_content = f'''"""Generated HTML viewer using pywebview."""

import sys
import tempfile
import shutil
from pathlib import Path

try:
    import webview
except ImportError:
    print("Error: pywebview is required but not installed.")
    print("Install with: pip install pywebview")
    sys.exit(1)


def extract_assets():
    """Extract bundled HTML assets to temp directory."""
    # Get the bundled assets path
    if hasattr(sys, '_MEIPASS'):
        bundle_dir = Path(sys._MEIPASS)
    else:
        bundle_dir = Path(__file__).parent

    assets_source = bundle_dir / "html_assets"
    if not assets_source.exists():
        raise RuntimeError(f"HTML assets not found: {{assets_source}}")

    # Create temp directory for assets
    temp_assets = Path(tempfile.mkdtemp(prefix="html2exe_"))
    shutil.copytree(assets_source, temp_assets / "html_assets")

    return temp_assets / "html_assets"


def main():
    """Main viewer entry point."""
    try:
        assets_dir = extract_assets()
        index_html = assets_dir / "index.html"

        if not index_html.exists():
            raise RuntimeError(f"index.html not found in assets: {{assets_dir}}")

        # Create webview window
        window = webview.create_window(
            title="{title or 'HTML2exe Application'}",
            url=str(index_html),
            width={width},
            height={height},
            resizable=True,
            shadow=True,
        )

        # Start webview
        webview.start(debug=False)

    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("HTML2exe Error", f"Failed to start application:\\n\\n{{str(e)}}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

    viewer_script.write_text(script_content, encoding="utf-8")
    return viewer_script


def run_pyinstaller(viewer_script: Path, assets_dir: Path, output_path: Path, check_mode: bool) -> None:
    """Run PyInstaller to create the EXE."""
    if check_mode:
        logger.info(f"CHECK MODE: Would create {output_path} from {viewer_script}")
        logger.info(f"Assets directory: {assets_dir}")
        return

    logger.info(f"Building EXE: {output_path}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--clean",
        "--distpath", str(output_path.parent),
        "--name", output_path.stem,
        "--add-data", f"{assets_dir};html_assets",
        str(viewer_script),
    ]

    logger.debug(f"PyInstaller command: {' '.join(cmd)}")

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    logger.debug(f"PyInstaller output: {result.stdout}")

    if not output_path.exists():
        raise RuntimeError(f"EXE was not created: {output_path}")

    logger.info(f"Successfully created: {output_path}")


def convert_html_to_exe(
    input_path: Path,
    output_path: Path,
    title: Optional[str] = None,
    width: int = 1024,
    height: int = 768,
    check_mode: bool = False
) -> None:
    """Convert HTML to Windows EXE."""
    logger.info(f"Converting {input_path} to {output_path}")

    # Validate input
    html_file = validate_input(input_path)

    # Use input name as title if not provided
    if title is None:
        title = input_path.stem

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="html2exe_") as temp_dir:
        temp_path = Path(temp_dir)

        # Prepare assets
        assets_dir = prepare_assets(input_path, temp_path)

        # Create viewer script
        viewer_script = create_viewer_script(temp_path, title, width, height)

        # Run PyInstaller
        run_pyinstaller(viewer_script, assets_dir, output_path, check_mode)

    if not check_mode:
        logger.info("Conversion completed successfully")
    else:
        logger.info("Check completed - all inputs valid")
