import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# -------------------------
# Database Connection
# -------------------------
conn = sqlite3.connect("elderly_care.db")
c = conn.cursor()


# -------------------------
# Senior Application Class
# -------------------------
class SeniorApp:
    def __init__(self, root, senior_id):
        self.root = root
        self.root.title(f"Senior Dashboard - ID {senior_id}")
        self.root.geometry("700x500")
        self.senior_id = senior_id

        tk.Label(root, text="Senior Dashboard", font=("Arial", 18, "bold")).pack(pady=10)

        notebook = ttk.Notebook(root)
        self.services_tab = ttk.Frame(notebook)
        self.book_tab = ttk.Frame(notebook)
        self.rating_tab = ttk.Frame(notebook)
        self.bill_tab = ttk.Frame(notebook)
        notebook.add(self.services_tab, text="View Services")
        notebook.add(self.book_tab, text="Book Service")
        notebook.add(self.rating_tab, text="Rate Provider")
        notebook.add(self.bill_tab, text="My Bills")
        notebook.pack(expand=True, fill="both")

        self.setup_services_tab()
        self.setup_book_tab()
        self.setup_rating_tab()
        self.setup_bill_tab()

    # -------------------------
    # Services Tab
    # -------------------------
    def setup_services_tab(self):
        tk.Label(self.services_tab, text="Available Services", font=("Arial", 14)).pack(pady=5)
        self.service_tree = ttk.Treeview(self.services_tab, columns=("id", "name", "provider", "rating", "price"), show="headings")
        self.service_tree.heading("id", text="Service ID")
        self.service_tree.heading("name", text="Service")
        self.service_tree.heading("provider", text="Provider")
        self.service_tree.heading("rating", text="Rating")
        self.service_tree.heading("price", text="Price ($)")
        self.service_tree.pack(expand=True, fill="both")
        self.load_services()

    def load_services(self):
    # Clear existing data
        self.service_tree.delete(*self.service_tree.get_children())
    
    # Fetch all services with provider names in a single query
        query = """
        SELECT s.id, s.service_name, p.name AS provider_name, 
               s.provider_overall_rating, s.payment_amount
        FROM services s
        JOIN providers p ON s.provider_id = p.id
    """
    
        for row in c.execute(query):
                self.service_tree.insert("", "end", values=row)

    # -------------------------
    # Booking Tab
    # -------------------------
    def setup_book_tab(self):
        tk.Label(self.book_tab, text="Book a Service", font=("Arial", 14)).pack(pady=5)

        tk.Label(self.book_tab, text="Service ID:").pack()
        self.book_service_id = tk.Entry(self.book_tab)
        self.book_service_id.pack()

        # Add day, month, year fields
        for label_text, attr_name in [("Day", "book_day"), ("Month", "book_month"), ("Year", "book_year")]:
            tk.Label(self.book_tab, text=f"{label_text}:").pack()
            entry = tk.Entry(self.book_tab)
            entry.pack()
            setattr(self, attr_name, entry)

        tk.Button(self.book_tab, text="Book Now", command=self.book_service).pack(pady=5)

    def book_service(self):
        sid = self.book_service_id.get()
        day = self.book_day.get()
        month = self.book_month.get()
        year = self.book_year.get()

        if not (sid and day and month and year):
            messagebox.showerror("Error", "Enter all booking details")
            return

        try:
            day, month, year = int(day), int(month), int(year)
            c.execute("SELECT provider_id, payment_amount FROM services WHERE id=?", (sid,))
            res = c.fetchone()
            if not res:
                messagebox.showerror("Error", "Service not found")
                return

            provider_id, amount = res

            # Insert booking
            c.execute("INSERT INTO bookings (senior_id, service_id, day, month, year) VALUES (?,?,?,?,?)",
                      (self.senior_id, sid, day, month, year))

            # Insert bill
            c.execute("INSERT INTO bills (status, senior_id, provider_id, amount) VALUES (?,?,?,?)",
                      ("Pending", self.senior_id, provider_id, amount))

            conn.commit()
            messagebox.showinfo("Booked", f"Service booked for {day}/{month}/{year} successfully!")

        except ValueError:
            messagebox.showerror("Error", "Day, month, and year must be integers")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------------
    # Rating Tab
    # -------------------------
    def setup_rating_tab(self):
        tk.Label(self.rating_tab, text="Rate a Provider", font=("Arial", 14)).pack(pady=5)

        tk.Label(self.rating_tab, text="Provider ID:").pack()
        self.provider_id_entry = tk.Entry(self.rating_tab)
        self.provider_id_entry.pack()

        tk.Label(self.rating_tab, text="Rating (1-5):").pack()
        self.rating_entry = tk.Entry(self.rating_tab)
        self.rating_entry.pack()

        tk.Button(self.rating_tab, text="Submit Rating", command=self.submit_rating).pack(pady=5)

    def submit_rating(self):
        try:
            pid = int(self.provider_id_entry.get())
            rating = int(self.rating_entry.get())
            if rating < 1 or rating > 5:
                messagebox.showerror("Error", "Rating must be between 1 and 5")
                return

            c.execute("INSERT INTO ratings (senior_id, provider_id, rating) VALUES (?,?,?)",
                      (self.senior_id, pid, rating))
            conn.commit()

            # Update provider overall rating automatically
            c.execute("SELECT AVG(rating) FROM ratings WHERE provider_id=?", (pid,))
            avg = c.fetchone()[0]
            if avg:
                c.execute("UPDATE providers SET rating=? WHERE id=?", (avg, pid))
                c.execute("UPDATE services SET provider_overall_rating=? WHERE provider_id=?", (avg, pid))
                conn.commit()

            messagebox.showinfo("Success", "Rating submitted and provider rating updated!")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------------
    # Bills Tab
    # -------------------------
    def setup_bill_tab(self):
        tk.Label(self.bill_tab, text="Your Bills", font=("Arial", 14)).pack(pady=5)
        self.bill_tree = ttk.Treeview(self.bill_tab, columns=("bill", "provider", "amount", "status"), show="headings")
        for col in ("bill", "provider", "amount", "status"):
            self.bill_tree.heading(col, text=col.capitalize())
        self.bill_tree.pack(expand=True, fill="both")
        tk.Button(self.bill_tab, text="Refresh", command=self.load_bills).pack(pady=5)
        tk.Button(self.bill_tab, text="Pay Selected Bill", command=self.pay_bill).pack()

    def load_bills(self):
        self.bill_tree.delete(*self.bill_tree.get_children())

    # Single query to get provider name along with bill info
        query = """
        SELECT b.bill_id, p.name AS provider_name, b.amount, b.status
        FROM bills b
        JOIN providers p ON b.provider_id = p.id
        WHERE b.senior_id = ?
    """
    
        for row in c.execute(query, (self.senior_id,)):
            self.bill_tree.insert("", "end", values=row)


    def pay_bill(self):
        selected = self.bill_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a bill first")
            return
        bill_id = self.bill_tree.item(selected[0])['values'][0]
        c.execute("UPDATE bills SET status='Paid' WHERE bill_id=?", (bill_id,))
        conn.commit()
        messagebox.showinfo("Paid", "Bill paid successfully!")
        self.load_bills()


# -------------------------
# Login Popup for Senior ID
# -------------------------
def senior_login():
    login = tk.Toplevel()
    login.title("Senior Login")
    login.geometry("300x150")
    tk.Label(login, text="Enter Senior ID:", font=("Arial", 12)).pack(pady=10)
    entry = tk.Entry(login)
    entry.pack(pady=5)

    def submit_login():
        sid = entry.get()
        if not sid.isdigit():
            messagebox.showerror("Error", "Senior ID must be numeric")
            return
        senior = c.execute("SELECT id FROM seniors WHERE id=?", (sid,)).fetchone()
        if senior:
            login.destroy()
            SeniorApp(root, int(sid))
        else:
            messagebox.showerror("Error", "Senior ID not found")

    tk.Button(login, text="Enter", command=submit_login).pack(pady=10)
    login.wait_window()


# -------------------------
# Run the Senior App
# -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window until login success
    senior_login()
    root.deiconify()  # Show dashboard only after successful login
    root.mainloop()


