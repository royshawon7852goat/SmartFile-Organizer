"""Activity History page for Smart File Organizer.
Displays previous organization and duplicate move sessions with audit inspection and safe undo.
"""
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk

from core.history_manager import history_manager
from core.undo_manager import undo_manager
from gui.components.history_modal import HistoryDetailModal
from gui.components.toast import ConfirmDialog

class HistoryPage(ctk.CTkFrame):
    """Activity History session viewer with inspection and undo controls."""

    def __init__(
        self,
        master,
        on_status_message: Optional[Callable[[str], None]] = None,
        on_history_updated: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_status_message = on_status_message
        self.on_history_updated = on_history_updated

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_sessions_container()

        self.refresh_history()

    def _build_header(self):
        """Top banner with Clear History action."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 16))
        header_frame.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Activity History",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Audit log of all file organization and duplicate quarantine operations.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#64748b", "#94a3b8")
        )
        sub_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        btn_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_box.grid(row=0, column=1, rowspan=2, sticky="e")

        refresh_btn = ctk.CTkButton(
            btn_box,
            text="⟳  Refresh",
            width=90,
            height=34,
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self.refresh_history
        )
        refresh_btn.pack(side="left", padx=(0, 10))

        clear_btn = ctk.CTkButton(
            btn_box,
            text="🗑  Clear History",
            width=120,
            height=34,
            fg_color="#ef4444",
            hover_color="#dc2626",
            text_color="#ffffff",
            command=self._confirm_clear_history
        )
        clear_btn.pack(side="left")

    def _build_sessions_container(self):
        """Scrollable list of past sessions."""
        container = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.scroll_list = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scroll_list.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.scroll_list.grid_columnconfigure(0, weight=1)

    def refresh_history(self):
        """Reloads all sessions from history.json."""
        for w in self.scroll_list.winfo_children():
            w.destroy()

        sessions = history_manager.get_all_sessions()
        if not sessions:
            ctk.CTkLabel(
                self.scroll_list,
                text="No organization history recorded yet.",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=("#94a3b8", "#64748b")
            ).pack(pady=60)
            return

        for idx, session in enumerate(sessions):
            self._render_session_card(session, idx)

    def _render_session_card(self, session: dict, _index: int):
        card = ctk.CTkFrame(
            self.scroll_list,
            fg_color=("#f8fafc", "#242738"),
            corner_radius=10,
            border_width=1,
            border_color=("#e2e8f0", "#2f334a")
        )
        card.pack(fill="x", padx=6, pady=6)
        card.grid_columnconfigure(1, weight=1)

        # Date & Time formatted
        raw_time = session.get("timestamp", "")
        try:
            date_fmt = datetime.fromisoformat(raw_time).strftime("%b %d, %Y  •  %H:%M:%S")
        except Exception:
            date_fmt = raw_time[:19].replace("T", " ")

        stype = session.get("session_type", "organize")
        icon = "📁" if stype == "organize" else "🔍"
        type_badge = "File Organization" if stype == "organize" else "Duplicate Quarantine"

        # Left Info Icon & Timestamp
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=20)).grid(row=0, column=0, rowspan=2, padx=(16, 10), pady=12)

        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="w", pady=(12, 2))

        ctk.CTkLabel(
            title_frame,
            text=f"{type_badge}  —  {date_fmt}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        ).pack(side="left")

        # Status badge
        status = session.get("status", "completed").replace("_", " ").title()
        status_color = "#10b981" if status.lower() == "completed" else "#3b82f6" if "undone" in status.lower() else "#ef4444"
        status_bg = ("#dcfce7", "#133e2b") if status.lower() == "completed" else ("#dbeafe", "#1e305e")
        pill = ctk.CTkLabel(
            title_frame,
            text=f" {status} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=status_color,
            fg_color=status_bg,
            corner_radius=4
        )
        pill.pack(side="left", padx=(10, 0))

        # Folder and stats line
        dir_path = session.get("directory", "")
        moved = session.get("files_moved", 0)
        failed = session.get("files_failed", 0)
        scanned = session.get("files_scanned", 0)

        details_text = f"Target Directory: {dir_path}   |   Scanned: {scanned}   |   Moved: {moved}"
        if failed > 0:
            details_text += f"   |   Failed: {failed}"

        ctk.CTkLabel(
            card,
            text=details_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        ).grid(row=1, column=1, sticky="w", pady=(0, 12))

        # Action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=2, rowspan=2, padx=16, pady=12)

        inspect_btn = ctk.CTkButton(
            btn_frame,
            text="Inspect Files",
            width=100,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color=("#e2e8f0", "#2d3348"),
            hover_color=("#cbd5e1", "#3b4259"),
            text_color=("#1e293b", "#e2e8f0"),
            command=lambda s=session: self._inspect_session(s)
        )
        inspect_btn.pack(side="left", padx=(0, 8))

        # Undo button (only for active organize sessions with moved records)
        has_active_records = any(r.get("status") == "moved" for r in session.get("records", []))
        if stype == "organize" and has_active_records:
            undo_btn = ctk.CTkButton(
                btn_frame,
                text="Undo",
                width=75,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#3b82f6",
                hover_color="#2563eb",
                command=lambda sid=session.get("session_id"): self._undo_session(sid)
            )
            undo_btn.pack(side="left")

    def _inspect_session(self, session: dict):
        HistoryDetailModal(self, session)

    def _undo_session(self, session_id: str):
        ConfirmDialog(
            self,
            title="Undo Organization Session",
            message="Restore files from this specific session back to their original locations?",
            confirm_text="Restore Files",
            cancel_text="Cancel",
            on_confirm=lambda: self._execute_undo_session(session_id)
        )

    def _execute_undo_session(self, session_id: str):
        ok, msg, _res = undo_manager.undo_session(session_id)
        if self.on_status_message:
            self.on_status_message(msg)
        if self.on_history_updated:
            self.on_history_updated()
        self.refresh_history()
        ConfirmDialog(self, title="Undo Results", message=msg, confirm_text="OK", cancel_text="")

    def _confirm_clear_history(self):
        ConfirmDialog(
            self,
            title="Clear Activity History",
            message=(
                "Are you sure you want to clear the entire organization history log?\n\n"
                "SAFEGUARD NOTICE: Clearing history only removes the audit logs from the application. "
                "It will NEVER delete or modify any of your organized files on disk."
            ),
            confirm_text="Clear History",
            cancel_text="Keep History",
            is_destructive=True,
            on_confirm=self._do_clear_history
        )

    def _do_clear_history(self):
        history_manager.clear_history()
        if self.on_status_message:
            self.on_status_message("Activity history cleared successfully.")
        if self.on_history_updated:
            self.on_history_updated()
        self.refresh_history()
