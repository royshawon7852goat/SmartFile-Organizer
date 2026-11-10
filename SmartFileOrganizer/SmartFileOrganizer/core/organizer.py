"""File Organizer core engine for Smart File Organizer.
Generates preview plans, creates category folders, and safely moves files without overwriting.
"""
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from core.config_manager import config_manager
from core.file_scanner import ScannedFile, file_scanner
from core.history_manager import history_manager
from core.logger import logger
from core.security import get_safe_destination, is_file_locked, is_safe_directory

@dataclass
class OrganizationAction:
    source_path: Path
    filename: str
    category: str
    target_dir: Path
    target_path: Path
    size_bytes: int
    status: str = "pending"  # "pending", "success", "failed", "skipped"
    error_message: Optional[str] = None

@dataclass
class OrganizationResult:
    session_id: Optional[str]
    directory: Path
    scanned_count: int
    moved_count: int
    failed_count: int
    skipped_count: int
    actions: List[OrganizationAction]
    error_summary: List[str]

class FileOrganizer:
    """Core engine responsible for planning and executing file categorization."""

    def __init__(self, history_mgr: Optional[HistoryManager] = None):
        self._history_manager = history_mgr

    @property
    def history_mgr(self) -> HistoryManager:
        return self._history_manager or history_manager

    def preview_organization(
        self,
        directory: Path | str,
        recursive: Optional[bool] = None,
        include_hidden: Optional[bool] = None,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[bool, str, List[OrganizationAction]]:
        """
        Generates a dry-run preview of planned file movements without making disk changes.
        Returns (is_valid, error_reason, list_of_actions).
        """
        dir_path = Path(directory).resolve()
        is_safe, reason = is_safe_directory(dir_path)
        if not is_safe:
            return False, reason, []

        scanned = file_scanner.scan_directory(
            dir_path,
            recursive=recursive,
            include_hidden=include_hidden,
            stop_event=stop_event
        )

        actions: List[OrganizationAction] = []
        for file_info in scanned:
            if stop_event and stop_event.is_set():
                break

            target_category_dir = dir_path / file_info.category

            # Skip if file is already inside target_category_dir
            try:
                if file_info.path.parent.resolve() == target_category_dir.resolve():
                    continue
            except Exception:
                pass

            # Calculate safe destination path (avoiding collision)
            # In preview, we calculate what the destination would be
            safe_dest = get_safe_destination(target_category_dir, file_info.name)

            actions.append(
                OrganizationAction(
                    source_path=file_info.path,
                    filename=file_info.name,
                    category=file_info.category,
                    target_dir=target_category_dir,
                    target_path=safe_dest,
                    size_bytes=file_info.size_bytes
                )
            )

        return True, "", actions

    def execute_organization(
        self,
        directory: Path | str,
        actions: Optional[List[OrganizationAction]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        stop_event: Optional[threading.Event] = None
    ) -> OrganizationResult:
        """
        Executes file movement according to the action plan.
        - Automatically creates target category directories.
        - Preserves original filenames.
        - Renames safely on conflict (never overwrites).
        - Records session in history.json for undo capability.
        """
        dir_path = Path(directory).resolve()
        is_safe, reason = is_safe_directory(dir_path)
        if not is_safe:
            return OrganizationResult(
                session_id=None,
                directory=dir_path,
                scanned_count=0,
                moved_count=0,
                failed_count=0,
                skipped_count=0,
                actions=[],
                error_summary=[reason]
            )

        # If actions list not provided, generate preview first
        if actions is None:
            valid, err, actions = self.preview_organization(dir_path, stop_event=stop_event)
            if not valid:
                return OrganizationResult(
                    session_id=None,
                    directory=dir_path,
                    scanned_count=0,
                    moved_count=0,
                    failed_count=0,
                    skipped_count=0,
                    actions=[],
                    error_summary=[err]
                )

        total_actions = len(actions)
        moved_count = 0
        failed_count = 0
        skipped_count = 0
        error_summary: List[str] = []
        history_records: List[Dict] = []

        logger.info("Executing organization on %s (%d files to move)", dir_path, total_actions)

        # Pre-create category directories
        categories_needed = {action.target_dir for action in actions}
        for target_dir in categories_needed:
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("Failed to create category folder %s: %s", target_dir, e)
                error_summary.append(f"Could not create folder {target_dir.name}: {e}")

        for index, action in enumerate(actions, start=1):
            if stop_event and stop_event.is_set():
                logger.warning("Organization interrupted by user stop signal.")
                break

            if progress_callback:
                progress_callback(index, total_actions, action.filename)

            # Check if source still exists
            if not action.source_path.exists():
                action.status = "skipped"
                action.error_message = "Source file no longer exists."
                skipped_count += 1
                continue

            # Check if source is locked
            if is_file_locked(action.source_path):
                action.status = "failed"
                action.error_message = "File is locked or in use by another application."
                failed_count += 1
                error_summary.append(f"{action.filename}: Locked by another program.")
                continue

            # Calculate safe destination right at execution time to prevent race conditions
            final_target_path = get_safe_destination(action.target_dir, action.filename)
            action.target_path = final_target_path

            try:
                # Perform safe move
                shutil.move(str(action.source_path), str(final_target_path))
                action.status = "success"
                moved_count += 1

                history_records.append({
                    "original_path": str(action.source_path),
                    "new_path": str(final_target_path),
                    "category": action.category,
                    "filename": action.filename,
                    "size_bytes": action.size_bytes,
                    "status": "moved"
                })

            except PermissionError as pe:
                action.status = "failed"
                action.error_message = f"Permission denied: {pe}"
                failed_count += 1
                error_summary.append(f"{action.filename}: Permission denied.")
                logger.error("Permission error moving %s to %s: %s", action.source_path, final_target_path, pe)
            except Exception as e:
                action.status = "failed"
                action.error_message = str(e)
                failed_count += 1
                error_summary.append(f"{action.filename}: {e}")
                logger.error("Error moving %s to %s: %s", action.source_path, final_target_path, e)

        # Record in history if any files were moved
        session_id = None
        if moved_count > 0:
            session_id = self.history_mgr.add_session(
                directory=str(dir_path),
                files_scanned=total_actions,
                files_moved=moved_count,
                files_failed=failed_count,
                records=history_records,
                session_type="organize",
                status="completed"
            )

        # Update last directory in config if remember_directory is true
        if config_manager.get("remember_directory", True):
            config_manager.set("last_directory", str(dir_path))

        logger.info(
            "Organization complete: %d moved, %d failed, %d skipped out of %d.",
            moved_count, failed_count, skipped_count, total_actions
        )

        return OrganizationResult(
            session_id=session_id,
            directory=dir_path,
            scanned_count=total_actions,
            moved_count=moved_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            actions=actions,
            error_summary=error_summary
        )

# Global singleton
file_organizer = FileOrganizer()
