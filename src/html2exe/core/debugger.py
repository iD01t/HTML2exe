import os
import sys
import importlib
import re
import traceback
from datetime import datetime
from typing import Dict, Any, List

from .config import AppConfig
from .builder import BuildEngine

class ExportDebugger:
    """Comprehensive debugging system for bullet-proof exports."""

    def __init__(self):
        self.debug_log = []
        self.export_attempts = 0
        self.debug_mode = False

    def log(self, message: str, level: str = "INFO"):
        """Log debug information."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.debug_log.append(log_entry)
        if self.debug_mode or level in ["ERROR", "WARNING"]:
            print(log_entry)

    def enable_debug_mode(self):
        """Enable verbose debug logging."""
        self.debug_mode = True
        self.log("Debug mode enabled", "DEBUG")

    def get_debug_report(self) -> str:
        """Get comprehensive debug report."""
        return "\n".join(self.debug_log)

    def save_debug_report(self, path: str):
        """Save debug report to file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"HTML2EXE Pro Premium - Debug Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Export Attempts: {self.export_attempts}\n")
            f.write("=" * 50 + "\n\n")
            f.write(self.get_debug_report())

    def diagnose_export_failure(self, error: Exception, config: 'AppConfig') -> Dict[str, Any]:
        """Diagnose export failure and provide solutions."""
        diagnosis = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "solutions": [],
            "recommendations": [],
            "missing_module": None
        }

        error_msg = str(error).lower()

        # Look for missing module
        match = re.search(r"modulenotfounderror: no module named '([\w\.]+)'", error_msg)
        if match:
            missing_module = match.group(1)
            diagnosis["missing_module"] = missing_module
            diagnosis["recommendations"].append(f"Try adding '{missing_module}' as a hidden import.")

        # Common error patterns and solutions
        if "permission denied" in error_msg or "access denied" in error_msg:
            diagnosis["solutions"].extend([
                "Run as administrator",
                "Check antivirus software settings",
                "Ensure output directory is writable",
                "Close any running instances of the target executable"
            ])

        elif "module not found" in error_msg or "import error" in error_msg:
            diagnosis["solutions"].extend([
                "Install missing dependencies: pip install -r requirements.txt",
                "Check Python environment and virtual environment",
                "Verify all required packages are installed"
            ])

        elif "pyinstaller" in error_msg or "build failed" in error_msg:
            diagnosis["solutions"].extend([
                "Update PyInstaller: pip install --upgrade pyinstaller",
                "Clear PyInstaller cache: pyinstaller --clean",
                "Try directory mode instead of onefile",
                "Check for problematic file names or paths"
            ])

        elif "memory" in error_msg or "out of memory" in error_msg:
            diagnosis["solutions"].extend([
                "Close other applications to free memory",
                "Use directory mode instead of onefile",
                "Disable UPX compression",
                "Reduce window size or remove large assets"
            ])

        elif "disk space" in error_msg or "no space" in error_msg:
            diagnosis["solutions"].extend([
                "Free up disk space (need at least 2GB)",
                "Change output directory to a drive with more space",
                "Clean temporary files and build artifacts"
            ])

        # Configuration-specific recommendations
        if config.build.onefile and len(config.build.source_path) > 100:
            diagnosis["recommendations"].append("Consider using directory mode for large projects")

        if config.build.upx_compress:
            diagnosis["recommendations"].append("Try disabling UPX compression if build fails")

        if not config.build.debug:
            diagnosis["recommendations"].append("Enable debug mode for more detailed error information")

        return diagnosis

class BulletProofExporter:
    """Bullet-proof export system with auto-debug and recovery."""

    def __init__(self, config: 'AppConfig'):
        self.config = config
        self.debugger = ExportDebugger()
        self.export_history = []

    def export_with_auto_debug(self) -> Dict[str, Any]:
        """Export with comprehensive debugging and auto-recovery."""
        self.debugger.log("Starting bullet-proof export process", "INFO")
        self.debugger.export_attempts += 1

        # Pre-export validation and preparation
        validation_result = self._pre_export_validation()
        if not validation_result["success"]:
            return validation_result

        strategies = self._get_export_strategies()

        i = 0
        while i < len(strategies):
            strategy = strategies[i]
            self.debugger.log(f"Trying export strategy {i+1}/{len(strategies)}: {strategy['name']}", "INFO")

            try:
                original_config = self.config.model_copy(deep=True)

                # Apply strategy modifications
                for key, value in strategy.get("modifications", {}).items():
                    setattr(self.config.build, key, value)

                extra_hidden_imports = strategy.get("extra_hidden_imports")

                # Attempt export
                result = self._execute_export(extra_hidden_imports)

                if result["success"]:
                    self.debugger.log(f"Export successful with strategy: {strategy['name']}", "SUCCESS")
                    result["strategy"] = strategy['name']
                    self.export_history.append({
                        "strategy": strategy["name"],
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    return result
                else:
                    self.debugger.log(f"Strategy {strategy['name']} failed: {result['error']}", "WARNING")
                    self.config = original_config

                    # Dynamic strategy based on error
                    diagnosis = self.debugger.diagnose_export_failure(Exception(result["error"]), self.config)
                    if diagnosis.get("missing_module"):
                        missing_module = diagnosis["missing_module"]
                        new_strategy = {
                            "name": f"Add Hidden Import: {missing_module}",
                            "modifications": {},
                            "extra_hidden_imports": [missing_module]
                        }
                        # Avoid adding duplicate strategies
                        if not any(s.get("extra_hidden_imports") == [missing_module] for s in strategies):
                            strategies.insert(i + 1, new_strategy)
                            self.debugger.log(f"Dynamically added new strategy: {new_strategy['name']}", "INFO")

            except Exception as e:
                self.debugger.log(f"Strategy {strategy['name']} failed with exception: {e}", "ERROR")
                self.config = original_config

            i += 1

        return self._generate_failure_report()

    def _pre_export_validation(self) -> Dict[str, Any]:
        """Comprehensive pre-export validation."""
        self.debugger.log("Running pre-export validation", "DEBUG")

        validation_checks = [
            self._check_system_requirements,
            self._check_source_validity,
            self._check_dependencies,
            self._check_disk_space,
            self._check_permissions,
            self._check_configuration
        ]

        for check in validation_checks:
            try:
                result = check()
                if not result["success"]:
                    self.debugger.log(f"Validation failed: {result['error']}", "ERROR")
                    return result
            except Exception as e:
                self.debugger.log(f"Validation check failed: {e}", "ERROR")
                return {"success": False, "error": f"Validation error: {e}"}

        self.debugger.log("Pre-export validation passed", "SUCCESS")
        return {"success": True}

    def _check_system_requirements(self) -> Dict[str, Any]:
        """Check system requirements."""
        if sys.version_info < (3, 8):
            return {"success": False, "error": "Python 3.8+ required"}
        try:
            import psutil
            available_memory = psutil.virtual_memory().available / (1024**3)
            if available_memory < 0.5:
                return {"success": False, "error": "Insufficient memory (need at least 500MB)"}
        except ImportError:
            pass
        return {"success": True}

    def _check_source_validity(self) -> Dict[str, Any]:
        """Check source validity."""
        if not self.config.build.source_path:
            return {"success": False, "error": "Source path not specified"}
        if self.config.build.source_type == "folder":
            if not os.path.exists(self.config.build.source_path):
                return {"success": False, "error": f"Source folder not found: {self.config.build.source_path}"}
            if not os.path.exists(os.path.join(self.config.build.source_path, "index.html")):
                self.debugger.log("No index.html found, will generate default", "WARNING")
        return {"success": True}

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check required dependencies."""
        required_modules = ["typer", "rich", "pydantic", "flask", "PyInstaller"]
        missing = [m for m in required_modules if not importlib.util.find_spec(m)]
        if missing:
            return {"success": False, "error": f"Missing dependencies: {', '.join(missing)}"}
        return {"success": True}

    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import shutil
            free_space = shutil.disk_usage(self.config.build.output_dir).free
            if free_space < 2 * 1024 * 1024 * 1024:
                return {"success": False, "error": f"Insufficient disk space. Need 2GB, have {free_space//(1024**3)}GB"}
        except:
            pass
        return {"success": True}

    def _check_permissions(self) -> Dict[str, Any]:
        """Check write permissions."""
        try:
            os.makedirs(self.config.build.output_dir, exist_ok=True)
            test_file = os.path.join(self.config.build.output_dir, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            return {"success": False, "error": f"No write permission to output directory: {e}"}
        return {"success": True}

    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity."""
        if not self.config.metadata.name.strip():
            return {"success": False, "error": "Application name is required"}
        invalid_chars = '<>:"/\\|?*'
        if any(char in self.config.metadata.name for char in invalid_chars):
            return {"success": False, "error": f"Application name contains invalid characters: {invalid_chars}"}
        return {"success": True}

    def _get_export_strategies(self) -> List[Dict[str, Any]]:
        """Get ordered list of export strategies to try."""
        return [
            {"name": "Standard Export", "modifications": {}},
            {"name": "Directory Mode", "modifications": {"onefile": False}},
            {"name": "No UPX Compression", "modifications": {"upx_compress": False}},
            {"name": "Debug Mode", "modifications": {"debug": True, "console": True}},
            {"name": "Minimal Configuration", "modifications": {"onefile": False, "upx_compress": False, "strip_debug": False, "debug": True}}
        ]

    def _execute_export(self, extra_hidden_imports: List[str] = None) -> Dict[str, Any]:
        """Execute the actual export."""
        try:
            engine = BuildEngine(self.config, self.debugger.log)
            return engine.build(extra_hidden_imports=extra_hidden_imports)
        except Exception as e:
            self.debugger.log(f"Export execution failed with exception: {e}\n{traceback.format_exc()}", "ERROR")
            return {"success": False, "error": str(e)}

    def _generate_failure_report(self) -> Dict[str, Any]:
        """Generate comprehensive failure report."""
        self.debugger.log("All export strategies failed, generating failure report", "ERROR")
        os.makedirs(self.config.build.output_dir, exist_ok=True)
        debug_report_path = os.path.join(self.config.build.output_dir, "debug_report.txt")
        self.debugger.save_debug_report(debug_report_path)
        return {
            "success": False, "error": "All export strategies failed",
            "debug_report": debug_report_path, "export_attempts": self.debugger.export_attempts,
            "strategies_tried": len(self.export_history),
            "recommendations": [
                "Check the debug report for detailed error information",
                "Try running as administrator",
                "Ensure all dependencies are installed",
                "Check antivirus software settings",
                "Try a different output directory",
                "Contact support with the debug report"
            ]
        }
