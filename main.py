import tkinter as tk
import pandas as pd
import subprocess
import os
import sys
import re

window = tk.Tk()
window.title("Task Manager - User Authentication")

SESSION_FILE = "session.txt"

def get_logged_in_user():
    if not os.path.exists(SESSION_FILE):
        return None
    with open(SESSION_FILE, "r") as f:
        username = f.read().strip()
    return username if username else None

# Center window
window_width = 650
window_height = 500
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)
window.geometry(f"{window_width}x{window_height}+{x}+{y}")
window.resizable(False, False)
window.configure(bg="#f5f5f5")

# --- Frames ---
signup_frame = tk.Frame(window, bg="#f5f5f5")
login_frame = tk.Frame(window, bg="#f5f5f5")

def show_signup():
    login_frame.pack_forget()
    signup_frame.pack(expand=True)

def show_login():
    signup_frame.pack_forget()
    login_frame.pack(expand=True)

# ---------------- SIGNUP ----------------
tk.Label(signup_frame, text='Project Task Manager', font=("Helvetica", 16, "bold"),
         bg="#f5f5f5", fg="#333").pack(pady=20)

tk.Label(signup_frame, text="Username:", font=("Segoe UI", 12, "bold"),
         bg="#f5f5f5", fg="#333").pack(pady=(10,5))
username_box = tk.Entry(signup_frame, width=30, font=("Segoe UI", 12),
                        relief="flat", highlightthickness=2,
                        highlightbackground="#ccc", highlightcolor="#4a90e2")
username_box.pack(ipady=5, pady=5)

tk.Label(signup_frame, text="Password:", font=("Segoe UI", 12, "bold"),
         bg="#f5f5f5", fg="#333").pack(pady=(10,5))
password_box = tk.Entry(signup_frame, width=30, font=("Segoe UI", 12),
                        relief="flat", highlightthickness=2,
                        highlightbackground="#ccc", highlightcolor="#4a90e2", show="*")
password_box.pack(ipady=5, pady=5)

feedback_label = tk.Label(signup_frame, text="", font=("Segoe UI", 10),
                          bg="#f5f5f5", fg="red")
feedback_label.pack(pady=5)

def launch_app():
    subprocess.call([sys.executable, "app.py"])
    window.destroy()

def valid_username(username: str) -> bool:
    if not re.fullmatch(r"^[a-zA-Z0-9][a-zA-Z0-9._]{2,29}$", username):
        return False
    if ".." in username:  # no consecutive periods
        return False
    if username.endswith("."):  # cannot end with a period
        return False
    return True

def sign_up():
    username = username_box.get().strip()
    password = password_box.get().strip()
    file_path = "localuserfile.csv"

    if not username or not password:
        feedback_label.config(text="⚠ Username and Password cannot be empty.", fg="red")
        return

    if not valid_username(username):
        feedback_label.config(
            text="❌ Invalid username. 3–30 chars, letters/numbers/._ only, and no '..' or ending with '.'",
            fg="red"
        )
        return

    new_data = {"username": username, "password": password}

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        if username in df["username"].values:
            feedback_label.config(text="❌ Username already exists.", fg="red")
            return
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    else:
        df = pd.DataFrame([new_data], columns=["username", "password"])

    df.to_csv(file_path, index=False)
    feedback_label.config(text="✅ Signup successful!", fg="green")
    username_box.delete(0, tk.END)
    password_box.delete(0, tk.END)

    with open("session.txt", "w") as f:
        f.write(username)

    window.after(500, launch_app)

tk.Button(signup_frame, text="Sign Up", command=sign_up,
          font=("Segoe UI", 12, "bold"), bg="#4a90e2", fg="white",
          activebackground="#357ABD", activeforeground="white",
          relief="flat", padx=10, pady=5).pack(pady=10)

login_link = tk.Label(signup_frame, text="Already signed up? Log in", font=("Segoe UI", 10, "underline"),
                      fg="blue", bg="#f5f5f5", cursor="hand2")
login_link.pack()
login_link.bind("<Button-1>", lambda e: show_login())

# ---------------- LOGIN ----------------
tk.Label(login_frame, text='Project Task Manager', font=("Helvetica", 16, "bold"),
         bg="#f5f5f5", fg="#333").pack(pady=20)

tk.Label(login_frame, text="Username:", font=("Segoe UI", 12, "bold"),
         bg="#f5f5f5", fg="#333").pack(pady=(10,5))
login_username_box = tk.Entry(login_frame, width=30, font=("Segoe UI", 12),
                              relief="flat", highlightthickness=2,
                              highlightbackground="#ccc", highlightcolor="#4a90e2")
login_username_box.pack(ipady=5, pady=5)

tk.Label(login_frame, text="Password:", font=("Segoe UI", 12, "bold"),
         bg="#f5f5f5", fg="#333").pack(pady=(10,5))
login_password_box = tk.Entry(login_frame, width=30, font=("Segoe UI", 12),
                              relief="flat", highlightthickness=2,
                              highlightbackground="#ccc", highlightcolor="#4a90e2",
                              show="*")
login_password_box.pack(ipady=5, pady=5)

login_feedback = tk.Label(login_frame, text="", font=("Segoe UI", 10),
                          bg="#f5f5f5", fg="red")
login_feedback.pack(pady=5)

def log_in():
    username = login_username_box.get().strip()
    password = login_password_box.get().strip()

    if not username or not password:
        login_feedback.config(text="⚠ Enter both username and password!", fg="red")
        return

    if not valid_username(username):
        login_feedback.config(
            text="❌ Invalid username format.", fg="red"
        )
        return

    if not os.path.exists("localuserfile.csv") or os.path.getsize("localuserfile.csv") == 0:
        login_feedback.config(text="❌ You haven't signed up yet!", fg="red")
        return

    df = pd.read_csv("localuserfile.csv")
    df.columns = df.columns.str.strip()
    user_row = df[(df["username"] == username) & (df["password"] == password)]
    if not user_row.empty:
        login_feedback.config(text="✅ Login successful!", fg="green")
        login_username_box.delete(0, tk.END)
        login_password_box.delete(0, tk.END)

        with open("session.txt", "w") as f:
            f.write(username)

        window.after(500, launch_app)
    else:
        login_feedback.config(text="❌ Incorrect username or password.", fg="red")

tk.Button(login_frame, text="Log In", command=log_in,
          font=("Segoe UI", 12, "bold"), bg="#4a90e2", fg="white",
          activebackground="#357ABD", activeforeground="white",
          relief="flat", padx=10, pady=5).pack(pady=10)

back_link = tk.Label(login_frame, text="Don't have an account? Sign up", font=("Segoe UI", 10, "underline"),
                     fg="blue", bg="#f5f5f5", cursor="hand2")
back_link.pack()
back_link.bind("<Button-1>", lambda e: show_signup())

if __name__ == "__main__":
    user = get_logged_in_user()
    if user:
        os.system(f"{sys.executable} app.py")
        sys.exit()

signup_frame.pack(expand=True)
window.mainloop()