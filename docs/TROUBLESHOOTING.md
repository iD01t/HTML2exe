# Troubleshooting

## WebView2 not installed
If the packaged app fails to launch or shows a blank window on Windows 10/11, install the **Microsoft Edge WebView2 Runtime**:
- System-wide installer: search for “Microsoft Edge WebView2 Runtime” and install the Evergreen Standalone version.

## PyInstaller data files on Windows
Ensure `--add-data` uses a semicolon `;` separator, e.g.:
````

\--add-data "src/html2exe;html2exe"

```

## Antivirus / SmartScreen
Code-signed binaries reduce warnings. On unsigned builds, use “More info → Run anyway” if you trust the source.

## Missing VC++ Redistributables
Some environments require the latest **Microsoft Visual C++ Redistributable**. Install if runtime errors mention missing MSVCRT components.
