"""Preview Modal dialog for inspecting dry-run file movements before committing changes."""
import customtkinter as ctk
from typing import Callable, List, Optional
from core.organizer import OrganizationAction

class PreviewModal(ctk.CTkToplevel):
    """Modern modal dialog showing planned file actions before execution."""

    def __init__(
        self,
        parent,
        actions: List[OrganizationAction],
        on_proceed: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title("Preview Organization Plan")
        self.geometry("780x560")
        self.minsize(700, 480)
        self.transient(parent)
        self.grab_set()

        self.actions = actions
        self.on_proceed = on_proceed
        self.on_cancel = on_cancel

        # Center on parent window
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (780 // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (560 // 2)
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.configure(fg_color=("#f8fafc", "#161622"))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text="Organization Preview",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=20, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        title_label.grid(row=0, column=0, sticky="w")

        sub_label = ctk.CTkLabel(
            header,
            text=f"Review {len(actions)} planned file movements. No files have been moved yet.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#64748b", "#94a3b8")
        )
        sub_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Search / filter box
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._populate_list())
        search_entry = ctk.CTkEntry(
            header,
            placeholder_text="Filter preview list...",
            textvariable=self.search_var,
            width=220,
            height=32
        )
        search_entry.grid(row=0, column=1, rowspan=2, sticky="e")

        # Scrollable table container
        table_container = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#1e1e2c"),
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#2d3348")
        )
        table_container.grid(row=1, column=0, sticky="nsew", padx=24, pady=10)
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(1, weight=1)

        # Column Headers
        col_header = ctk.CTkFrame(table_container, fg_color=("#f1f5f9", "#272a3d"), height=36, corner_radius=6)
        col_header.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        col_header.grid_columnconfigure(0, weight=4)  # Filename
        col_header.grid_columnconfigure(1, weight=2)  # Category
        col_header.grid_columnconfigure(2, weight=2)  # Size
        col_header.grid_columnconfigure(3, weight=5)  # Target Destination

        ctk.CTkLabel(col_header, text="ORIGINAL FILE", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=0, sticky="w", padx=12)
        ctk.CTkLabel(col_header, text="CATEGORY", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(col_header, text="SIZE", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=2, sticky="w", padx=8)
        ctk.CTkLabel(col_header, text="TARGET DIRECTORY", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=3, sticky="w", padx=12)

        # Scrollable list
        self.scroll_list = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
        self.scroll_list.grid_columnconfigure(0, weight=4)
        self.scroll_list.grid_columnconfigure(1, weight=2)
        self.scroll_list.grid_columnconfigure(2, weight=2)
        self.scroll_list.grid_columnconfigure(3, weight=5)

        self._populate_list()

        # Footer Bar
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(8, 20))
        footer.grid_columnconfigure(0, weight=1)

        summary_text = f"Total: {len(actions)} files to organize"
        summary_lbl = ctk.CTkLabel(
            footer,
            text=summary_text,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        )
        summary_lbl.grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(footer, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        cancel_btn = ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=100,
            height=36,
            fg_color=("#e2e8f0", "#2d3348"),
            hover_color=("#cbd5e1", "#3b4259"),
            text_color=("#334155", "#e2e8f0"),
            command=self._cancel
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        proceed_btn = ctk.CTkButton(
            btn_box,
            text="Execute Organization",
            width=160,
            height=36,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            text_color="#ffffff",
            font=ctk.CTkFont(weight="bold"),
            command=self._proceed
        )
        proceed_btn.pack(side="left")

    def _format_size(self, size_bytes: int) -> str:
        bytes_val = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"

    def _get_category_color(self, category: str) -> tuple[str, str]:
        colors = {
            "Documents": ("#dbeafe", "#1e3a8a"),
            "Images": ("#dcfce7", "#14532d"),
            "Videos": ("#fef3c7", "#78350f"),
            "Audio": ("#f3e8ff", "#581c87"),
            "Archives": ("#ffedd5", "#7c2d12"),
            "Applications": ("#ccfbf1", "#134e4a"),
            "Others": ("#f1f5f9", "#334155")
        }
        return colors.get(category, ("#f1f5f9", "#334155"))

    def _populate_list(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        search_query = self.search_var.get().strip().lower()
        row_idx = 0

        for action in self.actions:
            if search_query:
                if search_query not in action.filename.lower() and search_query not in action.category.lower():
                    continue

            bg = ("#f8fafc", "#232334") if row_idx % 2 == 0 else ("transparent", "transparent")
            row_frame = ctk.CTkFrame(self.scroll_list, fg_color=bg, corner_radius=6, height=32)
            row_frame.grid(row=row_idx, column=0, columnspan=4, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(0, weight=4)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=2)
            row_frame.grid_columnconfigure(3, weight=5)

            # Name
            ctk.CTkLabel(
                row_frame,
                text=action.filename,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=12, pady=4)

            # Category Pill
            cat_pill = ctk.CTkLabel(
                row_frame,
                text=action.category,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                width=80,
                height=22,
                corner_radius=6,
                fg_color=("#e0e7ff", "#2b3050"),
                text_color=("#3730a3", "#a5b4fc")
            )
            cat_pill.grid(row=0, column=1, sticky="w", padx=8, pady=4)

            # Size
            ctk.CTkLabel(
                row_frame,
                text=self._format_size(action.size_bytes),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            ).grid(row=0, column=2, sticky="w", padx=8, pady=4)

            # Target directory
            dest_display = f"{action.target_dir.name}/{action.target_path.name}"
            ctk.CTkLabel(
                row_frame,
                text=dest_display,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#3b82f6", "#60a5fa"),
                anchor="w"
            ).grid(row=0, column=3, sticky="w", padx=12, pady=4)

            row_idx += 1

        if row_idx == 0:
            ctk.CTkLabel(
                self.scroll_list,
                text="No matching files found.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=("#94a3b8", "#64748b")
            ).grid(row=0, column=0, columnspan=4, pady=30)

    def _proceed(self):
        self.destroy()
        if self.on_proceed:
            self.on_proceed()

    def _cancel(self):
        self.destroy()
        if self.on_cancel:
            self.on_cancel()
