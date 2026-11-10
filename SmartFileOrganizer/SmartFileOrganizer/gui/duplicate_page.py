"""Duplicate Finder page for Smart File Organizer.
Finds duplicate files via chunked SHA-256 hashing, groups them visually, and safely moves them to a review folder.
"""
import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional
import customtkinter as ctk

from core.config_manager import config_manager
from core.duplicate_finder import DuplicateFinder, DuplicateGroup, duplicate_finder
from core.security import is_safe_directory
from gui.components.toast import ConfirmDialog

class DuplicatePage(ctk.CTkFrame):
    """Modern duplicate detection and quarantine interface."""

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
        self.duplicate_groups: List[DuplicateGroup] = []
        self.file_checkboxes: Dict[str, ctk.BooleanVar] = {}  # file_path_str -> BooleanVar
        self.is_scanning = False
        self.stop_event = threading.Event()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Results area expands

        self._build_top_controls()
        self._build_action_bar()
        self._build_selection_bar()
        self._build_results_area()
        self._build_progress_bar()

    def _build_top_controls(self):
        """Folder selection bar and options."""
        top_frame = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top_frame,
            text="DUPLICATE DETECTION DIRECTORY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(12, 6))

        ctk.CTkLabel(top_frame, text="🔍", font=ctk.CTkFont(size=18)).grid(row=1, column=0, padx=(16, 8), pady=(0, 14))

        self.folder_var = ctk.StringVar(value=self.current_folder)
        self.folder_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text="Enter or browse folder to scan for duplicates...",
            height=38
        )
        self.folder_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 14))

        self.browse_btn = ctk.CTkButton(
            top_frame,
            text="Browse...",
            width=100,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self._browse_folder
        )
        self.browse_btn.grid(row=1, column=2, padx=(0, 8), pady=(0, 14))

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

        # Checkboxes
        opts_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        opts_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 12))

        self.recursive_var = ctk.BooleanVar(value=True)  # True by default for finding dupes across subdirs
        self.chk_recursive = ctk.CTkCheckBox(
            opts_frame,
            text="Scan subdirectories (Recursive)",
            variable=self.recursive_var,
            font=ctk.CTkFont(size=12)
        )
        self.chk_recursive.pack(side="left", padx=(0, 20))

        self.hidden_var = ctk.BooleanVar(value=False)
        self.chk_hidden = ctk.CTkCheckBox(
            opts_frame,
            text="Include hidden files",
            variable=self.hidden_var,
            font=ctk.CTkFont(size=12)
        )
        self.chk_hidden.pack(side="left")

    def _build_action_bar(self):
        """Action triggers: Scan, Move Selected, Stop."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        bar.grid_columnconfigure(3, weight=1)

        self.btn_scan = ctk.CTkButton(
            bar,
            text="🔍  Scan For Duplicates",
            height=38,
            width=180,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.start_duplicate_scan
        )
        self.btn_scan.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.btn_move_review = ctk.CTkButton(
            bar,
            text="📦  Move to Review Folder",
            height=38,
            width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#f59e0b",
            hover_color="#d97706",
            command=self._prompt_and_move_duplicates,
            state="disabled"
        )
        self.btn_move_review.grid(row=0, column=1, padx=(0, 10), sticky="w")

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
        self.btn_stop.grid(row=0, column=2, padx=(0, 10), sticky="w")

        self.summary_stats_lbl = ctk.CTkLabel(
            bar,
            text="Click 'Scan For Duplicates' to analyze files using SHA-256.",
            font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"),
            anchor="e"
        )
        self.summary_stats_lbl.grid(row=0, column=3, sticky="e")

    def _build_selection_bar(self):
        """Selection helpers (Keep first, newest, oldest, none)."""
        sel_frame = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=8,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348"),
            height=40
        )
        sel_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            sel_frame,
            text="SELECT DUPLICATES:",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).pack(side="left", padx=(14, 10))

        self.btn_sel_keep_first = ctk.CTkButton(
            sel_frame,
            text="Keep First Copy",
            height=28,
            width=120,
            font=ctk.CTkFont(size=11),
            fg_color=("#f1f5f9", "#272a3d"),
            hover_color=("#e2e8f0", "#33374d"),
            text_color=("#1e293b", "#e2e8f0"),
            command=lambda: self._select_by_rule("keep_first")
        )
        self.btn_sel_keep_first.pack(side="left", padx=4)

        self.btn_sel_keep_newest = ctk.CTkButton(
            sel_frame,
            text="Keep Newest",
            height=28,
            width=110,
            font=ctk.CTkFont(size=11),
            fg_color=("#f1f5f9", "#272a3d"),
            hover_color=("#e2e8f0", "#33374d"),
            text_color=("#1e293b", "#e2e8f0"),
            command=lambda: self._select_by_rule("keep_newest")
        )
        self.btn_sel_keep_newest.pack(side="left", padx=4)

        self.btn_sel_keep_oldest = ctk.CTkButton(
            sel_frame,
            text="Keep Oldest",
            height=28,
            width=110,
            font=ctk.CTkFont(size=11),
            fg_color=("#f1f5f9", "#272a3d"),
            hover_color=("#e2e8f0", "#33374d"),
            text_color=("#1e293b", "#e2e8f0"),
            command=lambda: self._select_by_rule("keep_oldest")
        )
        self.btn_sel_keep_oldest.pack(side="left", padx=4)

        self.btn_sel_none = ctk.CTkButton(
            sel_frame,
            text="Deselect All",
            height=28,
            width=100,
            font=ctk.CTkFont(size=11),
            fg_color=("#f1f5f9", "#272a3d"),
            hover_color=("#e2e8f0", "#33374d"),
            text_color=("#1e293b", "#e2e8f0"),
            command=lambda: self._select_by_rule("none")
        )
        self.btn_sel_none.pack(side="left", padx=4)

        self.sel_count_lbl = ctk.CTkLabel(
            sel_frame,
            text="0 files selected for review",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#3b82f6", "#60a5fa")
        )
        self.sel_count_lbl.pack(side="right", padx=16)

    def _build_results_area(self):
        """Scrollable view containing group cards."""
        self.results_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        self.results_scroll.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.results_scroll.grid_columnconfigure(0, weight=1)

        self._show_empty_message("No duplicate scan performed yet. Select a directory and start scan.")

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

    def _show_empty_message(self, message: str):
        for w in self.results_scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.results_scroll,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#94a3b8", "#64748b")
        ).pack(pady=50)

    def _browse_folder(self):
        folder = ctk.filedialog.askdirectory(initialdir=self.folder_var.get() or os.getcwd(), title="Select Duplicate Scan Folder")
        if folder:
            self.folder_var.set(folder)
            self.current_folder = folder
            if config_manager.get("remember_directory", True):
                config_manager.set("last_directory", folder)
            if self.on_folder_changed:
                self.on_folder_changed(folder)

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
        self.summary_stats_lbl.configure(text="Cancelling scan...")

    def start_duplicate_scan(self):
        """Scans for duplicate files in a background thread."""
        target_dir = self.folder_var.get().strip()
        if not target_dir:
            self.summary_stats_lbl.configure(text="Please select a folder first.")
            return

        is_safe, reason = is_safe_directory(target_dir)
        if not is_safe:
            ConfirmDialog(self, title="Invalid Directory", message=reason, confirm_text="OK", cancel_text="")
            return

        self._set_ui_state(scanning=True)
        self.stop_event.clear()
        self.progress_bar.set(0)
        self.summary_stats_lbl.configure(text="Scanning directory & hashing files...")

        def _progress(idx, total, filename):
            pct = idx / max(1, total)
            self.after(0, lambda: self._update_progress_ui(pct, f"Hashing ({idx}/{total}): {filename}"))

        def _worker():
            try:
                valid, err, groups = duplicate_finder.scan_duplicates(
                    target_dir,
                    recursive=self.recursive_var.get(),
                    include_hidden=self.hidden_var.get(),
                    progress_callback=_progress,
                    stop_event=self.stop_event
                )
                self.after(0, lambda: self._on_scan_finished(valid, err, groups))
            except Exception as e:
                self.after(0, lambda: self._on_scan_finished(False, str(e), []))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_progress_ui(self, pct: float, msg: str):
        self.progress_bar.set(pct)
        self.prog_text_lbl.configure(text=msg)

    def _on_scan_finished(self, valid: bool, err_msg: str, groups: List[DuplicateGroup]):
        self._set_ui_state(scanning=False)
        self.progress_bar.set(1.0)
        self.duplicate_groups = groups
        self.file_checkboxes.clear()

        if not valid:
            self.summary_stats_lbl.configure(text=f"Scan error: {err_msg}")
            self._show_empty_message(f"Error: {err_msg}")
            return

        for w in self.results_scroll.winfo_children():
            w.destroy()

        if not groups:
            self._show_empty_message("No duplicate files found! All files have unique contents.")
            self.summary_stats_lbl.configure(text="Clean! 0 duplicates detected.")
            self.btn_move_review.configure(state="disabled")
            return

        total_dupes = sum(len(g.files) - 1 for g in groups)
        total_wasted = sum(g.wasted_storage_bytes for g in groups)

        # Human formatted wasted size
        bytes_val = float(total_wasted)
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024.0:
                wasted_fmt = f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
                break
            bytes_val /= 1024.0
        else:
            wasted_fmt = f"{bytes_val:.1f} TB"

        self.summary_stats_lbl.configure(
            text=f"Found {len(groups)} duplicate groups ({total_dupes} extra copies, {wasted_fmt} wasted)"
        )
        self.btn_move_review.configure(state="normal")

        # Render duplicate group cards
        for g_idx, group in enumerate(groups):
            self._render_group_card(group, g_idx)

        # By default, select all duplicates keeping the first copy
        self._select_by_rule("keep_first")

    def _render_group_card(self, group: DuplicateGroup, _index: int):
        """Renders an individual duplicate group container."""
        group_card = ctk.CTkFrame(
            self.results_scroll,
            fg_color=("#f8fafc", "#232334"),
            corner_radius=10,
            border_width=1,
            border_color=("#e2e8f0", "#2f334a")
        )
        group_card.pack(fill="x", padx=6, pady=6)
        group_card.grid_columnconfigure(0, weight=1)

        # Group Header
        header = ctk.CTkFrame(group_card, fg_color=("#f1f5f9", "#292c3f"), height=32, corner_radius=6)
        header.pack(fill="x", padx=6, pady=6)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text=f"  {group.group_id}  |  {len(group.files)} Identical Files  |  Each: {group.formatted_size}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#1e293b", "#f8fafc")
        ).grid(row=0, column=0, sticky="w", padx=8, pady=4)

        hash_preview = f"SHA-256: {group.sha256_hash[:16]}..."
        ctk.CTkLabel(
            header,
            text=f"{hash_preview}  (Wasting {group.formatted_wasted_storage})  ",
            font=ctk.CTkFont(size=11),
            text_color=("#f59e0b", "#fbbf24")
        ).grid(row=0, column=1, sticky="e", padx=8, pady=4)

        # Files in group
        for f_idx, file_item in enumerate(group.files):
            file_row = ctk.CTkFrame(group_card, fg_color="transparent", height=28)
            file_row.pack(fill="x", padx=12, pady=2)
            file_row.grid_columnconfigure(1, weight=1)

            var = ctk.BooleanVar(value=False)
            self.file_checkboxes[str(file_item.path)] = var

            chk = ctk.CTkCheckBox(
                file_row,
                text="",
                variable=var,
                width=24,
                checkbox_width=18,
                checkbox_height=18,
                command=self._update_selected_count
            )
            chk.grid(row=0, column=0, sticky="w")

            # Path & filename
            rel_path = file_item.path.name
            try:
                rel_path = str(file_item.path.relative_to(Path(self.folder_var.get())))
            except Exception:
                rel_path = str(file_item.path)

            tag = "  (First Copy)" if f_idx == 0 else ""
            ctk.CTkLabel(
                file_row,
                text=f"{rel_path}{tag}",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if f_idx == 0 else "normal"),
                text_color=("#0f172a", "#f8fafc") if f_idx == 0 else ("#475569", "#cbd5e1"),
                anchor="w"
            ).grid(row=0, column=1, sticky="w", padx=6)

            ctk.CTkLabel(
                file_row,
                text=file_item.formatted_date,
                font=ctk.CTkFont(size=10),
                text_color=("#94a3b8", "#64748b")
            ).grid(row=0, column=2, sticky="e", padx=10)

    def _select_by_rule(self, rule: str):
        """Selects duplicates according to standard presets."""
        for group in self.duplicate_groups:
            if rule == "none":
                for f in group.files:
                    var = self.file_checkboxes.get(str(f.path))
                    if var:
                        var.set(False)

            elif rule == "keep_first":
                for idx, f in enumerate(group.files):
                    var = self.file_checkboxes.get(str(f.path))
                    if var:
                        var.set(idx > 0)  # check all except index 0

            elif rule == "keep_newest":
                # Find newest file
                newest = max(group.files, key=lambda x: x.modified_time)
                for f in group.files:
                    var = self.file_checkboxes.get(str(f.path))
                    if var:
                        var.set(f.path != newest.path)

            elif rule == "keep_oldest":
                # Find oldest file
                oldest = min(group.files, key=lambda x: x.modified_time)
                for f in group.files:
                    var = self.file_checkboxes.get(str(f.path))
                    if var:
                        var.set(f.path != oldest.path)

        self._update_selected_count()

    def _update_selected_count(self):
        selected_count = sum(1 for var in self.file_checkboxes.values() if var.get())
        self.sel_count_lbl.configure(text=f"{selected_count} files selected for review")
        self.btn_move_review.configure(state="normal" if selected_count > 0 else "disabled")

    def _prompt_and_move_duplicates(self):
        """Prompts confirmation and moves duplicates to quarantine review folder."""
        selected_paths: List[Path] = [
            Path(path_str) for path_str, var in self.file_checkboxes.items() if var.get()
        ]
        if not selected_paths:
            return

        ConfirmDialog(
            self,
            title="Move Duplicates to Review Folder",
            message=(
                f"Move {len(selected_paths)} duplicate files into a safe review folder?\n\n"
                "IMPORTANT: No files will be deleted. They will be placed in a dedicated "
                "'Duplicate_Review' folder so you can review them safely."
            ),
            confirm_text="Move to Review",
            cancel_text="Cancel",
            on_confirm=lambda: self._execute_move_duplicates(selected_paths)
        )

    def _execute_move_duplicates(self, selected_paths: List[Path]):
        base_dir = self.folder_var.get().strip()
        self._set_ui_state(scanning=True)
        self.stop_event.clear()
        self.progress_bar.set(0)
        self.summary_stats_lbl.configure(text="Moving duplicates to review folder...")

        def _progress(idx, total, filename):
            pct = idx / max(1, total)
            self.after(0, lambda: self._update_progress_ui(pct, f"Moving ({idx}/{total}): {filename}"))

        def _worker():
            try:
                moved, failed, errors, rev_dir = duplicate_finder.move_selected_duplicates(
                    base_dir,
                    selected_paths,
                    progress_callback=_progress,
                    stop_event=self.stop_event
                )
                self.after(0, lambda: self._on_move_finished(moved, failed, errors, rev_dir))
            except Exception as e:
                self.after(0, lambda: self.summary_stats_lbl.configure(text=f"Error moving duplicates: {e}"))
                self.after(0, lambda: self._set_ui_state(scanning=False))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_move_finished(self, moved: int, failed: int, errors: List[str], review_dir: Path):
        self._set_ui_state(scanning=False)
        self.progress_bar.set(1.0)
        msg = f"Moved {moved} duplicates to review folder: {review_dir.name}"
        self.summary_stats_lbl.configure(text=msg)

        if self.on_status_message:
            self.on_status_message(msg)

        # Notify user with option to open review folder
        ConfirmDialog(
            self,
            title="Duplicate Review Quarantine",
            message=f"Successfully moved {moved} duplicates to:\n{review_dir}\n\nFiles were safely moved, not deleted.",
            confirm_text="Open Review Folder",
            cancel_text="Close",
            on_confirm=lambda: os.startfile(review_dir) if review_dir.exists() else None
        )

        # Refresh scan to reflect remaining files
        self.start_duplicate_scan()

    def _set_ui_state(self, scanning: bool):
        self.is_scanning = scanning
        state = "disabled" if scanning else "normal"
        self.btn_scan.configure(state=state)
        self.browse_btn.configure(state=state)
        self.folder_entry.configure(state=state)
        self.btn_stop.configure(state="normal" if scanning else "disabled")
