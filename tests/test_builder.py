"""Tests for builder module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from html2exe.builder import (
    convert_html_to_exe,
    prepare_assets,
    validate_input,
    create_viewer_script,
)


class TestValidateInput:
    """Test input validation."""

    def test_nonexistent_path(self):
        """Test error for nonexistent path."""
        with pytest.raises(ValueError, match="does not exist"):
            validate_input(Path("nonexistent.html"))

    def test_valid_html_file(self):
        """Test valid HTML file."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            html_path = Path(f.name)

        try:
            result = validate_input(html_path)
            assert result == html_path
        finally:
            html_path.unlink()

    def test_invalid_file_extension(self):
        """Test error for non-HTML file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            txt_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="must be HTML"):
                validate_input(txt_path)
        finally:
            txt_path.unlink()

    def test_directory_with_index_html(self):
        """Test directory containing index.html."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            index_path = temp_path / "index.html"
            index_path.write_text("<html><body>Test</body></html>")

            result = validate_input(temp_path)
            assert result == index_path

    def test_directory_without_index_html(self):
        """Test error for directory without index.html."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="must contain index.html"):
                validate_input(Path(temp_dir))


class TestPrepareAssets:
    """Test asset preparation."""

    def test_single_html_file(self):
        """Test preparing assets from single HTML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source HTML file
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            html_file = source_dir / "test.html"
            html_file.write_text("<html><body>Test</body></html>")

            # Create CSS file in same directory
            css_file = source_dir / "style.css"
            css_file.write_text("body { margin: 0; }")

            # Prepare assets
            assets_dir = prepare_assets(html_file, Path(temp_dir))

            # Check results
            assert assets_dir.exists()
            assert (assets_dir / "index.html").exists()
            assert (assets_dir / "style.css").exists()

    def test_directory_with_assets(self):
        """Test preparing assets from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source directory structure
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            (source_dir / "index.html").write_text("<html><body>Test</body></html>")

            css_dir = source_dir / "css"
            css_dir.mkdir()
            (css_dir / "style.css").write_text("body { margin: 0; }")

            # Prepare assets
            assets_dir = prepare_assets(source_dir, Path(temp_dir))

            # Check results
            assert assets_dir.exists()
            assert (assets_dir / "index.html").exists()
            assert (assets_dir / "css" / "style.css").exists()


class TestCreateViewerScript:
    """Test viewer script creation."""

    def test_script_creation(self):
        """Test viewer script is created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = create_viewer_script(
                Path(temp_dir),
                "Test App",
                800,
                600
            )

            assert script_path.exists()
            assert script_path.suffix == ".py"

            content = script_path.read_text()
            assert "Test App" in content
            assert "800" in content
            assert "600" in content
            assert "webview.create_window" in content


class TestConvertHtmlToExe:
    """Test full conversion process."""

    @patch("html2exe.builder.run_pyinstaller")
    def test_check_mode(self, mock_pyinstaller):
        """Test conversion in check mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source HTML
            source_path = Path(temp_dir) / "test.html"
            source_path.write_text("<html><body>Test</body></html>")

            output_path = Path(temp_dir) / "output.exe"

            # Run in check mode
            convert_html_to_exe(source_path, output_path, check_mode=True)

            # Verify pyinstaller was called with check_mode=True
            mock_pyinstaller.assert_called_once()
            args = mock_pyinstaller.call_args[0]
            assert args[-1] is True  # check_mode parameter
