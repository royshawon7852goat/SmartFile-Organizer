"""Modern dialogs and feedback toasts for Smart File Organizer."""
import customtkinter as ctk
from typing import Callable, Optional

class ConfirmDialog(ctk.CTkToplevel):
    """Modern modal dialog for confirming actions (e.g. organizing, moving duplicates, clearing history)."""

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        is_destructive: bool = False,
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("460x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.result = False

        # Center on parent window
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (460 // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (220 // 2)
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.configure(fg_color=("#f8fafc", "#181824"))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Card container
        container = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#20202e"),
            corner_radius=14,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        container.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        container.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            container,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=("#0f172a", "#f8fafc"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        # Message
        msg_label = ctk.CTkLabel(
            container,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#475569", "#94a3b8"),
            wraplength=380,
            justify="left",
            anchor="w"
        )
        msg_label.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Buttons frame
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="e", padx=20, pady=(0, 16))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            width=90,
            height=34,
            fg_color=("#e2e8f0", "#2d3348"),
            hover_color=("#cbd5e1", "#3b4259"),
            text_color=("#334155", "#e2e8f0"),
            command=self._cancel
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        confirm_fg = "#ef4444" if is_destructive else "#3b82f6"
        confirm_hover = "#dc2626" if is_destructive else "#2563eb"

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            width=110,
            height=34,
            fg_color=confirm_fg,
            hover_color=confirm_hover,
            text_color="#ffffff",
            command=self._confirm
        )
        confirm_btn.pack(side="left")

        self.bind("<Escape>", lambda _: self._cancel())

    def _confirm(self):
        self.result = True
        self.destroy()
        if self.on_confirm:
            self.on_confirm()

    def _cancel(self):
        self.result = False
        self.destroy()
        if self.on_cancel:
            self.on_cancel()
