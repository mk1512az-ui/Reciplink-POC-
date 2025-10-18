import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

conn = sqlite3.connect("elderly_care.db")
c = conn.cursor()

class ProviderApp:
    def __init__(self, root, provider_id):
        self.root = root
        self.provider_id = provider_id

        self.root.title(f"Provider Dashboard - ID {provider_id}")
        self.root.geometry("800x500")

        tk.Label(root, text="Provider Dashboard", font=("Arial", 18, "bold")).pack(pady=10)

        notebook = ttk.Notebook(root)
        self.my_services_tab = ttk.Frame(notebook)
        self.bookings_tab = ttk.Frame(notebook)
        notebook.add(self.my_services_tab, text="My Services")
        notebook.add(self.bookings_tab, text="Bookings")
        notebook.pack(expand=True, fill="both")

        self.setup_services_tab()
        self.setup_bookings_tab()

    # -------------------- SERVICES TAB --------------------
    def setup_services_tab(self):
        tk.Label(self.my_services_tab, text="Manage My Services", font=("Arial", 14)).pack(pady=5)
        self.tree = ttk.Treeview(self.my_services_tab, columns=("id","name","desc","price"), show="headings")
        for col in ("id","name","desc","price"):
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(expand=True, fill="both")
        self.load_services()

        tk.Button(self.my_services_tab, text="Add Service", command=self.add_service).pack(side="left", padx=5)
        tk.Button(self.my_services_tab, text="Delete Service", command=self.delete_service).pack(side="left", padx=5)

    def load_services(self):
        self.tree.delete(*self.tree.get_children())
        for row in c.execute("SELECT id, service_name, service_description, payment_amount FROM services WHERE provider_id=?", (self.provider_id,)):
            self.tree.insert("", "end", values=row)

    def add_service(self):
        new_name = simple_input("Enter Service Name:")
        new_desc = simple_input("Enter Description:")
        new_price = simple_input("Enter Price:")
        if not new_name or not new_price:
            messagebox.showerror("Error", "Service name and price are required.")
            return
        c.execute("INSERT INTO services (service_name, provider_id, service_description, payment_amount) VALUES (?,?,?,?)",
                  (new_name, self.provider_id, new_desc, new_price))
        conn.commit()
        self.load_services()

    def delete_service(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a service")
            return
        sid = self.tree.item(selected[0])['values'][0]
        c.execute("DELETE FROM services WHERE id=?", (sid,))
        conn.commit()
        self.load_services()

    # -------------------- BOOKINGS TAB --------------------
    def setup_bookings_tab(self):
        tk.Label(self.bookings_tab, text="Bookings on My Services", font=("Arial", 14)).pack(pady=5)
        self.book_tree = ttk.Treeview(self.bookings_tab, columns=("booking_id","senior","service","date","bill_status"), show="headings")
        for col in ("booking_id","senior","service","date","bill_status"):
            self.book_tree.heading(col, text=col.capitalize())
        self.book_tree.pack(expand=True, fill="both")
        tk.Button(self.bookings_tab, text="Refresh", command=self.load_bookings).pack(pady=5)
        tk.Button(self.bookings_tab, text="Mark Selected as Paid", command=self.mark_paid).pack(pady=5)

    def load_bookings(self):
        self.book_tree.delete(*self.book_tree.get_children())

        query = """
        SELECT 
            b.booking_id,
            s2.name AS senior_name,
            s1.service_name,
            b.day, b.month, b.year,
            COALESCE(bi.status, 'No Bill') AS bill_status
        FROM bookings b
        JOIN services s1 ON b.service_id = s1.id
        JOIN seniors s2 ON b.senior_id = s2.id
        LEFT JOIN bills bi 
            ON bi.senior_id = b.senior_id
            AND bi.provider_id = s1.provider_id
            AND bi.amount = s1.payment_amount
        WHERE s1.provider_id = ?
        ORDER BY b.year DESC, b.month DESC, b.day DESC
    """

        for row in c.execute(query, (self.provider_id,)):
            booking_id, senior_name, service_name, day, month, year, bill_status = row
            date_str = f"{day}/{month}/{year}"
            self.book_tree.insert("", "end", values=(booking_id, senior_name, service_name, date_str, bill_status))

    def mark_paid(self):
        selected = self.book_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a booking")
            return
        booking_id = self.book_tree.item(selected[0])['values'][0]
        booking = c.execute("SELECT senior_id, service_id FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
        if booking:
            senior_id, service_id = booking
            c.execute("UPDATE bills SET status='Paid' WHERE senior_id=? AND provider_id=? AND amount=(SELECT payment_amount FROM services WHERE id=?)",
                      (senior_id, self.provider_id, service_id))
            conn.commit()
            messagebox.showinfo("Success", "Bill marked as Paid")
            self.load_bookings()
        else:
            messagebox.showerror("Error", "Booking not found")


# -------------------- HELPER: SIMPLE INPUT POPUP --------------------
def simple_input(prompt):
    popup = tk.Toplevel()
    popup.title(prompt)
    tk.Label(popup, text=prompt).pack(pady=5)
    entry = tk.Entry(popup)
    entry.pack(pady=5)
    val = tk.StringVar()
    def submit():
        val.set(entry.get())
        popup.destroy()
    tk.Button(popup, text="OK", command=submit).pack(pady=5)
    popup.wait_window()
    return val.get()

# -------------------- LOGIN PROMPT --------------------
def provider_login():
    login = tk.Toplevel()
    login.title("Provider Login")
    login.geometry("300x150")
    tk.Label(login, text="Enter Provider ID:", font=("Arial", 12)).pack(pady=10)
    entry = tk.Entry(login)
    entry.pack(pady=5)

    def submit_login():
        pid = entry.get()
        if not pid.isdigit():
            messagebox.showerror("Error", "Provider ID must be numeric")
            return
        provider = c.execute("SELECT id FROM providers WHERE id=?", (pid,)).fetchone()
        if provider:
            login.destroy()
            ProviderApp(root, int(pid))
        else:
            messagebox.showerror("Error", "Provider ID not found")

    tk.Button(login, text="Enter", command=submit_login).pack(pady=10)
    login.wait_window()

# -------------------- MAIN --------------------
root = tk.Tk()
root.withdraw()  # Hide main window until login success
provider_login()
root.deiconify()  # Show dashboard only after login
root.mainloop()


