import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.simpledialog as simpledialog
from datetime import datetime, timedelta, date as datetime_date
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import shutil
import glob
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# For WhatsApp messaging (install with 'pip install pywhatkit' in venv)
import pywhatkit as pwk

# Custom adapters for SQLite dates (fixes deprecation and type issues)
def adapt_date_iso(val):
    """Adapt datetime.date to SQLite ISO string."""
    return val.isoformat()

def convert_date(val):
    """Convert SQLite DATE string to datetime.date."""
    if val is None:
        return None
    if isinstance(val, bytes):
        val = val.decode('utf-8')
    return datetime.strptime(val, "%Y-%m-%d").date()

# Register globally
sqlite3.register_adapter(datetime_date, adapt_date_iso)
sqlite3.register_converter("DATE", convert_date)

class GymManagementSoftware:
    def __init__(self, root):
        self.root = root
        self.root.title("Gym Management Software")
        self.root.geometry("1200x800")
        
        # Load from env
        self.gym_name = os.getenv('GYM_NAME', 'Vivek Gym')
        self.gym_address = os.getenv('GYM_ADDRESS', '123 Main St, City')
        self.currency_symbol = os.getenv('CURRENCY_SYMBOL', '₹')
        self.theme_color = os.getenv('THEME_COLOR', '#e8f4fd')
        
        self.root.configure(bg=self.theme_color)  # Dynamic theme color
        
        # Enhanced Style for Beautiful UI
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', padding=12, font=('Arial', 10, 'bold'), background='#4CAF50', foreground='white')
        style.map('TButton', background=[('active', '#45a049')])
        style.configure('TLabel', font=('Arial', 11), background=self.theme_color)
        style.configure('TEntry', font=('Arial', 10), padding=5)
        style.configure('TLabelFrame', font=('Arial', 12, 'bold'), background=self.theme_color)
        style.configure('TNotebook', background=self.theme_color)
        style.configure('TNotebook.Tab', padding=[20, 8], font=('Arial', 11, 'bold'))
        
        # Header Label for Beauty with Gym Name
        header = tk.Label(root, text=f"🏋️ {self.gym_name} Management System", font=('Arial', 18, 'bold'), bg=self.theme_color, fg='#2E7D32')
        header.pack(pady=10)
        
        # Database setup with date detection
        self.conn = sqlite3.connect('gym.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor = self.conn.cursor()
        self.setup_database()
        
        # Load gym phone from env (e.g., GYM_PHONE=916238100393 in .env)
        self.gym_phone = os.getenv('GYM_PHONE', '916238100393')  # Default +91 6238100393
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tabs
        self.members_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.members_frame, text='👥 Members')
        self.setup_members_tab()
        
        self.payments_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.payments_frame, text='💰 Payments')
        self.setup_payments_tab()
        
        self.attendance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.attendance_frame, text='📅 Attendance')
        self.setup_attendance_tab()
        
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text='📊 Reports')
        self.setup_reports_tab()
        
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text='⚙️ Settings')
        self.setup_settings_tab()
        
        # Footer with Backup
        footer_frame = tk.Frame(root, bg=self.theme_color)
        footer_frame.pack(fill='x', pady=5)
        self.backup_btn = ttk.Button(footer_frame, text="💾 Backup Database", command=self.backup_db)
        self.backup_btn.pack(side='right', padx=10)
        
        # Auto-run on open: Check renewals and send messages
        self.check_and_send_renewals()
        self.auto_backup_and_cleanup()
    
    def setup_database(self):
        # Members table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                join_date DATE NOT NULL,
                expiry_date DATE NOT NULL
            )
        ''')
        
        # Payments table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                payment_date DATE NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
        ''')
        
        # Attendance table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                att_date DATE NOT NULL,
                status TEXT NOT NULL,  -- 'Present' or 'Absent'
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
        ''')
        
        # Subscription plans table (new)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duration_months INTEGER NOT NULL,
                price REAL NOT NULL,
                description TEXT
            )
        ''')
        
        # Insert default plans if empty
        self.cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        if self.cursor.fetchone()[0] == 0:
            default_plans = [
                (1, 500, "Monthly Plan"),
                (3, 1400, "Quarterly Plan"),
                (6, 2700, "Half-Yearly Plan"),
                (12, 5000, "Yearly Plan")
            ]
            self.cursor.executemany("INSERT INTO subscription_plans (duration_months, price, description) VALUES (?, ?, ?)", default_plans)
            self.conn.commit()
        
        self.conn.commit()
    
    # Members Tab
    def setup_members_tab(self):
        # Add Member Frame
        add_frame = ttk.LabelFrame(self.members_frame, text="➕ Add New Member", padding=15)
        add_frame.pack(fill='x', padx=10, pady=10)
        
        # Row 0
        ttk.Label(add_frame, text="👤 Name:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.name_entry = ttk.Entry(add_frame, width=20)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(add_frame, text="🌍 Country Code:").grid(row=0, column=2, sticky='w', pady=5, padx=5)
        self.country_code_var = tk.StringVar(value="+91")
        country_combo = ttk.Combobox(add_frame, textvariable=self.country_code_var, values=["+1", "+91", "+44", "+61", "+81"], state="readonly", width=10)
        country_combo.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        
        ttk.Label(add_frame, text="📱 Phone (local):").grid(row=0, column=4, sticky='w', pady=5, padx=5)
        self.phone_entry = ttk.Entry(add_frame, width=20)
        self.phone_entry.grid(row=0, column=5, padx=5, pady=5, sticky='w')
        
        # Row 1
        ttk.Label(add_frame, text="📅 Join Date (YYYY-MM-DD):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.join_entry = ttk.Entry(add_frame, width=20)
        self.join_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.join_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(add_frame, text="⏱️ Plan ID:").grid(row=1, column=2, sticky='w', pady=5, padx=5)
        self.plan_var = tk.StringVar(value="1")
        self.plan_combo = ttk.Combobox(add_frame, textvariable=self.plan_var, values=["1"], state="readonly", width=10)
        self.plan_combo.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        
        add_btn = ttk.Button(add_frame, text="➕ Add Member", command=self.add_member)
        add_btn.grid(row=2, column=2, columnspan=2, pady=15)
        
        # Members List
        list_frame = ttk.LabelFrame(self.members_frame, text="📋 Members List", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview
        columns = ('ID', 'Name', 'Phone', 'Join Date', 'Expiry Date', 'Status')
        self.members_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)
        
        # Color tags for members (Active green, Expired red)
        self.members_tree.tag_configure('active', background='lightgreen')
        self.members_tree.tag_configure('expired', background='lightcoral')
        
        for col in columns:
            self.members_tree.heading(col, text=col)
            self.members_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.members_tree.yview)
        self.members_tree.configure(yscrollcommand=scrollbar.set)
        
        self.members_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="✏️ Update", command=self.update_member).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete", command=self.delete_member).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_members).pack(side='right', padx=5)
        
        self.refresh_members()
    
    def add_member(self):
        name = self.name_entry.get().strip()
        country_code = self.country_code_var.get()
        phone_local = self.phone_entry.get().strip()
        if not phone_local.isdigit():
            messagebox.showerror("Error", "Phone number must be digits only!")
            return
        if country_code == '+91' and len(phone_local) != 10:
            messagebox.showerror("Error", "For India (+91), local phone must be exactly 10 digits!")
            return
        phone = country_code.lstrip('+') + phone_local  # e.g., 91 + 6238100393 = 916238100393
        join_str = self.join_entry.get().strip()
        plan_id = int(self.plan_var.get())
        
        if not all([name, phone_local, join_str]):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        # Get plan details
        self.cursor.execute("SELECT duration_months, price FROM subscription_plans WHERE id=?", (plan_id,))
        plan = self.cursor.fetchone()
        if not plan:
            messagebox.showerror("Error", "Invalid plan ID!")
            return
        months, price = plan
        
        try:
            join_date = datetime.strptime(join_str, '%Y-%m-%d').date()
            expiry_date = join_date + timedelta(days=30 * months)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date! Details: {e}")
            return
        
        # Check unique phone
        self.cursor.execute("SELECT id FROM members WHERE phone=?", (phone,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Phone number already exists!")
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO members (name, phone, join_date, expiry_date) VALUES (?, ?, ?, ?)",
                (name, phone, join_date, expiry_date)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Member added successfully!")
            
            # Welcome Message via WhatsApp (Sent to Member Phone) with Price, Gym Name, Address
            welcome_msg = f"Welcome to {self.gym_name}, {name}! You subscribed to {months}-month plan for {self.currency_symbol}{price}.\nStarts: {join_date.strftime('%Y-%m-%d')}, Expires: {expiry_date.strftime('%Y-%m-%d')}.\nAddress: {self.gym_address}\nEnjoy! 💪"
            try:
                pwk.sendwhatmsg_instantly(phone, welcome_msg)
                messagebox.showinfo("WhatsApp Sent", f"Welcome message sent to {phone} via WhatsApp! 📱")
            except Exception as wa_e:
                messagebox.showwarning("WhatsApp Issue", f"Failed to send (check country code/phone format): {wa_e}\nMessage: {welcome_msg}")
            
            self.clear_member_entries()
            self.refresh_members()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")
    
    def clear_member_entries(self):
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.join_entry.delete(0, tk.END)
        self.join_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
    
    def refresh_members(self):
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)
        
        self.cursor.execute("SELECT * FROM members ORDER BY id DESC")
        rows = self.cursor.fetchall()
        today = datetime.now().date()
        
        for row in rows:
            expiry = row[4]
            if expiry and today <= expiry:
                status = "🟢 Active"
                tag = 'active'
            else:
                status = "🔴 Expired"
                tag = 'expired'
            join_str = row[3].strftime('%Y-%m-%d') if hasattr(row[3], 'strftime') else str(row[3])
            expiry_str = row[4].strftime('%Y-%m-%d') if hasattr(row[4], 'strftime') else str(row[4])
            self.members_tree.insert('', 'end', values=(row[0], row[1], row[2], join_str, expiry_str, status), tags=(tag,))
        
        # Update plan combo values
        self.cursor.execute("SELECT id FROM subscription_plans ORDER BY id")
        plans = [str(row[0]) for row in self.cursor.fetchall()]
        self.plan_combo['values'] = plans
        if plans:
            self.plan_var.set(plans[0])
        
        self.members_tree.focus_set()
    
    def update_member(self):
        selected = self.members_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a member to update!")
            return
        
        item = self.members_tree.item(selected[0])
        member_id = item['values'][0]
        
        new_name = simpledialog.askstring("Update Name", "New Name:", initialvalue=item['values'][1])
        if new_name is not None:
            new_phone_local = simpledialog.askstring("Update Phone (local)", "New Phone (local digits only):", initialvalue=item['values'][2].lstrip(self.country_code_var.get().lstrip('+')))
            if new_phone_local is not None:
                if not new_phone_local.isdigit() or len(new_phone_local) != 10:
                    messagebox.showerror("Error", "Phone must be exactly 10 digits for India (+91)!")
                    return
                new_phone = self.country_code_var.get().lstrip('+') + new_phone_local.strip()
                try:
                    self.cursor.execute(
                        "UPDATE members SET name=?, phone=? WHERE id=?",
                        (new_name.strip(), new_phone, member_id)
                    )
                    self.conn.commit()
                    self.refresh_members()
                    messagebox.showinfo("Success", "Member updated!")
                except Exception as e:
                    messagebox.showerror("Error", f"Update failed: {e}")
            else:
                messagebox.showerror("Error", "Phone must be digits only!")
    
    def delete_member(self):
        selected = self.members_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a member to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this member?"):
            member_id = self.members_tree.item(selected[0])['values'][0]
            try:
                self.cursor.execute("DELETE FROM members WHERE id=?", (member_id,))
                self.conn.commit()
                self.refresh_members()
                messagebox.showinfo("Success", "Member deleted!")
            except Exception as e:
                messagebox.showerror("Error", f"Delete failed: {e}")
    
    # Payments Tab
    def setup_payments_tab(self):
        # Add Payment Frame
        add_frame = ttk.LabelFrame(self.payments_frame, text="➕ Add Payment", padding=15)
        add_frame.pack(fill='x', padx=10, pady=10)
        
        # Row 0
        ttk.Label(add_frame, text="🆔 Member ID:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.member_id_entry = ttk.Entry(add_frame, width=20)
        self.member_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(add_frame, text=f"💵 Amount ({self.currency_symbol}):").grid(row=0, column=2, sticky='w', pady=5, padx=5)
        self.amount_entry = ttk.Entry(add_frame, width=20)
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        
        # Row 1
        ttk.Label(add_frame, text="💳 Method:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.method_entry = ttk.Entry(add_frame, width=20)
        self.method_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(add_frame, text="📅 Payment Date (YYYY-MM-DD):").grid(row=1, column=2, sticky='w', pady=5, padx=5)
        self.payment_date_entry = ttk.Entry(add_frame, width=20)
        self.payment_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.payment_date_entry.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        
        add_btn = ttk.Button(add_frame, text="➕ Add Payment", command=self.add_payment)
        add_btn.grid(row=2, column=1, columnspan=2, pady=15)
        
        # Payments List
        list_frame = ttk.LabelFrame(self.payments_frame, text="📋 Payments History", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Member ID', 'Date', 'Amount', 'Method')
        self.payments_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)
        
        for col in columns:
            self.payments_tree.heading(col, text=col)
            self.payments_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.payments_tree.yview)
        self.payments_tree.configure(yscrollcommand=scrollbar.set)
        
        self.payments_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        ttk.Button(list_frame, text="🔄 Refresh", command=self.refresh_payments).pack(pady=5)
        
        self.refresh_payments()
    
    def add_payment(self):
        member_id = self.member_id_entry.get().strip()
        amount = self.amount_entry.get().strip()
        method = self.method_entry.get().strip()
        date_str = self.payment_date_entry.get().strip()
        
        if not all([member_id, amount, method, date_str]):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        try:
            amount = float(amount)
            payment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount or date!")
            return
        
        # Check if member exists
        self.cursor.execute("SELECT id FROM members WHERE id=?", (int(member_id),))
        if not self.cursor.fetchone():
            messagebox.showerror("Error", "Member ID does not exist!")
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO payments (member_id, payment_date, amount, method) VALUES (?, ?, ?, ?)",
                (int(member_id), payment_date, amount, method)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Payment added!")
            self.clear_payment_entries()
            self.refresh_payments()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")
    
    def clear_payment_entries(self):
        self.member_id_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.method_entry.delete(0, tk.END)
        self.payment_date_entry.delete(0, tk.END)
        self.payment_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
    
    def refresh_payments(self):
        for item in self.payments_tree.get_children():
            self.payments_tree.delete(item)
        
        self.cursor.execute("SELECT * FROM payments ORDER BY id DESC")
        for row in self.cursor.fetchall():
            date_str = row[2].strftime('%Y-%m-%d') if hasattr(row[2], 'strftime') else str(row[2])
            self.payments_tree.insert('', 'end', values=(row[0], row[1], date_str, f"{self.currency_symbol}{row[3]}", row[4]))
    
    # Attendance Tab
    def setup_attendance_tab(self):
        # Mark Attendance Frame
        add_frame = ttk.LabelFrame(self.attendance_frame, text="✅ Mark Attendance", padding=15)
        add_frame.pack(fill='x', padx=10, pady=10)
        
        # Row 0
        ttk.Label(add_frame, text="🆔 Member ID:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.att_member_id_entry = ttk.Entry(add_frame, width=20)
        self.att_member_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(add_frame, text="📊 Status:").grid(row=0, column=2, sticky='w', pady=5, padx=5)
        self.status_var = tk.StringVar(value="Present")
        status_combo = ttk.Combobox(add_frame, textvariable=self.status_var, values=["Present", "Absent"], state="readonly", width=15)
        status_combo.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        
        # Row 1
        ttk.Label(add_frame, text="📅 Date (YYYY-MM-DD):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.att_date_entry = ttk.Entry(add_frame, width=20)
        self.att_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.att_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        add_btn = ttk.Button(add_frame, text="✅ Mark Attendance", command=self.mark_attendance)
        add_btn.grid(row=2, column=1, columnspan=2, pady=15)
        
        # Attendance List
        list_frame = ttk.LabelFrame(self.attendance_frame, text="📋 Attendance History", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Member ID', 'Date', 'Status')
        self.attendance_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)
        
        # Color tags for attendance rows (Present green, Absent red)
        self.attendance_tree.tag_configure('present', background='lightgreen')
        self.attendance_tree.tag_configure('absent', background='lightcoral')
        
        for col in columns:
            self.attendance_tree.heading(col, text=col)
            self.attendance_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)
        
        self.attendance_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        ttk.Button(list_frame, text="🔄 Refresh", command=self.refresh_attendance).pack(pady=5)
        
        self.refresh_attendance()
    
    def mark_attendance(self):
        member_id = self.att_member_id_entry.get().strip()
        status = self.status_var.get()
        date_str = self.att_date_entry.get().strip()
        
        if not all([member_id, date_str]):
            messagebox.showerror("Error", "Member ID and Date are required!")
            return
        
        try:
            att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Error", "Invalid date!")
            return
        
        # Check if member exists
        self.cursor.execute("SELECT id FROM members WHERE id=?", (int(member_id),))
        if not self.cursor.fetchone():
            messagebox.showerror("Error", "Member ID does not exist!")
            return
        
        # Check if already marked for this date
        self.cursor.execute(
            "SELECT id FROM attendance WHERE member_id=? AND att_date=?",
            (int(member_id), att_date)
        )
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Attendance already marked for this date!")
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO attendance (member_id, att_date, status) VALUES (?, ?, ?)",
                (int(member_id), att_date, status)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Attendance marked!")
            self.clear_attendance_entries()
            self.refresh_attendance()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")
    
    def clear_attendance_entries(self):
        self.att_member_id_entry.delete(0, tk.END)
        self.att_date_entry.delete(0, tk.END)
        self.att_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
    
    def refresh_attendance(self):
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        
        self.cursor.execute("SELECT * FROM attendance ORDER BY id DESC")
        for row in self.cursor.fetchall():
            date_str = row[2].strftime('%Y-%m-%d') if hasattr(row[2], 'strftime') else str(row[2])
            tag = 'present' if row[3].lower() == 'present' else 'absent'
            self.attendance_tree.insert('', 'end', values=(row[0], row[1], date_str, row[3]), tags=(tag,))
    
    # Reports Tab
    def setup_reports_tab(self):
        btn_frame = ttk.Frame(self.reports_frame, padding=20)
        btn_frame.pack(pady=20, fill='x')
        
        ttk.Button(btn_frame, text="👥 View Members Report", command=lambda: self.show_report('members')).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="💰 View Payments Report", command=lambda: self.show_report('payments')).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📅 View Attendance Report", command=lambda: self.show_report('attendance')).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="📤 Export Members CSV", command=lambda: self.export_data('members', 'csv')).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📤 Export Payments CSV", command=lambda: self.export_data('payments', 'csv')).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📤 Export Attendance CSV", command=lambda: self.export_data('attendance', 'csv')).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="📈 Monthly Revenue Chart", command=self.monthly_revenue_chart).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🥧 Active vs Inactive", command=self.active_inactive_chart).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📊 Attendance Trend", command=self.attendance_trend_chart).pack(side='left', padx=5)
    
    def show_report(self, table):
        if table == 'members':
            df = pd.read_sql_query("SELECT * FROM members", self.conn)
            tree = self.members_tree
            self.notebook.select(0)
        elif table == 'payments':
            df = pd.read_sql_query("SELECT * FROM payments", self.conn)
            tree = self.payments_tree
            self.notebook.select(1)
        else:
            df = pd.read_sql_query("SELECT * FROM attendance", self.conn)
            tree = self.attendance_tree
            self.notebook.select(2)
        
        for item in tree.get_children():
            tree.delete(item)
        for _, row in df.iterrows():
            display_row = list(row)
            for i in range(len(display_row)):
                if hasattr(display_row[i], 'strftime'):
                    display_row[i] = display_row[i].strftime('%Y-%m-%d')
            tree.insert('', 'end', values=tuple(display_row))
        
        messagebox.showinfo("Report", f"{table.capitalize()} report loaded!")
    
    def export_data(self, table, format_type):
        if format_type == 'csv':
            if table == 'members':
                df = pd.read_sql_query("SELECT * FROM members", self.conn)
                filename = f"members_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif table == 'payments':
                df = pd.read_sql_query("SELECT * FROM payments", self.conn)
                filename = f"payments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            else:
                df = pd.read_sql_query("SELECT * FROM attendance", self.conn)
                filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Convert date objects to strings for export with timestamp
            for col in df.columns:
                if 'date' in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
            
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialvalue=filename)
            if file_path:
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported to {os.path.basename(file_path)} with timestamps!")
    
    def monthly_revenue_chart(self):
        df = pd.read_sql_query("SELECT payment_date, SUM(amount) as revenue FROM payments GROUP BY strftime('%Y-%m', payment_date)", self.conn)
        if df.empty:
            messagebox.showwarning("Warning", "No payment data!")
            return
        
        df['payment_date'] = pd.to_datetime(df['payment_date'])
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df['payment_date'], df['revenue'], marker='o', linewidth=2, color='green')
        ax.set_title('📈 Monthly Revenue', fontsize=16, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel(f'Revenue ({self.currency_symbol})')
        plt.tight_layout()
        plt.show()
    
    def active_inactive_chart(self):
        df = pd.read_sql_query("SELECT COUNT(*) as count, CASE WHEN expiry_date >= date('now') THEN 'Active' ELSE 'Inactive' END as status FROM members GROUP BY status", self.conn)
        if df.empty:
            messagebox.showwarning("Warning", "No member data!")
            return
        
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = ['#4CAF50', '#F44336']
        ax.pie(df['count'], labels=df['status'], autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title('🥧 Active vs Inactive Members', fontsize=16, fontweight='bold')
        plt.show()
    
    def attendance_trend_chart(self):
        df = pd.read_sql_query("SELECT att_date, COUNT(*) as count FROM attendance WHERE status='Present' GROUP BY strftime('%Y-%m', att_date)", self.conn)
        if df.empty:
            messagebox.showwarning("Warning", "No attendance data!")
            return
        
        df['att_date'] = pd.to_datetime(df['att_date'])
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(df['att_date'], df['count'], color='blue')
        ax.set_title('📊 Attendance Trend', fontsize=16, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Present Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    # Settings Tab (New)
    def setup_settings_tab(self):
        frame = ttk.Frame(self.settings_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        # Subscription Plans
        plans_frame = ttk.LabelFrame(frame, text="💰 Subscription Plans", padding=10)
        plans_frame.pack(fill='x', pady=10)
        
        columns = ('ID', 'Months', f'Price ({self.currency_symbol})', 'Description')
        self.plans_tree = ttk.Treeview(plans_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.plans_tree.heading(col, text=col)
            self.plans_tree.column(col, width=120)
        self.plans_tree.pack(fill='x')
        
        ttk.Button(plans_frame, text="🔄 Refresh Plans", command=self.refresh_plans).pack(pady=5)
        ttk.Button(plans_frame, text="➕ Add Plan", command=self.add_plan).pack(side='left', padx=5)
        ttk.Button(plans_frame, text="🗑️ Delete Plan", command=self.delete_plan).pack(side='left', padx=5)
        
        # Gym Phone
        phone_frame = ttk.LabelFrame(frame, text="📱 Gym Settings", padding=10)
        phone_frame.pack(fill='x', pady=10)
        ttk.Label(phone_frame, text=f"Gym Phone: {self.gym_phone}").pack()
        ttk.Button(phone_frame, text="Update Gym Phone", command=self.update_gym_phone).pack(pady=5)
        
        # Gym Info
        info_frame = ttk.LabelFrame(frame, text="🏠 Gym Info", padding=10)
        info_frame.pack(fill='x', pady=10)
        ttk.Label(info_frame, text=f"Name: {self.gym_name}").pack()
        ttk.Label(info_frame, text=f"Address: {self.gym_address}").pack()
        ttk.Label(info_frame, text=f"Currency: {self.currency_symbol}").pack()
        ttk.Label(info_frame, text=f"Theme Color: {self.theme_color}").pack()
        ttk.Button(info_frame, text="Update Gym Info", command=self.update_gym_info).pack(pady=5)
        
        self.refresh_plans()
    
    def refresh_plans(self):
        for item in self.plans_tree.get_children():
            self.plans_tree.delete(item)
        self.cursor.execute("SELECT * FROM subscription_plans ORDER BY duration_months")
        for row in self.cursor.fetchall():
            self.plans_tree.insert('', 'end', values=(row[0], row[1], f"{self.currency_symbol}{row[2]}", row[3]))
    
    def add_plan(self):
        months = simpledialog.askinteger("Add Plan", "Months:")
        if months:
            price = simpledialog.askfloat("Add Plan", f"Price ({self.currency_symbol}):")
            if price:
                desc = simpledialog.askstring("Add Plan", "Description:", initialvalue=f"{months}-Month Plan")
                try:
                    self.cursor.execute("INSERT INTO subscription_plans (duration_months, price, description) VALUES (?, ?, ?)", (months, price, desc))
                    self.conn.commit()
                    self.refresh_plans()
                    messagebox.showinfo("Success", "Plan added!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed: {e}")
    
    def delete_plan(self):
        selected = self.plans_tree.selection()
        if selected:
            plan_id = self.plans_tree.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", "Delete this plan?"):
                self.cursor.execute("DELETE FROM subscription_plans WHERE id=?", (plan_id,))
                self.conn.commit()
                self.refresh_plans()
                messagebox.showinfo("Success", "Plan deleted!")
    
    def update_gym_phone(self):
        new_phone = simpledialog.askstring("Update Gym Phone", "New Gym Phone (international digits only, e.g., 916238100393):", initialvalue=self.gym_phone)
        if new_phone and new_phone.isdigit():
            # Update .env (overwrite if exists)
            env_content = f"GYM_PHONE={new_phone}\n"
            with open('.env', 'w') as f:
                f.write(env_content)
            self.gym_phone = new_phone
            messagebox.showinfo("Success", "Gym phone updated!")
        else:
            messagebox.showerror("Error", "Phone must be digits only!")
    
    def update_gym_info(self):
        new_name = simpledialog.askstring("Update Gym Name", "New Gym Name:", initialvalue=self.gym_name)
        new_address = simpledialog.askstring("Update Gym Address", "New Address:", initialvalue=self.gym_address)
        new_currency = simpledialog.askstring("Update Currency Symbol", "New Symbol (e.g., ₹):", initialvalue=self.currency_symbol)
        new_theme = simpledialog.askstring("Update Theme Color", "New Color (e.g., #e8f4fd):", initialvalue=self.theme_color)
        
        if new_name:
            self.gym_name = new_name
            self.root.title(f"{self.gym_name} Management Software")
        if new_address:
            self.gym_address = new_address
        if new_currency:
            self.currency_symbol = new_currency
        if new_theme:
            self.theme_color = new_theme
            self.root.configure(bg=self.theme_color)
            # Note: Full restyle would require restart for labels/frames
        
        # Update .env
        env_content = f"GYM_NAME={self.gym_name}\nGYM_ADDRESS={self.gym_address}\nCURRENCY_SYMBOL={self.currency_symbol}\nTHEME_COLOR={self.theme_color}\n"
        with open('.env', 'w') as f:
            f.write(env_content)
        messagebox.showinfo("Success", "Gym info updated! Restart app for full theme changes.")
    
    def check_and_send_renewals(self):
        """Auto-send renewal reminders on app open"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        self.cursor.execute("""
            SELECT name, phone, expiry_date FROM members 
            WHERE expiry_date IN (?, ?) AND phone LIKE '91%'
        """, (today, tomorrow))
        renewals = self.cursor.fetchall()
        sent_count = 0
        for name, phone, expiry in renewals:
            renewal_msg = f"Hi {name}! Your {self.gym_name} membership expires on {expiry.strftime('%Y-%m-%d')}. Renew now! Address: {self.gym_address}. Contact: {self.gym_phone} 💪"
            try:
                pwk.sendwhatmsg_instantly(phone, renewal_msg)
                sent_count += 1
                print(f"Renewal sent to {phone}")
            except Exception as e:
                print(f"Failed to send to {phone}: {e}")
        if sent_count > 0:
            messagebox.showinfo("Renewals", f"Sent {sent_count} renewal reminders automatically!")
    
    def auto_backup_and_cleanup(self):
        """Auto backup on open and delete old backups (>7 days)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"gym_backup_{timestamp}.db"
        shutil.copy('gym.db', backup_path)
        
        # Cleanup old backups
        old_backups = glob.glob("gym_backup_*.db")
        week_ago = datetime.now() - timedelta(days=7)
        deleted = 0
        for backup in old_backups:
            mod_time = datetime.fromtimestamp(os.path.getmtime(backup))
            if mod_time < week_ago:
                os.remove(backup)
                deleted += 1
        if deleted > 0:
            print(f"Deleted {deleted} old backups")
        messagebox.showinfo("Auto Backup", f"Backed up to {backup_path}. Cleaned {deleted} old files.")
    
    def backup_db(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database files", "*.db")], initialvalue=f"gym_backup_{timestamp}.db")
        if file_path:
            shutil.copy('gym.db', file_path)
            messagebox.showinfo("Success", f"Database backed up to {os.path.basename(file_path)}!")
    
    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = GymManagementSoftware(root)
    root.mainloop()