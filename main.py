"""
main.py
-------
Polished Tkinter GUI for Smart File Organizer.

UI is redesigned without changing the project's core modules:
organizer.py, analyzer.py, duplicate_detector.py, undo_manager.py,
settings_manager.py, history_manager.py, report_generator.py,
auth_manager.py, logger.py and utils.py.

Run:
    python main.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

import organizer
import analyzer
import duplicate_detector
import undo_manager
import settings_manager
import history_manager
import report_generator
import auth_manager
import logger as log_module
from utils import format_size


# ============================================================
# THEME
# ============================================================

BG = "#F4F7FC"
CARD = "#FFFFFF"
TEXT = "#172033"
MUTED = "#7A8499"

PRIMARY = "#5B5FEF"
PRIMARY_DARK = "#474BC7"
SECONDARY = "#8B5CF6"
ACCENT = "#06B6D4"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"

SIDEBAR_BG = "#171B3A"
SIDEBAR_HOVER = "#242951"
SIDEBAR_ACTIVE = "#5B5FEF"
HEADER_BG = "#FFFFFF"
BORDER = "#E7EAF2"

FONT = "Segoe UI"

NAV_ITEMS = [
    ("▦", "Dashboard"),
    ("⌕", "Analyze"),
    ("↗", "Organize"),
    ("⧉", "Duplicates"),
    ("▣", "Large Files"),
    ("□", "Empty Folders"),
    ("◷", "History"),
    ("▤", "Reports"),
    ("⚙", "Settings"),
]


# ============================================================
# SMALL UI HELPERS
# ============================================================

def make_button(parent, text, command, bg=PRIMARY, fg="white",
                width=None, font_size=10, padx=18, pady=9):
    options = {
        "text": text,
        "command": command,
        "font": (FONT, font_size, "bold"),
        "bg": bg,
        "fg": fg,
        "activebackground": PRIMARY_DARK if bg == PRIMARY else bg,
        "activeforeground": fg,
        "relief": "flat",
        "bd": 0,
        "cursor": "hand2",
        "padx": padx,
        "pady": pady,
        "highlightthickness": 0,
    }
    if width:
        options["width"] = width

    button = tk.Button(parent, **options)

    # Slight visual hover effect.
    original = bg
    hover = PRIMARY_DARK if bg == PRIMARY else (
        "#6D28D9" if bg == SECONDARY else bg
    )
    button.bind("<Enter>", lambda e: button.config(bg=hover))
    button.bind("<Leave>", lambda e: button.config(bg=original))
    return button


def make_entry(parent, variable, show=None, width=30):
    wrapper = tk.Frame(parent, bg="#F7F8FC", highlightbackground=BORDER,
                       highlightthickness=1)
    entry = tk.Entry(
        wrapper,
        textvariable=variable,
        font=(FONT, 11),
        bg="#F7F8FC",
        fg=TEXT,
        insertbackground=PRIMARY,
        relief="flat",
        bd=0,
        width=width,
        show=show if show else "",
    )
    entry.pack(fill="x", padx=12, pady=10)
    return wrapper, entry


def make_card(parent, padx=18, pady=16):
    return tk.Frame(
        parent,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1,
        bd=0,
        padx=padx,
        pady=pady,
    )


# ============================================================
# REGISTER
# ============================================================

class RegisterDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Create Account")
        self.geometry("480x590")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        # Decorative top section.
        top = tk.Frame(self, bg=SIDEBAR_BG, height=125)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(
            top, text="✦", font=(FONT, 34, "bold"),
            bg=SIDEBAR_BG, fg="#A78BFA"
        ).pack(pady=(16, 0))

        tk.Label(
            top, text="Create your account",
            font=(FONT, 18, "bold"),
            bg=SIDEBAR_BG, fg="white"
        ).pack()

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=38, pady=25)

        tk.Label(
            content, text="Join Smart File Organizer",
            font=(FONT, 13, "bold"), bg=BG, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            content,
            text="Create an account to access your personal organizer.",
            font=(FONT, 9), bg=BG, fg=MUTED
        ).pack(anchor="w", pady=(3, 20))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()

        self._field(content, "Username", self.username_var)
        self._field(content, "Password", self.password_var, "*")
        self._field(content, "Confirm password", self.confirm_var, "*")

        self.message_label = tk.Label(
            content, text="", font=(FONT, 9, "bold"),
            bg=BG, fg=DANGER, wraplength=380
        )
        self.message_label.pack(anchor="w", pady=(4, 8))

        make_button(
            content, "CREATE ACCOUNT", self._on_register,
            bg=SUCCESS, width=22
        ).pack(fill="x", pady=(5, 8))

        tk.Label(
            content,
            text="Your password is securely hashed by auth_manager.py.",
            font=(FONT, 8), bg=BG, fg=MUTED
        ).pack(pady=(8, 0))

        self.bind("<Return>", lambda event: self._on_register())

    def _field(self, parent, label, variable, show=None):
        tk.Label(
            parent, text=label, font=(FONT, 9, "bold"),
            bg=BG, fg=TEXT
        ).pack(anchor="w", pady=(0, 6))

        wrapper, _ = make_entry(parent, variable, show=show, width=38)
        wrapper.pack(fill="x", pady=(0, 14))

    def _on_register(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if password != confirm:
            self.message_label.config(
                text="Passwords do not match.", fg=DANGER
            )
            return

        success, message = auth_manager.register_user(username, password)

        if success:
            self.message_label.config(text=message, fg=SUCCESS)
            self.after(1000, self.destroy)
        else:
            self.message_label.config(text=message, fg=DANGER)


# ============================================================
# LOGIN
# ============================================================

class LoginFrame(tk.Frame):
    def __init__(self, root, on_login_success):
        super().__init__(root, bg=BG)

        self.root = root
        self.on_login_success = on_login_success

        root.title("Smart File Organizer • Login")
        root.geometry("1050x700")
        root.minsize(900, 620)
        root.configure(bg=BG)

        self._build()

    def _build(self):
        # Left branding panel.
        left = tk.Frame(self, bg=SIDEBAR_BG, width=430)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(
            left, text="✦", font=(FONT, 58, "bold"),
            bg=SIDEBAR_BG, fg="#A78BFA"
        ).pack(pady=(100, 0))

        tk.Label(
            left, text="SMART", font=(FONT, 27, "bold"),
            bg=SIDEBAR_BG, fg="white"
        ).pack(pady=(12, 0))

        tk.Label(
            left, text="FILE ORGANIZER", font=(FONT, 27, "bold"),
            bg=SIDEBAR_BG, fg="#A78BFA"
        ).pack()

        tk.Label(
            left,
            text="Organize smarter.\nFind faster. Stay clutter-free.",
            font=(FONT, 12),
            bg=SIDEBAR_BG, fg="#C7CCE8",
            justify="center"
        ).pack(pady=22)

        feature_frame = tk.Frame(left, bg=SIDEBAR_BG)
        feature_frame.pack(pady=15)

        features = [
            ("✓", "Smart file categorization"),
            ("✓", "Duplicate detection"),
            ("✓", "Storage analysis"),
            ("✓", "Safe organization"),
        ]

        for icon, text in features:
            row = tk.Frame(feature_frame, bg=SIDEBAR_BG)
            row.pack(anchor="w", pady=7)
            tk.Label(
                row, text=icon, font=(FONT, 10, "bold"),
                bg=SIDEBAR_BG, fg="#34D399"
            ).pack(side="left", padx=(0, 10))
            tk.Label(
                row, text=text, font=(FONT, 10),
                bg=SIDEBAR_BG, fg="#E5E7F5"
            ).pack(side="left")

        # Right login panel.
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        card = tk.Frame(
            right, bg=CARD, highlightbackground=BORDER,
            highlightthickness=1, padx=48, pady=40
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=430)

        tk.Label(
            card, text="Welcome back 👋",
            font=(FONT, 23, "bold"), bg=CARD, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            card, text="Sign in to continue to your organizer",
            font=(FONT, 10), bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(5, 28))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Label(
            card, text="Username", font=(FONT, 9, "bold"),
            bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 6))

        user_wrap, self.username_entry = make_entry(
            card, self.username_var, width=31
        )
        user_wrap.pack(fill="x", pady=(0, 17))

        tk.Label(
            card, text="Password", font=(FONT, 9, "bold"),
            bg=CARD, fg=TEXT
        ).pack(anchor="w", pady=(0, 6))

        pass_wrap, self.password_entry = make_entry(
            card, self.password_var, show="*", width=31
        )
        pass_wrap.pack(fill="x", pady=(0, 9))

        self.message_label = tk.Label(
            card, text="", font=(FONT, 9, "bold"),
            bg=CARD, fg=DANGER, wraplength=320
        )
        self.message_label.pack(anchor="w", pady=(2, 8))

        make_button(
            card, "LOGIN  →", self._on_login,
            bg=PRIMARY, font_size=11, pady=11
        ).pack(fill="x", pady=(4, 12))

        register_row = tk.Frame(card, bg=CARD)
        register_row.pack()

        tk.Label(
            register_row, text="Don't have an account?",
            font=(FONT, 9), bg=CARD, fg=MUTED
        ).pack(side="left")

        register_btn = tk.Button(
            register_row, text="Create one",
            command=self._on_register,
            font=(FONT, 9, "bold"),
            bg=CARD, fg=PRIMARY,
            activebackground=CARD, activeforeground=PRIMARY_DARK,
            relief="flat", bd=0, cursor="hand2"
        )
        register_btn.pack(side="left", padx=(5, 0))

        self.root.bind("<Return>", lambda event: self._on_login())
        self.username_entry.focus_set()

    def _on_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self.message_label.config(
                text="Please enter both username and password.",
                fg=DANGER
            )
            return

        success, message = auth_manager.verify_login(username, password)

        if success:
            self.message_label.config(text=message, fg=SUCCESS)
            self.root.unbind("<Return>")
            self.after(250, self.on_login_success)
        else:
            self.message_label.config(text=message, fg=DANGER)

    def _on_register(self):
        RegisterDialog(self.root)


# ============================================================
# MAIN APPLICATION
# ============================================================

class SmartFileOrganizerApp:
    def __init__(self, root, username="User"):
        self.root = root
        self.username = username

        self.root.title("Smart File Organizer")
        self.root.geometry("1200x760")
        self.root.minsize(1000, 680)
        self.root.configure(bg=BG)

        # Application state.
        self.selected_folder = None
        self.metadata_list = []
        self.duplicate_groups = []
        self.large_files = []
        self.empty_folders = []
        self.dashboard_stats = None
        self.settings = settings_manager.load_settings()

        log_module.set_logging_enabled(
            self.settings["enable_logging"]
        )

        self.nav_buttons = {}
        self.pages = {}
        self.current_page = "Dashboard"

        self._configure_styles()
        self._build_layout()

        default_folder = self.settings.get("default_folder", "")
        if default_folder and Path(default_folder).is_dir():
            self.selected_folder = Path(default_folder)
            self.folder_status_label.config(
                text=str(self.selected_folder)
            )
            self.status_var.set(
                "Default folder loaded. Run an analysis when ready."
            )

        self._show_page("Dashboard")

    # --------------------------------------------------------
    # Styles
    # --------------------------------------------------------

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor="#E8EBF4",
            background=PRIMARY,
            bordercolor="#E8EBF4",
            lightcolor=PRIMARY,
            darkcolor=PRIMARY,
            thickness=10,
        )

        style.configure(
            "Modern.Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            rowheight=34,
            borderwidth=0,
            font=(FONT, 9),
        )

        style.configure(
            "Modern.Treeview.Heading",
            background="#EEF0F8",
            foreground=TEXT,
            font=(FONT, 9, "bold"),
            relief="flat",
            padding=8,
        )

        style.map(
            "Modern.Treeview",
            background=[("selected", "#E7E8FF")],
            foreground=[("selected", TEXT)],
        )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    def _build_layout(self):
        # Sidebar.
        sidebar = tk.Frame(self.root, bg=SIDEBAR_BG, width=235)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=SIDEBAR_BG)
        brand.pack(fill="x", padx=22, pady=(28, 30))

        tk.Label(
            brand, text="✦", font=(FONT, 30, "bold"),
            bg=SIDEBAR_BG, fg="#A78BFA"
        ).pack(side="left")

        title_frame = tk.Frame(brand, bg=SIDEBAR_BG)
        title_frame.pack(side="left", padx=10)

        tk.Label(
            title_frame, text="SMART FILE",
            font=(FONT, 12, "bold"),
            bg=SIDEBAR_BG, fg="white"
        ).pack(anchor="w")

        tk.Label(
            title_frame, text="ORGANIZER",
            font=(FONT, 12, "bold"),
            bg=SIDEBAR_BG, fg="#A78BFA"
        ).pack(anchor="w")

        self.nav_buttons = {}

        for icon, name in NAV_ITEMS:
            btn = tk.Button(
                sidebar,
                text=f"  {icon}    {name}",
                anchor="w",
                font=(FONT, 10, "bold"),
                bg=SIDEBAR_BG,
                fg="#D8DCF0",
                activebackground=SIDEBAR_HOVER,
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=16,
                pady=11,
                cursor="hand2",
                command=lambda page=name: self._show_page(page),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = btn

        # Bottom user area.
        user_area = tk.Frame(
            sidebar, bg=SIDEBAR_HOVER,
            highlightbackground="#33385F",
            highlightthickness=1
        )
        user_area.pack(side="bottom", fill="x", padx=14, pady=18)

        avatar = tk.Label(
            user_area, text="👤", font=(FONT, 16),
            bg=SIDEBAR_HOVER, fg="white"
        )
        avatar.pack(side="left", padx=(12, 7), pady=10)

        user_text = tk.Frame(user_area, bg=SIDEBAR_HOVER)
        user_text.pack(side="left", pady=8)

        tk.Label(
            user_text, text=self.username,
            font=(FONT, 9, "bold"),
            bg=SIDEBAR_HOVER, fg="white"
        ).pack(anchor="w")

        tk.Label(
            user_text, text="Signed in",
            font=(FONT, 8),
            bg=SIDEBAR_HOVER, fg="#AEB5D3"
        ).pack(anchor="w")

        # Main side.
        main_area = tk.Frame(self.root, bg=BG)
        main_area.pack(side="left", fill="both", expand=True)

        # Header.
        header = tk.Frame(
            main_area, bg=HEADER_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            height=76
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        left_header = tk.Frame(header, bg=HEADER_BG)
        left_header.pack(side="left", fill="y", padx=26)

        self.page_title_label = tk.Label(
            left_header, text="Dashboard",
            font=(FONT, 18, "bold"),
            bg=HEADER_BG, fg=TEXT
        )
        self.page_title_label.pack(anchor="w", pady=(13, 0))

        self.folder_status_label = tk.Label(
            left_header, text="No folder selected",
            font=(FONT, 8), bg=HEADER_BG, fg=MUTED
        )
        self.folder_status_label.pack(anchor="w")

        make_button(
            header, "📁  Select Folder", self.select_folder,
            bg=PRIMARY, font_size=9, padx=16, pady=8
        ).pack(side="right", padx=26, pady=16)

        # Pages.
        self.content_area = tk.Frame(main_area, bg=BG)
        self.content_area.pack(fill="both", expand=True, padx=20, pady=18)

        for _, item in NAV_ITEMS:
            frame = tk.Frame(self.content_area, bg=BG)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.pages[item] = frame

        # Status.
        status_bar = tk.Frame(main_area, bg="#ECEEF6", height=32)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self.status_var = tk.StringVar(
            value="Select a folder to begin."
        )

        tk.Label(
            status_bar, textvariable=self.status_var,
            font=(FONT, 8), bg="#ECEEF6", fg=MUTED,
            anchor="w"
        ).pack(fill="both", padx=15)

    # --------------------------------------------------------
    # Navigation
    # --------------------------------------------------------

    def _show_page(self, page_name):
        self.current_page = page_name

        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.config(
                    bg=SIDEBAR_ACTIVE,
                    fg="white"
                )
            else:
                btn.config(
                    bg=SIDEBAR_BG,
                    fg="#D8DCF0"
                )

        self.page_title_label.config(text=page_name)

        frame = self.pages[page_name]

        for widget in frame.winfo_children():
            widget.destroy()

        frame.tkraise()

        builder_name = (
            f"_build_{page_name.lower().replace(' ', '_')}_page"
        )

        getattr(self, builder_name)(frame)

    # --------------------------------------------------------
    # Shared helpers
    # --------------------------------------------------------

    def _page_heading(self, frame, title, subtitle=None):
        top = tk.Frame(frame, bg=BG)
        top.pack(fill="x", pady=(4, 18))

        tk.Label(
            top, text=title,
            font=(FONT, 22, "bold"),
            bg=BG, fg=TEXT
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                top, text=subtitle,
                font=(FONT, 9),
                bg=BG, fg=MUTED
            ).pack(anchor="w", pady=(4, 0))

    def _empty_state(self, frame, icon, title, message):
        card = make_card(frame, padx=30, pady=35)
        card.pack(fill="x", padx=5, pady=10)

        tk.Label(
            card, text=icon,
            font=(FONT, 35),
            bg=CARD, fg=PRIMARY
        ).pack()

        tk.Label(
            card, text=title,
            font=(FONT, 15, "bold"),
            bg=CARD, fg=TEXT
        ).pack(pady=(10, 5))

        tk.Label(
            card, text=message,
            font=(FONT, 9),
            bg=CARD, fg=MUTED,
            justify="center"
        ).pack()

    def _require_folder(self):
        if not self.selected_folder:
            messagebox.showwarning(
                "No Folder Selected",
                "Please select a folder first."
            )
            return False
        return True

    def _table(self, parent, columns, widths, height=15):
        container = tk.Frame(parent, bg=CARD)
        container.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            height=height,
            style="Modern.Treeview"
        )

        for column, width in zip(columns, widths):
            tree.heading(column, text=column.title())
            tree.column(column, width=width)

        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        return tree

    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Select a folder to organize"
        )

        if not folder:
            return

        self.selected_folder = Path(folder)
        self.folder_status_label.config(text=str(self.selected_folder))

        self.metadata_list = []
        self.duplicate_groups = []
        self.large_files = []
        self.empty_folders = []
        self.dashboard_stats = None

        self.status_var.set(
            "Folder selected. Go to Analyze to scan it."
        )
        self._show_page(self.current_page)

    # ========================================================
    # DASHBOARD
    # ========================================================

    def _build_dashboard_page(self, frame):
        self._page_heading(
            frame,
            "Dashboard",
            "A quick overview of your selected folder"
        )

        if not self.dashboard_stats:
            welcome = make_card(frame, padx=30, pady=28)
            welcome.pack(fill="x", padx=5, pady=5)

            tk.Label(
                welcome, text="👋 Welcome to your file dashboard",
                font=(FONT, 16, "bold"),
                bg=CARD, fg=TEXT
            ).pack(anchor="w")

            tk.Label(
                welcome,
                text="Select a folder and run an analysis to see your "
                     "files, storage, duplicates and categories here.",
                font=(FONT, 10),
                bg=CARD, fg=MUTED,
                wraplength=750, justify="left"
            ).pack(anchor="w", pady=(8, 18))

            make_button(
                welcome, "📁 Select Folder",
                self.select_folder, bg=PRIMARY
            ).pack(anchor="w")

            return

        stats = self.dashboard_stats

        cards_frame = tk.Frame(frame, bg=BG)
        cards_frame.pack(fill="x", pady=(0, 16))

        cards = [
            ("▦", "Total Files", stats["total_files"], PRIMARY),
            ("◉", "Storage Used", stats["total_size_readable"], ACCENT),
            ("⧉", "Duplicates", stats["duplicates"], DANGER),
            ("▣", "Large Files", stats["large_files"], WARNING),
            ("□", "Empty Folders", stats["empty_folders"], SECONDARY),
            ("●", "Categories", stats["categories"], SUCCESS),
        ]

        for i, (icon, label, value, accent) in enumerate(cards):
            card = make_card(cards_frame, padx=18, pady=16)
            card.grid(
                row=i // 3, column=i % 3,
                padx=7, pady=7, sticky="nsew"
            )
            cards_frame.grid_columnconfigure(
                i % 3, weight=1
            )

            tk.Label(
                card, text=icon, font=(FONT, 18, "bold"),
                bg=CARD, fg=accent
            ).pack(anchor="w")

            tk.Label(
                card, text=str(value),
                font=(FONT, 21, "bold"),
                bg=CARD, fg=TEXT
            ).pack(anchor="w", pady=(5, 0))

            tk.Label(
                card, text=label,
                font=(FONT, 9),
                bg=CARD, fg=MUTED
            ).pack(anchor="w")

        chart_card = make_card(frame, padx=22, pady=20)
        chart_card.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(
            chart_card, text="Files by Category",
            font=(FONT, 14, "bold"),
            bg=CARD, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            chart_card,
            text="Distribution of scanned files",
            font=(FONT, 9),
            bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(2, 16))

        distribution = stats.get("distribution", {})
        max_count = max(distribution.values()) if distribution else 1

        bar_colors = [
            PRIMARY, SECONDARY, ACCENT,
            SUCCESS, WARNING, DANGER
        ]

        for index, (category, count) in enumerate(
            sorted(distribution.items(), key=lambda kv: -kv[1])
        ):
            row = tk.Frame(chart_card, bg=CARD)
            row.pack(fill="x", pady=6)

            tk.Label(
                row, text=category,
                font=(FONT, 9, "bold"),
                bg=CARD, fg=TEXT,
                width=16, anchor="w"
            ).pack(side="left")

            track = tk.Frame(
                row, bg="#EDF0F7", height=12
            )
            track.pack(side="left", fill="x", expand=True, padx=8)
            track.pack_propagate(False)

            ratio = count / max_count if max_count else 0
            fill = tk.Frame(
                track,
                bg=bar_colors[index % len(bar_colors)]
            )
            fill.place(
                relx=0, rely=0,
                relwidth=max(ratio, 0.01),
                relheight=1
            )

            tk.Label(
                row, text=str(count),
                font=(FONT, 9, "bold"),
                bg=CARD, fg=MUTED,
                width=5, anchor="e"
            ).pack(side="right")

    # ========================================================
    # ANALYZE
    # ========================================================

    def _build_analyze_page(self, frame):
        self._page_heading(
            frame,
            "Analyze",
            "Scan metadata, duplicates, large files and empty folders"
        )

        card = make_card(frame, padx=25, pady=25)
        card.pack(fill="x", padx=5)

        tk.Label(
            card,
            text="🔎 Folder Analysis",
            font=(FONT, 15, "bold"),
            bg=CARD, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            card,
            text="The analyzer collects file metadata and then checks "
                 "for duplicates, large files and empty folders.",
            font=(FONT, 9),
            bg=CARD, fg=MUTED,
            wraplength=800,
            justify="left"
        ).pack(anchor="w", pady=(5, 18))

        subfolder_var = tk.BooleanVar(
            value=self.settings["include_subfolders"]
        )

        tk.Checkbutton(
            card,
            text="Include subfolders",
            variable=subfolder_var,
            command=lambda: self._update_subfolder_setting(
                subfolder_var.get()
            ),
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            selectcolor="#E9E9FF",
            font=(FONT, 9, "bold"),
        ).pack(anchor="w", pady=(0, 18))

        make_button(
            card, "▶  Run Analysis",
            self.run_analysis, bg=SUCCESS,
            font_size=10, padx=20, pady=10
        ).pack(anchor="w")

        progress_frame = tk.Frame(card, bg=CARD)
        progress_frame.pack(fill="x", pady=(20, 0))

        self.analyze_progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            style="Modern.Horizontal.TProgressbar"
        )
        self.analyze_progress.pack(fill="x")

        self.analyze_result_label = tk.Label(
            card, text="",
            font=(FONT, 9),
            bg=CARD, fg=MUTED,
            justify="left"
        )
        self.analyze_result_label.pack(
            anchor="w", pady=(12, 0)
        )

    def _update_subfolder_setting(self, value):
        self.settings = settings_manager.update_setting(
            "include_subfolders", value
        )

    def run_analysis(self):
        if not self._require_folder():
            return

        logger = log_module.setup_logger()
        include_subfolders = self.settings["include_subfolders"]

        self.status_var.set("Scanning folder...")
        self.root.update_idletasks()

        try:
            log_module.log_event(
                logger,
                f"Scan started for '{self.selected_folder}'"
            )

            self.metadata_list = analyzer.analyze_folder(
                self.selected_folder,
                include_subfolders=include_subfolders
            )

            log_module.log_event(
                logger,
                f"Scan completed: {len(self.metadata_list)} file(s)"
            )

        except (FileNotFoundError, NotADirectoryError) as e:
            messagebox.showerror("Folder Error", str(e))
            return
        except PermissionError:
            messagebox.showerror(
                "Permission Denied",
                "You don't have permission to read this folder."
            )
            return

        total = len(self.metadata_list)

        self.analyze_progress["maximum"] = max(total, 1)
        self.analyze_progress["value"] = total // 2
        self.root.update_idletasks()

        log_module.log_event(
            logger, "Duplicate detection started"
        )

        self.duplicate_groups = (
            duplicate_detector.find_duplicates(
                self.metadata_list
            )
        )

        log_module.log_event(
            logger,
            f"Duplicate detection completed: "
            f"{len(self.duplicate_groups)} group(s) found"
        )

        threshold = self.settings["large_file_threshold_mb"]

        self.large_files = analyzer.find_large_files(
            self.metadata_list, threshold
        )

        self.empty_folders = analyzer.find_empty_folders(
            self.selected_folder
        )

        self.analyze_progress["value"] = total

        self.dashboard_stats = analyzer.get_dashboard_stats(
            self.metadata_list,
            duplicate_group_count=len(self.duplicate_groups),
            large_file_count=len(self.large_files),
            empty_folder_count=len(self.empty_folders),
        )

        self.analyze_result_label.config(
            text=(
                f"✓ Analysis complete\n\n"
                f"Found {total} file(s)\n"
                f"• {len(self.duplicate_groups)} duplicate group(s)\n"
                f"• {len(self.large_files)} large file(s)\n"
                f"• {len(self.empty_folders)} empty folder(s)"
            ),
            fg=SUCCESS
        )

        self.status_var.set("Analysis complete.")
        self._show_page("Dashboard")

    # ========================================================
    # ORGANIZE
    # ========================================================

    def _build_organize_page(self, frame):
        self._page_heading(
            frame,
            "Organize",
            "Safely move files into category folders"
        )

        if not self.metadata_list:
            self._empty_state(
                frame, "↗",
                "Nothing ready to organize",
                "Run an analysis first. Your files will be categorized "
                "without overwriting existing files."
            )
            return

        card = make_card(frame, padx=25, pady=25)
        card.pack(fill="x", padx=5)

        tk.Label(
            card,
            text=f"📂 {len(self.metadata_list)} file(s) ready",
            font=(FONT, 16, "bold"),
            bg=CARD, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            card,
            text="Files will be moved into category folders. "
                 "Existing files are never overwritten.",
            font=(FONT, 9),
            bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(5, 18))

        actions = tk.Frame(card, bg=CARD)
        actions.pack(anchor="w")

        make_button(
            actions, "↗  Organize Files",
            self.organize_files, bg=PRIMARY
        ).pack(side="left", padx=(0, 10))

        make_button(
            actions, "↶  Undo Last Organization",
            self.undo_last_organization, bg=DANGER
        ).pack(side="left")

        self.organize_progress = ttk.Progressbar(
            card,
            orient="horizontal",
            mode="determinate",
            style="Modern.Horizontal.TProgressbar"
        )
        self.organize_progress.pack(fill="x", pady=(22, 0))

        self.organize_progress_label = tk.Label(
            card, text="",
            font=(FONT, 9), bg=CARD, fg=MUTED
        )
        self.organize_progress_label.pack(
            anchor="w", pady=(8, 0)
        )

        self.organize_summary_label = tk.Label(
            card, text="",
            font=(FONT, 9),
            bg=CARD, fg=TEXT,
            justify="left"
        )
        self.organize_summary_label.pack(
            anchor="w", pady=(14, 0)
        )

    def organize_files(self):
        if not self._require_folder() or not self.metadata_list:
            return

        total = len(self.metadata_list)

        if self.settings.get("confirm_before_organize", True):
            confirmed = messagebox.askyesno(
                "Confirm Organization",
                f"You are about to organize {total} file(s) "
                "into category folders.\n\n"
                "Existing files will not be overwritten.\n\n"
                "Continue?"
            )
            if not confirmed:
                return

        self.organize_progress["maximum"] = max(total, 1)
        self.organize_progress["value"] = 0
        self.status_var.set("Organizing...")

        def update_progress(done, total_count):
            self.organize_progress["value"] = done
            self.organize_progress_label.config(
                text=f"{done} / {total_count} files processed"
            )
            self.root.update_idletasks()

        include_subfolders = self.settings["include_subfolders"]

        try:
            summary = organizer.organize_files(
                self.selected_folder,
                include_subfolders=include_subfolders,
                progress_callback=update_progress
            )
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"Something went wrong:\n{e}"
            )
            self.status_var.set("Organization failed.")
            return

        moved_count = len(summary["moved"])
        skipped_count = len(summary["skipped"])
        error_count = len(summary["errors"])

        history_manager.add_history_entry(
            "Organization",
            moved_count,
            error_count == 0,
            details=(
                f"{moved_count} moved, "
                f"{skipped_count} skipped, "
                f"{error_count} errors"
            )
        )

        summary_text = (
            f"Organization Complete\n\n"
            f"Files scanned: {summary['total']}\n"
            f"Files organized: {moved_count}\n"
            f"Files skipped: {skipped_count}\n"
            f"Errors: {error_count}\n\n"
            f"Created categories: "
            f"{', '.join(summary['categories_used']) if summary['categories_used'] else 'none'}\n\n"
            f"Storage organized: {summary['storage_readable']}"
        )

        self.organize_summary_label.config(
            text=summary_text
        )

        messagebox.showinfo(
            "Organization Complete",
            summary_text
        )

        self.status_var.set(
            f"Done. {moved_count} organized, {error_count} error(s)."
        )

        self.metadata_list = []
        self.duplicate_groups = []
        self.large_files = []
        self.empty_folders = []
        self.dashboard_stats = None

        self._show_page("Organize")

    def undo_last_organization(self):
        confirmed = messagebox.askyesno(
            "Undo Organization",
            "This will move files back to where they were "
            "before the last organization.\n\nContinue?"
        )

        if not confirmed:
            return

        success, message, details = (
            undo_manager.undo_last_operation()
        )

        if not success:
            messagebox.showinfo(
                "Nothing to Undo", message
            )
            return

        restored = details.get("restored", [])
        errors = details.get("errors", [])

        history_manager.add_history_entry(
            "Undo",
            len(restored),
            len(errors) == 0,
            details=(
                f"{len(restored)} restored, "
                f"{len(errors)} errors"
            )
        )

        summary_lines = [
            message,
            "",
            f"Restored: {len(restored)} file(s)"
        ]

        if errors:
            summary_lines.append(
                f"Errors: {len(errors)}"
            )
            for line in errors[:10]:
                summary_lines.append(f"  {line}")

        messagebox.showinfo(
            "Undo Complete",
            "\n".join(summary_lines)
        )

        self.metadata_list = []
        self.duplicate_groups = []
        self.large_files = []
        self.empty_folders = []
        self.dashboard_stats = None

        self._show_page(self.current_page)

    # ========================================================
    # DUPLICATES
    # ========================================================

    def _build_duplicates_page(self, frame):
        self._page_heading(
            frame,
            "Duplicates",
            "Files with identical content detected during analysis"
        )

        if not self.metadata_list:
            self._empty_state(
                frame, "⧉",
                "Run an analysis first",
                "Duplicate detection results will appear here."
            )
            return

        if not self.duplicate_groups:
            self._empty_state(
                frame, "✓",
                "No duplicates found",
                "Great! No duplicate file groups were detected."
            )
            return

        total_wasted = sum(
            group["wasted_space_bytes"]
            for group in self.duplicate_groups
        )

        summary = make_card(frame, padx=20, pady=16)
        summary.pack(fill="x", padx=5, pady=(0, 12))

        tk.Label(
            summary,
            text=f"⧉  {len(self.duplicate_groups)} duplicate group(s)",
            font=(FONT, 13, "bold"),
            bg=CARD, fg=TEXT
        ).pack(side="left")

        tk.Label(
            summary,
            text=f"Potential wasted storage: {format_size(total_wasted)}",
            font=(FONT, 9),
            bg=CARD, fg=DANGER
        ).pack(side="right")

        table_card = make_card(frame, padx=10, pady=10)
        table_card.pack(fill="both", expand=True, padx=5)

        tree = self._table(
            table_card,
            ("group", "file", "size"),
            (80, 650, 120),
            height=16
        )

        for group_index, group in enumerate(
            self.duplicate_groups, start=1
        ):
            for entry in group["files"]:
                tree.insert(
                    "", "end",
                    values=(
                        group_index,
                        entry["path"],
                        entry["size_readable"]
                    )
                )

    # ========================================================
    # LARGE FILES
    # ========================================================

    def _build_large_files_page(self, frame):
        self._page_heading(
            frame,
            "Large Files",
            f"Files above your configured "
            f"{self.settings['large_file_threshold_mb']} MB threshold"
        )

        if not self.metadata_list:
            self._empty_state(
                frame, "▣",
                "Run an analysis first",
                "Large file results will appear here."
            )
            return

        if not self.large_files:
            self._empty_state(
                frame, "✓",
                "No large files found",
                "No files exceed your current threshold."
            )
            return

        total_bytes = sum(
            entry["size_bytes"]
            for entry in self.large_files
        )

        summary = make_card(frame, padx=20, pady=16)
        summary.pack(fill="x", padx=5, pady=(0, 12))

        tk.Label(
            summary,
            text=f"▣  {len(self.large_files)} large file(s)",
            font=(FONT, 13, "bold"),
            bg=CARD, fg=TEXT
        ).pack(side="left")

        tk.Label(
            summary,
            text=f"Total: {format_size(total_bytes)}",
            font=(FONT, 9),
            bg=CARD, fg=WARNING
        ).pack(side="right")

        table_card = make_card(frame, padx=10, pady=10)
        table_card.pack(fill="both", expand=True, padx=5)

        tree = self._table(
            table_card,
            ("file", "size", "path"),
            (220, 110, 560),
            height=16
        )

        for entry in self.large_files:
            tree.insert(
                "", "end",
                values=(
                    entry["name"],
                    entry["size_readable"],
                    entry["path"]
                )
            )

    # ========================================================
    # EMPTY FOLDERS
    # ========================================================

    def _build_empty_folders_page(self, frame):
        self._page_heading(
            frame,
            "Empty Folders",
            "Empty folders are reported only — never deleted automatically"
        )

        if not self.metadata_list:
            self._empty_state(
                frame, "□",
                "Run an analysis first",
                "Empty folder results will appear here."
            )
            return

        summary = make_card(frame, padx=20, pady=16)
        summary.pack(fill="x", padx=5, pady=(0, 12))

        count = len(self.empty_folders)

        tk.Label(
            summary,
            text=f"□  {count} empty folder(s) found",
            font=(FONT, 13, "bold"),
            bg=CARD,
            fg=SUCCESS if count == 0 else WARNING
        ).pack(anchor="w")

        if not self.empty_folders:
            tk.Label(
                summary,
                text="No empty folders were detected.",
                font=(FONT, 9),
                bg=CARD, fg=MUTED
            ).pack(anchor="w", pady=(4, 0))
            return

        table_card = make_card(frame, padx=10, pady=10)
        table_card.pack(fill="both", expand=True, padx=5)

        list_frame = tk.Frame(table_card, bg=CARD)
        list_frame.pack(fill="both", expand=True)

        listbox = tk.Listbox(
            list_frame,
            font=("Consolas", 9),
            bg=CARD,
            fg=TEXT,
            selectbackground="#E7E8FF",
            selectforeground=TEXT,
            relief="flat",
            highlightthickness=0,
            bd=0
        )
        listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=listbox.yview
        )
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        for path in self.empty_folders:
            listbox.insert("end", path)

    # ========================================================
    # HISTORY
    # ========================================================

    def _build_history_page(self, frame):
        self._page_heading(
            frame,
            "History",
            "A record of your organizer operations"
        )

        history = history_manager.load_history()

        if not history:
            self._empty_state(
                frame, "◷",
                "No operations yet",
                "Your organization and undo activity will appear here."
            )
            return

        card = make_card(frame, padx=10, pady=10)
        card.pack(fill="both", expand=True, padx=5)

        tree = self._table(
            card,
            ("timestamp", "operation", "files", "result", "details"),
            (160, 120, 70, 110, 430),
            height=18
        )

        for entry in history:
            display_time = entry["timestamp"].replace(
                "T", " "
            )

            tree.insert(
                "", "end",
                values=(
                    display_time,
                    entry["operation"],
                    entry["files_count"],
                    "Success"
                    if entry["success"]
                    else "Had errors",
                    entry["details"]
                )
            )

    # ========================================================
    # REPORTS
    # ========================================================

    def _build_reports_page(self, frame):
        self._page_heading(
            frame,
            "Reports",
            "Export the current analysis for later use"
        )

        if not self.metadata_list:
            self._empty_state(
                frame, "▤",
                "No report available",
                "Run an analysis first to generate CSV and JSON reports."
            )
            return

        card = make_card(frame, padx=25, pady=25)
        card.pack(fill="x", padx=5)

        tk.Label(
            card,
            text="▤  Export Reports",
            font=(FONT, 15, "bold"),
            bg=CARD, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            card,
            text="Save the current analysis inside the reports/ folder.",
            font=(FONT, 9),
            bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(5, 20))

        buttons = tk.Frame(card, bg=CARD)
        buttons.pack(anchor="w")

        make_button(
            buttons,
            "⬇  Export CSV",
            self.export_csv_report,
            bg=PRIMARY
        ).pack(side="left", padx=(0, 10))

        make_button(
            buttons,
            "⬇  Export JSON",
            self.export_json_report,
            bg=SECONDARY
        ).pack(side="left")

        self.report_result_label = tk.Label(
            card, text="",
            font=(FONT, 9),
            bg=CARD, fg=SUCCESS,
            wraplength=800,
            justify="left"
        )
        self.report_result_label.pack(
            anchor="w", pady=(18, 0)
        )

    def export_csv_report(self):
        path = report_generator.export_csv(
            self.metadata_list
        )
        self.report_result_label.config(
            text=f"✓ CSV report saved to:\n{path}"
        )
        messagebox.showinfo(
            "Report Exported",
            f"CSV report saved to:\n{path}"
        )

    def export_json_report(self):
        if not self.dashboard_stats:
            messagebox.showwarning(
                "No Statistics",
                "Run an analysis first."
            )
            return

        path = report_generator.export_json(
            self.dashboard_stats
        )
        self.report_result_label.config(
            text=f"✓ JSON report saved to:\n{path}"
        )
        messagebox.showinfo(
            "Report Exported",
            f"JSON report saved to:\n{path}"
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    def _build_settings_page(self, frame):
        self._page_heading(
            frame,
            "Settings",
            "Customize how Smart File Organizer behaves"
        )

        card = make_card(frame, padx=25, pady=25)
        card.pack(fill="x", padx=5)

        tk.Label(
            card,
            text="⚙  Organizer Settings",
            font=(FONT, 15, "bold"),
            bg=CARD, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            card,
            text="These settings are saved locally.",
            font=(FONT, 9),
            bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(4, 20))

        form = tk.Frame(card, bg=CARD)
        form.pack(fill="x")

        tk.Label(
            form, text="Large file threshold (MB)",
            font=(FONT, 9, "bold"),
            bg=CARD, fg=TEXT
        ).grid(row=0, column=0, sticky="w", pady=9)

        threshold_var = tk.StringVar(
            value=str(
                self.settings["large_file_threshold_mb"]
            )
        )

        threshold_entry = tk.Entry(
            form,
            textvariable=threshold_var,
            font=(FONT, 10),
            width=12,
            bg="#F7F8FC",
            fg=TEXT,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1
        )
        threshold_entry.grid(
            row=0, column=1,
            sticky="w", padx=20
        )

        subfolder_var = tk.BooleanVar(
            value=self.settings["include_subfolders"]
        )
        tk.Checkbutton(
            form,
            text="Include Subfolders",
            variable=subfolder_var,
            bg=CARD, fg=TEXT,
            activebackground=CARD,
            selectcolor="#E9E9FF",
            font=(FONT, 9)
        ).grid(
            row=1, column=0,
            columnspan=2,
            sticky="w", pady=6
        )

        never_overwrite_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            form,
            text="Never overwrite files (core safety guarantee)",
            variable=never_overwrite_var,
            state="disabled",
            bg=CARD, fg="#8B91A3",
            disabledforeground="#8B91A3",
            selectcolor="#EEEEF5",
            font=(FONT, 9)
        ).grid(
            row=2, column=0,
            columnspan=2,
            sticky="w", pady=6
        )

        logging_var = tk.BooleanVar(
            value=self.settings["enable_logging"]
        )
        tk.Checkbutton(
            form,
            text="Enable Logging",
            variable=logging_var,
            bg=CARD, fg=TEXT,
            activebackground=CARD,
            selectcolor="#E9E9FF",
            font=(FONT, 9)
        ).grid(
            row=3, column=0,
            columnspan=2,
            sticky="w", pady=6
        )

        confirm_var = tk.BooleanVar(
            value=self.settings["confirm_before_organize"]
        )
        tk.Checkbutton(
            form,
            text="Confirm Before Organization",
            variable=confirm_var,
            bg=CARD, fg=TEXT,
            activebackground=CARD,
            selectcolor="#E9E9FF",
            font=(FONT, 9)
        ).grid(
            row=4, column=0,
            columnspan=2,
            sticky="w", pady=6
        )

        tk.Label(
            form, text="Default folder",
            font=(FONT, 9, "bold"),
            bg=CARD, fg=TEXT
        ).grid(
            row=5, column=0,
            sticky="w", pady=9
        )

        default_folder_var = tk.StringVar(
            value=self.settings["default_folder"]
        )

        default_entry = tk.Entry(
            form,
            textvariable=default_folder_var,
            font=(FONT, 10),
            bg="#F7F8FC",
            fg=TEXT,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1,
            width=55
        )
        default_entry.grid(
            row=5, column=1,
            sticky="w", padx=20
        )

        def save():
            try:
                threshold_value = float(
                    threshold_var.get()
                )
                if threshold_value <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Value",
                    "Large file threshold must be a positive number."
                )
                return

            self.settings["large_file_threshold_mb"] = (
                threshold_value
            )
            self.settings["include_subfolders"] = (
                subfolder_var.get()
            )
            self.settings["enable_logging"] = (
                logging_var.get()
            )
            self.settings["confirm_before_organize"] = (
                confirm_var.get()
            )
            self.settings["default_folder"] = (
                default_folder_var.get().strip()
            )

            settings_manager.save_settings(
                self.settings
            )

            log_module.set_logging_enabled(
                self.settings["enable_logging"]
            )

            self.status_var.set(
                "Settings saved successfully."
            )

            messagebox.showinfo(
                "Settings Saved",
                "Your settings have been saved."
            )

        # Remove the harmless placeholder button created above.
        # The real button is below.
        for widget in card.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "✓  Save Settings":
                widget.destroy()

        make_button(
            card, "✓  Save Settings", save,
            bg=SUCCESS, padx=20, pady=10
        ).pack(anchor="w", pady=(22, 0))


# ============================================================
# STARTUP
# ============================================================

def main():
    root = tk.Tk()

    logger = log_module.setup_logger()
    log_module.log_event(
        logger, "Application started"
    )

    def launch_main_app():
        login_frame.destroy()

        root.title("Smart File Organizer")
        root.geometry("1200x760")
        root.minsize(1000, 680)

        log_module.log_event(
            logger, "User logged in"
        )

        SmartFileOrganizerApp(
            root,
            username=login_frame.username_var.get().strip()
        )

    login_frame = LoginFrame(
        root,
        on_login_success=launch_main_app
    )
    login_frame.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()

