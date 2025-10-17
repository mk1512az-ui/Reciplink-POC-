import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# -------------------------
# Database Connection
# -------------------------
conn = sqlite3.connect("elderly_care.db")
c = conn.cursor()


# -------------------------
# Admin Dashboard Class
# -------------------------
class AdminDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Elderly Care Admin Dashboard")
        self.root.geometry("1100x600")

        ttk.Label(self.root, text="Admin Dashboard", font=("Arial", 20, "bold")).pack(pady=10)

        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill="both")

        # Tabs for each table
        self.seniors_tab = ttk.Frame(notebook)
        self.providers_tab = ttk.Frame(notebook)
        self.services_tab = ttk.Frame(notebook)
        self.ratings_tab = ttk.Frame(notebook)
        self.bills_tab = ttk.Frame(notebook)
        self.bookings_tab = ttk.Frame(notebook)

        notebook.add(self.seniors_tab, text="Seniors")
        notebook.add(self.providers_tab, text="Providers")
        notebook.add(self.services_tab, text="Services")
        notebook.add(self.ratings_tab, text="Ratings")
        notebook.add(self.bills_tab, text="Bills")
        notebook.add(self.bookings_tab, text="Bookings")

        # Load CRUD for each table
        self.create_crud_tab(self.seniors_tab, "seniors", ["id", "name", "age", "email", "password"])
        self.create_crud_tab(self.providers_tab, "providers", ["id", "name", "age", "service_type", "rating", "email", "password"])
        self.create_crud_tab(self.services_tab, "services", ["id", "service_name", "provider_id", "provider_overall_rating", "service_description", "payment_amount"])
        self.create_crud_tab(self.ratings_tab, "ratings", ["id", "senior_id", "provider_id", "rating"])
        self.create_crud_tab(self.bills_tab, "bills", ["bill_id", "status", "senior_id", "provider_id", "amount"])
        self.create_crud_tab(self.bookings_tab, "bookings", ["booking_id", "senior_id", "service_id", "day", "month", "year"])

        self.root.mainloop()

    # -------------------------
    # CRUD Table Generator
    # -------------------------
    def create_crud_tab(self, frame, table_name, columns):
        label = ttk.Label(frame, text=f"{table_name.capitalize()} Table", font=("Arial", 14, "bold"))
        label.pack(pady=10)

        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(expand=True, fill="both", pady=10)

        # Buttons
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Refresh", command=lambda: self.load_data(tree, table_name)).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Add", command=lambda: self.add_record(table_name, columns, tree)).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Update", command=lambda: self.update_record(table_name, columns, tree)).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Delete", command=lambda: self.delete_record(table_name, tree)).grid(row=0, column=3, padx=5)

        self.load_data(tree, table_name)

    # -------------------------
    # Load Data Function
    # -------------------------
    def load_data(self, tree, table):
        for row in tree.get_children():
            tree.delete(row)
        try:
            c.execute(f"SELECT * FROM {table}")
            rows = c.fetchall()
            for r in rows:
                tree.insert("", tk.END, values=r)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load data: {e}")

    # -------------------------
    # Add Record
    # -------------------------
    def add_record(self, table, columns, tree):
        popup = tk.Toplevel()
        popup.title(f"Add Record to {table}")

        entries = {}
        for i, col in enumerate(columns):
            ttk.Label(popup, text=col).grid(row=i, column=0, padx=5, pady=5)
            e = ttk.Entry(popup)
            e.grid(row=i, column=1, padx=5, pady=5)
            entries[col] = e

        def save_record():
            values = [entries[col].get() for col in columns if col not in ("id", "bill_id", "booking_id")]
            cols = [col for col in columns if col not in ("id", "bill_id", "booking_id")]
            placeholders = ", ".join("?" * len(values))
            try:
                c.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})", values)
                conn.commit()
                messagebox.showinfo("Success", "Record added successfully!")
                popup.destroy()
                self.load_data(tree, table)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(popup, text="Save", command=save_record).grid(row=len(columns), column=0, columnspan=2, pady=10)

    # -------------------------
    # Update Record
    # -------------------------
    def update_record(self, table, columns, tree):
        selected = tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a record to update.")
            return
        old_values = tree.item(selected, "values")

        popup = tk.Toplevel()
        popup.title(f"Update Record in {table}")

        entries = {}
        for i, col in enumerate(columns):
            ttk.Label(popup, text=col).grid(row=i, column=0, padx=5, pady=5)
            e = ttk.Entry(popup)
            e.grid(row=i, column=1, padx=5, pady=5)
            e.insert(0, old_values[i])
            entries[col] = e

        def save_changes():
            set_clause = ", ".join(f"{col}=?" for col in columns if col not in ("id", "bill_id", "booking_id"))
            values = [entries[col].get() for col in columns if col not in ("id", "bill_id", "booking_id")]
            record_id = old_values[0]
            if "id" in columns:
                id_col = "id"
            elif "bill_id" in columns:
                id_col = "bill_id"
            else:
                id_col = "booking_id"
            try:
                c.execute(f"UPDATE {table} SET {set_clause} WHERE {id_col}=?", (*values, record_id))
                conn.commit()
                messagebox.showinfo("Success", "Record updated successfully!")
                popup.destroy()
                self.load_data(tree, table)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(popup, text="Save", command=save_changes).grid(row=len(columns), column=0, columnspan=2, pady=10)

    # -------------------------
    # Delete Record
    # -------------------------
    def delete_record(self, table, tree):
        selected = tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a record to delete.")
            return
        record = tree.item(selected, "values")
        record_id = record[0]
        if "id" in tree["columns"]:
            id_col = "id"
        elif "bill_id" in tree["columns"]:
            id_col = "bill_id"
        else:
            id_col = "booking_id"

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
            try:
                c.execute(f"DELETE FROM {table} WHERE {id_col}=?", (record_id,))
                conn.commit()
                self.load_data(tree, table)
                messagebox.showinfo("Success", "Record deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", str(e))


# -------------------------
# Run Admin Dashboard Directly
# -------------------------
if __name__ == "__main__":
    AdminDashboard()


