"""History Manager for Smart File Organizer.
Maintains persistent audit logs of all organization sessions in data/history.json.
Enables reliable undo operations and provides real data for the dashboard.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"

class HistoryManager:
    """Thread-safe manager for recording and querying organization history."""

    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = history_path or HISTORY_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Initializes empty history file if not present."""
        if not self.history_path.exists():
            self._write_raw({"sessions": []})

    def _read_raw(self) -> Dict[str, Any]:
        """Safely reads the history JSON file."""
        try:
            if self.history_path.exists():
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "sessions" in data:
                        return data
        except Exception as e:
            logger.error("Error reading history file %s: %s", self.history_path, e)
        return {"sessions": []}

    def _write_raw(self, data: Dict[str, Any]) -> bool:
        """Atomically writes data to history JSON file."""
        try:
            temp_path = self.history_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, self.history_path)
            return True
        except Exception as e:
            logger.error("Error writing history file %s: %s", self.history_path, e)
            return False

    def add_session(
        self,
        directory: str,
        files_scanned: int,
        files_moved: int,
        files_failed: int,
        records: List[Dict[str, Any]],
        session_type: str = "organize",
        status: str = "completed"
    ) -> str:
        """
        Records a completed organization or duplicate move session.
        Returns the generated session_id.
        """
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "directory": str(directory),
            "session_type": session_type,  # 'organize' or 'duplicate_move'
            "files_scanned": files_scanned,
            "files_moved": files_moved,
            "files_failed": files_failed,
            "status": status,  # 'completed', 'undone', 'partially_undone'
            "records": records
        }

        data = self._read_raw()
        data["sessions"].insert(0, session)  # newest first
        self._write_raw(data)
        logger.info("Recorded history session %s for directory %s (%d moved)", session_id, directory, files_moved)
        return session_id

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Returns all recorded sessions (newest first)."""
        return self._read_raw().get("sessions", [])

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Finds a session by its unique ID."""
        for session in self.get_all_sessions():
            if session.get("session_id") == session_id:
                return session
        return None

    def get_last_organize_session(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent 'organize' session that can be undone."""
        for session in self.get_all_sessions():
            if session.get("session_type") == "organize" and session.get("status") in ("completed", "partially_undone"):
                # Ensure it has active moved records
                has_active = any(r.get("status") == "moved" for r in session.get("records", []))
                if has_active:
                    return session
        return None

    def update_session(self, session_id: str, updated_session: Dict[str, Any]) -> bool:
        """Updates a specific session in the history file."""
        data = self._read_raw()
        sessions = data.get("sessions", [])
        for i, s in enumerate(sessions):
            if s.get("session_id") == session_id:
                sessions[i] = updated_session
                data["sessions"] = sessions
                return self._write_raw(data)
        return False

    def clear_history(self) -> bool:
        """
        Clears all history records.
        CRITICAL: Never deletes or modifies any user files on disk!
        """
        logger.warning("Clearing application history log (files remain untouched).")
        return self._write_raw({"sessions": []})

    def get_aggregate_statistics(self) -> Dict[str, Any]:
        """
        Calculates real historical statistics for the dashboard.
        """
        sessions = self.get_all_sessions()
        total_scanned = 0
        total_moved = 0
        total_failed = 0
        total_duplicates_detected = 0
        total_bytes_organized = 0
        last_organization_date = None

        category_counts: Dict[str, int] = {}

        for session in sessions:
            if session.get("session_type") == "organize":
                total_scanned += session.get("files_scanned", 0)
                total_moved += session.get("files_moved", 0)
                total_failed += session.get("files_failed", 0)
                if not last_organization_date:
                    last_organization_date = session.get("timestamp")

                for record in session.get("records", []):
                    cat = record.get("category", "Others")
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                    total_bytes_organized += record.get("size_bytes", 0)

            elif session.get("session_type") == "duplicate_move":
                total_duplicates_detected += session.get("files_moved", 0)

        return {
            "total_files_scanned": total_scanned,
            "total_files_organized": total_moved,
            "total_files_failed": total_failed,
            "total_duplicates_detected": total_duplicates_detected,
            "total_bytes_organized": total_bytes_organized,
            "last_organization_date": last_organization_date,
            "category_distribution": category_counts,
            "total_sessions": len(sessions)
        }

# Global singleton
history_manager = HistoryManager()
