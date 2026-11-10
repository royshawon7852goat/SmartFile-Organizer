"""History Detail Modal for inspecting files moved during a specific session."""
import customtkinter as ctk
from typing import Dict, List

class HistoryDetailModal(ctk.CTkToplevel):
    """Modal dialog displaying file movement records for a selected history session."""

    def __init__(self, parent, session: Dict):
        super().__init__(parent)
        self.session = session
        session_id = session.get("session_id", "Unknown")[:8]
        self.title(f"Session Details - {session_id}")
        self.geometry("780x520")
        self.minsize(680, 420)
        self.transient(parent)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (780 // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (520 // 2)
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.configure(fg_color=("#f8fafc", "#161622"))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=f"Session: {session.get('timestamp', '')[:19].replace('T', ' ')}",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=f"Directory: {session.get('directory', '')}  |  Moved: {session.get('files_moved', 0)}  |  Failed: {session.get('files_failed', 0)}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#64748b", "#94a3b8")
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Records Table Container
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

        # Column Header
        col_header = ctk.CTkFrame(table_container, fg_color=("#f1f5f9", "#272a3d"), height=36, corner_radius=6)
        col_header.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        col_header.grid_columnconfigure(0, weight=4)  # File Name
        col_header.grid_columnconfigure(1, weight=2)  # Category
        col_header.grid_columnconfigure(2, weight=5)  # Moved To
        col_header.grid_columnconfigure(3, weight=2)  # Status

        ctk.CTkLabel(col_header, text="FILE NAME", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=0, sticky="w", padx=12)
        ctk.CTkLabel(col_header, text="CATEGORY", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(col_header, text="DESTINATION PATH", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=2, sticky="w", padx=8)
        ctk.CTkLabel(col_header, text="STATUS", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#475569", "#94a3b8")).grid(row=0, column=3, sticky="w", padx=12)

        # Scrollable rows
        scroll_list = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        scroll_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
        scroll_list.grid_columnconfigure(0, weight=4)
        scroll_list.grid_columnconfigure(1, weight=2)
        scroll_list.grid_columnconfigure(2, weight=5)
        scroll_list.grid_columnconfigure(3, weight=2)

        records: List[Dict] = session.get("records", [])
        for idx, rec in enumerate(records):
            bg = ("#f8fafc", "#232334") if idx % 2 == 0 else ("transparent", "transparent")
            row_frame = ctk.CTkFrame(scroll_list, fg_color=bg, corner_radius=6, height=32)
            row_frame.grid(row=idx, column=0, columnspan=4, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(0, weight=4)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=5)
            row_frame.grid_columnconfigure(3, weight=2)

            filename = rec.get("filename", "")
            if not filename and "original_path" in rec:
                from pathlib import Path
                filename = Path(rec["original_path"]).name

            # Filename
            ctk.CTkLabel(
                row_frame,
                text=filename,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=12, pady=4)

            # Category
            ctk.CTkLabel(
                row_frame,
                text=rec.get("category", "Others"),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            ).grid(row=0, column=1, sticky="w", padx=8, pady=4)

            # Dest Path
            dest_str = rec.get("new_path", "")
            ctk.CTkLabel(
                row_frame,
                text=dest_str,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#3b82f6", "#60a5fa"),
                anchor="w"
            ).grid(row=0, column=2, sticky="w", padx=8, pady=4)

            # Status pill
            status_text = rec.get("status", "moved").capitalize()
            status_color = "#10b981" if status_text.lower() in ("moved", "restored") else "#ef4444"
            ctk.CTkLabel(
                row_frame,
                text=status_text,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=status_color,
                anchor="w"
            ).grid(row=0, column=3, sticky="w", padx=12, pady=4)

        if not records:
            ctk.CTkLabel(
                scroll_list,
                text="No file records found for this session.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=("#94a3b8", "#64748b")
            ).grid(row=0, column=0, columnspan=4, pady=30)

        # Close button
        btn_close = ctk.CTkButton(
            self,
            text="Close",
            width=100,
            height=34,
            command=self.destroy
        )
        btn_close.grid(row=2, column=0, sticky="e", padx=24, pady=(4, 20))
