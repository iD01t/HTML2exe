# HTML2exe — Convert HTML to Windows Executables

**Publisher:** iD01t Productions
**Website:** https://id01t.store
**Version:** 1.0.0
**Support:** itechinfomtl@gmail.com

Transform your HTML projects into standalone Windows executables using Edge WebView2. No browser installation required on target machines.

---

## Quick Start (End Users)

1. Download and run: `HTML2exe-Setup-1.0.0.exe`
2. Accept the EULA and install to your preferred directory
3. Launch HTML2exe from Start Menu or desktop shortcut

---

## Usage Examples

### Convert a single HTML file
```cmd
html2exe --input myapp.html --output dist/MyApp.exe
```

### Convert an HTML project folder
```cmd
html2exe --input myproject/ --output dist/MyProject.exe
```

### Check conversion without building
```cmd
html2exe --input myapp.html --output dist/MyApp.exe --check
```

### Using Python module
```cmd
python -m html2exe --input examples/minimal --output dist/Minimal.exe
```

---

## Features

- **Offline Operation**: No internet connection required for generated apps
- **Edge WebView2**: Uses modern web engine built into Windows 10/11
- **Single File**: Creates self-contained EXE files
- **Asset Bundling**: Automatically includes CSS, JS, images, and other resources
- **Fast Startup**: Optimized for quick launch times
- **Error Handling**: Clear error messages and logging

---

## Developer Setup (Windows)

### Prerequisites
- Windows 10/11 with Edge WebView2 Runtime
- Python 3.8+
- Git

### Installation
```powershell
git clone https://github.com/id01t/html2exe.git
cd html2exe
python -m venv .venv
.\.venv\Scripts\Activate.ps1
make install-dev
```

### Development Commands
```powershell
make format      # Format code
make lint        # Check code quality
make typecheck   # Run type checking
make test        # Run test suite
make build       # Build HTML2exe.exe
make dist        # Create installer
make ci          # Run all checks
```

---

## System Requirements

- **OS**: Windows 10 version 1903+ or Windows 11
- **RAM**: 100MB minimum
- **Disk**: 50MB for installation
- **Runtime**: Edge WebView2 (auto-installed if missing)

---

## Support

- **Email**: itechinfomtl@gmail.com
- **Website**: https://id01t.store
- **License**: MIT (see LICENSE.txt)
