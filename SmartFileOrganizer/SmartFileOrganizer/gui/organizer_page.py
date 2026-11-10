"""Organize Files page for Smart File Organizer.
Provides interactive folder selection, category previews, safe file movement, and progress tracking.
"""
import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, List, Optional
import customtkinter as ctk

from core.config_manager import config_manager
from core.file_scanner import file_scanner
from core.organizer import FileOrganizer, OrganizationAction, file_organizer
from core.security import is_safe_directory
from core.undo_manager import undo_manager
from gui.components.preview_modal import PreviewModal
from gui.components.toast import ConfirmDialog

class OrganizerPage(ctk.CTkFrame):
    """Modern file organizer interface with dry-run preview and safe execution."""

    def __init__(
        self,
        master,
        on_status_message: Optional[Callable[[str], None]] = None,
        on_folder_changed: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_status_message = on_status_message
        self.on_folder_changed = on_folder_changed

        self.current_folder: str = config_manager.get("last_directory", "") or config_manager.get("default_directory", "")
        self.planned_actions: List[OrganizationAction] = []
        self.is_processing = False
        self.stop_event = threading.Event()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Table / content expands

        self._build_top_controls()
        self._build_category_summary()
        self._build_action_bar()
        self._build_preview_table()
        self._build_progress_bar()

        if self.current_folder:
            self.set_folder(self.current_folder)

    def _build_top_controls(self):
        """Folder selection bar and scan options."""
        top_frame = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        top_frame.grid_columnconfigure(1, weight=1)

        # Title row
        title_lbl = ctk.CTkLabel(
            top_frame,
            text="TARGET DIRECTORY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        )
        title_lbl.grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(12, 6))

        # Folder icon
        ctk.CTkLabel(top_frame, text="📁", font=ctk.CTkFont(size=18)).grid(row=1, column=0, padx=(16, 8), pady=(0, 14))

        # Folder path entry
        self.folder_var = ctk.StringVar(value=self.current_folder)
        self.folder_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text="Enter or browse directory path to organize...",
            height=38
        )
        self.folder_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 14))

        # Browse button
        self.browse_btn = ctk.CTkButton(
            top_frame,
            text="Browse...",
            width=100,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self._browse_folder
        )
        self.browse_btn.grid(row=1, column=2, padx=(0, 8), pady=(0, 14))

        # Open in explorer button
        self.explorer_btn = ctk.CTkButton(
            top_frame,
            text="Open Folder",
            width=105,
            height=38,
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self._open_in_explorer
        )
        self.explorer_btn.grid(row=1, column=3, padx=(0, 16), pady=(0, 14))

        # Options check row
        opts_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        opts_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 12))

        self.recursive_var = ctk.BooleanVar(value=config_manager.get("recursive", False))
        self.chk_recursive = ctk.CTkCheckBox(
            opts_frame,
            text="Include subdirectories (Recursive)",
            variable=self.recursive_var,
            font=ctk.CTkFont(size=12)
        )
        self.chk_recursive.pack(side="left", padx=(0, 20))

        self.hidden_var = ctk.BooleanVar(value=config_manager.get("include_hidden", False))
        self.chk_hidden = ctk.CTkCheckBox(
            opts_frame,
            text="Include hidden and system files",
            variable=self.hidden_var,
            font=ctk.CTkFont(size=12)
        )
        self.chk_hidden.pack(side="left")

    def _build_category_summary(self):
        """Displays category summary count chips."""
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        for i in range(7):
            self.summary_frame.grid_columnconfigure(i, weight=1, uniform="cat_col")

        self.category_badges: dict[str, ctk.CTkFrame] = {}
        categories = ["Documents", "Images", "Videos", "Audio", "Archives", "Applications", "Others"]
        icons = ["📄", "🖼️", "🎬", "🎵", "📦", "⚙️", "📁"]

        for idx, (cat, icon) in enumerate(zip(categories, icons)):
            box = ctk.CTkFrame(
                self.summary_frame,
                fg_color=("#ffffff", "#1e1e2c"),
                corner_radius=10,
                border_width=1,
                border_color=("#e2e8f0", "#2d3348"),
                height=56
            )
            box.grid(row=0, column=idx, sticky="ew", padx=4)
            box.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(box, text=icon, font=ctk.CTkFont(size=16)).grid(row=0, column=0, rowspan=2, padx=(10, 6), pady=8)
            ctk.CTkLabel(
                box,
                text=cat,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=("#64748b", "#94a3b8")
            ).grid(row=0, column=1, sticky="w", pady=(6, 0))

            cnt_lbl = ctk.CTkLabel(
                box,
                text="0",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("#0f172a", "#f8fafc")
            )
            cnt_lbl.grid(row=1, column=1, sticky="w", pady=(0, 6))

            box.cnt_lbl = cnt_lbl
            self.category_badges[cat] = box

    def _build_action_bar(self):
        """Action triggers: Scan/Preview, Organize, Undo, Stop."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        bar.grid_columnconfigure(4, weight=1)

        self.btn_preview = ctk.CTkButton(
            bar,
            text="🔍  Scan & Preview",
            height=38,
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self.start_preview_scan
        )
        self.btn_preview.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.btn_organize = ctk.CTkButton(
            bar,
            text="⚡  Organize Now",
            height=38,
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.prompt_and_execute
        )
        self.btn_organize.grid(row=0, column=1, padx=(0, 10), sticky="w")

        self.btn_undo = ctk.CTkButton(
            bar,
            text="↩  Undo Last",
            height=38,
            width=130,
            font=ctk.CTkFont(size=13),
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self._handle_undo
        )
        self.btn_undo.grid(row=0, column=2, padx=(0, 10), sticky="w")

        self.btn_stop = ctk.CTkButton(
            bar,
            text="⏹  Cancel",
            height=38,
            width=100,
            font=ctk.CTkFont(size=13),
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self._stop_processing,
            state="disabled"
        )
        self.btn_stop.grid(row=0, column=3, sticky="w")

        self.status_lbl = ctk.CTkLabel(
            bar,
            text="Ready. Select folder and click 'Scan & Preview' to inspect files.",
            font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"),
            anchor="e"
        )
        self.status_lbl.grid(row=0, column=4, sticky="e", padx=(10, 0))

    def _build_preview_table(self):
        """Scrollable table showing files planned for organization."""
        table_container = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        table_container.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(1, weight=1)

        # Header Row
        col_header = ctk.CTkFrame(table_container, fg_color=("#f1f5f9", "#272a3d"), height=36, corner_radius=6)
        col_header.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        col_header.grid_columnconfigure(0, weight=4)  # Filename
        col_header.grid_columnconfigure(1, weight=2)  # Category
        col_header.grid_columnconfigure(2, weight=2)  # Size
        col_header.grid_columnconfigure(3, weight=4)  # Target Destination
        col_header.grid_columnconfigure(4, weight=2)  # Status

        ctk.CTkLabel(col_header, text="SOURCE FILE", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=0, sticky="w", padx=12)
        ctk.CTkLabel(col_header, text="CATEGORY", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(col_header, text="SIZE", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=2, sticky="w", padx=8)
        ctk.CTkLabel(col_header, text="TARGET DESTINATION", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=3, sticky="w", padx=8)
        ctk.CTkLabel(col_header, text="STATUS", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=4, sticky="w", padx=12)

        # Scrollable rows frame
        self.scroll_table = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll_table.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
        self.scroll_table.grid_columnconfigure(0, weight=4)
        self.scroll_table.grid_columnconfigure(1, weight=2)
        self.scroll_table.grid_columnconfigure(2, weight=2)
        self.scroll_table.grid_columnconfigure(3, weight=4)
        self.scroll_table.grid_columnconfigure(4, weight=2)

        self._show_empty_table_message("No files scanned. Choose a directory above to preview.")

    def _build_progress_bar(self):
        """Bottom progress indicator."""
        prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        prog_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 16))
        prog_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=8, corner_radius=4)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self.prog_text_lbl = ctk.CTkLabel(
            prog_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        )
        self.prog_text_lbl.grid(row=1, column=0, sticky="w")

    def _format_size(self, size_bytes: int) -> str:
        b = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if b < 1024.0:
                return f"{b:.1f} {unit}" if unit != "B" else f"{int(b)} B"
            b /= 1024.0
        return f"{b:.1f} TB"

    def _show_empty_table_message(self, message: str):
        for w in self.scroll_table.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll_table,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#94a3b8", "#64748b")
        ).grid(row=0, column=0, columnspan=5, pady=40)

    def _browse_folder(self):
        folder = ctk.filedialog.askdirectory(initialdir=self.folder_var.get() or os.getcwd(), title="Select Target Directory")
        if folder:
            self.set_folder(folder)

    def set_folder(self, folder_path: str):
        self.current_folder = folder_path
        self.folder_var.set(folder_path)
        if config_manager.get("remember_directory", True):
            config_manager.set("last_directory", folder_path)
        if self.on_folder_changed:
            self.on_folder_changed(folder_path)

        # Trigger quick preview
        self.start_preview_scan()

    def _open_in_explorer(self):
        folder = self.folder_var.get().strip()
        if folder and Path(folder).exists():
            try:
                os.startfile(folder)
            except Exception:
                subprocess.Popen(["explorer", folder])

    def _stop_processing(self):
        self.stop_event.set()
        self.btn_stop.configure(state="disabled")
        self.status_lbl.configure(text="Cancelling operation...")

    def start_preview_scan(self):
        """Scans the selected directory and renders preview in a non-blocking thread."""
        target_dir = self.folder_var.get().strip()
        if not target_dir:
            self.status_lbl.configure(text="Please select a folder first.")
            return

        is_safe, reason = is_safe_directory(target_dir)
        if not is_safe:
            self.status_lbl.configure(text=f"Directory error: {reason}")
            ConfirmDialog(self, title="Invalid Directory", message=reason, confirm_text="OK", cancel_text="")
            return

        self._set_ui_state(processing=True)
        self.stop_event.clear()
        self.progress_bar.set(0)
        self.status_lbl.configure(text="Scanning directory...")

        def _worker():
            try:
                valid, err, actions = file_organizer.preview_organization(
                    target_dir,
                    recursive=self.recursive_var.get(),
                    include_hidden=self.hidden_var.get(),
                    stop_event=self.stop_event
                )
                self.after(0, lambda: self._on_preview_finished(valid, err, actions))
            except Exception as e:
                self.after(0, lambda: self._on_preview_finished(False, str(e), []))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_preview_finished(self, valid: bool, err_msg: str, actions: List[OrganizationAction]):
        self._set_ui_state(processing=False)
        self.planned_actions = actions

        if not valid:
            self.status_lbl.configure(text=f"Scan failed: {err_msg}")
            self._show_empty_table_message(f"Error: {err_msg}")
            return

        # Update category badges
        cat_counts = {cat: 0 for cat in self.category_badges}
        for a in actions:
            cat_counts[a.category] = cat_counts.get(a.category, 0) + 1

        for cat, box in self.category_badges.items():
            cnt = cat_counts.get(cat, 0)
            box.cnt_lbl.configure(text=str(cnt))

        # Render preview rows
        for w in self.scroll_table.winfo_children():
            w.destroy()

        if not actions:
            self._show_empty_table_message("No unorganized files found in this directory.")
            self.status_lbl.configure(text="Folder is already clean or contains no eligible files.")
            self.btn_organize.configure(state="disabled")
            return

        self.btn_organize.configure(state="normal")
        self.status_lbl.configure(text=f"Found {len(actions)} files ready to organize.")

        for idx, action in enumerate(actions):
            bg = ("#f8fafc", "#232334") if idx % 2 == 0 else ("transparent", "transparent")
            row = ctk.CTkFrame(self.scroll_table, fg_color=bg, corner_radius=6, height=32)
            row.grid(row=idx, column=0, columnspan=5, sticky="ew", pady=1)
            row.grid_columnconfigure(0, weight=4)
            row.grid_columnconfigure(1, weight=2)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=4)
            row.grid_columnconfigure(4, weight=2)

            # Name
            ctk.CTkLabel(
                row,
                text=action.filename,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=12, pady=4)

            # Category
            ctk.CTkLabel(
                row,
                text=action.category,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                width=80,
                height=22,
                corner_radius=6,
                fg_color=("#e0e7ff", "#2b3050"),
                text_color=("#3730a3", "#a5b4fc")
            ).grid(row=0, column=1, sticky="w", padx=8, pady=4)

            # Size
            ctk.CTkLabel(
                row,
                text=self._format_size(action.size_bytes),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            ).grid(row=0, column=2, sticky="w", padx=8, pady=4)

            # Target Destination
            dest_text = f"{action.target_dir.name}/{action.target_path.name}"
            ctk.CTkLabel(
                row,
                text=dest_text,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#3b82f6", "#60a5fa"),
                anchor="w"
            ).grid(row=0, column=3, sticky="w", padx=8, pady=4)

            # Status
            status_lbl = ctk.CTkLabel(
                row,
                text="Pending",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            )
            status_lbl.grid(row=0, column=4, sticky="w", padx=12, pady=4)
            action.row_widget = status_lbl

    def prompt_and_execute(self):
        """Prompts user if confirmation is enabled, then executes organization."""
        if not self.planned_actions:
            self.start_preview_scan()
            return

        ask_before = config_manager.get("ask_before_organize", True)
        if ask_before:
            PreviewModal(
                self,
                actions=self.planned_actions,
                on_proceed=self._execute_organization
            )
        else:
            self._execute_organization()

    def _execute_organization(self):
        """Runs the file organization in background thread."""
        target_dir = self.folder_var.get().strip()
        self._set_ui_state(processing=True)
        self.stop_event.clear()
        self.progress_bar.set(0)
        self.status_lbl.configure(text="Organizing files...")

        def _progress(idx, total, filename):
            pct = idx / max(1, total)
            self.after(0, lambda: self._update_progress_ui(pct, f"Moving ({idx}/{total}): {filename}"))

        def _worker():
            try:
                result = file_organizer.execute_organization(
                    target_dir,
                    actions=self.planned_actions,
                    progress_callback=_progress,
                    stop_event=self.stop_event
                )
                self.after(0, lambda: self._on_organization_finished(result))
            except Exception as e:
                self.after(0, lambda: self.status_lbl.configure(text=f"Error executing organization: {e}"))
                self.after(0, lambda: self._set_ui_state(processing=False))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_progress_ui(self, pct: float, msg: str):
        self.progress_bar.set(pct)
        self.prog_text_lbl.configure(text=msg)

    def _on_organization_finished(self, result):
        self._set_ui_state(processing=False)
        self.progress_bar.set(1.0)

        # Update rows status
        for action in self.planned_actions:
            lbl = getattr(action, "row_widget", None)
            if lbl:
                if action.status == "success":
                    lbl.configure(text="Moved", text_color="#10b981")
                elif action.status == "failed":
                    lbl.configure(text="Failed", text_color="#ef4444")
                elif action.status == "skipped":
                    lbl.configure(text="Skipped", text_color="#f59e0b")

        summary_msg = f"Done: {result.moved_count} moved, {result.failed_count} failed."
        self.status_lbl.configure(text=summary_msg)
        self.prog_text_lbl.configure(text=summary_msg)

        if self.on_status_message:
            self.on_status_message(summary_msg)

        # Enable undo
        self.btn_undo.configure(state="normal")

        # Show notification dialog
        ConfirmDialog(
            self,
            title="Organization Complete",
            message=f"Successfully organized {result.moved_count} files into categorized folders.\nFailed: {result.failed_count}\nSkipped: {result.skipped_count}",
            confirm_text="Great",
            cancel_text=""
        )

    def _handle_undo(self):
        """Undoes last organization session."""
        if not undo_manager.can_undo():
            self.status_lbl.configure(text="No active session to undo.")
            return

        ConfirmDialog(
            self,
            title="Undo Organization",
            message="Restore organized files back to their original locations?",
            confirm_text="Restore Files",
            cancel_text="Cancel",
            on_confirm=self._do_undo
        )

    def _do_undo(self):
        self._set_ui_state(processing=True)
        self.status_lbl.configure(text="Restoring files...")

        def _worker():
            ok, msg, res = undo_manager.undo_last_session()
            self.after(0, lambda: self._on_undo_finished(ok, msg, res))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_undo_finished(self, ok: bool, msg: str, _res):
        self._set_ui_state(processing=False)
        self.status_lbl.configure(text=msg)
        self.btn_undo.configure(state="normal" if undo_manager.can_undo() else "disabled")
        ConfirmDialog(self, title="Undo Results", message=msg, confirm_text="OK", cancel_text="")
        # Refresh preview
        self.start_preview_scan()

    def _set_ui_state(self, processing: bool):
        self.is_processing = processing
        state = "disabled" if processing else "normal"
        self.btn_preview.configure(state=state)
        self.btn_organize.configure(state=state)
        self.browse_btn.configure(state=state)
        self.folder_entry.configure(state=state)
        self.btn_stop.configure(state="normal" if processing else "disabled")
