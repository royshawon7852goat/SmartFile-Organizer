"""Main entry point for Smart File Organizer.
Initializes Windows DPI awareness, logging, and launches the desktop GUI.
"""
import ctypes
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.logger import logger
from gui.app import SmartFileOrganizerApp

def enable_windows_dpi_awareness():
    """Enables Per-Monitor High-DPI awareness on Windows for crisp modern rendering."""
    if sys.platform == "win32":
        try:
            # Per monitor DPI aware (V2)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Fallback to system DPI aware
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

def handle_exception(exc_type, exc_value, exc_traceback):
    """Logs uncaught top-level exceptions instead of crashing silently."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught top-level exception:", exc_info=(exc_type, exc_value, exc_traceback))

def main():
    """Launches the Smart File Organizer GUI application."""
    sys.excepthook = handle_exception
    enable_windows_dpi_awareness()

    logger.info("Starting Smart File Organizer application...")
    try:
        app = SmartFileOrganizerApp()
        app.mainloop()
        logger.info("Smart File Organizer exited cleanly.")
    except Exception as e:
        logger.critical("Fatal crash during main loop execution: %s", e, exc_info=True)
        raise

if __name__ == "__main__":
    main()
