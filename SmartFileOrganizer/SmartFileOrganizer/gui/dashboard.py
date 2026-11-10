"""Dashboard page for Smart File Organizer.
Displays real-time statistics cards, category distribution, recent activity, and quick actions.
"""
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional
import customtkinter as ctk

from core.config_manager import config_manager
from core.file_scanner import file_scanner
from core.history_manager import history_manager
from core.undo_manager import undo_manager
from gui.components.stat_card import StatCard

class DashboardPage(ctk.CTkFrame):
    """Modern Windows 11 dashboard with real statistics and quick actions."""

    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None],
        on_folder_changed: Optional[Callable[[str], None]] = None,
        on_request_undo: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_navigate = on_navigate
        self.on_folder_changed = on_folder_changed
        self.on_request_undo = on_request_undo

        self.current_folder: str = config_manager.get("last_directory", "") or config_manager.get("default_directory", "")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Scrollable main canvas
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_stats_grid()
        self._build_quick_actions()
        self._build_middle_row()
        self._build_recent_activity()

        self.refresh_data()

    def _build_header(self):
        """Top greeting and refresh banner."""
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)

        greeting_lbl = ctk.CTkLabel(
            header_frame,
            text="Dashboard Overview",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        greeting_lbl.grid(row=0, column=0, sticky="w")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Real-time workspace statistics, category breakdown, and quick file management.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#64748b", "#94a3b8")
        )
        sub_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Refresh button
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="⟳  Refresh Data",
            width=120,
            height=34,
            corner_radius=8,
            fg_color=("#e2e8f0", "#24283b"),
            hover_color=("#cbd5e1", "#333954"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self.refresh_data
        )
        refresh_btn.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_stats_grid(self):
        """5 Attractive responsive metric cards."""
        grid_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        for col in range(5):
            grid_frame.grid_columnconfigure(col, weight=1, uniform="stat_col")

        self.card_scanned = StatCard(
            grid_frame,
            title="Files Scanned",
            value="0",
            subtext="Across all sessions",
            accent_color="#3b82f6",
            icon_text="📂"
        )
        self.card_scanned.grid(row=0, column=0, sticky="ew", padx=4)

        self.card_organized = StatCard(
            grid_frame,
            title="Files Organized",
            value="0",
            subtext="Successfully categorized",
            accent_color="#10b981",
            icon_text="✅"
        )
        self.card_organized.grid(row=0, column=1, sticky="ew", padx=4)

        self.card_storage = StatCard(
            grid_frame,
            title="Storage Handled",
            value="0 B",
            subtext="Data volume processed",
            accent_color="#8b5cf6",
            icon_text="💾"
        )
        self.card_storage.grid(row=0, column=2, sticky="ew", padx=4)

        self.card_duplicates = StatCard(
            grid_frame,
            title="Duplicates Moved",
            value="0",
            subtext="Quarantined safely",
            accent_color="#f59e0b",
            icon_text="🔍"
        )
        self.card_duplicates.grid(row=0, column=3, sticky="ew", padx=4)

        self.card_last_run = StatCard(
            grid_frame,
            title="Last Organization",
            value="Never",
            subtext="Session history status",
            accent_color="#06b6d4",
            icon_text="🕒"
        )
        self.card_last_run.grid(row=0, column=4, sticky="ew", padx=4)

    def _build_quick_actions(self):
        """Action bar for immediate operations."""
        actions_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        actions_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        actions_frame.grid_columnconfigure(4, weight=1)

        # Title
        title_lbl = ctk.CTkLabel(
            actions_frame,
            text="⚡ QUICK ACTIONS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        )
        title_lbl.grid(row=0, column=0, columnspan=5, sticky="w", padx=18, pady=(12, 8))

        btn1 = ctk.CTkButton(
            actions_frame,
            text="📁  Organize Folder",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=lambda: self.on_navigate("organizer")
        )
        btn1.grid(row=1, column=0, padx=(18, 8), pady=(0, 14))

        btn2 = ctk.CTkButton(
            actions_frame,
            text="🔍  Scan For Duplicates",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
            corner_radius=8,
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=lambda: self.on_navigate("duplicates")
        )
        btn2.grid(row=1, column=1, padx=8, pady=(0, 14))

        self.btn_undo_quick = ctk.CTkButton(
            actions_frame,
            text="↩  Undo Last Action",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
            corner_radius=8,
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self._handle_quick_undo
        )
        self.btn_undo_quick.grid(row=1, column=2, padx=8, pady=(0, 14))

        btn4 = ctk.CTkButton(
            actions_frame,
            text="📜  View History",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
            corner_radius=8,
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=lambda: self.on_navigate("history")
        )
        btn4.grid(row=1, column=3, padx=8, pady=(0, 14))

    def _build_middle_row(self):
        """Selected Folder Card + Category Breakdown."""
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=1)

        # Folder Info Card (Left)
        self.folder_card = ctk.CTkFrame(
            row_frame,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        self.folder_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.folder_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.folder_card,
            text="ACTIVE DIRECTORY STATUS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 6))

        self.folder_path_lbl = ctk.CTkLabel(
            self.folder_card,
            text="No folder selected",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#0f172a", "#f8fafc"),
            anchor="w"
        )
        self.folder_path_lbl.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 10))

        self.folder_details_lbl = ctk.CTkLabel(
            self.folder_card,
            text="Select a directory to inspect and organize its files.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        )
        self.folder_details_lbl.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 16))

        btn_box = ctk.CTkFrame(self.folder_card, fg_color="transparent")
        btn_box.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 16))

        browse_btn = ctk.CTkButton(
            btn_box,
            text="Browse Folder...",
            height=32,
            width=130,
            command=self._browse_folder
        )
        browse_btn.pack(side="left", padx=(0, 10))

        self.btn_open_explorer = ctk.CTkButton(
            btn_box,
            text="Open in Explorer",
            height=32,
            width=130,
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self._open_in_explorer
        )
        self.btn_open_explorer.pack(side="left")

        # Category Breakdown Card (Right)
        self.category_card = ctk.CTkFrame(
            row_frame,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        self.category_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.category_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.category_card,
            text="HISTORICAL CATEGORY DISTRIBUTION",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        self.cat_items_frame = ctk.CTkFrame(self.category_card, fg_color="transparent")
        self.cat_items_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 16))
        self.cat_items_frame.grid_columnconfigure(0, weight=1)

    def _build_recent_activity(self):
        """Recent activity table."""
        self.activity_container = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        self.activity_container.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        self.activity_container.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(self.activity_container, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row,
            text="RECENT ACTIVITY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, sticky="w")

        self.activity_rows_frame = ctk.CTkFrame(self.activity_container, fg_color="transparent")
        self.activity_rows_frame.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))
        self.activity_rows_frame.grid_columnconfigure(0, weight=1)

    def _format_bytes(self, num_bytes: int) -> str:
        b = float(num_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024.0:
                return f"{b:.1f} {unit}" if unit != "B" else f"{int(b)} B"
            b /= 1024.0
        return f"{b:.1f} PB"

    def refresh_data(self):
        """Fetches latest real statistics and updates the dashboard widgets."""
        stats = history_manager.get_aggregate_statistics()

        # Update metric cards
        self.card_scanned.update_value(f"{stats['total_files_scanned']:,}")
        self.card_organized.update_value(f"{stats['total_files_organized']:,}")
        self.card_storage.update_value(self._format_bytes(stats["total_bytes_organized"]))
        self.card_duplicates.update_value(f"{stats['total_duplicates_detected']:,}")

        last_date = stats.get("last_organization_date")
        if last_date:
            try:
                dt = datetime.fromisoformat(last_date)
                self.card_last_run.update_value(dt.strftime("%b %d, %H:%M"), subtext=dt.strftime("%Y"))
            except Exception:
                self.card_last_run.update_value(str(last_date)[:10])
        else:
            self.card_last_run.update_value("Never", subtext="Ready to organize")

        # Update Undo button status
        can_undo = undo_manager.can_undo()
        self.btn_undo_quick.configure(state="normal" if can_undo else "disabled")

        # Update Category Breakdown
        for w in self.cat_items_frame.winfo_children():
            w.destroy()

        cat_dist = stats.get("category_distribution", {})
        total_cat_files = sum(cat_dist.values()) or 1

        cat_colors = {
            "Documents": "#3b82f6",
            "Images": "#10b981",
            "Videos": "#f59e0b",
            "Audio": "#8b5cf6",
            "Archives": "#ec4899",
            "Applications": "#06b6d4",
            "Others": "#64748b"
        }

        if not cat_dist:
            ctk.CTkLabel(
                self.cat_items_frame,
                text="No files organized yet. Run an organization session to view distribution.",
                font=ctk.CTkFont(size=12),
                text_color=("#64748b", "#94a3b8")
            ).pack(anchor="w", pady=10)
        else:
            for cat_name, count in sorted(cat_dist.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_cat_files) * 100
                color = cat_colors.get(cat_name, "#3b82f6")

                item_frame = ctk.CTkFrame(self.cat_items_frame, fg_color="transparent")
                item_frame.pack(fill="x", pady=3)
                item_frame.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    item_frame,
                    text=cat_name,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=100,
                    anchor="w"
                ).grid(row=0, column=0, sticky="w")

                prog = ctk.CTkProgressBar(item_frame, height=8, corner_radius=4, progress_color=color)
                prog.set(count / total_cat_files)
                prog.grid(row=0, column=1, sticky="ew", padx=10)

                ctk.CTkLabel(
                    item_frame,
                    text=f"{count} files ({pct:.1f}%)",
                    font=ctk.CTkFont(size=11),
                    text_color=("#64748b", "#94a3b8"),
                    width=90,
                    anchor="e"
                ).grid(row=0, column=2, sticky="e")

        # Update Active Folder Info
        self._update_folder_info_async()

        # Update Recent Activity
        self._refresh_recent_activity()

    def _update_folder_info_async(self):
        """Scans current folder in background and updates folder card."""
        folder = self.current_folder
        if not folder or not Path(folder).is_dir():
            self.folder_path_lbl.configure(text="No folder selected")
            self.folder_details_lbl.configure(text="Click 'Browse Folder...' to select a directory.")
            self.btn_open_explorer.configure(state="disabled")
            return

        p = Path(folder)
        display_name = p.name if p.name else str(p)
        self.folder_path_lbl.configure(text=display_name)
        self.btn_open_explorer.configure(state="normal")

        def _worker():
            try:
                files = file_scanner.scan_directory(p, recursive=False)
                total_bytes = sum(f.size_bytes for f in files)
                info_text = f"Path: {p}\nFiles: {len(files)} items  |  Storage: {self._format_bytes(total_bytes)}"
                self.after(0, lambda: self.folder_details_lbl.configure(text=info_text))
            except Exception as e:
                self.after(0, lambda: self.folder_details_lbl.configure(text=f"Error inspecting folder: {e}"))

        threading.Thread(target=_worker, daemon=True).start()

    def _refresh_recent_activity(self):
        """Builds recent activity rows."""
        for w in self.activity_rows_frame.winfo_children():
            w.destroy()

        sessions = history_manager.get_all_sessions()[:4]  # Top 4 recent
        if not sessions:
            ctk.CTkLabel(
                self.activity_rows_frame,
                text="No recent organization history found.",
                font=ctk.CTkFont(size=12),
                text_color=("#64748b", "#94a3b8")
            ).pack(anchor="w", pady=10)
            return

        for idx, s in enumerate(sessions):
            bg = ("#f8fafc", "#242738") if idx % 2 == 0 else ("transparent", "transparent")
            row = ctk.CTkFrame(self.activity_rows_frame, fg_color=bg, corner_radius=8, height=44)
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(1, weight=1)

            # Date
            raw_time = s.get("timestamp", "")
            try:
                date_str = datetime.fromisoformat(raw_time).strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = raw_time[:16]

            ctk.CTkLabel(
                row,
                text=date_str,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                width=130,
                anchor="w"
            ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

            # Folder & summary
            folder_name = Path(s.get("directory", "")).name or s.get("directory", "")
            stype = s.get("session_type", "organize").replace("_", " ").title()
            summary = f"{stype} in '{folder_name}' - {s.get('files_moved', 0)} files moved"
            if s.get("files_failed", 0) > 0:
                summary += f" ({s.get('files_failed')} failed)"

            ctk.CTkLabel(
                row,
                text=summary,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                anchor="w"
            ).grid(row=0, column=1, padx=8, pady=10, sticky="w")

            # Status pill
            status = s.get("status", "completed").replace("_", " ").title()
            status_color = "#10b981" if status.lower() == "completed" else "#3b82f6" if "undone" in status.lower() else "#ef4444"
            ctk.CTkLabel(
                row,
                text=status,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=status_color,
                width=110,
                anchor="e"
            ).grid(row=0, column=2, padx=12, pady=10, sticky="e")

    def _browse_folder(self):
        """Opens folder browser."""
        folder = ctk.filedialog.askdirectory(initialdir=self.current_folder or os.getcwd(), title="Select Workspace Folder")
        if folder:
            self.set_current_folder(folder)

    def set_current_folder(self, folder_path: str):
        """Sets current folder and propagates."""
        self.current_folder = folder_path
        if config_manager.get("remember_directory", True):
            config_manager.set("last_directory", folder_path)
        if self.on_folder_changed:
            self.on_folder_changed(folder_path)
        self.refresh_data()

    def _open_in_explorer(self):
        """Opens active directory in Windows File Explorer."""
        if self.current_folder and Path(self.current_folder).exists():
            try:
                os.startfile(self.current_folder)
            except Exception:
                subprocess.Popen(["explorer", self.current_folder])

    def _handle_quick_undo(self):
        """Triggers undo action."""
        if self.on_request_undo:
            self.on_request_undo()
        else:
            undo_manager.undo_last_session()
            self.refresh_data()
