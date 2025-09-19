"""HTML viewer using pywebview for testing."""

import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional

try:
    import webview
except ImportError:
    webview = None


class HTMLViewer:
    """HTML viewer wrapper for testing."""

    def __init__(self, title: str = "HTML2exe", width: int = 1024, height: int = 768):
        self.title = title
        self.width = width
        self.height = height
        self._temp_dir: Optional[Path] = None

    def extract_assets(self, assets_source: Path) -> Path:
        """Extract HTML assets to temp directory."""
        if not assets_source.exists():
            raise RuntimeError(f"Assets not found: {assets_source}")

        self._temp_dir = Path(tempfile.mkdtemp(prefix="html2exe_"))
        assets_dir = self._temp_dir / "html_assets"
        shutil.copytree(assets_source, assets_dir)

        return assets_dir

    def show(self, html_path: Path, debug: bool = False) -> None:
        """Show HTML in webview window."""
        if webview is None:
            raise RuntimeError("pywebview is required but not installed")

        if not html_path.exists():
            raise RuntimeError(f"HTML file not found: {html_path}")

        # Create window
        webview.create_window(
            title=self.title,
            url=str(html_path),
            width=self.width,
            height=self.height,
            resizable=True,
            shadow=True,
        )

        # Start webview
        webview.start(debug=debug)

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None

    def __del__(self) -> None:
        self.cleanup()
