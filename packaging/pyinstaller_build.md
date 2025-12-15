# Aureon PyInstaller Packaging (Windows)

The launcher (`cli/launcher.py`) is bundled as a single-file Windows executable named `aureon.exe` using PyInstaller. The build steps assume you are on Windows with Python 3.11+ and the project dependencies installed.

## Build steps
1. Install build dependencies:
   ```powershell
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. Run PyInstaller with one-file mode and console output:
   ```powershell
   pyinstaller --onefile --name aureon --add-data "config.key;." --hidden-import requests --hidden-import cryptography.cli launcher.spec
   ```
   When a spec file is not present, you can build directly from the launcher entry point:
   ```powershell
   pyinstaller --onefile --name aureon cli\launcher.py --add-data "config.key;." --collect-all cryptography
   ```
3. Copy the resulting `dist\aureon.exe` to your deployment location.

## Post-build smoke test
Execute the smoke test after every build to ensure the binary starts and the dashboard API responds.

```powershell
python packaging\post_build_smoke_test.py --binary .\dist\aureon.exe
```

The smoke test will:
- Invoke `aureon.exe --start --no-dashboard` to confirm the CLI boots.
- Assert the process exits cleanly within the timeout.

## Notes
- The config is encrypted by default; ship the `config.key` alongside `config.json.enc` when migrating between machines.
- Auto-start is opt-in; use `aureon.exe --register-autostart` on Windows to create a scheduled task.
