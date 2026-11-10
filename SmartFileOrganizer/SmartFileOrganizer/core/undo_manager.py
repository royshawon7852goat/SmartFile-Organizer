"""Undo Manager for Smart File Organizer.
Restores moved files to their original directories without overwriting, and cleans up empty folders.
"""
import os
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from core.history_manager import history_manager
from core.logger import logger
from core.security import get_safe_destination, is_file_locked

@dataclass
class UndoResult:
    session_id: str
    restored_count: int
    failed_count: int
    skipped_count: int
    errors: List[str]

class UndoManager:
    """Manages restoring files from previous organization sessions."""

    def __init__(self, history_mgr: Optional[HistoryManager] = None):
        self._history_manager = history_mgr

    @property
    def history_mgr(self) -> HistoryManager:
        return self._history_manager or history_manager

    def can_undo(self) -> bool:
        """Returns True if there is an active session eligible for undo."""
        return self.history_mgr.get_last_organize_session() is not None

    def undo_last_session(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[bool, str, Optional[UndoResult]]:
        """
        Undoes the most recent active organization session.
        Returns (success, message, UndoResult).
        """
        last_session = self.history_mgr.get_last_organize_session()
        if not last_session:
            return False, "No previous organization session available to undo.", None

        return self.undo_session(
            last_session["session_id"],
            progress_callback=progress_callback,
            stop_event=stop_event
        )

    def undo_session(
        self,
        session_id: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[bool, str, Optional[UndoResult]]:
        """
        Restores files from a specific session ID back to their original locations.
        """
        session = self.history_mgr.get_session(session_id)
        if not session:
            return False, f"Session '{session_id}' not found.", None

        records = session.get("records", [])
        active_records = [r for r in records if r.get("status") == "moved"]

        if not active_records:
            return False, "All files from this session have already been undone or were not moved.", None

        total = len(active_records)
        restored_count = 0
        failed_count = 0
        skipped_count = 0
        errors: List[str] = []
        touched_category_dirs = set()

        logger.info("Undoing session %s (%d records to restore)", session_id, total)

        for i, record in enumerate(active_records, start=1):
            if stop_event and stop_event.is_set():
                logger.warning("Undo operation cancelled by user.")
                break

            current_path = Path(record["new_path"])
            original_path = Path(record["original_path"])
            filename = record.get("filename", current_path.name)

            if progress_callback:
                progress_callback(i, total, filename)

            # Check if file exists at its moved location
            if not current_path.exists():
                record["status"] = "failed"
                record["error"] = "File no longer exists at moved location."
                skipped_count += 1
                errors.append(f"{filename}: File missing from {current_path.parent.name}")
                continue

            if is_file_locked(current_path):
                record["status"] = "failed"
                record["error"] = "File is locked."
                failed_count += 1
                errors.append(f"{filename}: File is currently locked.")
                continue

            # Ensure original directory exists
            try:
                original_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to recreate folder {original_path.parent}: {e}")
                continue

            # Determine safe destination at original location (prevent overwriting if another file took its place)
            safe_original_path = get_safe_destination(original_path.parent, original_path.name)

            try:
                touched_category_dirs.add(current_path.parent)
                shutil.move(str(current_path), str(safe_original_path))
                record["status"] = "restored"
                restored_count += 1
            except Exception as e:
                record["status"] = "failed"
                record["error"] = str(e)
                failed_count += 1
                errors.append(f"{filename}: {e}")
                logger.error("Failed to restore %s to %s: %s", current_path, safe_original_path, e)

        # Clean up empty category directories if they contain no files/folders
        for cat_dir in touched_category_dirs:
            try:
                if cat_dir.exists() and not any(cat_dir.iterdir()):
                    cat_dir.rmdir()
                    logger.info("Cleaned up empty directory after undo: %s", cat_dir)
            except Exception as e:
                logger.debug("Did not remove directory %s: %s", cat_dir, e)

        # Update session status
        remaining_moved = any(r.get("status") == "moved" for r in records)
        if remaining_moved:
            session["status"] = "partially_undone"
        else:
            session["status"] = "undone"

        self.history_mgr.update_session(session_id, session)

        result = UndoResult(
            session_id=session_id,
            restored_count=restored_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            errors=errors
        )

        msg = f"Restored {restored_count} files successfully."
        if failed_count > 0 or skipped_count > 0:
            msg += f" ({failed_count} failed, {skipped_count} skipped)"

        logger.info("Undo complete for session %s: %s", session_id, msg)
        return True, msg, result

# Singleton instance
undo_manager = UndoManager()
