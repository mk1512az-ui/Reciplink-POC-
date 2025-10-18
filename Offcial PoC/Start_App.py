import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import sys

# -------------------------
# Database Setup
# -------------------------
conn = sqlite3.connect("elderly_care.db")
c = conn.cursor()

# Create tables (schema)
c.executescript("""
CREATE TABLE IF NOT EXISTS seniors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    service_type TEXT CHECK(service_type IN ('Nursing', 'Transportation', 'Food and Dinery', 'Companion')),
    rating REAL DEFAULT 0,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_id INTEGER,
    provider_id INTEGER,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    FOREIGN KEY (senior_id) REFERENCES seniors(id),
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    provider_id INTEGER,
    provider_overall_rating REAL DEFAULT 0,
    service_description TEXT,
    payment_amount REAL,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE TABLE IF NOT EXISTS bills (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT CHECK(status IN ('Pending', 'Paid', 'Cancelled')),
    senior_id INTEGER,
    provider_id INTEGER,
    amount REAL,
    FOREIGN KEY (senior_id) REFERENCES seniors(id),
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    admin_key TEXT NOT NULL
);
                CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    day INTEGER NOT NULL CHECK(day BETWEEN 1 AND 31),
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    year INTEGER NOT NULL,
    FOREIGN KEY (senior_id) REFERENCES seniors(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);
""")
conn.commit()

# -------------------------
# Helper Functions
# -------------------------
def signup_user(role, name, age, email, password, service_type=None, admin_key=None):
    try:
        if role == "Senior":
            c.execute("INSERT INTO seniors (name, age, email, password) VALUES (?, ?, ?, ?)",
                      (name, age, email, password))
        elif role == "Provider":
            c.execute("INSERT INTO providers (name, age, service_type, email, password) VALUES (?, ?, ?, ?, ?)",
                      (name, age, service_type, email, password))
        elif role == "Admin":
            c.execute("INSERT INTO admin (email, password, admin_key) VALUES (?, ?, ?)",
                      (email, password, admin_key))
        else:
            messagebox.showerror("Error", "Invalid user type!")
            return
        conn.commit()
        messagebox.showinfo("Success", f"{role} registered successfully!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Email already exists!")

def login_user(role, email, password):
    if role == "Senior":
        c.execute("SELECT * FROM seniors WHERE email=? AND password=?", (email, password))
    elif role == "Provider":
        c.execute("SELECT * FROM providers WHERE email=? AND password=?", (email, password))
    elif role == "Admin":
        c.execute("SELECT * FROM admin WHERE email=? AND password=?", (email, password))
    else:
        messagebox.showerror("Error", "Invalid role selected!")
        return

    user = c.fetchone()
    if user:
        messagebox.showinfo("Login Success", f"Welcome, {role}!")
        root.destroy()  # Close the main login/signup window

        # Launch the corresponding app
        if role == "Senior":
            subprocess.Popen([sys.executable, "senior_app.py"])
        elif role == "Provider":
            subprocess.Popen([sys.executable, "provider_app.py"])
        elif role == "Admin":
            subprocess.Popen([sys.executable, "admin_app.py"])
    else:
        messagebox.showerror("Login Failed", "Incorrect email or password.")

# -------------------------
# Tkinter UI
# -------------------------
root = tk.Tk()
root.title("Elderly Care App - Login & Signup")
root.geometry("450x500")

notebook = ttk.Notebook(root)
login_frame = ttk.Frame(notebook)
signup_frame = ttk.Frame(notebook)
notebook.add(login_frame, text="Login")
notebook.add(signup_frame, text="Signup")
notebook.pack(expand=True, fill="both")

# -------------------------
# Login Tab
# -------------------------
tk.Label(login_frame, text="Login", font=("Arial", 18, "bold")).pack(pady=20)

role_var_login = tk.StringVar(value="Senior")
tk.Label(login_frame, text="Select Role:").pack()
ttk.Combobox(login_frame, textvariable=role_var_login, values=["Senior", "Provider", "Admin"], state="readonly").pack()

tk.Label(login_frame, text="Email:").pack(pady=5)
email_login = tk.Entry(login_frame)
email_login.pack()

tk.Label(login_frame, text="Password:").pack(pady=5)
password_login = tk.Entry(login_frame, show="*")
password_login.pack()

tk.Button(login_frame, text="Login", width=20, command=lambda: 
           login_user(role_var_login.get(), email_login.get(), password_login.get())
          ).pack(pady=20)

# -------------------------
# Signup Tab
# -------------------------
tk.Label(signup_frame, text="Signup", font=("Arial", 18, "bold")).pack(pady=20)

role_var_signup = tk.StringVar(value="Senior")
tk.Label(signup_frame, text="Select Role:").pack()
role_menu = ttk.Combobox(signup_frame, textvariable=role_var_signup, values=["Senior", "Provider", "Admin"], state="readonly")
role_menu.pack()

# Fields
name_entry = tk.Entry(signup_frame)
age_entry = tk.Entry(signup_frame)
email_entry = tk.Entry(signup_frame)
password_entry = tk.Entry(signup_frame, show="*")
service_type_entry = ttk.Combobox(signup_frame, values=["Nursing", "Transportation", "Food and Dinery", "Companion"], state="readonly")
admin_key_entry = tk.Entry(signup_frame)

# Field Labels and Layout
tk.Label(signup_frame, text="Name:").pack(pady=3)
name_entry.pack()
tk.Label(signup_frame, text="Age:").pack(pady=3)
age_entry.pack()
tk.Label(signup_frame, text="Email:").pack(pady=3)
email_entry.pack()
tk.Label(signup_frame, text="Password:").pack(pady=3)
password_entry.pack()

# Dynamic field shown depending on role
def update_fields(*args):
    service_type_entry.pack_forget()
    admin_key_entry.pack_forget()
    if role_var_signup.get() == "Provider":
        tk.Label(signup_frame, text="Service Type:").pack(pady=3)
        service_type_entry.pack()
    elif role_var_signup.get() == "Admin":
        tk.Label(signup_frame, text="Admin Key:").pack(pady=3)
        admin_key_entry.pack()

role_var_signup.trace("w", update_fields)

tk.Button(signup_frame, text="Signup", width=20, command=lambda:
           signup_user(role_var_signup.get(), name_entry.get(), age_entry.get(),
                       email_entry.get(), password_entry.get(),
                       service_type_entry.get() if role_var_signup.get() == "Provider" else None,
                       admin_key_entry.get() if role_var_signup.get() == "Admin" else None)
          ).pack(pady=20)

root.mainloop()
