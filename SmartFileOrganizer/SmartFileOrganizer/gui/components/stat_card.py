"""StatCard component for modern Windows 11 style dashboard metrics."""
import customtkinter as ctk
from typing import Optional

class StatCard(ctk.CTkFrame):
    """Modern rounded statistic card with hover highlight and accent styling."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtext: str = "",
        accent_color: str = "#3b82f6",
        icon_text: str = "📊",
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=("#ffffff", "#1e1e2a"),
            border_width=1,
            border_color=("#e2e8f0", "#2d3348"),
            **kwargs
        )
        self.accent_color = accent_color
        self.default_border = ("#e2e8f0", "#2d3348")
        self.hover_border = (accent_color, accent_color)

        self.grid_columnconfigure(0, weight=1)

        # Header row (Icon + Title)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        header_frame.grid_columnconfigure(1, weight=1)

        self.icon_badge = ctk.CTkLabel(
            header_frame,
            text=icon_text,
            font=ctk.CTkFont(size=18),
            width=32,
            height=32,
            corner_radius=8,
            fg_color=("#f1f5f9", "#272a3d")
        )
        self.icon_badge.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=title.upper(),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        )
        self.title_label.grid(row=0, column=1, sticky="w")

        # Value label
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"),
            text_color=("#0f172a", "#f8fafc"),
            anchor="w"
        )
        self.value_label.grid(row=1, column=0, sticky="w", padx=16, pady=(2, 2))

        # Subtext label
        self.subtext_label = ctk.CTkLabel(
            self,
            text=subtext,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#94a3b8", "#64748b"),
            anchor="w"
        )
        self.subtext_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))

        # Hover bindings
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for child in [self.value_label, self.subtext_label, header_frame, self.title_label]:
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event=None):
        self.configure(border_color=self.hover_border)

    def _on_leave(self, _event=None):
        self.configure(border_color=self.default_border)

    def update_value(self, new_value: str, subtext: Optional[str] = None):
        """Thread-safe update of the card value."""
        self.value_label.configure(text=str(new_value))
        if subtext is not None:
            self.subtext_label.configure(text=str(subtext))
