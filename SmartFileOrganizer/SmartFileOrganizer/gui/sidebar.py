"""Sidebar Navigation component for Smart File Organizer."""
import customtkinter as ctk
from pathlib import Path
from typing import Callable, Dict, Optional
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
ICON_PATH = BASE_DIR / "assets" / "icons" / "app_icon.png"

class Sidebar(ctk.CTkFrame):
    """Modern Windows 11 style sidebar navigation with icon support and active tab styling."""

    NAV_ITEMS = [
        ("dashboard", "Dashboard", "📊"),
        ("organizer", "Organize Files", "📁"),
        ("duplicates", "Duplicate Finder", "🔍"),
        ("history", "Activity History", "📜"),
        ("settings", "Settings", "⚙️"),
        ("about", "About", "ℹ️"),
    ]

    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None],
        on_undo_requested: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            width=240,
            corner_radius=0,
            fg_color=("#f1f5f9", "#181824"),
            border_width=0,
            **kwargs
        )
        self.on_navigate = on_navigate
        self.on_undo_requested = on_undo_requested
        self.buttons: Dict[str, ctk.CTkButton] = {}
        self.current_page = "dashboard"

        self.grid_rowconfigure(len(self.NAV_ITEMS) + 3, weight=1)  # Spacer pushes bottom items
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_nav_buttons()
        self._build_bottom_section()

    def _build_header(self):
        """Builds the top app title and brand icon."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(24, 20))
        header_frame.grid_columnconfigure(1, weight=1)

        # Icon
        try:
            if ICON_PATH.exists():
                pil_img = Image.open(ICON_PATH).resize((38, 38), Image.Resampling.LANCZOS)
                self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(38, 38))
                icon_lbl = ctk.CTkLabel(header_frame, image=self.logo_img, text="")
                icon_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="w")
        except Exception:
            icon_lbl = ctk.CTkLabel(header_frame, text="📁", font=ctk.CTkFont(size=24))
            icon_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="w")

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Smart Organizer",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
            text_color=("#0f172a", "#f8fafc"),
            anchor="w"
        )
        title_lbl.grid(row=0, column=1, sticky="w")

        version_lbl = ctk.CTkLabel(
            header_frame,
            text="v1.0 Pro Desktop",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=("#3b82f6", "#60a5fa"),
            anchor="w"
        )
        version_lbl.grid(row=1, column=1, sticky="w")

        # Subtle divider
        divider = ctk.CTkFrame(self, height=1, fg_color=("#e2e8f0", "#262b3d"))
        divider.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

    def _build_nav_buttons(self):
        """Creates the primary navigation buttons."""
        for idx, (page_key, label_text, icon) in enumerate(self.NAV_ITEMS, start=2):
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}   {label_text}",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color=("#e2e8f0", "#232638"),
                text_color=("#475569", "#cbd5e1"),
                command=lambda pk=page_key: self._on_nav_btn_clicked(pk)
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=12, pady=3)
            self.buttons[page_key] = btn

    def _on_nav_btn_clicked(self, page_key: str):
        """Triggered when user clicks a sidebar button."""
        self.set_active_page(page_key)
        self.on_navigate(page_key)

    def _build_bottom_section(self):
        """Builds bottom container with Quick Undo button and active directory indicator."""
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=len(self.NAV_ITEMS) + 4, column=0, sticky="ew", padx=12, pady=(0, 16))
        bottom_frame.grid_columnconfigure(0, weight=1)

        # Quick Undo Button
        self.undo_btn = ctk.CTkButton(
            bottom_frame,
            text="↩  Undo Last Action",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=36,
            corner_radius=8,
            fg_color=("#e2e8f0", "#25283a"),
            hover_color=("#cbd5e1", "#363a52"),
            text_color=("#334155", "#e2e8f0"),
            command=self._on_undo_click
        )
        self.undo_btn.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Selected Folder Badge
        self.folder_box = ctk.CTkFrame(
            bottom_frame,
            fg_color=("#e2e8f0", "#1f2233"),
            corner_radius=8,
            height=46
        )
        self.folder_box.grid(row=1, column=0, sticky="ew")
        self.folder_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.folder_box,
            text="ACTIVE FOLDER",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(6, 0))

        self.folder_label = ctk.CTkLabel(
            self.folder_box,
            text="No folder selected",
            font=ctk.CTkFont(size=11),
            text_color=("#0f172a", "#cbd5e1"),
            anchor="w"
        )
        self.folder_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 6))

    def _on_undo_click(self):
        if self.on_undo_requested:
            self.on_undo_requested()

    def set_active_page(self, page_key: str):
        """Highlights the active navigation button and updates visual state."""
        self.current_page = page_key
        for key, btn in self.buttons.items():
            if key == page_key:
                btn.configure(
                    fg_color=("#e0e7ff", "#2a3356"),
                    hover_color=("#dbeafe", "#313b63"),
                    text_color=("#1d4ed8", "#93c5fd"),
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=("#e2e8f0", "#232638"),
                    text_color=("#475569", "#cbd5e1"),
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal")
                )

    def update_active_folder(self, folder_path: str):
        """Updates the active folder badge text in the sidebar."""
        if not folder_path:
            self.folder_label.configure(text="No folder selected")
            return
        p = Path(folder_path)
        display = p.name if p.name else str(p)
        if len(display) > 22:
            display = display[:19] + "..."
        self.folder_label.configure(text=f"📁 {display}")

    def set_undo_enabled(self, enabled: bool):
        """Toggles the undo button state."""
        if enabled:
            self.undo_btn.configure(
                state="normal",
                text="↩  Undo Last Action",
                fg_color=("#dbeafe", "#2b3558"),
                text_color=("#1e40af", "#93c5fd")
            )
        else:
            self.undo_btn.configure(
                state="disabled",
                text="↩  Undo (None)",
                fg_color=("#f1f5f9", "#1f2233"),
                text_color=("#94a3b8", "#64748b")
            )
