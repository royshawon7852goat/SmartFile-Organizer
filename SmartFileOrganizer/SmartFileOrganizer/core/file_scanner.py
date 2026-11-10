"""File scanner module for Smart File Organizer.
Safely scans directories, extracts file metadata, and prevents recursive organization loops.
"""
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Set
from core.config_manager import config_manager
from core.logger import logger
from core.security import is_hidden_or_system

@dataclass
class ScannedFile:
    path: Path
    name: str
    ext: str
    size_bytes: int
    category: str
    modified_time: datetime

    @property
    def formatted_size(self) -> str:
        """Returns human-readable file size (e.g. 1.25 MB)."""
        bytes_val = float(self.size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"

    @property
    def formatted_date(self) -> str:
        return self.modified_time.strftime("%Y-%m-%d %H:%M:%S")

class FileScanner:
    """Provides methods for safe directory scanning with progress updates and cancellation."""

    def __init__(self):
        pass

    def scan_directory(
        self,
        directory_path: Path | str,
        recursive: Optional[bool] = None,
        include_hidden: Optional[bool] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        stop_event: Optional[threading.Event] = None
    ) -> List[ScannedFile]:
        """
        Scans files within directory_path.
        - Ignores existing category destination folders to avoid recursive organization loops.
        - Respects include_hidden and recursive settings.
        - Invokes progress_callback(processed_count, current_filename) if provided.
        - Halts if stop_event.is_set().
        """
        root = Path(directory_path).resolve()
        if not root.is_dir():
            logger.warning("Target scan path is not a valid directory: %s", root)
            return []

        if recursive is None:
            recursive = config_manager.get("recursive", False)
        if include_hidden is None:
            include_hidden = config_manager.get("include_hidden", False)

        # Standard category folder names to exclude from top-level scanning
        configured_categories = config_manager.get_all_categories()
        protected_category_folder_names: Set[str] = {cat.lower() for cat in configured_categories.keys()}
        protected_category_folder_names.add("duplicate_review")

        scanned_files: List[ScannedFile] = []
        count = 0

        logger.info("Starting scan of %s (recursive=%s, include_hidden=%s)", root, recursive, include_hidden)

        try:
            if not recursive:
                # Top-level scan only (standard mode)
                try:
                    entries = list(os.scandir(root))
                except PermissionError as e:
                    logger.error("Permission error accessing directory %s: %e", root, e)
                    return []

                for entry in entries:
                    if stop_event and stop_event.is_set():
                        logger.info("File scan stopped by user.")
                        break

                    # Skip directories
                    if entry.is_dir(follow_symlinks=False):
                        continue

                    entry_path = Path(entry.path)

                    # Check hidden/system
                    if not include_hidden and is_hidden_or_system(entry_path):
                        continue

                    try:
                        stat = entry.stat(follow_symlinks=False)
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue

                    category = config_manager.get_category_for_ext(entry_path.suffix)
                    scanned_files.append(
                        ScannedFile(
                            path=entry_path,
                            name=entry_path.name,
                            ext=entry_path.suffix.lower(),
                            size_bytes=size,
                            category=category,
                            modified_time=mtime
                        )
                    )
                    count += 1
                    if progress_callback:
                        progress_callback(count, entry_path.name)

            else:
                # Recursive scan
                for dirpath_str, dirnames, filenames in os.walk(root, topdown=True):
                    if stop_event and stop_event.is_set():
                        logger.info("File scan stopped by user.")
                        break

                    current_dir = Path(dirpath_str)

                    # Filter out category folders if they are immediate children of root
                    if current_dir == root:
                        dirnames[:] = [d for d in dirnames if d.lower() not in protected_category_folder_names]

                    # Filter out hidden directories
                    if not include_hidden:
                        dirnames[:] = [d for d in dirnames if not is_hidden_or_system(current_dir / d)]

                    for filename in filenames:
                        if stop_event and stop_event.is_set():
                            break

                        file_path = current_dir / filename

                        if not include_hidden and is_hidden_or_system(file_path):
                            continue

                        try:
                            stat = file_path.stat()
                            size = stat.st_size
                            mtime = datetime.fromtimestamp(stat.st_mtime)
                        except (PermissionError, FileNotFoundError, OSError):
                            continue

                        category = config_manager.get_category_for_ext(file_path.suffix)
                        scanned_files.append(
                            ScannedFile(
                                path=file_path,
                                name=filename,
                                ext=file_path.suffix.lower(),
                                size_bytes=size,
                                category=category,
                                modified_time=mtime
                            )
                        )
                        count += 1
                        if progress_callback:
                            progress_callback(count, filename)

        except Exception as e:
            logger.error("Unexpected error during file scan of %s: %s", root, e, exc_info=True)

        logger.info("Scan completed: Found %d files in %s", len(scanned_files), root)
        return scanned_files

# Singleton instance
file_scanner = FileScanner()
