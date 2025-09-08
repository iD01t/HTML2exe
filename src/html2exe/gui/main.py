import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import webbrowser
import tempfile
import threading
from datetime import datetime
import subprocess

from ..core.config import AppConfig
from ..core.preflight import PreflightChecker
from ..core.icon_generator import IconGenerator
from ..core.debugger import BulletProofExporter

class ToolTip:
    """Simple tooltip widget for tkinter."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify='left',
                        background="#ffffe0", relief='solid', borderwidth=1,
                        font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def on_leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class ModernGUI:
    """Modern React-style GUI interface."""

    def __init__(self):
        self.root = None
        self.config = AppConfig.load()

    def run(self):
        """Run the modern GUI application."""
        self.root = tk.Tk()
        self.root.title(f"HTML2EXE Pro Premium")
        self.root.geometry("600x400")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(False, False)

        self._setup_styles()
        self._create_main_layout()

        self.root.eval('tk::PlaceWindow . center')
        self.root.mainloop()

    def _setup_styles(self):
        """Setup modern styling."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TFrame', background='#1a1a1a')
        style.configure('Card.TFrame', background='#2d2d2d', relief='raised', borderwidth=1)
        style.configure('Modern.TLabel', background='#1a1a1a', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Title.TLabel', background='#1a1a1a', foreground='#00D4AA', font=('Segoe UI', 16, 'bold'))
        style.configure('Modern.TButton', font=('Segoe UI', 10))
        style.configure('Primary.TButton', font=('Segoe UI', 12, 'bold'), background='#00D4AA', foreground='#1a1a1a')

    def _create_main_layout(self):
        """Create the main simplified layout."""
        main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding=20)
        main_frame.pack(fill='both', expand=True)

        self._create_header(main_frame)

        content_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=20)
        content_frame.pack(fill='both', expand=True, pady=20)

        self._create_simple_form(content_frame)

        self._create_footer(main_frame)

    def _create_header(self, parent):
        """Create modern header."""
        header_frame = ttk.Frame(parent, style='Modern.TFrame')
        header_frame.pack(fill='x')
        title_label = ttk.Label(header_frame, text="HTML2EXE Pro Premium", style='Title.TLabel')
        title_label.pack(anchor='w')
        subtitle_label = ttk.Label(header_frame, text="Convert HTML to professional desktop apps", style='Modern.TLabel')
        subtitle_label.pack(anchor='w')

    def _create_simple_form(self, parent):
        """Create the simplified main form."""
        source_frame = ttk.LabelFrame(parent, text="Source (Folder or URL)", padding=10)
        source_frame.pack(fill='x', pady=10)
        self.source_path_var = tk.StringVar(value=self.config.build.source_path)
        source_entry = ttk.Entry(source_frame, textvariable=self.source_path_var, font=('Consolas', 10))
        source_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(source_frame, text="Browse...", command=self._browse_source).pack(side='right')

        name_frame = ttk.LabelFrame(parent, text="Application Name", padding=10)
        name_frame.pack(fill='x', pady=10)
        self.app_name_var = tk.StringVar(value=self.config.metadata.name)
        name_entry = ttk.Entry(name_frame, textvariable=self.app_name_var, font=('Segoe UI', 10))
        name_entry.pack(fill='x')

    def _create_footer(self, parent):
        """Create footer with build button."""
        footer_frame = ttk.Frame(parent, style='Modern.TFrame')
        footer_frame.pack(fill='x', pady=(20, 0))

        self.build_btn = ttk.Button(footer_frame, text="🚀 BUILD", command=self._start_build, style='Primary.TButton')
        self.build_btn.pack(side='right', fill='x', expand=True)

        ttk.Button(footer_frame, text="Advanced...", command=self._show_advanced).pack(side='left')

    def _sync_config_from_ui(self):
        """Synchronize configuration from UI variables."""
        if hasattr(self, 'source_path_var'):
            self.config.build.source_path = self.source_path_var.get()
            self.config.build.source_type = "url" if self.config.build.source_path.startswith(("http://", "https://")) else "folder"
        if hasattr(self, 'app_name_var'):
            self.config.metadata.name = self.app_name_var.get()

    def _browse_source(self):
        """Browse for source folder or enter URL."""
        folder = filedialog.askdirectory(title="Select HTML Folder")
        if folder:
            self.source_path_var.set(folder)

    def _start_build(self):
        """Start the build process with progress dialog."""
        self._sync_config_from_ui()

        report = PreflightChecker.run_all_checks(self.config.build.source_path, self.config.build.source_type)

        if report["errors"]:
            messagebox.showerror("Pre-flight Check Failed", "\n".join(report["errors"]))
            return

        if report["warnings"]:
            if not messagebox.askyesno("Pre-flight Check Warnings", "\n".join(report["warnings"]) + "\n\nContinue?"):
                return

        progress_dialog = BuildProgressDialog(self.root, self.config)
        progress_dialog.start_build()

    def _show_advanced(self):
        """Show advanced settings dialog."""
        AdvancedDialog(self.root, self.config).show()

class AdvancedDialog:
    """Advanced configuration dialog."""

    def __init__(self, parent, config: AppConfig):
        self.parent = parent
        self.config = config
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Advanced Configuration")
        self.dialog.geometry("700x600")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.transient(self.parent)

        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=20, pady=20)

        self._create_window_tab(notebook)
        self._create_security_tab(notebook)
        self._create_build_tab(notebook)

        button_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=(0, 10))
        button_frame.pack(fill='x', padx=20, pady=(0, 20))

        ttk.Button(button_frame, text="OK", command=self._apply_and_close).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side='right')

    def _create_window_tab(self, notebook):
        frame = ttk.Frame(notebook, style='Modern.TFrame', padding=10)
        notebook.add(frame, text="Window")

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
        opts = [("resizable", "Resizable"), ("fullscreen", "Start Fullscreen"), ("always_on_top", "Always On Top")]
        for field, text in opts:
            var = tk.BooleanVar(value=getattr(self.config.window, field))
            self.window_vars[field] = var
            ttk.Checkbutton(options_frame, text=text, variable=var).pack(anchor='w', pady=2)

    def _create_security_tab(self, notebook):
        frame = ttk.Frame(notebook, style='Modern.TFrame', padding=10)
        notebook.add(frame, text="Security")

        self.security_vars = {}
        opts = [("allow_devtools", "Allow Developer Tools"), ("block_external_urls", "Block External URLs")]
        for field, text in opts:
            var = tk.BooleanVar(value=getattr(self.config.security, field))
            self.security_vars[field] = var
            ttk.Checkbutton(frame, text=text, variable=var).pack(anchor='w', pady=5)

    def _create_build_tab(self, notebook):
        frame = ttk.Frame(notebook, style='Modern.TFrame', padding=10)
        notebook.add(frame, text="Build")

        self.build_vars = {}
        opts = [("onefile", "Single File Executable"), ("console", "Show Console Window"), ("debug", "Debug Mode")]
        for field, text in opts:
            var = tk.BooleanVar(value=getattr(self.config.build, field))
            self.build_vars[field] = var
            ttk.Checkbutton(frame, text=text, variable=var).pack(anchor='w', pady=5)

    def _apply_and_close(self):
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

        self.config.save()
        self.dialog.destroy()

    def show(self):
        self.dialog.grab_set()
        self.dialog.wait_window()

class BuildProgressDialog:
    feature/refactor-and-improve-export
    def __init__(self, parent, config: AppConfig):

    def __init__(self, parent, config: AppConfig, use_bullet_proof: bool = True):
    main
        self.parent = parent
        self.config = config
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Building Application...")
        self.dialog.geometry("600x400")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        title_label = tk.Label(self.dialog, text="🚀 Building Your Application", font=('Segoe UI', 16, 'bold'), fg='#00D4AA', bg='#1a1a1a')
        title_label.pack(pady=(20, 10))

        self.log_text = tk.Text(self.dialog, height=15, wrap='word', font=('Consolas', 9), bg='#2d2d2d', fg='#ffffff')
        self.log_text.pack(fill='both', expand=True, padx=20, pady=20)

    def start_build(self):
        self.build_thread = threading.Thread(target=self._build_worker, daemon=True)
        self.build_thread.start()

    def _build_worker(self):
        def progress_callback(message):
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)

        exporter = BulletProofExporter(self.config)
        exporter.debugger.log = progress_callback
        result = exporter.export_with_auto_debug()

        if result["success"]:
            messagebox.showinfo("Success", f"Build completed successfully!\nOutput: {result['exe_path']}")
        else:
            messagebox.showerror("Build Failed", f"Build failed: {result['error']}")

        self.dialog.destroy()
