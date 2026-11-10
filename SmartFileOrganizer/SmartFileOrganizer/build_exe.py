"""Windows Executable Builder for Smart File Organizer using PyInstaller.
Generates a standalone, windowed (no-console) executable with all assets and themes bundled.
"""
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build_executable():
    """Compiles Smart File Organizer into a standalone Windows .exe."""
    print("=" * 60)
    print("Building Smart File Organizer Standalone Executable")
    print("=" * 60)

    # Ensure assets exist
    ico_path = BASE_DIR / "assets" / "icons" / "app_icon.ico"
    if not ico_path.exists():
        print("Generating application icons...")
        from assets.generate_assets import create_app_icon
        create_app_icon()

    # PyInstaller command arguments
    # Note on Windows: data separator is ';'
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconsole",
        "--name=SmartFileOrganizer",
        f"--icon={ico_path}",
        "--add-data=assets;assets",
        "--collect-all=customtkinter",
        "--clean",
        "--noconfirm",
        "main.py"
    ]

    print("\nRunning PyInstaller command:")
    print(" ".join(cmd))
    print("\nCompiling... (this may take a minute)")

    result = subprocess.run(cmd, cwd=str(BASE_DIR))

    if result.returncode == 0:
        exe_path = BASE_DIR / "dist" / "SmartFileOrganizer" / "SmartFileOrganizer.exe"
        onefile_exe = BASE_DIR / "dist" / "SmartFileOrganizer.exe"
        final_path = onefile_exe if onefile_exe.exists() else exe_path
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Executable output: {final_path}")
        print("You can launch SmartFileOrganizer.exe directly without a terminal.")
        print("=" * 60)
    else:
        print("\nBuild failed with exit code:", result.returncode)
        sys.exit(result.returncode)

if __name__ == "__main__":
    build_executable()
