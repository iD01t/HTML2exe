"""End-to-end smoke tests."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from html2exe.cli import main


class TestE2ESmoke:
    """End-to-end smoke tests using --check mode."""

    def test_single_html_file_smoke(self):
        """Test converting single HTML file (check mode)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create simple HTML file
            html_file = temp_path / "app.html"
            html_file.write_text("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test App</title>
                <style>
                    body { font-family: Arial; margin: 20px; }
                    h1 { color: blue; }
                </style>
            </head>
            <body>
                <h1>Hello HTML2exe!</h1>
                <p>This is a test application.</p>
                <script>
                    console.log('App loaded successfully');
                </script>
            </body>
            </html>
            """)

            output_path = temp_path / "TestApp.exe"

            # Run conversion in check mode
            result = main([
                "--input", str(html_file),
                "--output", str(output_path),
                "--title", "Test App",
                "--width", "1200",
                "--height", "800",
                "--check",
                "--verbose"
            ])

            assert result == 0

    def test_html_directory_smoke(self):
        """Test converting HTML directory (check mode)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create HTML project directory
            project_dir = temp_path / "myproject"
            project_dir.mkdir()

            # Create index.html
            (project_dir / "index.html").write_text("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>My Project</title>
                <link rel="stylesheet" href="css/main.css">
            </head>
            <body>
                <h1>My Project</h1>
                <p>A multi-file HTML project.</p>
                <script src="js/app.js"></script>
            </body>
            </html>
            """)

            # Create CSS directory and file
            css_dir = project_dir / "css"
            css_dir.mkdir()
            (css_dir / "main.css").write_text("""
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            h1 { text-align: center; }
            """)

            # Create JS directory and file
            js_dir = project_dir / "js"
            js_dir.mkdir()
            (js_dir / "app.js").write_text("""
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Multi-file project loaded');
                document.querySelector('h1').addEventListener('click', function() {
                    alert('Project is working!');
                });
            });
            """)

            output_path = temp_path / "MyProject.exe"

            # Run conversion in check mode
            result = main([
                "--input", str(project_dir),
                "--output", str(output_path),
                "--check"
            ])

            assert result == 0
