import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from pathlib import Path
import datetime
import shutil
import csv
import calendar

# ---------------- Constants ----------------
JOURNAL_FILE = Path("learning_journal.txt")
BACKUP_FOLDER = Path("journal_backups")
SEPARATOR = "-" * 50
DATE_FORMAT = "%Y-%m-%d — %I:%M %p"

# ---------------- Utilities ----------------


def ensure_backup_folder():
    BACKUP_FOLDER.mkdir(exist_ok=True)


def create_backup():
    if not JOURNAL_FILE.exists():
        return
    ensure_backup_folder()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = BACKUP_FOLDER / f"backup_{stamp}.txt"
    shutil.copy(JOURNAL_FILE, backup_name)


def append_entry_to_file(entry_text, rating):
    create_backup()
    now = datetime.datetime.now()
    date_str = now.strftime(DATE_FORMAT)
    parts = [f"🗓️ {date_str}", entry_text]
    if rating:
        parts.append(f"Productivity Rating: {rating}/5")
    entry_block = "\n".join(parts) + "\n" + SEPARATOR + "\n"
    JOURNAL_FILE.open("a", encoding="utf-8").write(entry_block)


def read_all_entries_raw():
    if not JOURNAL_FILE.exists():
        return []
    content = JOURNAL_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return []
    blocks = [b.strip() for b in content.split(SEPARATOR) if b.strip()]
    return blocks


def parse_entry(block):
    """
    Parse a block and return dict: {'datetime':..., 'text':..., 'rating': int|None, 'raw': ...}
    This relies on the format we write entries in.
    """
    lines = [l.rstrip() for l in block.splitlines() if l.strip()]
    dt = None
    rating = None
    text_lines = []
    for i, line in enumerate(lines):
        if line.startswith("🗓️"):
            dt = line.replace("🗓️", "").strip()
        elif line.lower().startswith("productivity rating"):
            # extract rating like 'Productivity Rating: 4/5'
            try:
                rating = int(line.split(":")[1].strip().split("/")[0])
            except Exception:
                rating = None
        else:
            # treat as content
            text_lines.append(line)
    text = "\n".join(text_lines).strip()
    return {"datetime": dt, "text": text, "rating": rating, "raw": block}


def get_statistics():
    entries = read_all_entries_raw()
    parsed = [parse_entry(e) for e in entries]
    total = len(parsed)
    ratings = [p["rating"] for p in parsed if isinstance(p["rating"], int)]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    # Most recent: assume file append order is chronological; last entries are newest
    recent = parsed[-3:][::-1]  # newest first (max 3)
    return {"total": total, "avg_rating": avg_rating, "recent": recent, "parsed_all": parsed}


def export_to_csv(path):
    stats = get_statistics()
    parsed = stats["parsed_all"]
    if not parsed:
        raise ValueError("No entries to export.")
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Entry", "Rating"])
        for p in parsed:
            writer.writerow(
                [p["datetime"] or "", p["text"], p["rating"] or ""])
    return path


# file-modification helpers
def replace_block_in_file(old_block, new_block):
    """Replace the exact old_block with new_block in the journal file."""
    if not JOURNAL_FILE.exists():
        raise FileNotFoundError("Journal file not found.")
    content = JOURNAL_FILE.read_text(encoding="utf-8")
    if old_block.strip() not in content:
        raise ValueError("Original entry not found in file.")
    create_backup()
    content = content.replace(old_block.strip(), new_block.strip())
    JOURNAL_FILE.write_text(content.strip() + "\n", encoding="utf-8")


def delete_block_from_file(old_block):
    if not JOURNAL_FILE.exists():
        return
    content = JOURNAL_FILE.read_text(encoding="utf-8")
    create_backup()
    content = content.replace(old_block.strip(), "")
    # Clean up extra separators and whitespace
    new = "\n".join([l for l in [s.strip()
                    for s in content.split(SEPARATOR)] if l])
    if new:
        JOURNAL_FILE.write_text(new.strip() + "\n", encoding="utf-8")
    else:
        JOURNAL_FILE.write_text("", encoding="utf-8")


def clear_all_entries():
    if JOURNAL_FILE.exists():
        create_backup()
        JOURNAL_FILE.unlink()


# ---------------- GUI Application ----------------


class JournalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📓 MindTrack 📓 — Capture. Reflect. Grow.")
        self.geometry("1000x650")
        self.minsize(900, 520)
        self.style = ttk.Style(self)
        # in-memory theme, default dark
        self.dark_mode = True
        self.configure_ui()
        self.create_widgets()
        self.refresh_dashboard()

    def configure_ui(self):
        # Define colors for light/dark
        self.light_colors = {
            "bg": "#f4f6f8",
            "panel": "#ffffff",
            "fg": "#222222",
            "accent": "#0b79d0"
        }
        self.dark_colors = {
            "bg": "#1f2326",
            "panel": "#2a2f33",
            "fg": "#e6eef8",
            "accent": "#5aa9ff"
        }
        self.apply_theme()

    def apply_theme(self):
        c = self.dark_colors if self.dark_mode else self.light_colors
        self.configure(bg=c["bg"])
        # ttk styling for frames, buttons, labels
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("Panel.TFrame", background=c["panel"])
        self.style.configure(
            "TLabel", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", background=c["bg"], foreground=c["fg"], font=(
            "Segoe UI", 14, "bold"))
        self.style.configure(
            "Accent.TButton", background=c["accent"], foreground=c["fg"], relief="flat")
        self.style.map("Accent.TButton", background=[("active", c["accent"])])
        self.style.configure(
            "TButton", background=c["panel"], foreground=c["fg"])

    def create_widgets(self):
        c = self.dark_colors if self.dark_mode else self.light_colors

        # Left Sidebar
        sidebar = ttk.Frame(self, width=260, style="TFrame")
        sidebar.pack(side="left", fill="y", padx=(12, 6), pady=12)

        header = ttk.Label(sidebar, text="📓 MindTrack 📓",
                           style="Header.TLabel")
        header.pack(pady=(6, 12), padx=10, anchor="w")

        ttk.Button(sidebar, text="Dashboard", command=self.show_dashboard).pack(
            fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Add Entry", command=self.show_add_entry).pack(
            fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="View All", command=self.show_all_entries).pack(
            fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Search", command=self.show_search).pack(
            fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Calendar", command=self.show_calendar).pack(
            fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Export to CSV", command=self.gui_export_csv).pack(
            fill="x", padx=8, pady=6)
        ttk.Separator(sidebar, orient="horizontal").pack(
            fill="x", pady=12, padx=8)

        # Clear All button
        ttk.Button(sidebar, text="Clear All Entries", command=self.gui_clear_all).pack(
            fill="x", padx=8, pady=6)

        # Dark mode toggle
        self.theme_var = tk.StringVar(
            value="Dark" if self.dark_mode else "Light")
        ttk.Button(sidebar, textvariable=self.theme_var,
                   command=self.toggle_theme).pack(fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Quit", command=self.quit).pack(
            fill="x", padx=8, pady=12)

        # Main content area
        self.content = ttk.Frame(self, style="TFrame")
        self.content.pack(side="left", fill="both",
                          expand=True, padx=(6, 12), pady=12)

        # Initialize frames for pages
        self.frames = {}
        for F in (DashboardFrame, AddEntryFrame, ViewAllFrame, SearchFrame, CalendarFrame):
            page = F(parent=self.content, controller=self)
            self.frames[F.__name__] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_dashboard()

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        # If frame has refresh method, call it
        if hasattr(frame, "refresh"):
            frame.refresh()

    def show_dashboard(self):
        self.show_frame("DashboardFrame")

    def show_add_entry(self):
        self.show_frame("AddEntryFrame")

    def show_all_entries(self):
        self.show_frame("ViewAllFrame")

    def show_search(self):
        self.show_frame("SearchFrame")

    def show_calendar(self):
        self.show_frame("CalendarFrame")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme_var.set("Dark" if self.dark_mode else "Light")
        self.apply_theme()
        # re-render by restyling frames to apply new colors
        for name, frame in self.frames.items():
            if hasattr(frame, "restyle"):
                frame.restyle()
        self.refresh_dashboard()

    def refresh_dashboard(self):
        # call dashboard's refresh if exists
        if "DashboardFrame" in self.frames:
            frame = self.frames["DashboardFrame"]
            frame.refresh()

    def gui_export_csv(self):
        try:
            default = f"learning_journal_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default,
                                                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
            if not path:
                return
            export_to_csv(path)
            messagebox.showinfo("Exported", f"Exported entries to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def gui_clear_all(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete ALL entries? This action cannot be undone."):
            try:
                clear_all_entries()
                messagebox.showinfo(
                    "Cleared", "All entries removed. A backup was created before deletion.")
                self.refresh_dashboard()
                # refresh frames that show content
                if "ViewAllFrame" in self.frames:
                    self.frames["ViewAllFrame"].refresh()
                if "SearchFrame" in self.frames:
                    self.frames["SearchFrame"].clear_results()
                if "CalendarFrame" in self.frames:
                    self.frames["CalendarFrame"].refresh()
            except Exception as e:
                messagebox.showerror("Clear failed", str(e))


# ---------------- Individual Page Frames ----------------


class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self.create_ui()

    def restyle(self):
        # called when theme changes
        self.configure(style="TFrame")
        for child in self.winfo_children():
            try:
                child.configure(style="TFrame")
            except Exception:
                pass

    def create_ui(self):
        pad = 12
        title = ttk.Label(self, text="Dashboard", style="Header.TLabel")
        title.pack(anchor="nw", pady=(6, 6), padx=pad)

        # Stats frame
        stats_frame = ttk.Frame(self, style="Panel.TFrame")
        stats_frame.pack(fill="x", padx=pad, pady=(6, 12))

        self.total_var = tk.StringVar(value="Total entries : 0")
        self.avg_var = tk.StringVar(value="Average rating : ")
        ttk.Label(stats_frame, textvariable=self.total_var, font=(
            "Segoe UI", 12)).pack(anchor="w", padx=10, pady=6)
        ttk.Label(stats_frame, textvariable=self.avg_var, font=(
            "Segoe UI", 12)).pack(anchor="w", padx=10, pady=6)

        # Recent entries panel
        recent_label = ttk.Label(
            self, text="Recent Entries", style="Header.TLabel")
        recent_label.pack(anchor="nw", padx=pad)
        self.recent_box = scrolledtext.ScrolledText(
            self, height=10, wrap=tk.WORD)
        self.recent_box.pack(fill="both", expand=False, padx=pad, pady=(6, 12))
        self.recent_box.configure(state=tk.DISABLED)

        # Quick actions
        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=pad, pady=(6, 12))
        ttk.Button(actions, text="Add New Entry",
                   command=self.controller.show_add_entry).pack(side="left", padx=6)
        ttk.Button(actions, text="View All", command=self.controller.show_all_entries).pack(
            side="left", padx=6)
        ttk.Button(actions, text="Search", command=self.controller.show_search).pack(
            side="left", padx=6)

    def refresh(self):
        stats = get_statistics()
        self.total_var.set(f"Total entries : {stats['total']}")
        avg = stats["avg_rating"]
        self.avg_var.set(f"Average rating : {avg if avg is not None else ''}")
        # recent entries text
        self.recent_box.configure(state=tk.NORMAL)
        self.recent_box.delete("1.0", tk.END)
        if stats["recent"]:
            for r in stats["recent"]:
                self.recent_box.insert(tk.END, f"{r['datetime'] or ''}\n")
                self.recent_box.insert(tk.END, f"{r['text']}\n")
                if r['rating'] is not None:
                    self.recent_box.insert(
                        tk.END, f"Rating: {r['rating']}/5\n")
                self.recent_box.insert(tk.END, SEPARATOR + "\n")
        else:
            self.recent_box.insert(
                tk.END, "No entries yet. Add your first learning note!")
        self.recent_box.configure(state=tk.DISABLED)


class AddEntryFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self.create_ui()

    def restyle(self):
        self.configure(style="TFrame")

    def create_ui(self):
        pad = 12
        title = ttk.Label(self, text="Add Entry", style="Header.TLabel")
        title.pack(anchor="nw", pady=(6, 6), padx=pad)

        ttk.Label(self, text="What did you learn today?").pack(
            anchor="nw", padx=pad)
        self.entry_box = scrolledtext.ScrolledText(
            self, height=12, wrap=tk.WORD)
        self.entry_box.pack(fill="both", expand=False, padx=pad, pady=(6, 8))

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=pad, pady=6)
        ttk.Label(
            bottom, text="Productivity Rating (1-5, optional):").pack(side="left")
        self.rating_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.rating_var,
                  width=6).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="Save Entry", command=self.save_entry).pack(
            side="right", padx=6)

    def save_entry(self):
        text = self.entry_box.get("1.0", tk.END).strip()
        rating = self.rating_var.get().strip()
        if not text:
            messagebox.showerror(
                "Missing text", "Please write what you learned.")
            return
        if rating:
            if not rating.isdigit() or not (1 <= int(rating) <= 5):
                messagebox.showerror(
                    "Invalid rating", "Please enter rating between 1 and 5.")
                return
            rating_val = int(rating)
        else:
            rating_val = None
        try:
            append_entry_to_file(text, rating_val)
            messagebox.showinfo("Saved", "Your entry was saved successfully.")
            self.entry_box.delete("1.0", tk.END)
            self.rating_var.set("")
            self.controller.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Save failed", str(e))


class ViewAllFrame(ttk.Frame):
    """Shows all entries; each entry has Edit, Update and Delete buttons."""

    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self.create_ui()

    def restyle(self):
        self.configure(style="TFrame")

    def create_ui(self):
        pad = 8
        title = ttk.Label(self, text="All Entries", style="Header.TLabel")
        title.pack(anchor="nw", pady=(6, 6), padx=pad)

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=pad, pady=(6, 12))

        self.refresh_btn = ttk.Button(self, text="Refresh",
                                      command=self.refresh)
        self.refresh_btn.pack(pady=(0, 6))

    def refresh(self):
        for child in self.container.winfo_children():
            child.destroy()

        blocks = read_all_entries_raw()
        if not blocks:
            lab = ttk.Label(
                self.container, text="No entries found. Add your first learning note!")
            lab.pack(anchor="center", pady=20)
            return

        # For each block show a framed row: datetime, editable Text, rating entry, buttons
        for i, b in enumerate(blocks[::-1]):  # show newest first
            parsed = parse_entry(b)
            frame = ttk.Frame(self.container, style="Panel.TFrame", padding=8)
            frame.pack(fill="x", pady=6)

            top = ttk.Frame(frame)
            top.pack(fill="x")
            dt_label = ttk.Label(top, text=parsed.get(
                "datetime") or "", font=("Segoe UI", 10, "bold"))
            dt_label.pack(side="left")

            btns = ttk.Frame(top)
            btns.pack(side="right")

            edit_btn = ttk.Button(btns, text="Edit")
            update_btn = ttk.Button(btns, text="Update")
            del_btn = ttk.Button(btns, text="Delete")

            edit_btn.pack(side="left", padx=4)
            update_btn.pack(side="left", padx=4)
            del_btn.pack(side="left", padx=4)

            # Text area
            text_widget = scrolledtext.ScrolledText(
                frame, height=5, wrap=tk.WORD)
            text_widget.insert(tk.END, parsed.get("text") or "")
            text_widget.configure(state=tk.DISABLED)
            text_widget.pack(fill="both", padx=(0, 0), pady=(6, 6))

            # Rating edit
            rating_frame = ttk.Frame(frame)
            rating_frame.pack(fill="x")
            ttk.Label(rating_frame, text="Rating (1-5):").pack(side="left")
            rating_var = tk.StringVar(value=str(parsed.get("rating") or ""))
            rating_entry = ttk.Entry(
                rating_frame, textvariable=rating_var, width=6)
            rating_entry.pack(side="left", padx=(6, 0))
            rating_entry.configure(state=tk.DISABLED)

            # Wire up buttons
            def on_edit(tw=text_widget, rv=rating_var, re=rating_entry, eb=edit_btn, ub=update_btn):
                tw.configure(state=tk.NORMAL)
                re.configure(state=tk.NORMAL)
                eb.configure(state=tk.DISABLED)
                ub.configure(state=tk.NORMAL)

            def on_update(old_block=b, tw=text_widget, rv=rating_var, eb=edit_btn, ub=update_btn):
                new_text = tw.get("1.0", tk.END).strip()
                rating_val = rv.get().strip()
                if rating_val:
                    if not rating_val.isdigit() or not (1 <= int(rating_val) <= 5):
                        messagebox.showerror(
                            "Invalid rating", "Please enter rating between 1 and 5.")
                        return
                    rating_int = int(rating_val)
                else:
                    rating_int = None
                # Build new block: keep original datetime line from old block
                parsed_old = parse_entry(old_block)
                dt_line = f"🗓️ {parsed_old['datetime']}" if parsed_old[
                    'datetime'] else f"🗓️ {datetime.datetime.now().strftime(DATE_FORMAT)}"
                parts = [dt_line, new_text]
                if rating_int is not None:
                    parts.append(f"Productivity Rating: {rating_int}/5")
                new_block = "\n".join(parts) + "\n" + SEPARATOR + "\n"
                try:
                    replace_block_in_file(old_block, new_block)
                    messagebox.showinfo(
                        "Updated", "Entry updated successfully.")
                    # disable editing controls
                    tw.configure(state=tk.DISABLED)
                    re.configure(state=tk.DISABLED)
                    eb.configure(state=tk.NORMAL)
                    ub.configure(state=tk.DISABLED)
                    # refresh dashboard and other frames
                    self.controller.refresh_dashboard()
                except Exception as e:
                    messagebox.showerror("Update failed", str(e))

            def on_delete(old_block=b, container_frame=frame):
                if not messagebox.askyesno("Confirm Delete", "Delete this entry?"):
                    return
                try:
                    delete_block_from_file(old_block)
                    messagebox.showinfo(
                        "Deleted", "Entry removed. A backup was created.")
                    container_frame.destroy()
                    self.controller.refresh_dashboard()
                except Exception as e:
                    messagebox.showerror("Delete failed", str(e))

            edit_btn.configure(command=on_edit)
            update_btn.configure(command=on_update)
            del_btn.configure(command=on_delete)
            update_btn.configure(state=tk.DISABLED)


class SearchFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self.create_ui()

    def restyle(self):
        self.configure(style="TFrame")

    def create_ui(self):
        pad = 12
        title = ttk.Label(self, text="Search Entries", style="Header.TLabel")
        title.pack(anchor="nw", pady=(6, 6), padx=pad)

        form = ttk.Frame(self)
        form.pack(fill="x", padx=pad, pady=(6, 6))
        ttk.Label(form, text="Keyword or date (YYYY-MM-DD):").pack(side="left")
        self.qvar = tk.StringVar()
        ttk.Entry(form, textvariable=self.qvar, width=30).pack(
            side="left", padx=(8, 0))
        ttk.Button(form, text="Search", command=self.do_search).pack(
            side="left", padx=8)

        self.results_container = ttk.Frame(self)
        self.results_container.pack(
            fill="both", expand=True, padx=pad, pady=(6, 12))

        ttk.Button(self, text="Clear",
                   command=self.clear_results).pack(pady=(0, 12))

    def do_search(self):
        q = self.qvar.get().strip().lower()
        if not q:
            messagebox.showerror(
                "Enter query", "Please enter a keyword or date to search.")
            return
        blocks = read_all_entries_raw()
        matches = [b for b in blocks if q in b.lower()]

        for child in self.results_container.winfo_children():
            child.destroy()

        if not matches:
            lab = ttk.Label(self.results_container, text="No matches found.")
            lab.pack(anchor="center", pady=20)
            return

        # show matches with Edit/Update/Delete similar to ViewAllFrame
        for b in matches[::-1]:
            parsed = parse_entry(b)
            frame = ttk.Frame(self.results_container,
                              style="Panel.TFrame", padding=8)
            frame.pack(fill="x", pady=6)

            top = ttk.Frame(frame)
            top.pack(fill="x")
            dt_label = ttk.Label(top, text=parsed.get(
                "datetime") or "", font=("Segoe UI", 10, "bold"))
            dt_label.pack(side="left")

            btns = ttk.Frame(top)
            btns.pack(side="right")

            edit_btn = ttk.Button(btns, text="Edit")
            update_btn = ttk.Button(btns, text="Update")
            del_btn = ttk.Button(btns, text="Delete")

            edit_btn.pack(side="left", padx=4)
            update_btn.pack(side="left", padx=4)
            del_btn.pack(side="left", padx=4)

            text_widget = scrolledtext.ScrolledText(
                frame, height=5, wrap=tk.WORD)
            text_widget.insert(tk.END, parsed.get("text") or "")
            text_widget.configure(state=tk.DISABLED)
            text_widget.pack(fill="both", padx=(0, 0), pady=(6, 6))

            rating_frame = ttk.Frame(frame)
            rating_frame.pack(fill="x")
            ttk.Label(rating_frame, text="Rating (1-5):").pack(side="left")
            rating_var = tk.StringVar(value=str(parsed.get("rating") or ""))
            rating_entry = ttk.Entry(
                rating_frame, textvariable=rating_var, width=6)
            rating_entry.pack(side="left", padx=(6, 0))
            rating_entry.configure(state=tk.DISABLED)

            def on_edit(tw=text_widget, re=rating_entry, eb=edit_btn, ub=update_btn):
                tw.configure(state=tk.NORMAL)
                re.configure(state=tk.NORMAL)
                eb.configure(state=tk.DISABLED)
                ub.configure(state=tk.NORMAL)

            def on_update(old_block=b, tw=text_widget, rv=rating_var, eb=edit_btn, ub=update_btn):
                new_text = tw.get("1.0", tk.END).strip()
                rating_val = rv.get().strip()
                if rating_val:
                    if not rating_val.isdigit() or not (1 <= int(rating_val) <= 5):
                        messagebox.showerror(
                            "Invalid rating", "Please enter rating between 1 and 5.")
                        return
                    rating_int = int(rating_val)
                else:
                    rating_int = None
                parsed_old = parse_entry(old_block)
                dt_line = f"🗓️ {parsed_old['datetime']}" if parsed_old[
                    'datetime'] else f"🗓️ {datetime.datetime.now().strftime(DATE_FORMAT)}"
                parts = [dt_line, new_text]
                if rating_int is not None:
                    parts.append(f"Productivity Rating: {rating_int}/5")
                new_block = "\n".join(parts) + "\n" + SEPARATOR + "\n"
                try:
                    replace_block_in_file(old_block, new_block)
                    messagebox.showinfo(
                        "Updated", "Entry updated successfully.")
                    tw.configure(state=tk.DISABLED)
                    re.configure(state=tk.DISABLED)
                    eb.configure(state=tk.NORMAL)
                    ub.configure(state=tk.DISABLED)
                    self.controller.refresh_dashboard()
                except Exception as e:
                    messagebox.showerror("Update failed", str(e))

            def on_delete(old_block=b, container_frame=frame):
                if not messagebox.askyesno("Confirm Delete", "Delete this entry?"):
                    return
                try:
                    delete_block_from_file(old_block)
                    messagebox.showinfo(
                        "Deleted", "Entry removed. A backup was created.")
                    container_frame.destroy()
                    self.controller.refresh_dashboard()
                except Exception as e:
                    messagebox.showerror("Delete failed", str(e))

            edit_btn.configure(command=on_edit)
            update_btn.configure(command=on_update)
            del_btn.configure(command=on_delete)
            update_btn.configure(state=tk.DISABLED)

    def clear_results(self):
        self.qvar.set("")
        for child in self.results_container.winfo_children():
            child.destroy()


class CalendarFrame(ttk.Frame):
    """A very simple calendar view implemented with stdlib calendar module.
    Dates that have entries are emphasized; clicking a date shows entries for that date.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self.today = datetime.date.today()
        self.current_year = self.today.year
        self.current_month = self.today.month
        self.create_ui()

    def restyle(self):
        self.configure(style="TFrame")

    def create_ui(self):
        pad = 8
        header = ttk.Label(self, text="Calendar", style="Header.TLabel")
        header.pack(anchor="nw", pady=(6, 6), padx=pad)

        nav = ttk.Frame(self)
        nav.pack(fill="x", padx=pad)
        ttk.Button(nav, text="Prev", command=self.prev_month).pack(side="left")
        ttk.Button(nav, text="Today", command=self.go_today).pack(
            side="left", padx=6)
        ttk.Button(nav, text="Next", command=self.next_month).pack(side="left")

        self.month_label = ttk.Label(nav, text="")
        self.month_label.pack(side="right")

        self.cal_frame = ttk.Frame(self)
        self.cal_frame.pack(fill="both", expand=False, padx=pad, pady=(6, 12))

        self.entries_box = scrolledtext.ScrolledText(self, height=12)
        self.entries_box.pack(fill="both", expand=True, padx=pad, pady=(6, 12))
        self.entries_box.configure(state=tk.DISABLED)

        self.refresh()

    def refresh(self):
        # Build map of dates that have entries
        blocks = read_all_entries_raw()
        date_map = {}
        for b in blocks:
            p = parse_entry(b)
            dt = p.get("datetime")
            if dt:
                # assume format starts with YYYY-MM-DD
                try:
                    date_key = dt.strip()[:10]
                except Exception:
                    continue
                date_map.setdefault(date_key, []).append(p)

        # render month
        for child in self.cal_frame.winfo_children():
            child.destroy()

        year = self.current_year
        month = self.current_month
        month_name = calendar.month_name[month]
        self.month_label.configure(text=f"{month_name} {year}")

        week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        header_row = ttk.Frame(self.cal_frame)
        header_row.pack()
        for wd in week_days:
            ttk.Label(header_row, text=wd, width=4).pack(side="left")

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        for week in month_days:
            row = ttk.Frame(self.cal_frame)
            row.pack()
            for d in week:
                if d == 0:
                    ttk.Label(row, text=" ", width=4).pack(side="left")
                else:
                    date_str = f"{year}-{month:02d}-{d:02d}"
                    btn = ttk.Button(row, text=str(d), width=4,
                                     command=lambda ds=date_str: self.show_entries_for_date(ds))
                    # highlight if date has entries
                    if date_str in date_map:
                        # decorate the button label with an asterisk
                        btn.config(text=f"{d}*")
                    btn.pack(side="left")

    def show_entries_for_date(self, date_str):
        # date_str like YYYY-MM-DD
        blocks = read_all_entries_raw()
        matches = []
        for b in blocks:
            if date_str in b:
                matches.append(b)
        self.entries_box.configure(state=tk.NORMAL)
        self.entries_box.delete("1.0", tk.END)
        if not matches:
            self.entries_box.insert(tk.END, "No entries for this date.")
        else:
            for m in matches:
                parsed = parse_entry(m)
                self.entries_box.insert(
                    tk.END, f"{parsed.get('datetime') or ''}\n")
                self.entries_box.insert(
                    tk.END, f"{parsed.get('text') or ''}\n")
                if parsed.get('rating') is not None:
                    self.entries_box.insert(
                        tk.END, f"Rating: {parsed.get('rating')}/5\n")
                self.entries_box.insert(tk.END, SEPARATOR + "\n")
        self.entries_box.configure(state=tk.DISABLED)

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh()

    def go_today(self):
        self.today = datetime.date.today()
        self.current_year = self.today.year
        self.current_month = self.today.month
        self.refresh()


# ---------------- Run App ----------------


def main():
    app = JournalApp()
    app.mainloop()


if __name__ == "__main__":
    main()
