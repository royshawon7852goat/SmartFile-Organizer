"""Main application window for Smart File Organizer."""
import os
import sys
from pathlib import Path
from typing import Dict
import customtkinter as ctk

from core.config_manager import config_manager
from core.undo_manager import undo_manager
from gui.about_page import AboutPage
from gui.components.toast import ConfirmDialog
from gui.dashboard import DashboardPage
from gui.duplicate_page import DuplicatePage
from gui.history_page import HistoryPage
from gui.organizer_page import OrganizerPage
from gui.settings_page import SettingsPage
from gui.sidebar import Sidebar

BASE_DIR = Path(__file__).resolve().parent.parent
ICON_ICO = BASE_DIR / "assets" / "icons" / "app_icon.ico"
ICON_PNG = BASE_DIR / "assets" / "icons" / "app_icon.png"

class SmartFileOrganizerApp(ctk.CTk):
    """Main Application Window."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Smart File Organizer")
        self.geometry("1160x760")
        self.minsize(1100, 700)

        # Set appearance mode from config
        saved_theme = config_manager.get("theme", "dark")
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("blue")

        # Set Window Icon
        self._set_app_icon()

        # Grid Layout: Sidebar (col 0), Main View (col 1), Status Bar (row 1)
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0, minsize=28)

        # Active Directory tracking
        self.active_directory: str = config_manager.get("last_directory", "") or config_manager.get("default_directory", "")

        # Sidebar
        self.sidebar = Sidebar(
            self,
            on_navigate=self.navigate_to_page,
            on_undo_requested=self.handle_global_undo
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Main Content Container
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Status Bar
        self._build_status_bar()

        # Instantiate Pages
        self.pages: Dict[str, ctk.CTkFrame] = {}
        self._init_pages()

        # Initial folder & undo state setup
        if self.active_directory:
            self.set_active_directory(self.active_directory)
        self.update_undo_state()

        # Show initial page
        self.navigate_to_page("dashboard")

    def _set_app_icon(self):
        """Sets the window icon for Windows taskbar and titlebar."""
        try:
            if sys.platform == "win32" and ICON_ICO.exists():
                self.iconbitmap(default=str(ICON_ICO))
            elif ICON_PNG.exists():
                import tkinter as tk
                from PIL import ImageTk, Image
                img = ImageTk.PhotoImage(Image.open(ICON_PNG))
                self.iconphoto(False, img)
        except Exception:
            pass

    def _build_status_bar(self):
        """Bottom status bar showing application status and current folder."""
        self.status_bar = ctk.CTkFrame(
            self,
            height=28,
            corner_radius=0,
            fg_color=("#e2e8f0", "#12121a"),
            border_width=1,
            border_color=("#cbd5e1", "#1e1e2c")
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_columnconfigure(1, weight=1)

        self.status_text_lbl = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748b", "#94a3b8")
        )
        self.status_text_lbl.grid(row=0, column=0, sticky="w", padx=16, pady=2)

        self.status_folder_lbl = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#475569", "#cbd5e1"),
            anchor="center"
        )
        self.status_folder_lbl.grid(row=0, column=1, sticky="ew", padx=10, pady=2)

        self.status_security_badge = ctk.CTkLabel(
            self.status_bar,
            text="🔒 System Protection Active",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=("#10b981", "#34d399")
        )
        self.status_security_badge.grid(row=0, column=2, sticky="e", padx=16, pady=2)

    def _init_pages(self):
        """Initializes all subpages."""
        self.pages["dashboard"] = DashboardPage(
            self.content_container,
            on_navigate=self.navigate_to_page,
            on_folder_changed=self.set_active_directory,
            on_request_undo=self.handle_global_undo
        )

        self.pages["organizer"] = OrganizerPage(
            self.content_container,
            on_status_message=self.set_status_message,
            on_folder_changed=self.set_active_directory
        )

        self.pages["duplicates"] = DuplicatePage(
            self.content_container,
            on_status_message=self.set_status_message,
            on_folder_changed=self.set_active_directory
        )

        self.pages["history"] = HistoryPage(
            self.content_container,
            on_status_message=self.set_status_message,
            on_history_updated=self._on_history_mutated
        )

        self.pages["settings"] = SettingsPage(
            self.content_container,
            on_theme_changed=self._on_theme_changed,
            on_status_message=self.set_status_message
        )

        self.pages["about"] = AboutPage(self.content_container)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def navigate_to_page(self, page_name: str):
        """Switches view to the requested page."""
        target_page = self.pages.get(page_name)
        if target_page:
            target_page.tkraise()
            self.sidebar.set_active_page(page_name)

            # Auto refresh data when navigating to dashboard or history
            if page_name == "dashboard" and hasattr(target_page, "refresh_data"):
                target_page.refresh_data()
            elif page_name == "history" and hasattr(target_page, "refresh_history"):
                target_page.refresh_history()

            self.update_undo_state()

    def set_active_directory(self, folder_path: str):
        """Coordinates folder updates across all pages and sidebar."""
        self.active_directory = folder_path
        self.sidebar.update_active_folder(folder_path)

        if folder_path:
            p = Path(folder_path)
            self.status_folder_lbl.configure(text=f"Active Folder: {p.name} ({p})")
        else:
            self.status_folder_lbl.configure(text="No active folder selected")

        # Propagate to organizer and duplicate pages if not already matching
        org_page: OrganizerPage = self.pages.get("organizer")  # type: ignore
        if org_page and org_page.folder_var.get() != folder_path:
            org_page.set_folder(folder_path)

        dup_page: DuplicatePage = self.pages.get("duplicates")  # type: ignore
        if dup_page and dup_page.folder_var.get() != folder_path:
            dup_page.folder_var.set(folder_path)

        dash_page: DashboardPage = self.pages.get("dashboard")  # type: ignore
        if dash_page and dash_page.current_folder != folder_path:
            dash_page.current_folder = folder_path
            dash_page.refresh_data()

    def set_status_message(self, message: str):
        """Updates the status bar message."""
        self.status_text_lbl.configure(text=str(message))

    def update_undo_state(self):
        """Updates undo button states throughout the UI."""
        can_undo = undo_manager.can_undo()
        self.sidebar.set_undo_enabled(can_undo)

    def handle_global_undo(self):
        """Global undo requested from sidebar or dashboard."""
        if not undo_manager.can_undo():
            self.set_status_message("No recent organization session available to undo.")
            return

        ConfirmDialog(
            self,
            title="Undo Last Organization",
            message="Restore organized files from the last session back to their original locations?",
            confirm_text="Restore Files",
            cancel_text="Cancel",
            on_confirm=self._execute_global_undo
        )

    def _execute_global_undo(self):
        self.set_status_message("Restoring files...")
        ok, msg, _res = undo_manager.undo_last_session()
        self.set_status_message(msg)
        self.update_undo_state()
        self._on_history_mutated()
        ConfirmDialog(self, title="Undo Results", message=msg, confirm_text="OK", cancel_text="")

    def _on_history_mutated(self):
        """Called when history was updated or undone."""
        self.update_undo_state()
        dash_page: DashboardPage = self.pages.get("dashboard")  # type: ignore
        if dash_page:
            dash_page.refresh_data()

    def _on_theme_changed(self, theme_name: str):
        """Updates app theme."""
        ctk.set_appearance_mode(theme_name)
        self.set_status_message(f"Appearance theme switched to {theme_name.capitalize()}.")
