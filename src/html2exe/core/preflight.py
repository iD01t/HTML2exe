import os
import sys
import json
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import urllib

from .config import AppConfig

class PreflightChecker:
    """Comprehensive pre-flight check system for bullet-proof exports."""

    @staticmethod
    def run_all_checks(source_path: str, source_type: str) -> Dict[str, Any]:
        """Run all pre-flight checks and return a report."""
        report = {
            "recommendations": [],
            "warnings": [],
            "errors": [],
            "suggestions": [],
            "estimated_size": "40-80 MB",
            "recommended_onefile": True,
            "recommended_console": False,
            "recommended_debug": False,
            "recommended_upx": True,
        }

        # System checks
        PreflightChecker._check_python_version(report)
        PreflightChecker._check_pyinstaller(report)
        PreflightChecker._check_memory(report)

        # Source checks
        if source_type == "folder":
            PreflightChecker._check_folder_source(source_path, report)
        elif source_type == "url":
            PreflightChecker._check_url_source(source_path, report)

        return report

    @staticmethod
    def _check_python_version(report: Dict[str, Any]):
        if sys.version_info < (3, 8):
            report["errors"].append("Python 3.8+ is required.")

    @staticmethod
    def _check_pyinstaller(report: Dict[str, Any]):
        try:
            import PyInstaller
        except ImportError:
            report["errors"].append("PyInstaller is not installed. Please run 'pip install pyinstaller'.")

    @staticmethod
    def _check_memory(report: Dict[str, Any]):
        try:
            import psutil
            available_memory = psutil.virtual_memory().available / (1024**3)  # GB
            if available_memory < 1:
                report["warnings"].append(f"Low memory detected ({available_memory:.2f}GB). Builds may be slow or fail.")
                report["recommended_onefile"] = False
                report["suggestions"].append("Consider using directory mode (--no-onefile) for better performance on low-memory systems.")
        except ImportError:
            report["warnings"].append("Could not check available memory. 'psutil' is not installed.")

    @staticmethod
    def _check_folder_source(source_path: str, report: Dict[str, Any]):
        if not os.path.exists(source_path):
            report["errors"].append(f"Source folder not found: {source_path}")
            return

        files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(source_path) for f in filenames]

        if not any(f.endswith("index.html") for f in files):
            report["warnings"].append("No 'index.html' file found in the source folder. A default one will be generated.")

        # Check for package.json
        package_json_path = os.path.join(source_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    report["suggestions"].append(f"Found 'package.json' for project '{package_data.get('name', 'N/A')}'.")
            except json.JSONDecodeError:
                report["warnings"].append("'package.json' is present but could not be read (invalid JSON).")

        # Check for broken links and absolute paths
        html_files = [f for f in files if f.endswith((".html", ".htm"))]
        for html_file in html_files:
            PreflightChecker._scan_html_file(html_file, source_path, report)

    @staticmethod
    def _check_url_source(source_path: str, report: Dict[str, Any]):
        try:
            response = urllib.request.urlopen(source_path, timeout=10)
            if response.getcode() >= 400:
                report["errors"].append(f"URL returned status code {response.getcode()}.")
        except Exception as e:
            report["errors"].append(f"Could not access URL: {e}")

    @staticmethod
    def _scan_html_file(html_file_path: str, base_path: str, report: Dict[str, Any]):
        try:
            with open(html_file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
        except Exception as e:
            report["warnings"].append(f"Could not parse HTML file: {html_file_path}. Error: {e}")
            return

        tags_and_attrs = {
            "a": "href",
            "link": "href",
            "img": "src",
            "script": "src",
            "source": "src",
        }

        for tag, attr in tags_and_attrs.items():
            for element in soup.find_all(tag):
                if element.has_attr(attr):
                    url = element[attr]
                    if not url or url.startswith(("#", "data:", "http:", "https:", "//")):
                        continue

                    if os.path.isabs(url):
                        report["errors"].append(f"Found absolute path in '{os.path.basename(html_file_path)}': '{url}'. This will not work in the final executable.")
                        continue

                    parsed_url = urllib.parse.urlparse(url)
                    if parsed_url.scheme or parsed_url.netloc:
                        continue # Skip external URLs

                    local_path = os.path.join(os.path.dirname(html_file_path), url)
                    if not os.path.exists(local_path):
                        report["warnings"].append(f"Broken link in '{os.path.basename(html_file_path)}': File not found for '{url}'.")

    @staticmethod
    def apply_recommended_settings(config: AppConfig, settings: Dict[str, Any]):
        """Apply recommended settings to configuration."""
        if settings.get("recommended_onefile") is not None:
            config.build.onefile = settings["recommended_onefile"]

        if settings.get("recommended_console") is not None:
            config.build.console = settings["recommended_console"]

        if settings.get("recommended_debug") is not None:
            config.build.debug = settings["recommended_debug"]

        if settings.get("recommended_upx") is not None:
            config.build.upx_compress = settings["recommended_upx"]

        if settings.get("recommended_offline") is not None:
            config.build.offline_mode = settings["recommended_offline"]
