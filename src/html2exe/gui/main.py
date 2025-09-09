import os
import sys
import tempfile
import webbrowser
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime

from ..core.config import AppConfig
from ..core.builder import BuildEngine
from ..core.icon_generator import IconGenerator
from ..core.preflight import run_preflight_checks
from ..core.packager import create_installer
from ..main import APP_NAME, APP_VERSION


class ModernGUI:
    """Modern React-style GUI interface."""

    def __init__(self):
        self.root = None
        self.config = AppConfig.load()
        self.current_step = 0
        self.steps = [
            "Source", "Metadata", "Window", "Security", "Build", "Advanced", "Review"
        ]
        self.step_frames = {}
        self.preview_window = None
        self.theme = 'dark'

    def run(self):
        """Run the modern GUI application."""
        self.root = tk.Tk()
        self.root.withdraw() # Hide root window initially

        # Splash screen
        splash = tk.Toplevel(self.root)
        splash.title(f"{APP_NAME}")
        splash.geometry("500x300")
        splash.configure(bg='#1a1a1a')
        splash.overrideredirect(True) # Frameless

        # Center splash
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 300) // 2
        splash.geometry(f"+{x}+{y}")

        title_frame = tk.Frame(splash, bg='#1a1a1a')
        title_frame.pack(pady=40)
        title_label = tk.Label(title_frame, text="HTML2EXE", font=('Arial', 24, 'bold'), fg='#00D4AA', bg='#1a1a1a')
        title_label.pack()
        subtitle_label = tk.Label(title_frame, text="Pro Premium", font=('Arial', 14), fg='#ffffff', bg='#1a1a1a')
        subtitle_label.pack()
        status_label = tk.Label(splash, text="Loading...", font=('Arial', 11), fg='#cccccc', bg='#1a1a1a')
        status_label.pack(pady=20)
        progress = ttk.Progressbar(splash, length=300, mode='indeterminate')
        progress.pack(pady=10)
        progress.start()

        splash.update()

        self.root.title(f"{APP_NAME} - Premium Edition")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        self._setup_styles()
        self._set_theme()
        self._create_layout()

        splash.destroy()
        self.root.deiconify() # Show root window
        self.root.eval('tk::PlaceWindow . center')
        self.root.mainloop()

    def _setup_styles(self):
        """Setup modern styling."""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Dark theme
        self.style.configure('Dark.TFrame', background='#1a1a1a')
        self.style.configure('Dark.Card.TFrame', background='#2d2d2d', relief='raised', borderwidth=1)
        self.style.configure('Dark.TLabel', background='#1a1a1a', foreground='#ffffff', font=('Segoe UI', 10))
        self.style.configure('Dark.Title.TLabel', background='#1a1a1a', foreground='#00D4AA', font=('Segoe UI', 16, 'bold'))
        self.style.configure('Dark.TButton', font=('Segoe UI', 10))
        self.style.configure('Dark.Primary.TButton', font=('Segoe UI', 10, 'bold'))

        # Light theme
        self.style.configure('Light.TFrame', background='#f0f0f0')
        self.style.configure('Light.Card.TFrame', background='#ffffff', relief='raised', borderwidth=1)
        self.style.configure('Light.TLabel', background='#f0f0f0', foreground='#000000', font=('Segoe UI', 10))
        self.style.configure('Light.Title.TLabel', background='#f0f0f0', foreground='#0078D7', font=('Segoe UI', 16, 'bold'))
        self.style.configure('Light.TButton', font=('Segoe UI', 10))
        self.style.configure('Light.Primary.TButton', font=('Segoe UI', 10, 'bold'))

    def _set_theme(self):
        """Set the current theme."""
        theme_prefix = 'Dark' if self.theme == 'dark' else 'Light'
        self.root.configure(bg=self.style.lookup(f'{theme_prefix}.TFrame', 'background'))
        self.style.configure('Modern.TFrame', background=self.style.lookup(f'{theme_prefix}.TFrame', 'background'))
        self.style.configure('Card.TFrame', background=self.style.lookup(f'{theme_prefix}.Card.TFrame', 'background'), relief='raised', borderwidth=1)
        self.style.configure('Modern.TLabel', background=self.style.lookup(f'{theme_prefix}.TLabel', 'background'), foreground=self.style.lookup(f'{theme_prefix}.TLabel', 'foreground'), font=('Segoe UI', 10))
        self.style.configure('Title.TLabel', background=self.style.lookup(f'{theme_prefix}.Title.TLabel', 'background'), foreground=self.style.lookup(f'{theme_prefix}.Title.TLabel', 'foreground'), font=('Segoe UI', 16, 'bold'))
        self.style.configure('Modern.TButton', font=('Segoe UI', 10))
        self.style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'))

    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self._set_theme()
        self._create_layout()

    def _create_layout(self):
        """Create the main layout."""
        # Destroy existing widgets if they exist
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        self._create_header(main_frame)
        content_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        content_frame.pack(fill='both', expand=True, pady=(20, 0))
        self._create_sidebar(content_frame)
        self._create_main_content(content_frame)
        self._create_footer(main_frame)
        self._show_step(self.current_step)

    def _create_header(self, parent):
        """Create modern header."""
        header_frame = ttk.Frame(parent, style='Modern.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        title_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        title_frame.pack(side='left')
        ttk.Label(title_frame, text="HTML2EXE Pro", style='Title.TLabel').pack(anchor='w')
        ttk.Label(title_frame, text="Premium Edition - Convert HTML to Professional Desktop Apps",
                  style='Modern.TLabel').pack(anchor='w')
        actions_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        actions_frame.pack(side='right')

        theme_btn_text = "☀️" if self.theme == 'dark' else "🌙"
        ttk.Button(actions_frame, text=theme_btn_text, command=self._toggle_theme).pack(side='right', padx=(0, 10))
        ttk.Button(actions_frame, text="Load Config", command=self._load_config).pack(side='right', padx=(0, 10))
        ttk.Button(actions_frame, text="Save Config", command=self._save_config).pack(side='right', padx=(0, 10))
        ttk.Button(actions_frame, text="Preview", command=self._show_preview).pack(side='right', padx=(0, 10))

    def _create_sidebar(self, parent):
        """Create sidebar with step navigation."""
        sidebar_frame = ttk.Frame(parent, style='Card.TFrame')
        sidebar_frame.pack(side='left', fill='y', padx=(0, 20), pady=10)
        sidebar_frame.configure(width=200)
        ttk.Label(sidebar_frame, text="Configuration Steps", style='Title.TLabel').pack(pady=(20, 10))
        self.step_buttons = []
        for i, step in enumerate(self.steps):
            btn_frame = ttk.Frame(sidebar_frame, style='Modern.TFrame')
            btn_frame.pack(fill='x', padx=10, pady=2)
            step_btn = ttk.Button(btn_frame, text=f"{i + 1}. {step}", command=lambda x=i: self._show_step(x))
            step_btn.pack(fill='x')
            self.step_buttons.append(step_btn)
        ttk.Separator(sidebar_frame, orient='horizontal').pack(fill='x', pady=20, padx=10)
        ttk.Label(sidebar_frame, text="Quick Actions", style='Title.TLabel').pack(pady=(0, 10))
        quick_build_btn = ttk.Button(sidebar_frame, text="🚀 Quick Build", command=self._quick_build)
        quick_build_btn.pack(fill='x', padx=10, pady=2)
        Tooltip(quick_build_btn, "Start a build with the current configuration.")

        open_folder_btn = ttk.Button(sidebar_frame, text="📁 Open Folder", command=self._select_folder)
        open_folder_btn.pack(fill='x', padx=10, pady=2)
        Tooltip(open_folder_btn, "Select a local folder as the source.")

        test_url_btn = ttk.Button(sidebar_frame, text="🌐 Test URL", command=self._test_url)
        test_url_btn.pack(fill='x', padx=10, pady=2)
        Tooltip(test_url_btn, "Enter and test a URL as the source.")

        check_system_btn = ttk.Button(sidebar_frame, text="🩺 Check System", command=self._run_system_check)
        check_system_btn.pack(fill='x', padx=10, pady=2)
        Tooltip(check_system_btn, "Check if your system is ready to build.")

        advanced_btn = ttk.Button(sidebar_frame, text="⚙️ Advanced", command=self._show_advanced)
        advanced_btn.pack(fill='x', padx=10, pady=2)
        Tooltip(advanced_btn, "Show advanced settings.")

    def _create_main_content(self, parent):
        """Create main content area."""
        content_frame = ttk.Frame(parent, style='Modern.TFrame')
        content_frame.pack(side='left', fill='both', expand=True)
        self.content_container = ttk.Frame(content_frame, style='Card.TFrame')
        self.content_container.pack(fill='both', expand=True, pady=(0, 10))
        self._create_step_frames()

    def _create_footer(self, parent):
        """Create footer with navigation buttons."""
        footer_frame = ttk.Frame(parent, style='Modern.TFrame')
        footer_frame.pack(fill='x', pady=(20, 0))
        nav_frame = ttk.Frame(footer_frame, style='Modern.TFrame')
        nav_frame.pack(side='right')
        self.prev_btn = ttk.Button(nav_frame, text="← Previous", command=self._prev_step)
        self.prev_btn.pack(side='left', padx=(0, 10))
        self.next_btn = ttk.Button(nav_frame, text="Next →", command=self._next_step)
        self.next_btn.pack(side='left', padx=(0, 10))
        self.build_btn = ttk.Button(nav_frame, text="🚀 BUILD", command=self._start_build, style='Primary.TButton')
        self.build_btn.pack(side='left', padx=(10, 0))
        self.progress_label = ttk.Label(footer_frame, text="Ready to configure", style='Modern.TLabel')
        self.progress_label.pack(side='left')

    def _create_step_frames(self):
        """Create all step configuration frames."""
        self.step_frames[0] = self._create_source_step()
        self.step_frames[1] = self._create_metadata_step()
        self.step_frames[2] = self._create_window_step()
        self.step_frames[3] = self._create_security_step()
        self.step_frames[4] = self._create_build_step()
        self.step_frames[5] = self._create_advanced_step()
        self.step_frames[6] = self._create_review_step()

    def _create_source_step(self):
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        ttk.Label(frame, text="📁 Source Configuration", style='Title.TLabel').pack(pady=(20, 10))
        type_frame = ttk.LabelFrame(frame, text="Source Type", padding=20)
        type_frame.pack(fill='x', padx=20, pady=10)
        self.source_type_var = tk.StringVar(value=self.config.build.source_type)
        ttk.Radiobutton(type_frame, text="📁 Local HTML Folder", variable=self.source_type_var, value="folder",
                        command=self._update_source_type).pack(anchor='w', pady=5)
        ttk.Radiobutton(type_frame, text="🌐 Remote URL", variable=self.source_type_var, value="url",
                        command=self._update_source_type).pack(anchor='w', pady=5)
        path_frame = ttk.LabelFrame(frame, text="Source Path/URL", padding=20)
        path_frame.pack(fill='x', padx=20, pady=10)
        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill='x')
        self.source_path_var = tk.StringVar(value=self.config.build.source_path)
        vcmd = (self.root.register(self._validate_source_path), '%P')
        self.source_path_entry = ttk.Entry(path_input_frame, textvariable=self.source_path_var, font=('Consolas', 10),
                                           validate='focusout', validatecommand=vcmd)
        self.source_path_entry.pack(side='left', fill='x', expand=True)
        Tooltip(self.source_path_entry, "Enter the path to your local HTML folder or a remote URL.")
        self.browse_btn = ttk.Button(path_input_frame, text="Browse...", command=self._browse_source)
        self.browse_btn.pack(side='right', padx=(10, 0))
        offline_frame = ttk.LabelFrame(frame, text="Offline Options", padding=20)
        offline_frame.pack(fill='x', padx=20, pady=10)
        self.offline_var = tk.BooleanVar(value=self.config.build.offline_mode)
        ttk.Checkbutton(offline_frame, text="📱 Package for offline use (cache assets)",
                        variable=self.offline_var).pack(anchor='w')
        return frame

    def _create_metadata_step(self):
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        ttk.Label(frame, text="📋 Application Metadata", style='Title.TLabel').pack(pady=(20, 10))
        canvas = tk.Canvas(frame, bg='#2d2d2d', highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        fields = [("App Name", "name", "MyHTMLApp"), ("Version", "version", "1.0.0"),
                  ("Company", "company", "My Company"), ("Author", "author", "Developer"),
                  ("Email", "email", "developer@company.com"), ("Website", "website", "https://company.com"),
                  ("Description", "description", "HTML Desktop Application"),
                  ("Copyright", "copyright", f"© {datetime.now().year} My Company"),
                  ("License", "license", "Proprietary")]
        self.metadata_vars = {}
        for label_text, field_name, default_value in fields:
            field_frame = ttk.LabelFrame(scrollable_frame, text=label_text, padding=10)
            field_frame.pack(fill='x', pady=5)
            var = tk.StringVar(value=getattr(self.config.metadata, field_name, default_value))
            self.metadata_vars[field_name] = var
            ttk.Entry(field_frame, textvariable=var, font=('Segoe UI', 10)).pack(fill='x')
        return frame

    def _create_window_step(self):
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        ttk.Label(frame, text="🪟 Window Configuration", style='Title.TLabel').pack(pady=(20, 10))
        dims_frame = ttk.LabelFrame(frame, text="Dimensions", padding=20)
        dims_frame.pack(fill='x', padx=20, pady=10)
        dims_grid = ttk.Frame(dims_frame)
        dims_grid.pack(fill='x')
        ttk.Label(dims_grid, text="Width:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.width_var = tk.IntVar(value=self.config.window.width)
        ttk.Spinbox(dims_grid, from_=400, to=4096, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=(0, 20))
        ttk.Label(dims_grid, text="Height:").grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.height_var = tk.IntVar(value=self.config.window.height)
        ttk.Spinbox(dims_grid, from_=300, to=2160, textvariable=self.height_var, width=10).grid(row=0, column=3)
        options_frame = ttk.LabelFrame(frame, text="Window Options", padding=20)
        options_frame.pack(fill='x', padx=20, pady=10)
        self.window_vars = {}
        window_options = [("resizable", "🔄 Resizable", True), ("fullscreen", "🖥️ Start Fullscreen", False),
                          ("kiosk", "🔒 Kiosk Mode", False), ("frameless", "🚫 Frameless", False),
                          ("always_on_top", "📌 Always On Top", False), ("center", "🎯 Center Window", True),
                          ("maximized", "📏 Start Maximized", False)]
        for field_name, label_text, default_value in window_options:
            var = tk.BooleanVar(value=getattr(self.config.window, field_name, default_value))
            self.window_vars[field_name] = var
            ttk.Checkbutton(options_frame, text=label_text, variable=var).pack(anchor='w', pady=2)
        return frame

    def _create_security_step(self):
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        ttk.Label(frame, text="🔒 Security Configuration", style='Title.TLabel').pack(pady=(20, 10))
        security_frame = ttk.LabelFrame(frame, text="Security Options", padding=20)
        security_frame.pack(fill='x', padx=20, pady=10)
        self.security_vars = {}
        security_options = [("csp_enabled", "🛡️ Enable Content Security Policy", True),
                            ("allow_devtools", "🔧 Allow Developer Tools", True),
                            ("block_external_urls", "🚫 Block External URLs", False),
                            ("disable_context_menu", "📝 Disable Context Menu", False)]
        for field_name, label_text, default_value in security_options:
            var = tk.BooleanVar(value=getattr(self.config.security, field_name, default_value))
            self.security_vars[field_name] = var
            ttk.Checkbutton(security_frame, text=label_text, variable=var).pack(anchor='w', pady=2)
        csp_frame = ttk.LabelFrame(frame, text="Content Security Policy", padding=20)
        csp_frame.pack(fill='x', padx=20, pady=10)
        self.csp_var = tk.StringVar(value=self.config.security.csp_policy)
        csp_text = tk.Text(csp_frame, height=4, wrap='word', font=('Consolas', 9))
        csp_text.pack(fill='x')
        csp_text.insert('1.0', self.csp_var.get())
        return frame

    def _create_build_step(self):
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        ttk.Label(frame, text="⚙️ Build Configuration", style='Title.TLabel').pack(pady=(20, 10))
        build_frame = ttk.LabelFrame(frame, text="Build Options", padding=20)
        build_frame.pack(fill='x', padx=20, pady=10)
        self.build_vars = {}
        build_options = [("onefile", "📦 Single File Executable", True),
                         ("console", "💻 Show Console Window", False), ("debug", "🐛 Verbose Logging", False),
                         ("upx_compress", "🗜️ UPX Compression", False),
                         ("single_instance", "👤 Single Instance", True), ("tray_menu", "📱 System Tray", True),
                         ("strip_debug", "✂️ Strip Debug Info", True)]
        for field_name, label_text, default_value in build_options:
            var = tk.BooleanVar(value=getattr(self.config.build, field_name, default_value))
            self.build_vars[field_name] = var
            ttk.Checkbutton(build_frame, text=label_text, variable=var).pack(anchor='w', pady=2)
        icon_frame = ttk.LabelFrame(frame, text="Application Icon", padding=20)
        icon_frame.pack(fill='x', padx=20, pady=10)
        icon_input_frame = ttk.Frame(icon_frame)
        icon_input_frame.pack(fill='x')
        self.icon_path_var = tk.StringVar(value=self.config.build.icon_path)
        ttk.Entry(icon_input_frame, textvariable=self.icon_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(icon_input_frame, text="Browse...", command=self._browse_icon).pack(side='right', padx=(10, 0))
        ttk.Button(icon_input_frame, text="Generate", command=self._generate_icon).pack(side='right', padx=(10, 0))
        return frame

    def _create_advanced_step(self):
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        ttk.Label(frame, text="🚀 Advanced Configuration", style='Title.TLabel').pack(pady=(20, 10))
        advanced_frame = ttk.LabelFrame(frame, text="Premium Features", padding=20)
        advanced_frame.pack(fill='x', padx=20, pady=10)
        self.advanced_vars = {}
        advanced_options = [("auto_updater", "🔄 Auto Updater", False), ("analytics", "📊 Analytics", False),
                            ("crash_reporting", "💥 Crash Reporting", False),
                            ("deep_links", "🔗 Deep Link Support", False)]
        for field_name, label_text, default_value in advanced_options:
            var = tk.BooleanVar(value=getattr(self.config.advanced, field_name, default_value))
            self.advanced_vars[field_name] = var
            ttk.Checkbutton(advanced_frame, text=label_text, variable=var).pack(anchor='w', pady=2)
        protocol_frame = ttk.LabelFrame(frame, text="Custom Protocol", padding=20)
        protocol_frame.pack(fill='x', padx=20, pady=10)
        protocol_input_frame = ttk.Frame(protocol_frame)
        protocol_input_frame.pack(fill='x')
        ttk.Label(protocol_input_frame, text="Protocol:").pack(side='left')
        self.protocol_var = tk.StringVar(value=self.config.build.custom_protocol)
        ttk.Entry(protocol_input_frame, textvariable=self.protocol_var).pack(side='left', fill='x', expand=True,
                                                                              padx=(10, 0))
        ttk.Label(protocol_input_frame, text="://").pack(side='left')
        return frame

    def _create_review_step(self):
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        ttk.Label(frame, text="📋 Configuration Review", style='Title.TLabel').pack(pady=(20, 10))
        review_frame = ttk.LabelFrame(frame, text="Final Configuration", padding=20)
        review_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self.review_text = tk.Text(review_frame, wrap='word', font=('Consolas', 9), bg='#2d2d2d', fg='#ffffff',
                                   insertbackground='#ffffff')
        scrollbar_review = ttk.Scrollbar(review_frame, orient="vertical", command=self.review_text.yview)
        self.review_text.configure(yscrollcommand=scrollbar_review.set)
        self.review_text.pack(side="left", fill="both", expand=True)
        scrollbar_review.pack(side="right", fill="y")
        return frame

    def _show_step(self, step_index):
        for frame in self.step_frames.values():
            frame.pack_forget()
        if step_index in self.step_frames:
            self.step_frames[step_index].pack(fill='both', expand=True)
            self.current_step = step_index
            self.prev_btn.config(state='normal' if step_index > 0 else 'disabled')
            self.next_btn.config(state='normal' if step_index < len(self.steps) - 1 else 'disabled')
            self.progress_label.config(text=f"Step {step_index + 1}/{len(self.steps)}: {self.steps[step_index]}")
            if step_index == len(self.steps) - 1:
                self._update_review()

    def _update_review(self):
        self._sync_config_from_ui()
        review_content = f"""
HTML2EXE Pro Premium - Configuration Review
==========================================
...
        """.strip() # Simplified for brevity
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(1.0, review_content)

    def _next_step(self):
        if self.current_step < len(self.steps) - 1:
            self._sync_config_from_ui()
            self._show_step(self.current_step + 1)

    def _prev_step(self):
        if self.current_step > 0:
            self._sync_config_from_ui()
            self._show_step(self.current_step - 1)

    def _sync_config_from_ui(self):
        # Source
        self.config.build.source_type = self.source_type_var.get()
        self.config.build.source_path = self.source_path_var.get()
        self.config.build.offline_mode = self.offline_var.get()
        # Metadata
        for field, var in self.metadata_vars.items():
            setattr(self.config.metadata, field, var.get())
        # Window
        self.config.window.width = self.width_var.get()
        self.config.window.height = self.height_var.get()
        for field, var in self.window_vars.items():
            setattr(self.config.window, field, var.get())
        # Security
        for field, var in self.security_vars.items():
            setattr(self.config.security, field, var.get())
        # Build
        for field, var in self.build_vars.items():
            setattr(self.config.build, field, var.get())
        self.config.build.icon_path = self.icon_path_var.get()
        # Advanced
        for field, var in self.advanced_vars.items():
            setattr(self.config.advanced, field, var.get())
        self.config.build.custom_protocol = self.protocol_var.get()

    def _browse_source(self):
        if self.source_type_var.get() == "folder":
            folder = filedialog.askdirectory(title="Select HTML Folder")
            if folder:
                self.source_path_var.set(folder)
        else:
            url = simpledialog.askstring("URL Input", "Enter the URL:")
            if url:
                self.source_path_var.set(url)

    def _browse_icon(self):
        icon_file = filedialog.askopenfilename(
            title="Select Application Icon",
            filetypes=[("Icon files", "*.ico"), ("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if icon_file:
            self.icon_path_var.set(icon_file)

    def _generate_icon(self):
        app_name = self.metadata_vars['name'].get() or "App"
        icon_path = os.path.join(tempfile.gettempdir(), f"{app_name.replace(' ', '_')}.ico")
        try:
            IconGenerator.generate_icon(app_name[:2].upper(), icon_path)
            self.icon_path_var.set(icon_path)
            messagebox.showinfo("Success", f"Icon generated successfully!\nSaved to: {icon_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate icon: {e}")

    def _show_preview(self):
        self._sync_config_from_ui()
        if not self.config.build.source_path:
            messagebox.showwarning("Warning", "Please configure a source path/URL first.")
            return
        if self.config.build.source_type == "url":
            webbrowser.open(self.config.build.source_path)
        else:
            # Simplified for now
            messagebox.showinfo("Preview", "Preview for local folders will be implemented.")

    def _quick_build(self):
        """Perform a quick build with sane defaults."""
        self._sync_config_from_ui()
        if not self.config.build.source_path:
            messagebox.showwarning("Quick Build Error", "Please specify a source folder or URL first.")
            return

        # Use a temporary config for quick build
        quick_config = self.config.copy(deep=True)
        quick_config.build.onefile = True
        quick_config.build.console = False
        quick_config.build.debug = False
        quick_config.build.upx_compress = True # Try to make it small

        if not quick_config.build.icon_path or not os.path.exists(quick_config.build.icon_path):
            app_name = quick_config.metadata.name or "App"
            icon_path = os.path.join(tempfile.gettempdir(), f"{app_name.replace(' ', '_')}_quick.ico")
            try:
                IconGenerator.generate_icon(app_name[:2].upper(), icon_path)
                quick_config.build.icon_path = icon_path
            except Exception as e:
                print(f"Could not auto-generate icon: {e}")

        BuildProgressDialog(self.root, quick_config).start_build()

    def _start_build(self):
        self._sync_config_from_ui()
        if not self._validate_config():
            return
        BuildProgressDialog(self.root, self.config).start_build()

    def _validate_config(self) -> bool:
        errors = []
        if not self.config.build.source_path:
            errors.append("Source path/URL is required")
        if self.config.build.source_type == "folder":
            if not os.path.exists(self.config.build.source_path):
                errors.append("Source folder does not exist")
            elif not os.path.exists(os.path.join(self.config.build.source_path, "index.html")):
                errors.append("index.html not found in source folder")
        if not self.config.metadata.name.strip():
            errors.append("Application name is required")
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return False
        return True

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select HTML Folder")
        if folder:
            self.source_type_var.set("folder")
            self.source_path_var.set(folder)
            messagebox.showinfo("Success", f"Source folder set to:\n{folder}")

    def _test_url(self):
        url = simpledialog.askstring("URL Test", "Enter URL to test:")
        if url:
            try:
                import urllib.request
                response = urllib.request.urlopen(url, timeout=10)
                if response.getcode() == 200:
                    self.source_type_var.set("url")
                    self.source_path_var.set(url)
                    messagebox.showinfo("Success", f"URL is accessible!\nSet as source: {url}")
                else:
                    messagebox.showwarning("Warning", f"URL returned status: {response.getcode()}")
            except Exception as e:
                messagebox.showerror("Error", f"URL test failed: {e}")

    def _show_advanced(self):
        AdvancedDialog(self.root, self.config).show()

    def _load_config(self):
        config_file = filedialog.askopenfilename(title="Load Configuration",
                                                 filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if config_file:
            try:
                self.config = AppConfig.load(config_file)
                self._refresh_ui()
                messagebox.showinfo("Success", "Configuration loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")

    def _save_config(self):
        self._sync_config_from_ui()
        config_file = filedialog.asksaveasfilename(title="Save Configuration", defaultextension=".json",
                                                   filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if config_file:
            try:
                self.config.save(config_file)
                messagebox.showinfo("Success", "Configuration saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def _refresh_ui(self):
        # This needs to be implemented to update all UI fields from self.config
        pass

    def _update_source_type(self):
        if self.source_type_var.get() == "folder":
            self.browse_btn.config(text="Browse Folder...")
        else:
            self.browse_btn.config(text="Enter URL...")

    def _run_system_check(self):
        """Run pre-flight checks and show results."""
        self._sync_config_from_ui()
        errors = run_preflight_checks(self.config)
        if errors:
            messagebox.showerror("System Check Failed", "\n".join(errors))
        else:
            messagebox.showinfo("System Check Passed", "Your system is ready to build applications.")

    def _validate_source_path(self, new_value):
        """Validate the source path."""
        if self.source_type_var.get() == "folder":
            if not os.path.exists(new_value):
                self.source_path_entry.config(foreground="red")
                return False
        else: # url
            if not new_value.startswith(("http://", "https://")):
                self.source_path_entry.config(foreground="red")
                return False
        self.source_path_entry.config(foreground="black")
        return True


class Tooltip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None


class BuildProgressDialog:
    """Modern build progress dialog with real-time updates."""

    def __init__(self, parent, config: AppConfig):
        self.parent = parent
        self.config = config
        self.dialog = None
        self.progress_var = None
        self.status_var = None
        self.build_thread = None

    def start_build(self):
        """Start the build process with progress dialog."""
        self._create_dialog()

        self.build_thread = threading.Thread(target=self._build_worker, daemon=True)
        self.build_thread.start()

        self._update_progress()

    def _create_dialog(self):
        """Create modern progress dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Building Application...")
        self.dialog.geometry("600x400")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self.dialog.geometry(f"+{self.parent.winfo_rootx()+50}+{self.parent.winfo_rooty()+50}")

        title_label = tk.Label(self.dialog, text="🚀 Building Your Application",
                              font=('Segoe UI', 16, 'bold'), fg='#00D4AA', bg='#1a1a1a')
        title_label.pack(pady=(20, 10))

        info_label = tk.Label(self.dialog, text=f"Building: {self.config.metadata.name} v{self.config.metadata.version}",
                             font=('Segoe UI', 12), fg='#ffffff', bg='#1a1a1a')
        info_label.pack(pady=(0, 20))

        progress_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        progress_frame.pack(fill='x', padx=40, pady=10)

        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=500, mode='determinate')
        progress_bar.pack(fill='x', pady=(0, 10))

        self.status_var = tk.StringVar(value="Initializing build...")
        status_label = tk.Label(progress_frame, textvariable=self.status_var,
                               font=('Segoe UI', 10), fg='#cccccc', bg='#1a1a1a')
        status_label.pack()

        log_frame = tk.LabelFrame(self.dialog, text="Build Log", font=('Segoe UI', 10), fg='#ffffff', bg='#1a1a1a')
        log_frame.pack(fill='both', expand=True, padx=20, pady=(10, 20))

        self.log_text = tk.Text(log_frame, height=10, wrap='word', font=('Consolas', 9),
                               bg='#2d2d2d', fg='#ffffff', insertbackground='#ffffff')

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        self.cancel_btn = ttk.Button(self.dialog, text="Cancel", command=self._cancel_build)
        self.cancel_btn.pack(pady=(0, 20))

    def _build_worker(self):
        """Worker thread for build process."""
        try:
            def progress_callback(message):
                self.status_var.set(message)
                self._log_message(message)

            engine = BuildEngine(self.config, progress_callback)
            result = engine.build()

            if result["success"]:
                self.progress_var.set(100)
                self.status_var.set("✅ Build completed successfully!")
                self._log_message(f"✅ Build completed in {result['build_time']}")
                self._log_message(f"📁 Output: {result['exe_path']}")
                self._log_message(f"📊 Size: {result['exe_size']}")

                self.dialog.after(100, lambda: self._build_success(result))
            else:
                self.status_var.set("❌ Build failed!")
                self._log_message(f"❌ Build failed: {result['error']}")
                self.dialog.after(100, lambda: self._build_error(result['error']))

        except Exception as e:
            self.status_var.set("❌ Build error!")
            self._log_message(f"❌ Unexpected error: {e}")
            self.dialog.after(100, lambda: self._build_error(str(e)))

    def _log_message(self, message):
        """Add message to build log."""
        if self.log_text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            self.dialog.after(0, lambda: self._append_log(log_entry))

    def _append_log(self, message):
        """Append message to log text widget."""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.dialog.update_idletasks()

    def _update_progress(self):
        """Update progress periodically."""
        if self.build_thread and self.build_thread.is_alive():
            current = self.progress_var.get()
            if current < 90:
                self.progress_var.set(current + 1)
            self.dialog.after(500, self._update_progress)

    def _build_success(self, result):
        """Handle successful build."""
        self.cancel_btn.config(text="Close")

        button_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        button_frame.pack(pady=(10, 0))

        ttk.Button(button_frame, text="📁 Open Folder",
                  command=lambda: self._open_output_folder(result['exe_path'])).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🚀 Run Application",
                  command=lambda: self._run_application(result['exe_path'])).pack(side='left', padx=5)

        installer_btn = ttk.Button(button_frame, text="📦 Create Installer",
                  command=lambda: self._create_installer(self.config, result['exe_path']))
        installer_btn.pack(side='left', padx=5)

        from ..core.preflight import find_iscc
        if not find_iscc():
            installer_btn.config(state='disabled')
            Tooltip(installer_btn, "Inno Setup not found. Please install it to create an installer.")

    def _build_error(self, error):
        """Handle build error."""
        self.cancel_btn.config(text="Close")

        error_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        error_frame.pack(pady=(10, 0))

        ttk.Button(error_frame, text="📋 Copy Error",
                  command=lambda: self._copy_error(error)).pack(side='left', padx=5)
        ttk.Button(error_frame, text="🔧 Troubleshoot",
                  command=lambda: TroubleshootingDialog(self.dialog, error).show()).pack(side='left', padx=5)

    def _open_output_folder(self, exe_path):
        try:
            os.startfile(os.path.dirname(exe_path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def _run_application(self, exe_path):
        try:
            subprocess.Popen([exe_path], shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run application: {e}")

    def _copy_error(self, error):
        try:
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(error)
            messagebox.showinfo("Success", "Error message copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy error: {e}")

    def _create_installer(self, config, exe_path):
        try:
            installer_path = create_installer(config, exe_path)
            messagebox.showinfo("Success", f"Installer created successfully!\nOutput: {installer_path}")
        except Exception as e:
            messagebox.showerror("Installer Error", f"Failed to create installer: {e}")

    def _cancel_build(self):
        """Cancel build or close dialog."""
        if self.build_thread and self.build_thread.is_alive():
            if messagebox.askyesno("Cancel Build", "Are you sure you want to cancel the build? This may not work immediately."):
                # A more robust implementation would be needed to safely terminate the build process
                self.dialog.destroy()
        else:
            self.dialog.destroy()

class AdvancedDialog:
    """Advanced configuration dialog."""

    def __init__(self, parent, config: AppConfig):
        self.parent = parent
        self.config = config
        self.dialog = None

    def show(self):
        """Show advanced configuration dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Advanced Configuration")
        self.dialog.geometry("700x600")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.transient(self.parent)

        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=20, pady=20)

        perf_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(perf_frame, text="Performance")
        self._create_performance_tab(perf_frame)

        integ_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(integ_frame, text="System Integration")
        self._create_integration_tab(integ_frame)

        dev_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(dev_frame, text="Developer")
        self._create_developer_tab(dev_frame)

        button_frame = ttk.Frame(self.dialog, style='Modern.TFrame')
        button_frame.pack(fill='x', padx=20, pady=(0, 20))

        ttk.Button(button_frame, text="OK", command=self.dialog.destroy).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="Apply", command=self._apply_settings).pack(side='right')

    def _create_performance_tab(self, parent):
        mem_frame = ttk.LabelFrame(parent, text="Memory Optimization", padding=15)
        mem_frame.pack(fill='x', pady=10)

        ttk.Checkbutton(mem_frame, text="Enable memory optimization").pack(anchor='w')
        ttk.Checkbutton(mem_frame, text="Preload critical resources").pack(anchor='w')

        startup_frame = ttk.LabelFrame(parent, text="Startup Optimization", padding=15)
        startup_frame.pack(fill='x', pady=10)

        ttk.Checkbutton(startup_frame, text="Fast startup mode").pack(anchor='w')
        ttk.Checkbutton(startup_frame, text="Lazy load modules").pack(anchor='w')

    def _create_integration_tab(self, parent):
        file_frame = ttk.LabelFrame(parent, text="File Associations", padding=15)
        file_frame.pack(fill='x', pady=10)

        ttk.Label(file_frame, text="Associate file extensions (comma-separated):").pack(anchor='w')
        self.file_associations_var = tk.StringVar(value=", ".join(self.config.advanced.file_associations))
        ttk.Entry(file_frame, width=50, textvariable=self.file_associations_var).pack(fill='x', pady=5)

        reg_frame = ttk.LabelFrame(parent, text="Windows Integration", padding=15)
        reg_frame.pack(fill='x', pady=10)

        self.auto_start_var = tk.BooleanVar(value=self.config.build.auto_start)
        ttk.Checkbutton(reg_frame, text="Add to Windows startup", variable=self.auto_start_var).pack(anchor='w')

    def _create_developer_tab(self, parent):
        debug_frame = ttk.LabelFrame(parent, text="Debugging", padding=15)
        debug_frame.pack(fill='x', pady=10)

        self.debug_var = tk.BooleanVar(value=self.config.build.debug)
        ttk.Checkbutton(debug_frame, text="Enable debug console", variable=self.debug_var).pack(anchor='w')

    def _apply_settings(self):
        """Apply advanced settings."""
        self.config.advanced.file_associations = [ext.strip() for ext in self.file_associations_var.get().split(',')]
        self.config.build.auto_start = self.auto_start_var.get()
        self.config.build.debug = self.debug_var.get()
        messagebox.showinfo("Success", "Advanced settings applied.")
        self.dialog.destroy()

class TroubleshootingDialog:
    """Troubleshooting and help dialog."""

    def __init__(self, parent, error_message=""):
        self.parent = parent
        self.error_message = error_message
        self.dialog = None

    def show(self):
        """Show troubleshooting dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Troubleshooting Guide")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg='#1a1a1a')

        text_frame = ttk.Frame(self.dialog)
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)

        text_widget = tk.Text(text_frame, wrap='word', font=('Segoe UI', 10),
                             bg='#2d2d2d', fg='#ffffff')
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add troubleshooting content
        troubleshooting_text = self.get_troubleshooting_text()

        text_widget.insert(1.0, troubleshooting_text)
        text_widget.config(state='disabled')

        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=(0, 20))

    def get_troubleshooting_text(self):
        """Get troubleshooting text, with context-aware suggestions."""

        # Basic troubleshooting text
        base_text = """
HTML2EXE Pro Premium - Troubleshooting Guide
===========================================

COMMON BUILD ISSUES
------------------
1. "ModuleNotFoundError" during build
   - Cause: A required Python package is not included in the build.
   - Solution: Add the missing module to the `hidden_imports` in advanced settings.

2. "Permission denied" error
   - Cause: Antivirus software or system permissions are blocking file access.
   - Solution: Run the application as an administrator. Temporarily disable your antivirus.

3. Large executable size
   - Cause: Large assets or many dependencies.
   - Solution: Enable UPX compression. Use one-dir mode instead of one-file.

4. Slow startup times
   - Cause: One-file mode has to unpack files on every start.
   - Solution: Use one-dir (directory) mode for much faster startup.

5. Missing DLL errors (e.g., VCRUNTIME140.dll)
   - Cause: Missing Microsoft Visual C++ Redistributable.
   - Solution: Install the latest VC++ Redistributable from Microsoft's website.

6. "RecursionError: maximum recursion depth exceeded"
   - Cause: Often happens with complex applications.
   - Solution: Increase Python's recursion limit. This is an advanced fix.

CONFIGURATION ISSUES
-------------------
1. HTML/CSS/JS files not loading
   - Cause: Incorrect source path or files not included in build.
   - Solution: Ensure `index.html` is at the root of your source folder. Check file paths.

2. App appears but is blank or shows an error
   - Cause: JavaScript errors or incorrect paths in your HTML.
   - Solution: Enable the console (`console=True`) to see error messages.

SYSTEM REQUIREMENTS
------------------
- Windows 10 or later (64-bit recommended)
- Python 3.10 or later
- 4GB+ RAM, 2GB+ free disk space
- Internet connection for first run

GETTING HELP
------------
- Check the `build.log` file in your output directory for detailed errors.
- Copy the error and search online.
- Try building a very simple "Hello, World" HTML file to isolate the issue.
"""

        # Context-aware suggestions
        suggestions = "\n\nSPECIFIC SUGGESTIONS FOR YOUR ERROR:\n-------------------------------------\n"
        if "ModuleNotFoundError" in self.error_message:
            suggestions += "- It seems a module was not found. Try adding it to 'hidden imports' in the advanced build settings.\n"
        elif "Permission denied" in self.error_message:
            suggestions += "- A file permission error occurred. Try running this application as an administrator.\n"
        else:
            suggestions += "- No specific suggestions for this error. Check the general guide above.\n"

        return base_text + suggestions
