"""About Page for Smart File Organizer."""
import platform
import sys
from pathlib import Path
from PIL import Image
import customtkinter as ctk

BASE_DIR = Path(__file__).resolve().parent.parent
ICON_PATH = BASE_DIR / "assets" / "icons" / "app_icon.png"

class AboutPage(ctk.CTkFrame):
    """About & System Specification screen."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        scroll.grid_columnconfigure(0, weight=1)

        # Brand Hero Card
        hero_card = ctk.CTkFrame(
            scroll,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=14,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        hero_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        hero_card.grid_columnconfigure(1, weight=1)

        # App Icon
        try:
            if ICON_PATH.exists():
                pil_img = Image.open(ICON_PATH).resize((64, 64), Image.Resampling.LANCZOS)
                self.app_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(64, 64))
                ctk.CTkLabel(hero_card, image=self.app_img, text="").grid(row=0, column=0, rowspan=3, padx=24, pady=24)
        except Exception:
            ctk.CTkLabel(hero_card, text="📁", font=ctk.CTkFont(size=48)).grid(row=0, column=0, rowspan=3, padx=24, pady=24)

        ctk.CTkLabel(
            hero_card,
            text="Smart File Organizer",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        ).grid(row=0, column=1, sticky="w", pady=(24, 0))

        ctk.CTkLabel(
            hero_card,
            text="Version 1.0.0 Pro Edition  •  Windows Desktop Application",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#3b82f6", "#60a5fa")
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

        ctk.CTkLabel(
            hero_card,
            text="High-performance desktop file categorization, SHA-256 duplicate quarantine, and non-destructive undo system.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=2, column=1, sticky="w", pady=(2, 24))

        # Architecture & Safety Guarantees
        guard_card = ctk.CTkFrame(
            scroll,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        guard_card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        guard_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            guard_card,
            text="SECURITY & ARCHITECTURAL SAFEGUARDS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 12))

        guarantees = [
            ("🛡️ Zero Automatic Deletion", "Duplicate files are never permanently deleted by the application. Selected duplicates are safely moved into a dedicated quarantine review folder."),
            ("↩️ Reversible Undo System", "Every file movement is indexed in an atomic JSON history audit log. You can restore organized files back to their exact original locations anytime."),
            ("🔒 System Directory Protection", "Strict path validation blocks modifications to Windows root drives (C:\\), System32, Program Files, ProgramData, or the app's installation directory."),
            ("⚡ Collision-Proof Renaming", "Files are never overwritten. When moving or restoring files where a matching filename exists, files are safely incremented to 'filename (1).ext'."),
            ("🚀 Memory-Efficient Streaming", "Duplicate hashing uses 64KB block streaming SHA-256 with initial file-size grouping, eliminating memory overhead on large files.")
        ]

        for idx, (title, desc) in enumerate(guarantees, start=1):
            g_frame = ctk.CTkFrame(guard_card, fg_color="transparent")
            g_frame.grid(row=idx, column=0, sticky="ew", padx=20, pady=6)
            g_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                g_frame,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=("#0f172a", "#f8fafc")
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                g_frame,
                text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#64748b", "#94a3b8"),
                wraplength=700,
                justify="left"
            ).grid(row=1, column=0, sticky="w", pady=(1, 4))

        # Bottom padding for guard card
        ctk.CTkFrame(guard_card, height=10, fg_color="transparent").grid(row=len(guarantees) + 1, column=0)

        # System Information
        sys_card = ctk.CTkFrame(
            scroll,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        sys_card.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        sys_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            sys_card,
            text="SYSTEM SPECIFICATIONS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 12))

        sys_info = [
            ("Python Runtime:", f"{sys.version.split()[0]} ({platform.python_implementation()})"),
            ("Operating System:", f"{platform.system()} {platform.release()} (Build {platform.version()})"),
            ("Machine Architecture:", platform.machine()),
            ("GUI Framework:", f"CustomTkinter {ctk.__version__}"),
            ("Working Directory:", str(BASE_DIR)),
        ]

        for s_idx, (k, v) in enumerate(sys_info, start=1):
            ctk.CTkLabel(
                sys_card,
                text=k,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=("#475569", "#94a3b8"),
                width=160,
                anchor="w"
            ).grid(row=s_idx, column=0, sticky="w", padx=(20, 8), pady=3)

            ctk.CTkLabel(
                sys_card,
                text=v,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=("#0f172a", "#f8fafc"),
                anchor="w"
            ).grid(row=s_idx, column=1, sticky="w", padx=8, pady=3)

        ctk.CTkFrame(sys_card, height=12, fg_color="transparent").grid(row=len(sys_info) + 1, column=0)
