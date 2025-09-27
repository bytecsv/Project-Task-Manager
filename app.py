import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv, os, sys

SESSION_FILE = "session.txt"

def get_logged_in_user():
    if not os.path.exists(SESSION_FILE):
        return None
    with open(SESSION_FILE, "r") as f:
        username = f.read().strip()
    return username if username else None

def get_task_file(username):
    return f"tasks_{username}.csv"

def ensure_task_file(username):
    task_file = get_task_file(username)
    if not os.path.exists(task_file):
        with open(task_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "description", "status"])
    return task_file

class TaskApp:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title(f"Task Manager - {username}")
        self.root.configure(bg="#f7f7f7")

        self.task_file = ensure_task_file(username)
        self.selected_ids = set()
        self.checkbox_vars = {}
        self.checkbuttons = {}
        self.master_checked = False
        self.search_highlight = None

        # --- Top bar ---
        self.top_bar = tk.Frame(root, bg="#f7f7f7", padx=20, pady=10)
        self.top_bar.pack(fill="x")

        self.lbl_welcome = tk.Label(self.top_bar, text=f"Welcome, {username}!",
                                    font=("Segoe UI", 16, "bold"), bg="#f7f7f7")
        self.lbl_welcome.pack(side="left")

        self.btn_add = tk.Button(self.top_bar, text="+ Add Task", command=self.add_task)
        self.btn_add.pack(side="right")

        self.frame_bulk = tk.Frame(self.top_bar, bg="#f7f7f7")
        self.btn_bulk_complete = tk.Button(self.frame_bulk, text="Bulk Complete", command=self.bulk_complete)
        self.btn_bulk_delete = tk.Button(self.frame_bulk, text="Bulk Delete", command=self.bulk_delete)
        self.btn_bulk_complete.pack(side="left", padx=5)
        self.btn_bulk_delete.pack(side="left", padx=5)

        # --- Treeview ---
        columns = ("Select", "ID", "Task", "Status", "Actions")
        tree_frame = tk.Frame(root)
        tree_frame.pack(padx=20, pady=(0, 5), fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="none")
        self.tree.heading("Select", text="[  ]", command=self.toggle_master_checkbox)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Task", text="Task")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Actions", text="Actions")

        self.tree.column("Select", width=60, anchor="center")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Task", width=400, anchor="w")
        self.tree.column("Status", width=120, anchor="center")
        self.tree.column("Actions", width=180, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='#f0f0f0')
        self.tree.tag_configure('highlight', background='#a0c8ff', foreground='white')

        # --- Search bar directly under table ---
        search_row = tk.Frame(root, bg="#f7f7f7")
        search_row.pack(fill="x", padx=20, pady=(0, 10))

        search_container = tk.Frame(search_row, bg="#f7f7f7")
        search_container.pack(side="right")

        self.search_entry = tk.Entry(search_container, font=("Segoe UI", 10), fg="gray", width=35)
        self.search_entry.insert(0, "Search format: id:3 or task:groceries")
        self.search_entry.bind("<FocusIn>", lambda e: self.clear_placeholder())
        self.search_entry.bind("<FocusOut>", lambda e: self.restore_placeholder())
        self.search_entry.bind("<Return>", lambda e: self.search_task())
        self.search_entry.pack(side="left", ipady=2)

        tk.Button(search_container, text="Search", command=self.search_task).pack(side="left", padx=(5, 0))

        # --- Logout button centered below search ---
        bottom_bar = tk.Frame(root, bg="#f7f7f7")
        bottom_bar.pack(fill="x", pady=(0, 10), padx=20)

        logout_row = tk.Frame(bottom_bar, bg="#f7f7f7")
        logout_row.pack(fill="x", pady=(5, 0))
        tk.Button(logout_row, text="Logout", command=self.logout).pack(anchor="center")

        self.refresh_tasks()
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Configure>", lambda e: self.position_checkbuttons())
        self.tree.bind("<Motion>", lambda e: self.position_checkbuttons())
        self.root.bind("<Button-1>", self.handle_click_outside)

    def handle_click_outside(self, event):
        widget = event.widget
        if widget != self.search_entry:
            self.restore_placeholder()
            self.clear_search_highlight()

    def clear_placeholder(self):
        if self.search_entry.get() == "Search format: id:3 or task:groceries":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="black")

    def restore_placeholder(self):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search format: id:3 or task:groceries")
            self.search_entry.config(fg="gray")

    def load_tasks(self):
        with open(self.task_file, "r") as f:
            return list(csv.DictReader(f))

    def save_tasks(self, tasks):
        with open(self.task_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "description", "status"])
            writer.writeheader()
            writer.writerows(tasks)

    def generate_task_id(self):
        tasks = self.load_tasks()
        return 1 if not tasks else max(int(t["id"]) for t in tasks) + 1

    def refresh_tasks(self):
        self.tree.delete(*self.tree.get_children())
        for btn in self.checkbuttons.values():
            btn.destroy()
        self.checkbox_vars.clear()
        self.checkbuttons.clear()

        tasks = self.load_tasks()
        for idx, task in enumerate(tasks):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            bg_color = '#f0f0f0' if tag == 'evenrow' else 'white'
            action_text = "[Undo] | [Delete]" if task["status"] == "Completed" else "[Complete] | [Delete]"
            iid = self.tree.insert("", "end",
                                   values=("", task["id"], task["description"], task["status"], action_text),
                                   tags=(tag,))
            var = tk.BooleanVar(value=int(task["id"]) in self.selected_ids)
            cb = tk.Checkbutton(self.tree, variable=var, command=self.update_selected,
                                bg=bg_color, highlightthickness=0, bd=0,
                                font=("Segoe UI", 9), padx=0, pady=0)
            self.checkbox_vars[task["id"]] = var
            self.checkbuttons[task["id"]] = cb
        self.position_checkbuttons()
        self.update_top_bar()
        self.update_master_checkbox_state()

    def position_checkbuttons(self):
        for iid in self.tree.get_children():
            values = self.tree.item(iid, "values")
            task_id = values[1]
            if task_id in self.checkbuttons:
                bbox = self.tree.bbox(iid, column="#1")
                if bbox:
                    x, y, w, h = bbox
                    self.checkbuttons[task_id].place(in_=self.tree, x=x+2, y=y, width=w, height=h)
                else:
                    self.checkbuttons[task_id].place_forget()

    def update_selected(self):
        self.selected_ids = {int(tid) for tid, var in self.checkbox_vars.items() if var.get()}
        self.update_top_bar()
        self.update_master_checkbox_state()
        self.validate_bulk_complete()

    def validate_bulk_complete(self):
        statuses = set()
        tasks = self.load_tasks()
        for task in tasks:
            if int(task["id"]) in self.selected_ids:
                statuses.add(task["status"])
        self.btn_bulk_complete.config(state="normal" if statuses == {"Pending"} else "disabled")

    def search_task(self):
        query = self.search_entry.get().strip().lower()
        if not query or query == "search format: id:3 or task:groceries":
            return
        self.clear_search_highlight()

        match_iid = None
        if query.startswith("id:"):
            target_id = query[3:].strip()
            for iid in self.tree.get_children():
                values = self.tree.item(iid, "values")
                if str(values[1]) == target_id:
                    match_iid = iid
                    break
        elif query.startswith("task:"):
            target_text = query[5:].strip()
            for iid in self.tree.get_children():
                values = self.tree.item(iid, "values")
                if target_text in values[2].lower():
                    match_iid = iid
                    break
        else:
            messagebox.showinfo("Search Format", "Use 'id:<number>' or 'task:<keyword>' to search.")
            return

        if match_iid:
            self.tree.item(match_iid, tags=("highlight",))
            task_id = self.tree.item(match_iid, "values")[1]
            if task_id in self.checkbuttons:
                self.checkbuttons[task_id].config(bg="#a0c8ff")
            self.search_highlight = match_iid
            self.tree.see(match_iid)


    def clear_search_highlight(self):
        if self.search_highlight:
            original_tag = 'evenrow' if self.tree.index(self.search_highlight) % 2 == 0 else 'oddrow'
            self.tree.item(self.search_highlight, tags=(original_tag,))
            task_id = self.tree.item(self.search_highlight, "values")[1]
            if task_id in self.checkbuttons:
                bg_color = '#f0f0f0' if original_tag == 'evenrow' else 'white'
                self.checkbuttons[task_id].config(bg=bg_color)
            self.search_highlight = None

    def add_task(self):
        desc = simpledialog.askstring("Add Task", "Enter task description:")
        if not desc:
            return
        tasks = self.load_tasks()
        if any(t["description"].strip().lower() == desc.strip().lower() for t in tasks):
            messagebox.showerror("Error", "Task already exists!")
            return

        new_id = self.generate_task_id()
        with open(self.task_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([new_id, desc.strip(), "Pending"])
        self.refresh_tasks()

    def toggle_complete(self, task_id):
        tasks = self.load_tasks()
        for task in tasks:
            if int(task["id"]) == int(task_id):
                task["status"] = "Completed" if task["status"] == "Pending" else "Pending"
        self.save_tasks(tasks)
        self.refresh_tasks()

    def delete_task(self, task_id):
        if messagebox.askokcancel("Warning", "Are you sure you want to delete?"):
            tasks = [t for t in self.load_tasks() if int(t["id"]) != int(task_id)]
            self.save_tasks(tasks)
            self.refresh_tasks()

    def bulk_complete(self):
        tasks = self.load_tasks()
        for task in tasks:
            if int(task["id"]) in self.selected_ids:
                task["status"] = "Completed"
        self.save_tasks(tasks)
        self.selected_ids.clear()
        self.refresh_tasks()

    def bulk_delete(self):
        if messagebox.askokcancel("Warning", f"Are you sure you want to bulk delete {len(self.selected_ids)} task(s)?"):
            tasks = [t for t in self.load_tasks() if int(t["id"]) not in self.selected_ids]
            self.save_tasks(tasks)
            self.selected_ids.clear()
            self.refresh_tasks()

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id:
            return
        values = self.tree.item(item_id, "values")
        task_id, status = values[1], values[3]
        if column == "#5":
            x_cell, _, width_cell, _ = self.tree.bbox(item_id, column)
            rel_x = event.x - x_cell
            if rel_x < width_cell / 2:
                self.toggle_complete(task_id)
            else:
                self.delete_task(task_id)

    def update_top_bar(self):
        if self.selected_ids:
            self.btn_add.pack_forget()
            self.frame_bulk.pack(side="right")
        else:
            self.frame_bulk.pack_forget()
            self.btn_add.pack(side="right")

    def toggle_master_checkbox(self):
        self.master_checked = not self.master_checked
        self.tree.heading("Select", text="[x]" if self.master_checked else "[  ]")
        for tid, var in self.checkbox_vars.items():
            var.set(self.master_checked)
        self.update_selected()

    def update_master_checkbox_state(self):
        all_checked = all(var.get() for var in self.checkbox_vars.values()) if self.checkbox_vars else False
        none_checked = all(not var.get() for var in self.checkbox_vars.values()) if self.checkbox_vars else True
        if all_checked:
            self.master_checked = True
            self.tree.heading("Select", text="[x]")
        elif none_checked:
            self.master_checked = False
            self.tree.heading("Select", text="[  ]")
        else:
            self.master_checked = False
            self.tree.heading("Select", text="[-]")

    def logout(self):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        self.root.destroy()
        os.system(f"{sys.executable} main.py")

if __name__ == "__main__":
    user = get_logged_in_user()
    if not user:
        os.system(f"{sys.executable} main.py")
        sys.exit()

    window = tk.Tk()
    window_width = 900
    window_height = 650
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    app = TaskApp(window, user)
    window.mainloop()