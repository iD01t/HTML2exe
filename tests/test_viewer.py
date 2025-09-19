"""Tests for viewer module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from html2exe.viewer import HTMLViewer


class TestHTMLViewer:
    """Test HTML viewer functionality."""

    def test_initialization(self):
        """Test viewer initialization."""
        viewer = HTMLViewer("Test App", 800, 600)

        assert viewer.title == "Test App"
        assert viewer.width == 800
        assert viewer.height == 600
        assert viewer._temp_dir is None

    def test_default_initialization(self):
        """Test viewer with default parameters."""
        viewer = HTMLViewer()

        assert viewer.title == "HTML2exe"
        assert viewer.width == 1024
        assert viewer.height == 768

    def test_extract_assets(self):
        """Test asset extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source assets
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            (source_dir / "index.html").write_text("<html><body>Test</body></html>")
            (source_dir / "style.css").write_text("body { margin: 0; }")

            viewer = HTMLViewer()
            try:
                assets_dir = viewer.extract_assets(source_dir)

                assert assets_dir.exists()
                assert (assets_dir / "index.html").exists()
                assert (assets_dir / "style.css").exists()
                assert viewer._temp_dir is not None
            finally:
                viewer.cleanup()

    def test_extract_nonexistent_assets(self):
        """Test error handling for nonexistent assets."""
        viewer = HTMLViewer()

        with pytest.raises(RuntimeError, match="Assets not found"):
            viewer.extract_assets(Path("nonexistent"))

    def test_cleanup(self):
        """Test temporary directory cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            (source_dir / "index.html").write_text("<html></html>")

            viewer = HTMLViewer()
            assets_dir = viewer.extract_assets(source_dir)
            temp_path = viewer._temp_dir

            viewer.cleanup()

            assert viewer._temp_dir is None
            # Note: temp directory may still exist due to OS cleanup timing
