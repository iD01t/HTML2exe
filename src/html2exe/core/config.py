import os
import json
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
import appdirs

APP_NAME = "HTML2EXE Pro Premium"
CONFIG_DIR = appdirs.user_config_dir(APP_NAME)

class WindowConfig(BaseModel):
    """Advanced window configuration."""
    width: int = Field(default=1200, ge=400, le=4096)
    height: int = Field(default=800, ge=300, le=2160)
    min_width: int = Field(default=400, ge=200)
    min_height: int = Field(default=300, ge=200)
    resizable: bool = True
    fullscreen: bool = False
    kiosk: bool = False
    frameless: bool = False
    dpi_aware: bool = True
    always_on_top: bool = False
    center: bool = True
    maximized: bool = False

class SecurityConfig(BaseModel):
    """Enhanced security configuration."""
    csp_enabled: bool = True
    csp_policy: str = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; img-src 'self' data: blob: *;"
    same_origin_only: bool = False
    allow_devtools: bool = True
    block_external_urls: bool = False
    allowed_domains: List[str] = Field(default_factory=list)
    disable_context_menu: bool = False

class AppMetadata(BaseModel):
    """Enhanced application metadata."""
    name: str = "MyHTMLApp"
    version: str = "1.0.0"
    company: str = "My Company"
    copyright: str = Field(default_factory=lambda: f"© {datetime.now().year} My Company")
    description: str = "HTML Desktop Application"
    author: str = "Developer"
    email: str = "developer@company.com"
    website: str = "https://company.com"
    license: str = "Proprietary"

class BuildConfig(BaseModel):
    """Advanced build configuration."""
    source_type: str = Field(default="folder", pattern="^(folder|url)$")
    source_path: str = ""
    output_dir: str = "dist"
    offline_mode: bool = False
    onefile: bool = True
    console: bool = False
    debug: bool = False
    upx_compress: bool = False
    icon_path: str = ""
    splash_screen: str = ""
    custom_protocol: str = ""
    single_instance: bool = True
    tray_menu: bool = True
    auto_start: bool = False
    include_ffmpeg: bool = False
    strip_debug: bool = True

class AdvancedConfig(BaseModel):
    """Advanced features configuration."""
    auto_updater: bool = False
    update_url: str = ""
    deep_links: bool = False
    file_associations: List[str] = Field(default_factory=list)
    startup_sound: str = ""
    theme: str = "auto"  # auto, light, dark

class AppConfig(BaseModel):
    """Complete premium application configuration."""
    metadata: AppMetadata = Field(default_factory=AppMetadata)
    window: WindowConfig = Field(default_factory=WindowConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    build: BuildConfig = Field(default_factory=BuildConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)

    def save(self, path: str = None):
        """Save configuration to file."""
        if path is None:
            path = os.path.join(CONFIG_DIR, "config.json")
        with open(path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load(cls, path: str = None):
        """Load configuration from file."""
        if path is None:
            path = os.path.join(CONFIG_DIR, "config.json")
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                return cls.model_validate(data)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        return cls()
