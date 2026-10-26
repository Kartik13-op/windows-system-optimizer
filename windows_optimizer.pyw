"""Windows maintenance dashboard; the interface uses only standard Tkinter/ttk."""

import tkinter as tk
from tkinter import messagebox, ttk

from launcher import command_script, launch_action, launch_commands
from maintenance import ACTIONS, CATEGORIES


class OptimizerApp:
    def __init__(self, window):
        self.window = window
        window.title("Windows Optimizer")
        window.geometry("1080x760")
        window.minsize(940, 680)
        window.option_add("*Font", "{Segoe UI} 10")
        style = ttk.Style(window)
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("Muted.TLabel", foreground="#555555")
        style.configure("Nav.Toolbutton", padding=(10, 9))
        style.configure("Action.TCheckbutton", font=("Segoe UI", 10, "bold"))
        style.configure("Run.TButton", padding=(14, 6))

        self.selected = tk.StringVar(window, value="Fast Optimize")
        self.filter_text = tk.StringVar(window)
        self.status = tk.StringVar(window, value="Choose actions, then Run selected. Output and prompts stay in their Windows windows.")
        self.checked = {key: tk.BooleanVar(window) for key in ACTIONS}
        self.visible_ids = []

        outer = ttk.Frame(window, padding=20)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="Windows Optimizer", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text=f"{len(ACTIONS)} actions. Direct maintenance, useful diagnostics, visible results.", style="Muted.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Separator(outer).pack(fill="x", pady=(0, 16))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        navigation = ttk.Frame(body)
        navigation.grid(row=0, column=0, sticky="ns", padx=(0, 20))
        ttk.Label(navigation, text="MAINTENANCE", style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        for name in CATEGORIES:
            ttk.Radiobutton(navigation, text=name, value=name, variable=self.selected,
                            style="Nav.Toolbutton", command=self.show_category, width=23).pack(fill="x", pady=(0, 3))
        ttk.Separator(navigation).pack(fill="x", pady=12)
        ttk.Button(navigation, text="Cancel Defender scan", command=lambda: self.run_action("cancel_scan")).pack(fill="x")
        ttk.Label(navigation, text="For other commands, use Ctrl+C\nin their console. A servicing\nbatch stops as a group.", style="Muted.TLabel").pack(anchor="w", pady=10)

        detail = ttk.Frame(body)
        detail.grid(row=0, column=1, sticky="nsew")
        self.title = ttk.Label(detail, style="Heading.TLabel")
        self.title.pack(anchor="w")
        self.subtitle = ttk.Label(detail, style="Muted.TLabel", wraplength=720)
        self.subtitle.pack(fill="x", pady=(5, 12))
        toolbar = ttk.Frame(detail)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Label(toolbar, text="Filter:").pack(side="left", padx=(0, 6))
        ttk.Entry(toolbar, textvariable=self.filter_text).pack(side="left", fill="x", expand=True)
        ttk.Button(toolbar, text="Use preset", command=self.use_preset).pack(side="left", padx=(8, 5))
        ttk.Button(toolbar, text="Clear", command=self.clear_selection).pack(side="left")

        viewport = ttk.Frame(detail)
        viewport.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(viewport, highlightthickness=0, background=style.lookup("TFrame", "background"))
        scrollbar = ttk.Scrollbar(viewport, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.rows = ttk.Frame(self.canvas)
        self.rows_window = self.canvas.create_window((0, 0), window=self.rows, anchor="nw")
        self.rows.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.resize_rows)
        window.bind("<MouseWheel>", self.scroll_rows, add="+")

        controls = ttk.Frame(detail)
        controls.pack(fill="x", pady=(12, 0))
        self.count = ttk.Label(controls, style="Muted.TLabel")
        self.count.pack(side="left")
        self.run_button = ttk.Button(controls, text="Run selected", style="Run.TButton", command=self.run_selected)
        self.run_button.pack(side="right")
        ttk.Button(controls, text="Preview selected", command=self.preview_selected).pack(side="right", padx=(0, 8))

        ttk.Separator(outer).pack(fill="x", pady=(16, 10))
        footer = ttk.Frame(outer)
        footer.pack(fill="x")
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=(12, 0))
        ttk.Label(footer, textvariable=self.status, style="Muted.TLabel", wraplength=890).pack(side="left", fill="x", expand=True)
        self.filter_text.trace_add("write", lambda *args: self.render_rows())
        self.show_category()
        window.bind("<Escape>", lambda event: window.destroy())

    def category_ids(self):
        return CATEGORIES[self.selected.get()][1]

    def show_category(self):
        name = self.selected.get()
        self.title.configure(text=name)
        self.subtitle.configure(text=CATEGORIES[name][0])
        for variable in self.checked.values():
            variable.set(False)
        for key in CATEGORIES[name][2]:
            self.checked[key].set(True)
        self.filter_text.set("")
        self.render_rows()
        self.canvas.yview_moveto(0)

    def render_rows(self):
        query = self.filter_text.get().strip().lower()
        self.visible_ids = [key for key in self.category_ids()
                            if query in (ACTIONS[key].title + " " + ACTIONS[key].description).lower()]
        for child in self.rows.winfo_children():
            child.destroy()
        if not self.visible_ids:
            ttk.Label(self.rows, text="No matching actions in this category.", padding=12).pack(anchor="w")
        for key in self.visible_ids:
            action = ACTIONS[key]
            row = ttk.Frame(self.rows, padding=(6, 11))
            row.pack(fill="x")
            row.columnconfigure(0, weight=1)
            ttk.Checkbutton(row, text=action.title, variable=self.checked[key],
                            style="Action.TCheckbutton", command=self.update_count).grid(row=0, column=0, sticky="w")
            ttk.Button(row, text="Run" if action.script else "Open", width=8,
                       command=lambda action_id=key: self.run_action(action_id)).grid(row=0, column=1, rowspan=3, padx=(12, 5))
            ttk.Label(row, text=action.description, style="Muted.TLabel", wraplength=self.wrap_width(), justify="left").grid(row=1, column=0, sticky="w", padx=(23, 0), pady=(4, 3))
            badge = "Automatic command" if action.script else "Windows window"
            if action.admin:
                badge += " | Administrator prompt"
            ttk.Label(row, text=badge, style="Muted.TLabel").grid(row=2, column=0, sticky="w", padx=(23, 0))
            ttk.Separator(self.rows).pack(fill="x")
        self.update_count()

    def wrap_width(self):
        return max(330, self.canvas.winfo_width() - 135)

    def resize_rows(self, event):
        self.canvas.itemconfigure(self.rows_window, width=event.width)
        self.subtitle.configure(wraplength=max(300, event.width - 10))
        for row in self.rows.winfo_children():
            for child in row.winfo_children():
                if child.winfo_class() == "TLabel" and child.cget("wraplength"):
                    child.configure(wraplength=self.wrap_width())

    def scroll_rows(self, event):
        if str(event.widget).startswith(str(self.rows)) or event.widget == self.canvas:
            self.canvas.yview_scroll(-int(event.delta / 120), "units")
            return "break"

    def chosen_ids(self):
        return [key for key in self.category_ids() if self.checked[key].get()]

    def update_count(self):
        count = len(self.chosen_ids())
        shown = len(self.visible_ids)
        total = len(self.category_ids())
        self.count.configure(text=f"{count} selected | {shown} shown / {total} in category")
        self.run_button.configure(text=f"Run selected ({count})", state="normal" if count else "disabled")

    def use_preset(self):
        recommended = CATEGORIES[self.selected.get()][2]
        for key in self.category_ids():
            self.checked[key].set(key in recommended)
        self.update_count()

    def clear_selection(self):
        for key in self.category_ids():
            self.checked[key].set(False)
        self.update_count()

    def report_error(self, title, error):
        self.status.set(f"Could not launch {title}.")
        messagebox.showerror(f"Could not launch {title}", f"Windows reported:\n{error}", parent=self.window)

    def run_action(self, key):
        try:
            launch_action(key)
        except OSError as error:
            self.report_error(ACTIONS[key].title, error)
        else:
            self.status.set(f"Requested: {ACTIONS[key].title}. Review output in its Windows window.")

    def run_selected(self):
        chosen = self.chosen_ids()
        for pair in (("balanced", "high_performance"), ("quick_scan", "cancel_scan"), ("full_scan", "cancel_scan")):
            if all(key in chosen for key in pair):
                messagebox.showinfo("Choose one action", "Run these actions individually: " + " and ".join(ACTIONS[key].title for key in pair), parent=self.window)
                return
        # Windows servicing actions share a single sequential console, with no
        # polling or success checks. Other actions each get their own window.
        servicing = [key for key in chosen if ACTIONS[key].servicing]
        serial_started = False
        for key in chosen:
            if ACTIONS[key].servicing:
                if not serial_started:
                    try:
                        launch_commands(servicing)
                    except OSError as error:
                        self.report_error("Windows servicing", error)
                    else:
                        self.status.set("Requested the selected Windows servicing tasks in one console. Review its output.")
                    serial_started = True
            else:
                self.run_action(key)

    def preview_selected(self):
        chosen = self.chosen_ids()
        if not chosen:
            return
        preview = tk.Toplevel(self.window)
        preview.title("Selected actions - preview only")
        preview.geometry("850x560")
        text = tk.Text(preview, wrap="word", padx=14, pady=12, font=("Consolas", 10))
        scroll = ttk.Scrollbar(preview, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        for key in chosen:
            action = ACTIONS[key]
            text.insert("end", f"{action.title}\n{action.description}\n")
            text.insert("end", command_script([key]) if action.script else f"Open Windows: {action.target} {' '.join(action.arguments)}")
            text.insert("end", "\n\n" + "-" * 60 + "\n\n")
        text.configure(state="disabled")


def create_window():
    window = tk.Tk()
    window.app = OptimizerApp(window)
    return window


if __name__ == "__main__":
    create_window().mainloop()
