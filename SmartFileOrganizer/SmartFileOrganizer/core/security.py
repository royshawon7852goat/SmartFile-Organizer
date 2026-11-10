"""Security, directory validation, and safe file operation utilities.
Ensures the application never modifies system dirs, overwrites files, or causes data loss.
"""
import os
import sys
import ctypes
from pathlib import Path
from typing import Tuple, Optional
from core.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent

# Windows File Attribute Constants
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

def get_protected_directories() -> list[Path]:
    """Returns a list of resolved Path objects for protected Windows system locations."""
    protected: list[Path] = []

    # Windows root / System directories
    for env_var in ["SystemRoot", "windir"]:
        val = os.environ.get(env_var)
        if val:
            protected.append(Path(val).resolve())

    # Program Files
    for env_var in ["ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "CommonProgramFiles", "CommonProgramFiles(x86)"]:
        val = os.environ.get(env_var)
        if val:
            protected.append(Path(val).resolve())

    # ProgramData
    val = os.environ.get("ProgramData")
    if val:
        protected.append(Path(val).resolve())

    # User profile root directory (e.g. C:\Users\Username) - only root itself is protected, subfolders are okay
    val = os.environ.get("USERPROFILE")
    if val:
        protected.append(Path(val).resolve())

    # App own directory
    protected.append(BASE_DIR.resolve())
    protected.append(Path(os.getcwd()).resolve())

    return protected

def is_safe_directory(target_path: Path | str) -> Tuple[bool, str]:
    """
    Validates whether a directory is safe to scan and organize.
    Returns:
        (True, "") if safe.
        (False, error_reason) if unsafe.
    """
    try:
        path = Path(target_path).resolve()
    except Exception as e:
        return False, f"Invalid path format: {e}"

    if not path.exists():
        return False, f"Directory does not exist: {path}"

    if not path.is_dir():
        return False, f"Path is not a directory: {path}"

    # Check root drives (e.g. 'C:\\', 'D:\\')
    if path.parent == path or len(path.parts) <= 1:
        return False, "Organizing the root drive directory (e.g. C:\\) is strictly prohibited."

    # Check app directory
    try:
        if path == BASE_DIR.resolve() or BASE_DIR.resolve() in path.parents:
            return False, "Cannot organize the application's own installation folder."
    except Exception:
        pass

    # Check protected system folders
    protected_dirs = get_protected_directories()
    for protected in protected_dirs:
        try:
            # If path IS the protected directory
            if path == protected:
                if "USERPROFILE" in os.environ and path == Path(os.environ["USERPROFILE"]).resolve():
                    return False, "Organizing the user root profile folder directly is prohibited. Please select a subfolder (such as Downloads, Documents, or Desktop)."
                return False, f"Organizing system directory '{path}' is strictly prohibited."

            # If path is INSIDE a system directory (except user profile which has subfolders)
            user_profile = Path(os.environ.get("USERPROFILE", "")).resolve() if os.environ.get("USERPROFILE") else None
            if protected != user_profile and protected in path.parents:
                return False, f"Directory is located inside protected system location: {protected}"
        except Exception:
            continue

    # Test read & write permissions safely
    try:
        test_file = path / f".sfo_test_perm_{os.getpid()}"
        test_file.touch(exist_ok=True)
        test_file.unlink(missing_ok=True)
    except PermissionError:
        return False, f"Permission denied: Application does not have write access to '{path}'."
    except Exception as e:
        return False, f"Write permission check failed for '{path}': {e}"

    return True, ""

def is_hidden_or_system(file_path: Path) -> bool:
    """Checks if a file or folder is marked as hidden or system."""
    # Dotfiles (Unix-style hidden)
    if file_path.name.startswith("."):
        return True

    # Windows attributes
    if sys.platform == "win32":
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path.resolve()))
            if attrs != -1:
                if (attrs & FILE_ATTRIBUTE_HIDDEN) or (attrs & FILE_ATTRIBUTE_SYSTEM):
                    return True
        except Exception:
            pass

    return False

def get_safe_destination(destination_dir: Path, filename: str) -> Path:
    """
    Generates a unique destination path so that existing files are NEVER overwritten.
    If 'file.txt' exists, returns 'file (1).txt', 'file (2).txt', etc.
    """
    dest_path = destination_dir / filename
    if not dest_path.exists():
        return dest_path

    # Extract stem and extension
    stem = dest_path.stem
    suffix = dest_path.suffix
    counter = 1

    while True:
        candidate_name = f"{stem} ({counter}){suffix}"
        candidate_path = destination_dir / candidate_name
        if not candidate_path.exists():
            return candidate_path
        counter += 1

def is_file_locked(file_path: Path) -> bool:
    """Checks whether a file is locked or currently being written/used by another process."""
    if not file_path.exists():
        return False
    try:
        # Try renaming the file to itself or opening in exclusive append mode
        with open(file_path, "a+b"):
            pass
        return False
    except (IOError, PermissionError, OSError):
        return True
