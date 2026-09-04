"""
main.py
-------
The GUI (Tkinter). This file is the only one that knows about buttons,
labels and windows - all the real file-organizing logic lives in
organizer.py / utils.py / categories.py / logger.py / undo_manager.py.

Run this file to start the application:
    python main.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

import organizer
import undo_manager


class SmartFileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart File Organizer")
        self.root.geometry("720x600")
        self.root.minsize(680, 560)
        self.root.configure(bg="#f4f6f8")

        # --- state that this class keeps track of ---
        self.selected_folder = None       # Path chosen by the user
        self.current_preview = []         # list of (Path, category)
        self.all_preview_rows = []        # unfiltered rows shown in the tree

        self._build_widgets()
        self._refresh_undo_button()

    # ------------------------------------------------------------------
    # Building the UI
    # ------------------------------------------------------------------
    def _build_widgets(self):
        FONT_HEADER = ("Segoe UI", 18, "bold")
        FONT_SUB = ("Segoe UI", 10)
        FONT_NORMAL = ("Segoe UI", 10)

        # ---------- Header ----------
        header_frame = tk.Frame(self.root, bg="#2c3e50", pady=16)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame, text="Smart File Organizer",
            font=FONT_HEADER, fg="white", bg="#2c3e50"
        ).pack()
        tk.Label(
            header_frame, text="Automatically organize your files",
            font=FONT_SUB, fg="#d0d7de", bg="#2c3e50"
        ).pack()

        # ---------- Folder selection ----------
        folder_frame = tk.Frame(self.root, bg="#f4f6f8", pady=10)
        folder_frame.pack(fill="x", padx=16)

        tk.Button(
            folder_frame, text="Select Folder", command=self.select_folder,
            font=FONT_NORMAL, bg="#3498db", fg="white", relief="flat", padx=10, pady=4
        ).pack(side="left")

        self.folder_label = tk.Label(
            folder_frame, text="Selected Folder:\n(none selected)",
            font=FONT_NORMAL, bg="#f4f6f8", justify="left", anchor="w"
        )
        self.folder_label.pack(side="left", padx=12)

        # ---------- Action buttons ----------
        action_frame = tk.Frame(self.root, bg="#f4f6f8", pady=6)
        action_frame.pack(fill="x", padx=16)

        self.preview_button = tk.Button(
            action_frame, text="Preview Organization", command=self.preview_organization,
            font=FONT_NORMAL, bg="#2ecc71", fg="white", relief="flat", padx=10, pady=4,
            state="disabled"
        )
        self.preview_button.pack(side="left")

        self.organize_button = tk.Button(
            action_frame, text="Organize Files", command=self.organize_files,
            font=FONT_NORMAL, bg="#e67e22", fg="white", relief="flat", padx=10, pady=4,
            state="disabled"
        )
        self.organize_button.pack(side="left", padx=8)

        self.undo_button = tk.Button(
            action_frame, text="Undo Last Organization", command=self.undo_last_organization,
            font=FONT_NORMAL, bg="#e74c3c", fg="white", relief="flat", padx=10, pady=4,
            state="disabled"
        )
        self.undo_button.pack(side="left")

        # ---------- Search box ----------
        search_frame = tk.Frame(self.root, bg="#f4f6f8", pady=6)
        search_frame.pack(fill="x", padx=16)

        tk.Label(search_frame, text="Search:", font=FONT_NORMAL, bg="#f4f6f8").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._apply_search_filter())
        tk.Entry(search_frame, textvariable=self.search_var, font=FONT_NORMAL, width=30).pack(
            side="left", padx=6
        )

        # ---------- Preview table ----------
        table_frame = tk.Frame(self.root, bg="#f4f6f8")
        table_frame.pack(fill="both", expand=True, padx=16, pady=6)

        columns = ("filename", "category")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree.heading("filename", text="File Name")
        self.tree.heading("category", text="Category")
        self.tree.column("filename", width=380)
        self.tree.column("category", width=160)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # ---------- Statistics ----------
        self.stats_label = tk.Label(
            self.root, text="Files Found: 0", justify="left", anchor="w",
            font=FONT_NORMAL, bg="#f4f6f8"
        )
        self.stats_label.pack(fill="x", padx=16)

        # ---------- Progress bar ----------
        progress_frame = tk.Frame(self.root, bg="#f4f6f8", pady=6)
        progress_frame.pack(fill="x", padx=16)

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x")

        self.progress_label = tk.Label(
            progress_frame, text="", font=FONT_NORMAL, bg="#f4f6f8"
        )
        self.progress_label.pack(anchor="w")

        # ---------- Status bar ----------
        self.status_var = tk.StringVar(value="Select a folder to begin.")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var, bd=1, relief="sunken",
            anchor="w", font=("Segoe UI", 9), bg="#eaeaea"
        )
        status_bar.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # Folder selection
    # ------------------------------------------------------------------
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select a folder to organize")
        if not folder:
            return  # user clicked cancel

        self.selected_folder = Path(folder)
        self.folder_label.config(text=f"Selected Folder:\n{self.selected_folder}")
        self.preview_button.config(state="normal")
        self.organize_button.config(state="disabled")  # must preview first
        self._clear_preview_table()
        self.stats_label.config(text="Files Found: 0")
        self.status_var.set("Folder selected. Click 'Preview Organization' to continue.")

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------
    def preview_organization(self):
        if not self.selected_folder:
            return

        try:
            self.current_preview = organizer.preview_organization(self.selected_folder)
        except (FileNotFoundError, NotADirectoryError) as e:
            messagebox.showerror("Folder Error", str(e))
            return
        except PermissionError:
            messagebox.showerror("Permission Denied", "You don't have permission to read this folder.")
            return

        self.all_preview_rows = self.current_preview
        self._populate_preview_table(self.current_preview)

        stats = organizer.get_statistics(self.current_preview)
        self._display_statistics(stats)

        if self.current_preview:
            self.organize_button.config(state="normal")
            self.status_var.set(f"Preview ready - {len(self.current_preview)} file(s) found.")
        else:
            self.organize_button.config(state="disabled")
            self.status_var.set("No files found directly inside this folder.")

    def _populate_preview_table(self, preview_rows):
        self._clear_preview_table()
        for file_path, category in preview_rows:
            self.tree.insert("", "end", values=(file_path.name, category))

    def _clear_preview_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _apply_search_filter(self):
        query = self.search_var.get().strip().lower()
        if not query:
            filtered = self.all_preview_rows
        else:
            filtered = [
                (file_path, category)
                for file_path, category in self.all_preview_rows
                if query in file_path.name.lower() or query in category.lower()
            ]
        self._populate_preview_table(filtered)

    def _display_statistics(self, stats: dict):
        lines = [f"Files Found: {stats['total_files']}", ""]
        for category, count in sorted(stats["by_category"].items()):
            lines.append(f"{category}: {count}")
        lines.append("")
        lines.append(f"Total Size: {stats['total_size_readable']}")
        self.stats_label.config(text="\n".join(lines))

    # ------------------------------------------------------------------
    # Organize
    # ------------------------------------------------------------------
    def organize_files(self):
        if not self.selected_folder or not self.current_preview:
            return

        confirmed = messagebox.askyesno(
            "Confirm Organization",
            "Are you sure you want to organize these files?"
        )
        if not confirmed:
            return

        total = len(self.current_preview)
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = 0
        self.progress_label.config(text=f"0 / {total} files processed")
        self.status_var.set("Organizing...")

        def update_progress(done, total_count):
            self.progress_bar["value"] = done
            self.progress_label.config(text=f"{done} / {total_count} files processed")
            # Forces the window to redraw immediately, so the progress
            # bar visibly moves instead of jumping to 100% at the end.
            self.root.update_idletasks()

        try:
            summary = organizer.organize_files(self.selected_folder, progress_callback=update_progress)
        except Exception as e:  # noqa: BLE001 - last-resort safety net for the GUI
            messagebox.showerror("Unexpected Error", f"Something went wrong:\n{e}")
            self.status_var.set("Organization failed.")
            return

        self._show_organize_summary(summary)
        self._refresh_undo_button()

        # Refresh the preview - the folder now looks different.
        self.preview_organization()

    def _show_organize_summary(self, summary: dict):
        moved_count = len(summary["moved"])
        error_count = len(summary["errors"])

        message_lines = [f"Organization completed.\n", f"Moved: {moved_count} file(s)"]
        if summary["moved"]:
            message_lines.append("")
            for entry in summary["moved"][:10]:
                message_lines.append(f"  {entry['file']} -> {Path(entry['destination']).parent.name}")
            if moved_count > 10:
                message_lines.append(f"  ...and {moved_count - 10} more")

        message_lines.append(f"\nErrors: {error_count}")
        if summary["errors"]:
            for entry in summary["errors"][:10]:
                message_lines.append(f"  {entry['file']}: {entry['error']}")

        messagebox.showinfo("Organization Complete", "\n".join(message_lines))
        self.status_var.set(f"Done. Moved {moved_count} file(s), {error_count} error(s).")

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------
    def undo_last_organization(self):
        confirmed = messagebox.askyesno(
            "Undo Organization",
            "This will move files back to where they were before the last "
            "organization. Continue?"
        )
        if not confirmed:
            return

        success, message, details = undo_manager.undo_last_operation()
        if not success:
            messagebox.showinfo("Nothing to Undo", message)
            return

        restored = details.get("restored", [])
        errors = details.get("errors", [])

        summary_lines = [message, "", f"Restored: {len(restored)} file(s)"]
        if errors:
            summary_lines.append(f"Errors: {len(errors)}")
            for line in errors[:10]:
                summary_lines.append(f"  {line}")

        messagebox.showinfo("Undo Complete", "\n".join(summary_lines))
        self._refresh_undo_button()

        # Refresh preview since the folder contents changed.
        if self.selected_folder:
            self.preview_organization()

    def _refresh_undo_button(self):
        if undo_manager.has_undo_available():
            self.undo_button.config(state="normal")
        else:
            self.undo_button.config(state="disabled")


def main():
    root = tk.Tk()
    app = SmartFileOrganizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
