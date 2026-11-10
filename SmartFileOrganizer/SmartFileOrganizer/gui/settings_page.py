"""Settings page for Smart File Organizer.
Allows configuring appearance theme, default directory, behavior toggles, and custom category file extensions.
"""
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional
import customtkinter as ctk

from core.config_manager import DEFAULT_CATEGORIES, config_manager
from gui.components.toast import ConfirmDialog

class SettingsPage(ctk.CTkFrame):
    """Modern Settings management panel with category extension editor."""

    def __init__(
        self,
        master,
        on_theme_changed: Optional[Callable[[str], None]] = None,
        on_status_message: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_theme_changed = on_theme_changed
        self.on_status_message = on_status_message

        self.categories: Dict[str, List[str]] = dict(config_manager.get_all_categories())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_general_settings()
        self._build_behavior_settings()
        self._build_extension_editor()
        self._build_save_bar()

    def _build_header(self):
        """Top banner."""
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text="Settings & Preferences",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header_frame,
            text="Customize application theme, scanning rules, safety prompts, and file category extensions.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _build_general_settings(self):
        """Theme and default directory."""
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="GENERAL PREFERENCES",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=18, pady=(16, 12))

        # Appearance Mode
        ctk.CTkLabel(
            card,
            text="Appearance Theme:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", padx=18, pady=8)

        self.theme_var = ctk.StringVar(value=config_manager.get("theme", "dark").capitalize())
        theme_menu = ctk.CTkOptionMenu(
            card,
            values=["Dark", "Light", "System"],
            variable=self.theme_var,
            width=140,
            command=self._on_theme_select
        )
        theme_menu.grid(row=1, column=1, sticky="w", padx=8, pady=8)

        # Default Directory
        ctk.CTkLabel(
            card,
            text="Default Directory:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            anchor="w"
        ).grid(row=2, column=0, sticky="w", padx=18, pady=(8, 16))

        self.default_dir_var = ctk.StringVar(value=config_manager.get("default_directory", ""))
        self.default_dir_entry = ctk.CTkEntry(
            card,
            textvariable=self.default_dir_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            placeholder_text="Optional default folder (leave empty for last used)...",
            height=34
        )
        self.default_dir_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=(8, 16))

        browse_btn = ctk.CTkButton(
            card,
            text="Browse...",
            width=90,
            height=34,
            command=self._browse_default_dir
        )
        browse_btn.grid(row=2, column=2, padx=(0, 18), pady=(8, 16))

    def _build_behavior_settings(self):
        """Switches for organization and safety behavior."""
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="BEHAVIOR & SAFETY RULES",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        self.remember_dir_var = ctk.BooleanVar(value=config_manager.get("remember_directory", True))
        ctk.CTkSwitch(
            card,
            text="Remember last opened directory across application restarts",
            variable=self.remember_dir_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", padx=18, pady=6)

        self.ask_before_var = ctk.BooleanVar(value=config_manager.get("ask_before_organize", True))
        ctk.CTkSwitch(
            card,
            text="Show interactive preview & confirmation before organizing files",
            variable=self.ask_before_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, sticky="w", padx=18, pady=6)

        self.auto_create_var = ctk.BooleanVar(value=config_manager.get("auto_create_folders", True))
        ctk.CTkSwitch(
            card,
            text="Automatically create category subfolders (Documents, Images, etc.)",
            variable=self.auto_create_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=3, column=0, sticky="w", padx=18, pady=6)

        self.include_hidden_var = ctk.BooleanVar(value=config_manager.get("include_hidden", False))
        ctk.CTkSwitch(
            card,
            text="Include hidden and Windows system files during scans by default",
            variable=self.include_hidden_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=4, column=0, sticky="w", padx=18, pady=(6, 16))

    def _build_extension_editor(self):
        """Custom file category extensions editor."""
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        card.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)

        # Header with Reset to Defaults
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row,
            text="FILE CATEGORIES & EXTENSIONS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, sticky="w")

        reset_btn = ctk.CTkButton(
            header_row,
            text="Reset to Defaults",
            width=130,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=("#e2e8f0", "#272a3d"),
            hover_color=("#cbd5e1", "#373b56"),
            text_color=("#1e293b", "#e2e8f0"),
            command=self._reset_categories
        )
        reset_btn.grid(row=0, column=1, sticky="e")

        # Container for category rows
        self.cats_container = ctk.CTkFrame(card, fg_color="transparent")
        self.cats_container.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))
        self.cats_container.grid_columnconfigure(0, weight=1)

        self._render_category_rows()

    def _render_category_rows(self):
        """Renders list of categories with editable extensions."""
        for w in self.cats_container.winfo_children():
            w.destroy()

        for idx, (cat_name, exts) in enumerate(self.categories.items()):
            row = ctk.CTkFrame(
                self.cats_container,
                fg_color=("#f8fafc", "#242738"),
                corner_radius=8,
                border_width=1,
                border_color=("#e2e8f0", "#2e334a")
            )
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(1, weight=1)

            # Category Name
            ctk.CTkLabel(
                row,
                text=cat_name,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                width=110,
                anchor="w"
            ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

            if cat_name == "Others":
                ctk.CTkLabel(
                    row,
                    text="Catch-all category for any extensions not matched above.",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=("#64748b", "#94a3b8"),
                    anchor="w"
                ).grid(row=0, column=1, padx=8, pady=10, sticky="w")
                continue

            # Extensions entry
            ext_str = ", ".join(e.lstrip(".") for e in exts)
            entry = ctk.CTkEntry(row, height=32, font=ctk.CTkFont(size=11))
            entry.insert(0, ext_str)
            entry.grid(row=0, column=1, sticky="ew", padx=8, pady=8)

            row.entry = entry
            row.cat_name = cat_name

    def _build_save_bar(self):
        """Save settings button."""
        bar = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        bar.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        bar.grid_columnconfigure(0, weight=1)

        save_btn = ctk.CTkButton(
            bar,
            text="💾  Save All Settings",
            width=180,
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.save_all_settings
        )
        save_btn.grid(row=0, column=0, sticky="e")

    def _on_theme_select(self, theme_choice: str):
        theme_str = theme_choice.lower()
        ctk.set_appearance_mode(theme_str)
        if self.on_theme_changed:
            self.on_theme_changed(theme_str)

    def _browse_default_dir(self):
        folder = ctk.filedialog.askdirectory(initialdir=self.default_dir_var.get() or os.getcwd(), title="Select Default Organization Folder")
        if folder:
            self.default_dir_var.set(folder)

    def _reset_categories(self):
        self.categories = {cat: list(exts) for cat, exts in DEFAULT_CATEGORIES.items()}
        self._render_category_rows()
        if self.on_status_message:
            self.on_status_message("Categories reset to defaults. Click 'Save All Settings' to persist.")

    def save_all_settings(self):
        """Gathers values from inputs and persists to config.json."""
        # Read back category extensions from rows
        updated_categories: Dict[str, List[str]] = {}
        for child in self.cats_container.winfo_children():
            cat_name = getattr(child, "cat_name", None)
            entry = getattr(child, "entry", None)
            if cat_name and entry:
                raw_text = entry.get()
                parsed = [
                    f".{e.strip().lstrip('.').lower()}"
                    for e in raw_text.split(",")
                    if e.strip()
                ]
                updated_categories[cat_name] = parsed
            elif cat_name == "Others":
                updated_categories["Others"] = []

        # Merge with existing categories in case any were missing
        self.categories = updated_categories

        # Update config manager
        config_manager.set("theme", self.theme_var.get().lower(), save=False)
        config_manager.set("default_directory", self.default_dir_var.get().strip(), save=False)
        config_manager.set("remember_directory", self.remember_dir_var.get(), save=False)
        config_manager.set("ask_before_organize", self.ask_before_var.get(), save=False)
        config_manager.set("auto_create_folders", self.auto_create_var.get(), save=False)
        config_manager.set("include_hidden", self.include_hidden_var.get(), save=False)
        config_manager.set("categories", updated_categories, save=True)

        if self.on_status_message:
            self.on_status_message("Settings saved successfully to config.json.")

        ConfirmDialog(
            self,
            title="Settings Saved",
            message="Your preferences and category extensions have been saved successfully.",
            confirm_text="OK",
            cancel_text=""
        )
