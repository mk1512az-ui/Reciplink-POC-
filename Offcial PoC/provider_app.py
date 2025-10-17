import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

conn = sqlite3.connect("elderly_care.db")
c = conn.cursor()

class ProviderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Provider Dashboard")
        self.root.geometry("800x500")

        tk.Label(root, text="Provider Dashboard", font=("Arial", 18, "bold")).pack(pady=10)

        notebook = ttk.Notebook(root)
        self.my_services_tab = ttk.Frame(notebook)
        self.bookings_tab = ttk.Frame(notebook)
        notebook.add(self.my_services_tab, text="My Services")
        notebook.add(self.bookings_tab, text="Bookings")
        notebook.pack(expand=True, fill="both")

        self.provider_id = 1  # Assume provider is logged in

        self.setup_services_tab()
        self.setup_bookings_tab()

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
        SELECT b.booking_id, b.senior_id, b.service_id, b.day, b.month, b.year
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        WHERE s.provider_id = ?
        """
        for row in c.execute(query, (self.provider_id,)):
            booking_id, senior_id, service_id, day, month, year = row
            # Get senior name
            sname = c.execute("SELECT name FROM seniors WHERE id=?", (senior_id,)).fetchone()
            sname = sname[0] if sname else "Unknown"
            # Get service name
            sname_service = c.execute("SELECT service_name FROM services WHERE id=?", (service_id,)).fetchone()
            sname_service = sname_service[0] if sname_service else "Unknown"
            # Get bill status
            bill = c.execute("SELECT status FROM bills WHERE senior_id=? AND provider_id=? AND amount=(SELECT payment_amount FROM services WHERE id=?)",
                             (senior_id, self.provider_id, service_id)).fetchone()
            bill_status = bill[0] if bill else "No Bill"
            # Format date
            date_str = f"{day}/{month}/{year}"
            self.book_tree.insert("", "end", values=(booking_id, sname, sname_service, date_str, bill_status))

    def mark_paid(self):
        selected = self.book_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a booking")
            return
        booking_id = self.book_tree.item(selected[0])['values'][0]
        # Get booking info
        booking = c.execute("SELECT senior_id, service_id FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
        if booking:
            senior_id, service_id = booking
            # Update bill if exists
            c.execute("UPDATE bills SET status='Paid' WHERE senior_id=? AND provider_id=? AND amount=(SELECT payment_amount FROM services WHERE id=?)",
                      (senior_id, self.provider_id, service_id))
            conn.commit()
            messagebox.showinfo("Success", "Bill marked as Paid")
            self.load_bookings()
        else:
            messagebox.showerror("Error", "Booking not found")


def simple_input(prompt):
    popup = tk.Toplevel()
    popup.title(prompt)
    tk.Label(popup, text=prompt).pack()
    entry = tk.Entry(popup)
    entry.pack()
    val = tk.StringVar()
    def submit():
        val.set(entry.get())
        popup.destroy()
    tk.Button(popup, text="OK", command=submit).pack()
    popup.wait_window()
    return val.get()

root = tk.Tk()
ProviderApp(root)
root.mainloop()

