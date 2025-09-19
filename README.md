# HTML2exe

Convert HTML projects into **stand-alone Windows executables** powered by Microsoft Edge **WebView2**—with a professional NSIS installer, a typed Python package, and full CI/test coverage.&#x20;

## ✨ Features

* **One-click conversion** from a single HTML file or a folder with `index.html`.&#x20;
* **Modern rendering** via Edge WebView2 for HTML5/CSS3/JS compatibility.&#x20;
* **Offline by design**: no telemetry or network access during conversion or runtime.&#x20;
* **Single-file EXE output** (PyInstaller `--onefile`).&#x20;
* **Professional Windows installer (NSIS)** with Start Menu integration and clean uninstall.&#x20;
* **Dev-friendly CLI** with validation, `--check` dry-run, and `--verbose` logging.&#x20;

## 🧰 System requirements

* Windows 10 (1903+) or Windows 11 and Edge WebView2 Runtime.&#x20;
* Python 3.8+ for developers using the CLI.&#x20;

---

## 🚀 Quick start (CLI)

Create an EXE from an HTML file or a folder containing `index.html`:

```bash
html2exe --input myapp.html --output dist/MyApp.exe
```

Dry-run with extra logs (no build performed):

```bash
html2exe --input examples/demo.html --output dist/Demo.exe --check --verbose
```

These commands mirror the examples in the Windows build script and CI smoke steps. &#x20;

### CLI options

* `--input, -i` (file or directory with `index.html`) – **required**
* `--output, -o` (target `.exe` path) – **required**
* `--title, -t` (window title; defaults to input name)
* `--width` (default: 1024), `--height` (default: 768)
* `--check` (validate & show what would be built)
* `--verbose` (enable verbose logging)
* `--version` (prints `HTML2exe 1.0.0`)&#x20;

---

## 🧱 How it works (high level)

1. **Validate & prepare assets**

   * For a single HTML file, it becomes `index.html`; related assets in common folders (e.g., `css`, `js`, `images`, `assets`) are bundled. For a directory, contents are copied as-is.&#x20;

2. **Generate a viewer**

   * A small `pywebview` script is created to load the packaged assets. On runtime, it extracts bundled resources from the PyInstaller temp dir (`_MEIPASS`). &#x20;

3. **Build with PyInstaller**

   * Single-file, windowed EXE; assets are added with the **Windows semicolon** path separator in `--add-data`.&#x20;

---

## 🛠️ Developer setup

Install in editable mode with dev extras and run the test suite:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -v
```

These steps are the same used in the CI pipeline.&#x20;

### Make targets

* `make format` / `make lint` / `make typecheck` / `make test`
* `make build` → builds `dist/HTML2exe.exe`
* `make dist` → builds the NSIS installer `dist/HTML2exe-Setup-1.0.0.exe`&#x20;

> **Windows tip:** When calling PyInstaller directly, ensure `--add-data` uses `;` (semicolon) on Windows:
> `--add-data "src/html2exe;html_assets"`. The project’s builder already does this correctly.&#x20;

---

## 🧪 Tests & quality

* **Unit & smoke tests** cover CLI parsing, asset prep, viewer generation, and a dry-run end-to-end flow. Run `pytest -v`.  &#x20;
* **Pre-commit hooks**, **ruff**, **mypy** are enabled; CI runs across Python 3.8–3.12, uploads artifacts, and can report coverage to Codecov.&#x20;

---

## 📦 Building on a fresh Windows VM

The repository includes a copy-paste **PowerShell** sequence to set up Python/NSIS, run checks, create a demo `examples\demo.html`, build the EXE, and produce the installer—plus a silent installer test. See “Build & Release Commands (Windows, fresh VM)”. &#x20;

Key outputs:

* `dist\HTML2exe.exe` (application)
* `dist\HTML2exe-Setup-1.0.0.exe` (installer)&#x20;

---

## 🧩 NSIS installer

* Creates Start Menu shortcuts, writes proper Add/Remove Programs metadata, and launches the app from the finish page. Uninstall removes all components.&#x20;

---

## 🗂️ Project structure (excerpt)

```
src/html2exe/
  __init__.py          # __version__ = "1.0.0", author/email, exports
  __main__.py          # python -m html2exe entry
  cli.py               # CLI parsing & validation
  builder.py           # assets prep, viewer generation, PyInstaller
  viewer.py            # test viewer wrapper for dev
  logging_utils.py     # logging setup
  config.py            # simple TOML config, ~/.html2exe/config.toml
  py.typed             # PEP 561 marker
tests/                 # unit + e2e smoke tests
installer/             # NSIS script + EULA
.github/workflows/     # Windows CI building EXE + installer
```

See sources for details: init/version & exports, CLI arguments, builder PyInstaller command, and config location.   &#x20;

---

## ⚙️ Configuration

A simple TOML config can live at:

```
%UserProfile%\.html2exe\config.toml
```

Default keys include window width/height and a `build.debug` flag; values are retrieved via dot-notation (e.g., `window.width`).&#x20;

---

## 🔍 Troubleshooting

* **WebView2 missing**: install the **Evergreen** WebView2 Runtime if the app window fails to appear. (The viewer code expects WebView2 to be present.)&#x20;
* **PyInstaller data on Windows**: ensure `--add-data` uses `;` (semicolon). The project’s builder uses `f"{assets_dir};html_assets"`.&#x20;
* **Antivirus warnings**: unsigned EXEs may trigger SmartScreen; signing is supported in CI via optional secrets.&#x20;

---

## 🔐 Privacy

**No data collection.** HTML2exe operates entirely offline with no telemetry or usage tracking. &#x20;

---

## 📄 License

MIT © 2024 iD01t Productions. See `LICENSE.txt`.&#x20;

---

## 🗓️ Changelog

See `CHANGELOG.md` for the **1.0.0** release notes.&#x20;

---

## 💬 Support

* Email: [itechinfomtl@gmail.com](mailto:itechinfomtl@gmail.com)
* Website: [https://id01t.store](https://id01t.store)&#x20;

---

## 🙌 Credits

Built by **iD01t Productions** with love for developers who ship desktop-friendly web apps. Initial release includes CLI, typed API, full tests, CI, and an NSIS installer.&#x20;

---

### Appendix: Example (generate and test a demo app)

```powershell
# From repo root on Windows
mkdir examples
@'
<!DOCTYPE html>
<html>
<head>
  <title>HTML2exe Example</title>
</head>
<body>
  <h1>HTML2exe Works!</h1>
  <script>setTimeout(()=>alert('Welcome to HTML2exe!'), 1000);</script>
</body>
</html>
'@ | Out-File -FilePath "examples\demo.html" -Encoding UTF8

html2exe --input examples\demo.html --output dist\Demo.exe --check --verbose
make build
make dist
```

