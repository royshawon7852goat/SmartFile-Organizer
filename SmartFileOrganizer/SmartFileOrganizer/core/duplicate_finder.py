"""Duplicate Finder module for Smart File Organizer.
Identifies identical files using chunked SHA-256 hashing without loading full files into memory.
Supports moving duplicates safely to a user review folder. Never deletes automatically.
"""
import hashlib
import os
import shutil
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from core.config_manager import config_manager
from core.file_scanner import ScannedFile, file_scanner
from core.history_manager import history_manager
from core.logger import logger
from core.security import get_safe_destination, is_file_locked, is_safe_directory

CHUNK_SIZE = 64 * 1024  # 64 KB chunks for memory efficiency

@dataclass
class DuplicateGroup:
    group_id: str
    sha256_hash: str
    file_size: int
    files: List[ScannedFile]

    @property
    def formatted_size(self) -> str:
        bytes_val = float(self.file_size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"

    @property
    def wasted_storage_bytes(self) -> int:
        """Total storage wasted by duplicates (excluding 1 original copy)."""
        return max(0, (len(self.files) - 1) * self.file_size)

    @property
    def formatted_wasted_storage(self) -> str:
        bytes_val = float(self.wasted_storage_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"

class DuplicateFinder:
    """Finds duplicates via two-pass size & chunked SHA-256 hashing."""

    def __init__(self, history_mgr: Optional[HistoryManager] = None):
        self._history_manager = history_mgr

    @property
    def history_mgr(self) -> HistoryManager:
        return self._history_manager or history_manager

    @staticmethod
    def calculate_sha256(file_path: Path, stop_event: Optional[threading.Event] = None) -> Optional[str]:
        """Calculates SHA-256 hash of a file in 64KB blocks."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    if stop_event and stop_event.is_set():
                        return None
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, FileNotFoundError, OSError) as e:
            logger.warning("Could not hash file %s: %s", file_path, e)
            return None

    def scan_duplicates(
        self,
        directory: Path | str,
        recursive: bool = True,
        include_hidden: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[bool, str, List[DuplicateGroup]]:
        """
        Scans directory for duplicate files.
        Pass 1: Group files by byte size.
        Pass 2: Compute SHA-256 hash only for files that share identical sizes.
        Returns: (is_valid, error_reason, list_of_duplicate_groups)
        """
        dir_path = Path(directory).resolve()
        is_safe, reason = is_safe_directory(dir_path)
        if not is_safe:
            return False, reason, []

        logger.info("Starting duplicate scan in %s (recursive=%s)", dir_path, recursive)

        # Step 1: Scan files
        scanned_files = file_scanner.scan_directory(
            dir_path,
            recursive=recursive,
            include_hidden=include_hidden,
            stop_event=stop_event
        )

        if stop_event and stop_event.is_set():
            return True, "Scan cancelled", []

        # Step 2: Group by file size
        size_groups: Dict[int, List[ScannedFile]] = defaultdict(list)
        for f in scanned_files:
            size_groups[f.size_bytes].append(f)

        # Candidates are groups with > 1 file and size > 0
        candidate_files: List[ScannedFile] = []
        for size, files in size_groups.items():
            if len(files) > 1 and size > 0:
                candidate_files.extend(files)

        total_candidates = len(candidate_files)
        logger.info("Found %d candidate files sharing sizes out of %d total scanned.", total_candidates, len(scanned_files))

        if total_candidates == 0:
            return True, "", []

        # Step 3: Compute SHA-256 hashes for candidates
        hash_groups: Dict[str, List[ScannedFile]] = defaultdict(list)
        processed = 0

        for file_info in candidate_files:
            if stop_event and stop_event.is_set():
                logger.info("Duplicate scan hashing cancelled by user.")
                break

            processed += 1
            if progress_callback:
                progress_callback(processed, total_candidates, file_info.name)

            file_hash = self.calculate_sha256(file_info.path, stop_event=stop_event)
            if file_hash:
                hash_groups[file_hash].append(file_info)

        # Step 4: Build duplicate groups (only where count >= 2)
        duplicate_groups: List[DuplicateGroup] = []
        group_counter = 1

        for h, files in hash_groups.items():
            if len(files) >= 2:
                # Sort files by creation/modification time
                files.sort(key=lambda x: x.modified_time)
                duplicate_groups.append(
                    DuplicateGroup(
                        group_id=f"GRP-{group_counter:03d}",
                        sha256_hash=h,
                        file_size=files[0].size_bytes,
                        files=files
                    )
                )
                group_counter += 1

        # Sort groups by wasted storage descending
        duplicate_groups.sort(key=lambda g: g.wasted_storage_bytes, reverse=True)

        logger.info("Duplicate scan finished. Found %d duplicate groups.", len(duplicate_groups))
        return True, "", duplicate_groups

    def move_selected_duplicates(
        self,
        base_dir: Path | str,
        files_to_move: List[Path],
        custom_review_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[int, int, List[str], Path]:
        """
        Moves selected duplicate files to a safe review directory.
        CRITICAL: Never deletes duplicate files!
        Returns (moved_count, failed_count, error_messages, review_folder_path).
        """
        base = Path(base_dir).resolve()
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        if custom_review_dir:
            review_dir = Path(custom_review_dir).resolve()
        else:
            review_dir = base / f"Duplicate_Review_{timestamp_str}"

        try:
            review_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create duplicate review directory %s: %s", review_dir, e)
            return 0, len(files_to_move), [f"Failed to create review folder: {e}"], review_dir

        total = len(files_to_move)
        moved_count = 0
        failed_count = 0
        errors: List[str] = []
        history_records: List[Dict] = []

        logger.info("Moving %d duplicates to review folder: %s", total, review_dir)

        for i, file_path in enumerate(files_to_move, start=1):
            if stop_event and stop_event.is_set():
                break

            if progress_callback:
                progress_callback(i, total, file_path.name)

            if not file_path.exists():
                failed_count += 1
                errors.append(f"{file_path.name}: File not found.")
                continue

            if is_file_locked(file_path):
                failed_count += 1
                errors.append(f"{file_path.name}: File is locked by another program.")
                continue

            # Target safe destination
            safe_dest = get_safe_destination(review_dir, file_path.name)

            try:
                size_bytes = file_path.stat().st_size
                shutil.move(str(file_path), str(safe_dest))
                moved_count += 1

                history_records.append({
                    "original_path": str(file_path),
                    "new_path": str(safe_dest),
                    "category": "Duplicate",
                    "filename": file_path.name,
                    "size_bytes": size_bytes,
                    "status": "moved"
                })
            except Exception as e:
                failed_count += 1
                errors.append(f"{file_path.name}: {e}")
                logger.error("Error moving duplicate %s: %s", file_path, e)

        if moved_count > 0:
            self.history_mgr.add_session(
                directory=str(base),
                files_scanned=total,
                files_moved=moved_count,
                files_failed=failed_count,
                records=history_records,
                session_type="duplicate_move",
                status="completed"
            )

        return moved_count, failed_count, errors, review_dir

# Singleton instance
duplicate_finder = DuplicateFinder()
