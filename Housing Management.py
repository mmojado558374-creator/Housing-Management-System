"""
Vanguard Housing Management System
Built with Python tkinter (GUI) + MySQL/MariaDB database
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk  # <-- Gidugang para sa Logo
import os
from datetime import date
import mysql.connector
from mysql.connector import Error as DB_ERROR
from mysql.connector import IntegrityError as DB_INTEGRITY_ERROR

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "housing_management_system",
    "port": 3306,
}

class MySQLCursorAdapter:
    def __init__(self, cursor):
        self.cursor = cursor

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    def execute(self, sql, params=None):
        self.cursor.execute(self._convert_sql(sql), params or ())
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def _convert_sql(self, sql):
        return sql.replace("?", "%s")

class MySQLConnectionAdapter:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return MySQLCursorAdapter(self.conn.cursor())

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    conn.cmd_query("SET SESSION sql_mode = CONCAT(@@sql_mode, ',PIPES_AS_CONCAT')")
    return MySQLConnectionAdapter(conn)

def init_db():
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"]
    )
    c = conn.cursor()
    c.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    conn.commit()
    conn.close()

    conn = get_connection()
    c = conn.cursor()

    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS landlords (
            landlord_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            phone VARCHAR(50) NOT NULL,
            address TEXT,
            date_registered DATE DEFAULT (CURRENT_DATE)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS properties (
            property_id INT AUTO_INCREMENT PRIMARY KEY,
            landlord_id INT NOT NULL,
            property_address TEXT NOT NULL,
            square_feet INT,
            rent_amount DECIMAL(10,2) NOT NULL CHECK(rent_amount > 0),
            security_deposit DECIMAL(10,2) NOT NULL CHECK(security_deposit >= 0),
            date_added DATE DEFAULT (CURRENT_DATE),
            FOREIGN KEY (landlord_id) REFERENCES landlords(landlord_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS properties_description (
            prop_description_id INT AUTO_INCREMENT PRIMARY KEY,
            property_id INT NOT NULL,
            property_type ENUM('house','apartment','condo','townhouse') NOT NULL,
            bedrooms INT NOT NULL CHECK(bedrooms >= 0),
            bathrooms INT NOT NULL CHECK(bathrooms >= 0),
            property_status ENUM('available','occupied','under_maintenance') NOT NULL DEFAULT 'available',
            FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            phone VARCHAR(50) NOT NULL,
            date_of_birth DATE NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tenants_description (
            tenant_description_id INT AUTO_INCREMENT PRIMARY KEY,
            tenant_id INT NOT NULL,
            employment_status TEXT,
            emergency_contact_name VARCHAR(150),
            emergency_contact_phone VARCHAR(50),
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS leases (
            lease_id INT AUTO_INCREMENT PRIMARY KEY,
            property_id INT NOT NULL,
            tenant_id INT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            monthly_rent DECIMAL(10,2) NOT NULL CHECK(monthly_rent > 0),
            security_deposit DECIMAL(10,2) NOT NULL CHECK(security_deposit >= 0),
            lease_status ENUM('active','expired','terminated') NOT NULL DEFAULT 'active',
            date_created DATE DEFAULT (CURRENT_DATE),
            FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
            CHECK(end_date > start_date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            lease_id INT NOT NULL,
            payment_amount DECIMAL(10,2) NOT NULL CHECK(payment_amount > 0),
            payment_date DATE NOT NULL,
            notes TEXT,
            date_recorded DATE DEFAULT (CURRENT_DATE),
            FOREIGN KEY (lease_id) REFERENCES leases(lease_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payment_description (
            pay_description_id INT AUTO_INCREMENT PRIMARY KEY,
            payment_id INT NOT NULL,
            payment_method ENUM('cash','check','bank_transfer','credit_card','online') NOT NULL,
            payment_type ENUM('rent','security_deposit','late_fee','utilities') NOT NULL DEFAULT 'rent',
            payment_status ENUM('paid','pending','failed') NOT NULL DEFAULT 'paid',
            FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS maintenance_request (
            request_id INT AUTO_INCREMENT PRIMARY KEY,
            property_id INT NOT NULL,
            tenant_id INT NOT NULL,
            request_title VARCHAR(200) NOT NULL,
            description TEXT,
            date_requested DATE DEFAULT (CURRENT_DATE),
            date_completed DATE,
            FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS maintenance_request_description (
            request_description_id INT AUTO_INCREMENT PRIMARY KEY,
            request_id INT NOT NULL,
            priority ENUM('low','medium','high','emergency') NOT NULL DEFAULT 'medium',
            request_status ENUM('open','in_progress','completed','cancelled') NOT NULL DEFAULT 'open',
            estimated_cost DECIMAL(10,2) CHECK(estimated_cost >= 0),
            actual_cost DECIMAL(10,2) CHECK(actual_cost >= 0),
            FOREIGN KEY (request_id) REFERENCES maintenance_request(request_id) ON DELETE CASCADE
        )
        """
    ]

    for statement in statements:
        c.execute(statement)

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin123')")

    conn.commit()
    conn.close()

COLORS = {
    "bg": "#F8F8F8",
    "sidebar": "#1E2A3A",
    "sidebar_active": "#2C3E55",
    "sidebar_text": "#BDC3C7",
    "sidebar_text_active": "#FFFFFF",
    "primary": "#185FA5",
    "primary_hover": "#0C447C",
    "white": "#FFFFFF",
    "border": "#E0E0E0",
    "header_bg":"#FFFFFF",
    "text": "#1A1A1A",
    "text_muted":"#6B7280",
    "green_bg": "#EAF3DE",
    "green_fg": "#3B6D11",
    "amber_bg": "#FAEEDA",
    "amber_fg": "#854F0B",
    "red_bg": "#FCEBEB",
    "red_fg": "#A32D2D",
    "blue_bg": "#E6F1FB",
    "blue_fg": "#185FA5",
}

def make_button(parent, text, command, primary=False, danger=False, small=False):
    size = 9 if small else 10
    if primary:
        btn = tk.Button(parent, text=text, command=command,
                        font=("Segoe UI", size, "bold"),
                        bg=COLORS["primary"], fg="white",
                        activebackground=COLORS["primary_hover"],
                        activeforeground="white",
                        relief="flat", padx=10, pady=4, cursor="hand2", bd=0)
    elif danger:
        btn = tk.Button(parent, text=text, command=command,
                        font=("Segoe UI", size),
                        bg=COLORS["red_fg"], fg="white",
                        activebackground="#7B1F1F",
                        activeforeground="white",
                        relief="flat", padx=8, pady=3, cursor="hand2", bd=0)
    else:
        btn = tk.Button(parent, text=text, command=command,
                        font=("Segoe UI", size),
                        bg=COLORS["white"], fg=COLORS["text"],
                        activebackground=COLORS["bg"],
                        relief="solid", padx=8, pady=3,
                        cursor="hand2", bd=1, highlightthickness=0)
    return btn

def styled_entry(parent, width=30, **kwargs):
    e = tk.Entry(parent, width=width, font=("Segoe UI", 10),
                 relief="solid", bd=1, highlightthickness=1,
                 highlightcolor=COLORS["primary"],
                 highlightbackground=COLORS["border"], **kwargs)
    return e

def styled_combo(parent, values, width=28):
    cb = ttk.Combobox(parent, values=values, width=width,
                      font=("Segoe UI", 10), state="readonly")
    return cb

def scrolled_tree(parent, columns, headings, col_widths=None, height=16):
    frame = tk.Frame(parent, bg=COLORS["white"], bd=1, relief="solid")
    frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    style = ttk.Style()
    style.configure("HMS.Treeview", background=COLORS["white"], foreground=COLORS["text"], rowheight=28, fieldbackground=COLORS["white"], font=("Segoe UI", 10))
    style.configure("HMS.Treeview.Heading", background=COLORS["bg"], foreground=COLORS["text_muted"], font=("Segoe UI", 9, "bold"), relief="flat")
    style.map("HMS.Treeview", background=[("selected", COLORS["blue_bg"])], foreground=[("selected", COLORS["blue_fg"])])

    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height, style="HMS.Treeview")

    for i, (col, heading) in enumerate(zip(columns, headings)):
        w = col_widths[i] if col_widths else 120
        tree.heading(col, text=heading, command=lambda c=col, t=tree: sort_tree(t, c, False))
        tree.column(col, width=w, anchor="w", stretch=True)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    tree.tag_configure("oddrow", background="#FAFAFA")
    tree.tag_configure("evenrow", background=COLORS["white"])
    return tree

def sort_tree(tree, col, reverse):
    data = [(tree.set(k, col), k) for k in tree.get_children("")]
    try:
        data.sort(key=lambda x: float(x[0].replace(",", "").replace("₱", "")), reverse=reverse)
    except ValueError:
        data.sort(reverse=reverse)
    for idx, (_, k) in enumerate(data):
        tree.move(k, "", idx)
    tree.heading(col, command=lambda: sort_tree(tree, col, not reverse))

def fmt_peso(amount):
    try:
        return f"₱{float(amount):,.2f}"
    except Exception:
        return str(amount)

class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title, width=460, height=500):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=COLORS["white"])
        self.grab_set()
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - width // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - height // 2
        self.geometry(f"{width}x{height}+{px}+{py}")

        hdr = tk.Frame(self, bg=COLORS["primary"], height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title, font=("Segoe UI", 11, "bold"), bg=COLORS["primary"], fg="white").pack(side="left", padx=16, pady=10)

        self.body = tk.Frame(self, bg=COLORS["white"])
        self.body.pack(fill="both", expand=True, padx=20, pady=16)
        self.result = None

    def add_field(self, label, widget, row, column=0):
        tk.Label(self.body, text=label, font=("Segoe UI", 9), fg=COLORS["text_muted"], bg=COLORS["white"], anchor="w").grid(row=row*2, column=column, sticky="w", padx=(0, 12), pady=(8, 2))
        widget.grid(row=row*2+1, column=column, sticky="ew", padx=(0, 12), pady=(0, 2))
        self.body.columnconfigure(column, weight=1)

    def add_buttons(self, save_cmd):
        btn_frame = tk.Frame(self, bg=COLORS["white"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))
        make_button(btn_frame, "Cancel", self.destroy).pack(side="right", padx=(4, 0))
        make_button(btn_frame, "Save", save_cmd, primary=True).pack(side="right")


# ---------------------------------------------------------
# Entity Dialogs
# ---------------------------------------------------------
class LandlordDialog(BaseDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent, "Add Landlord" if not record else "Edit Landlord", height=440)
        self.record = record
        fields = [("First name *", "fname"), ("Last name *", "lname"), ("Email *", "email"), ("Phone *", "phone"), ("Address", "address")]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            e = styled_entry(self.body, width=40)
            if record:
                vals = [record[1], record[2], record[3], record[4], record[5]]
                e.insert(0, vals[i] or "")
            self.add_field(label, e, i)
            self.entries[key] = e
        self.add_buttons(self.save)

    def save(self):
        fname, lname, email, phone, address = (self.entries[k].get().strip() for k in ["fname", "lname", "email", "phone", "address"])
        if not fname or not lname or not email or not phone:
            messagebox.showerror("Validation", "First name, last name, email and phone are required.", parent=self)
            return
        self.result = (fname, lname, email, phone, address)
        self.destroy()

class PropertyDialog(BaseDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent, "Add Property" if not record else "Edit Property", width=720, height=520)
        conn = get_connection()
        landlords = conn.execute("SELECT landlord_id, first_name||' '||last_name FROM landlords").fetchall()
        conn.close()
        self.landlord_map = {f"{name}": lid for lid, name in landlords}

        fields_data = {
            "address": ("Property address *", styled_entry(self.body, width=40)),
            "sqft":    ("Square feet",        styled_entry(self.body, width=40)),
            "rent":    ("Monthly rent (₱) *", styled_entry(self.body, width=40)),
            "deposit": ("Security deposit (₱) *", styled_entry(self.body, width=40)),
            "type":    ("Property type *",    styled_combo(self.body, ["house","apartment","condo","townhouse"])),
            "beds":    ("Bedrooms *",         styled_entry(self.body, width=40)),
            "baths":   ("Bathrooms *",        styled_entry(self.body, width=40)),
            "status":  ("Status",             styled_combo(self.body, ["available","occupied","under_maintenance"])),
            "landlord":("Landlord *",         styled_combo(self.body, list(self.landlord_map.keys()))),
        }
        self.widgets = {}
        for i, (key, (label, widget)) in enumerate(fields_data.items()):
            self.add_field(label, widget, i // 2, i % 2)
            self.widgets[key] = widget

        if record:
            for k, idx in zip(["address","sqft","rent","deposit","type","beds","baths","status"], [2,3,4,5,7,8,9,10]):
                if k in ["type","status"]: self.widgets[k].set(record[idx] or "")
                else: self.widgets[k].insert(0, record[idx] or "")
            for name, lid in self.landlord_map.items():
                if lid == record[1]: self.widgets["landlord"].set(name)
        else:
            self.widgets["type"].set("house")
            self.widgets["status"].set("available")
        self.add_buttons(self.save)

    def save(self):
        w = self.widgets
        addr, rent_str, dep_str, l_name, beds, baths, ptype, status, sqft = (
            w["address"].get().strip(), w["rent"].get().strip(), w["deposit"].get().strip(), w["landlord"].get(),
            w["beds"].get().strip(), w["baths"].get().strip(), w["type"].get(), w["status"].get(), w["sqft"].get().strip() or "0"
        )
        if not all([addr, rent_str, dep_str, l_name, beds, baths]):
            messagebox.showerror("Validation", "Required fields missing.", parent=self)
            return
        try:
            self.result = (self.landlord_map.get(l_name), addr, int(sqft), float(rent_str), float(dep_str), ptype, int(beds), int(baths), status)
            self.destroy()
        except ValueError:
            messagebox.showerror("Validation", "Numeric fields invalid.", parent=self)

class TenantDialog(BaseDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent, "Add Tenant" if not record else "Edit Tenant", height=580)
        fields = [("First name *", "fname"), ("Last name *", "lname"), ("Email *", "email"), ("Phone *", "phone"), ("Date of birth (YYYY-MM-DD) *", "dob"), ("Employment status", "employ"), ("Emergency contact name", "ec_name"), ("Emergency contact phone", "ec_phone")]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            e = styled_entry(self.body, width=40)
            if record and i < 8: e.insert(0, record[i+1] or "")
            self.add_field(label, e, i)
            self.entries[key] = e
        self.add_buttons(self.save)

    def save(self):
        vals = [self.entries[k].get().strip() for k in ["fname", "lname", "email", "phone", "dob", "employ", "ec_name", "ec_phone"]]
        if not all(vals[:5]):
            messagebox.showerror("Validation", "Name, email, phone, and dob required.", parent=self)
            return
        self.result = tuple(vals)
        self.destroy()

class LeaseDialog(BaseDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent, "Add Lease" if not record else "Edit Lease", height=580)
        conn = get_connection()
        self.tenant_map = {name: tid for tid, name in conn.execute("SELECT tenant_id, first_name||' '||last_name FROM tenants").fetchall()}
        self.prop_map = {addr: pid for pid, addr in conn.execute("SELECT property_id, property_address FROM properties").fetchall()}
        conn.close()

        fields_data = {
            "tenant":  ("Tenant *",                   styled_combo(self.body, list(self.tenant_map.keys()))),
            "prop":    ("Property *",                  styled_combo(self.body, list(self.prop_map.keys()))),
            "start":   ("Start date (YYYY-MM-DD) *",  styled_entry(self.body, width=40)),
            "end":     ("End date (YYYY-MM-DD) *",    styled_entry(self.body, width=40)),
            "rent":    ("Monthly rent (₱) *",         styled_entry(self.body, width=40)),
            "deposit": ("Security deposit (₱) *",     styled_entry(self.body, width=40)),
            "status":  ("Lease status",               styled_combo(self.body, ["active","expired","terminated"])),
        }
        self.widgets = {}
        for i, (key, (label, widget)) in enumerate(fields_data.items()):
            self.add_field(label, widget, i)
            self.widgets[key] = widget

        if record:
            for name, tid in self.tenant_map.items():
                if tid == record[2]: self.widgets["tenant"].set(name)
            for addr, pid in self.prop_map.items():
                if pid == record[1]: self.widgets["prop"].set(addr)
            for k, idx in zip(["start","end","rent","deposit","status"], [3,4,5,6,7]):
                if k == "status": self.widgets[k].set(record[idx] or "active")
                else: self.widgets[k].insert(0, record[idx] or "")
        else:
            self.widgets["status"].set("active")
        self.add_buttons(self.save)

    def save(self):
        w = self.widgets
        try:
            self.result = (self.prop_map.get(w["prop"].get()), self.tenant_map.get(w["tenant"].get()), w["start"].get().strip(), w["end"].get().strip(), float(w["rent"].get().strip()), float(w["deposit"].get().strip()), w["status"].get())
            self.destroy()
        except ValueError:
            messagebox.showerror("Validation", "Missing or invalid fields.", parent=self)

class PaymentDialog(BaseDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent, "Add Payment" if not record else "Edit Payment", height=520)
        conn = get_connection()
        self.lease_map = {desc: lid for lid, desc in conn.execute("SELECT l.lease_id, t.first_name||' '||t.last_name||' — '||p.property_address FROM leases l JOIN tenants t ON l.tenant_id=t.tenant_id JOIN properties p ON l.property_id=p.property_id").fetchall()}
        conn.close()

        fields_data = {
            "lease":   ("Lease *",                          styled_combo(self.body, list(self.lease_map.keys()))),
            "amount":  ("Amount (₱) *",                    styled_entry(self.body, width=40)),
            "date":    ("Payment date (YYYY-MM-DD) *",     styled_entry(self.body, width=40)),
            "method":  ("Payment method *",                styled_combo(self.body, ["cash","check","bank_transfer","credit_card","online"])),
            "type":    ("Payment type *",                  styled_combo(self.body, ["rent","security_deposit","late_fee","utilities"])),
            "status":  ("Payment status",                  styled_combo(self.body, ["paid","pending","failed"])),
            "notes":   ("Notes",                           styled_entry(self.body, width=40)),
        }
        self.widgets = {}
        for i, (key, (label, widget)) in enumerate(fields_data.items()):
            self.add_field(label, widget, i)
            self.widgets[key] = widget

        if record:
            # record: (payment_id, lease_id, amount, date, notes, method, type, status)
            for desc, lid in self.lease_map.items():
                if lid == record[1]:
                    self.widgets["lease"].set(desc)
            self.widgets["amount"].insert(0, record[2] or "")
            self.widgets["date"].insert(0, record[3] or "")
            self.widgets["notes"].insert(0, record[4] or "")
            self.widgets["method"].set(record[5] or "cash")
            self.widgets["type"].set(record[6] or "rent")
            self.widgets["status"].set(record[7] or "paid")
        else:
            self.widgets["method"].set("cash")
            self.widgets["type"].set("rent")
            self.widgets["status"].set("paid")

        self.add_buttons(self.save)

    def save(self):
        w = self.widgets
        lease_desc = w["lease"].get()
        amount_str = w["amount"].get().strip()
        pay_date   = w["date"].get().strip()
        method     = w["method"].get()
        ptype      = w["type"].get()
        status     = w["status"].get()
        notes      = w["notes"].get().strip()

        if not lease_desc or not amount_str or not pay_date or not method:
            messagebox.showerror("Validation", "Lease, amount, date, and method are required.", parent=self)
            return
        try:
            self.result = (
                self.lease_map.get(lease_desc),
                float(amount_str),
                pay_date,
                notes,
                method,
                ptype,
                status,
            )
            self.destroy()
        except ValueError:
            messagebox.showerror("Validation", "Amount must be a valid number.", parent=self)


class MaintenanceDialog(BaseDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent, "Add Maintenance Request" if not record else "Edit Maintenance Request", height=580)
        conn = get_connection()
        self.prop_map = {addr: pid for pid, addr in conn.execute("SELECT property_id, property_address FROM properties").fetchall()}
        self.tenant_map = {name: tid for tid, name in conn.execute("SELECT tenant_id, first_name||' '||last_name FROM tenants").fetchall()}
        conn.close()

        fields_data = {
            "prop":     ("Property *",               styled_combo(self.body, list(self.prop_map.keys()))),
            "tenant":   ("Tenant *",                 styled_combo(self.body, list(self.tenant_map.keys()))),
            "title":    ("Request title *",          styled_entry(self.body, width=40)),
            "desc":     ("Description",              styled_entry(self.body, width=40)),
            "priority": ("Priority",                 styled_combo(self.body, ["low","medium","high","emergency"])),
            "status":   ("Status",                   styled_combo(self.body, ["open","in_progress","completed","cancelled"])),
            "est_cost": ("Estimated cost (₱)",      styled_entry(self.body, width=40)),
            "act_cost": ("Actual cost (₱)",         styled_entry(self.body, width=40)),
        }
        self.widgets = {}
        for i, (key, (label, widget)) in enumerate(fields_data.items()):
            self.add_field(label, widget, i)
            self.widgets[key] = widget

        if record:
            for addr, pid in self.prop_map.items():
                if pid == record[1]: self.widgets["prop"].set(addr)
            for name, tid in self.tenant_map.items():
                if tid == record[2]: self.widgets["tenant"].set(name)
            self.widgets["title"].insert(0, record[3] or "")
            self.widgets["desc"].insert(0, record[4] or "")
            self.widgets["priority"].set(record[7] or "medium")
            self.widgets["status"].set(record[8] or "open")
            self.widgets["est_cost"].insert(0, record[9] or "")
            self.widgets["act_cost"].insert(0, record[10] or "")
        else:
            self.widgets["priority"].set("medium")
            self.widgets["status"].set("open")

        self.add_buttons(self.save)

    def save(self):
        w = self.widgets
        prop    = w["prop"].get()
        tenant  = w["tenant"].get()
        title   = w["title"].get().strip()
        desc    = w["desc"].get().strip()
        priority = w["priority"].get()
        status  = w["status"].get()
        est_str = w["est_cost"].get().strip() or "0"
        act_str = w["act_cost"].get().strip() or "0"

        if not prop or not tenant or not title:
            messagebox.showerror("Validation", "Property, tenant, and title are required.", parent=self)
            return
        try:
            self.result = (
                self.prop_map.get(prop),
                self.tenant_map.get(tenant),
                title,
                desc,
                priority,
                status,
                float(est_str),
                float(act_str),
            )
            self.destroy()
        except ValueError:
            messagebox.showerror("Validation", "Cost fields must be valid numbers.", parent=self)


# ---------------------------------------------------------
# Tab Panels
# ---------------------------------------------------------
class BasePanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])

    def make_header(self, title, subtitle, add_cmd):
        hdr = tk.Frame(self, bg=COLORS["header_bg"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        inner = tk.Frame(hdr, bg=COLORS["header_bg"])
        inner.pack(fill="both", expand=True, padx=20, pady=10)
        tk.Label(inner, text=title, font=("Segoe UI", 14, "bold"), bg=COLORS["header_bg"], fg=COLORS["text"]).pack(side="left")
        tk.Label(inner, text=subtitle, font=("Segoe UI", 9), bg=COLORS["header_bg"], fg=COLORS["text_muted"]).pack(side="left", padx=(10, 0), pady=(4, 0))
        make_button(inner, f"+ Add {title}", add_cmd, primary=True).pack(side="right")

    def make_search(self, var, cmd):
        sf = tk.Frame(self, bg=COLORS["bg"])
        sf.pack(fill="x", padx=16, pady=(12, 8))
        tk.Label(sf, text="🔍", bg=COLORS["bg"], font=("Segoe UI", 11)).pack(side="left")
        e = styled_entry(sf, width=40, textvariable=var)
        e.pack(side="left", padx=6)
        e.bind("<KeyRelease>", lambda _: cmd())
        return e


class LandlordPanel(BasePanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.search_var = tk.StringVar()
        self.make_header("Landlords", "Manage property owners", self.add)
        self.make_search(self.search_var, self.load)
        cols = ("id","fname","lname","email","phone","address","registered")
        heads = ("ID","First Name","Last Name","Email","Phone","Address","Registered")
        widths = [40,100,100,160,100,180,100]
        self.tree = scrolled_tree(self, cols, heads, widths)
        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.pack(fill="x", padx=16, pady=(0,12))
        make_button(bf, "✏ Edit", self.edit).pack(side="left", padx=(0,6))
        make_button(bf, "🗑 Delete", self.delete, danger=True).pack(side="left")
        self.load()

    def load(self):
        q = self.search_var.get().strip()
        conn = get_connection()
        rows = conn.execute("SELECT * FROM landlords" + (" WHERE first_name LIKE %s OR last_name LIKE %s OR email LIKE %s" if q else ""),
                            (f"%{q}%", f"%{q}%", f"%{q}%") if q else None).fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=r, tags=(tag,))

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a record first.")
            return None
        return self.tree.item(sel[0])["values"]

    def add(self):
        d = LandlordDialog(self)
        self.wait_window(d)
        if d.result:
            conn = get_connection()
            conn.execute("INSERT INTO landlords (first_name,last_name,email,phone,address) VALUES (%s,%s,%s,%s,%s)", d.result)
            conn.commit(); conn.close(); self.load()

    def edit(self):
        rec = self.selected()
        if not rec: return
        d = LandlordDialog(self, rec)
        self.wait_window(d)
        if d.result:
            conn = get_connection()
            conn.execute("UPDATE landlords SET first_name=%s,last_name=%s,email=%s,phone=%s,address=%s WHERE landlord_id=%s", (*d.result, rec[0]))
            conn.commit(); conn.close(); self.load()

    def delete(self):
        rec = self.selected()
        if not rec: return
        if messagebox.askyesno("Delete", f"Delete landlord '{rec[1]} {rec[2]}'?"):
            conn = get_connection()
            conn.execute("DELETE FROM landlords WHERE landlord_id=%s", (rec[0],))
            conn.commit(); conn.close(); self.load()


class PropertyPanel(BasePanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.search_var = tk.StringVar()
        self.make_header("Properties", "Manage rental properties", self.add)
        self.make_search(self.search_var, self.load)
        cols = ("id","landlord","address","sqft","rent","deposit","added","type","beds","baths","status")
        heads = ("ID","Landlord","Address","Sqft","Rent","Deposit","Added","Type","Beds","Baths","Status")
        widths = [40,130,180,60,90,90,90,90,50,50,100]
        self.tree = scrolled_tree(self, cols, heads, widths)
        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.pack(fill="x", padx=16, pady=(0,12))
        make_button(bf, "✏ Edit", self.edit).pack(side="left", padx=(0,6))
        make_button(bf, "🗑 Delete", self.delete, danger=True).pack(side="left")
        self.load()

    def load(self):
        q = self.search_var.get().strip()
        conn = get_connection()
        sql = """SELECT p.property_id, l.first_name||' '||l.last_name, p.property_address,
                        p.square_feet, p.rent_amount, p.security_deposit, p.date_added,
                        pd.property_type, pd.bedrooms, pd.bathrooms, pd.property_status
                 FROM properties p
                 JOIN landlords l ON p.landlord_id=l.landlord_id
                 LEFT JOIN properties_description pd ON p.property_id=pd.property_id"""
        rows = conn.execute(sql + (" WHERE p.property_address LIKE %s OR l.first_name LIKE %s OR l.last_name LIKE %s" if q else ""),
                            (f"%{q}%", f"%{q}%", f"%{q}%") if q else None).fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            vals = list(r)
            vals[4] = fmt_peso(r[4]); vals[5] = fmt_peso(r[5])
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a record first.")
            return None
        return self.tree.item(sel[0])["values"]

    def add(self):
        d = PropertyDialog(self)
        self.wait_window(d)
        if d.result:
            lid, addr, sqft, rent, dep, ptype, beds, baths, status = d.result
            conn = get_connection()
            cur = conn.execute("INSERT INTO properties (landlord_id,property_address,square_feet,rent_amount,security_deposit) VALUES (%s,%s,%s,%s,%s)",
                               (lid, addr, sqft, rent, dep))
            pid = cur.lastrowid
            conn.execute("INSERT INTO properties_description (property_id,property_type,bedrooms,bathrooms,property_status) VALUES (%s,%s,%s,%s,%s)",
                         (pid, ptype, beds, baths, status))
            conn.commit(); conn.close(); self.load()

    def edit(self):
        rec = self.selected()
        if not rec: return
        conn = get_connection()
        full = conn.execute("""SELECT p.property_id, p.landlord_id, p.property_address, p.square_feet,
                                      p.rent_amount, p.security_deposit, p.date_added,
                                      pd.property_type, pd.bedrooms, pd.bathrooms, pd.property_status
                               FROM properties p
                               LEFT JOIN properties_description pd ON p.property_id=pd.property_id
                               WHERE p.property_id=%s""", (rec[0],)).fetchone()
        conn.close()
        d = PropertyDialog(self, full)
        self.wait_window(d)
        if d.result:
            lid, addr, sqft, rent, dep, ptype, beds, baths, status = d.result
            conn = get_connection()
            conn.execute("UPDATE properties SET landlord_id=%s,property_address=%s,square_feet=%s,rent_amount=%s,security_deposit=%s WHERE property_id=%s",
                         (lid, addr, sqft, rent, dep, rec[0]))
            conn.execute("UPDATE properties_description SET property_type=%s,bedrooms=%s,bathrooms=%s,property_status=%s WHERE property_id=%s",
                         (ptype, beds, baths, status, rec[0]))
            conn.commit(); conn.close(); self.load()

    def delete(self):
        rec = self.selected()
        if not rec: return
        if messagebox.askyesno("Delete", f"Delete property '{rec[2]}'?"):
            conn = get_connection()
            conn.execute("DELETE FROM properties WHERE property_id=%s", (rec[0],))
            conn.commit(); conn.close(); self.load()


class TenantPanel(BasePanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.search_var = tk.StringVar()
        self.make_header("Tenants", "Manage tenants", self.add)
        self.make_search(self.search_var, self.load)
        cols = ("id","fname","lname","email","phone","dob","employ","ec_name","ec_phone")
        heads = ("ID","First","Last","Email","Phone","DOB","Employment","EC Name","EC Phone")
        widths = [40,100,100,160,100,100,120,130,100]
        self.tree = scrolled_tree(self, cols, heads, widths)
        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.pack(fill="x", padx=16, pady=(0,12))
        make_button(bf, "✏ Edit", self.edit).pack(side="left", padx=(0,6))
        make_button(bf, "🗑 Delete", self.delete, danger=True).pack(side="left")
        self.load()

    def load(self):
        q = self.search_var.get().strip()
        conn = get_connection()
        sql = """SELECT t.tenant_id, t.first_name, t.last_name, t.email, t.phone, t.date_of_birth,
                        td.employment_status, td.emergency_contact_name, td.emergency_contact_phone
                 FROM tenants t LEFT JOIN tenants_description td ON t.tenant_id=td.tenant_id"""
        rows = conn.execute(sql + (" WHERE t.first_name LIKE %s OR t.last_name LIKE %s OR t.email LIKE %s" if q else ""),
                            (f"%{q}%", f"%{q}%", f"%{q}%") if q else None).fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=r, tags=(tag,))

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a record first.")
            return None
        return self.tree.item(sel[0])["values"]

    def add(self):
        d = TenantDialog(self)
        self.wait_window(d)
        if d.result:
            fname, lname, email, phone, dob, employ, ec_name, ec_phone = d.result
            conn = get_connection()
            cur = conn.execute("INSERT INTO tenants (first_name,last_name,email,phone,date_of_birth) VALUES (%s,%s,%s,%s,%s)",
                               (fname, lname, email, phone, dob))
            tid = cur.lastrowid
            conn.execute("INSERT INTO tenants_description (tenant_id,employment_status,emergency_contact_name,emergency_contact_phone) VALUES (%s,%s,%s,%s)",
                         (tid, employ, ec_name, ec_phone))
            conn.commit(); conn.close(); self.load()

    def edit(self):
        rec = self.selected()
        if not rec: return
        d = TenantDialog(self, rec)
        self.wait_window(d)
        if d.result:
            fname, lname, email, phone, dob, employ, ec_name, ec_phone = d.result
            conn = get_connection()
            conn.execute("UPDATE tenants SET first_name=%s,last_name=%s,email=%s,phone=%s,date_of_birth=%s WHERE tenant_id=%s",
                         (fname, lname, email, phone, dob, rec[0]))
            conn.execute("UPDATE tenants_description SET employment_status=%s,emergency_contact_name=%s,emergency_contact_phone=%s WHERE tenant_id=%s",
                         (employ, ec_name, ec_phone, rec[0]))
            conn.commit(); conn.close(); self.load()

    def delete(self):
        rec = self.selected()
        if not rec: return
        if messagebox.askyesno("Delete", f"Delete tenant '{rec[1]} {rec[2]}'?"):
            conn = get_connection()
            conn.execute("DELETE FROM tenants WHERE tenant_id=%s", (rec[0],))
            conn.commit(); conn.close(); self.load()


class LeasePanel(BasePanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.search_var = tk.StringVar()
        self.make_header("Leases", "Manage lease agreements", self.add)
        self.make_search(self.search_var, self.load)
        cols = ("id","property","tenant","start","end","rent","deposit","status","created")
        heads = ("ID","Property","Tenant","Start","End","Rent","Deposit","Status","Created")
        widths = [40,180,140,100,100,90,90,90,90]
        self.tree = scrolled_tree(self, cols, heads, widths)
        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.pack(fill="x", padx=16, pady=(0,12))
        make_button(bf, "✏ Edit", self.edit).pack(side="left", padx=(0,6))
        make_button(bf, "🗑 Delete", self.delete, danger=True).pack(side="left")
        self.load()

    def load(self):
        q = self.search_var.get().strip()
        conn = get_connection()
        sql = """SELECT l.lease_id, p.property_address, t.first_name||' '||t.last_name,
                        l.start_date, l.end_date, l.monthly_rent, l.security_deposit,
                        l.lease_status, l.date_created
                 FROM leases l
                 JOIN properties p ON l.property_id=p.property_id
                 JOIN tenants t ON l.tenant_id=t.tenant_id"""
        rows = conn.execute(sql + (" WHERE p.property_address LIKE %s OR t.first_name LIKE %s OR t.last_name LIKE %s" if q else ""),
                            (f"%{q}%", f"%{q}%", f"%{q}%") if q else None).fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            vals = list(r)
            vals[5] = fmt_peso(r[5]); vals[6] = fmt_peso(r[6])
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a record first.")
            return None
        return self.tree.item(sel[0])["values"]

    def add(self):
        d = LeaseDialog(self)
        self.wait_window(d)
        if d.result:
            pid, tid, start, end, rent, dep, status = d.result
            conn = get_connection()
            conn.execute("INSERT INTO leases (property_id,tenant_id,start_date,end_date,monthly_rent,security_deposit,lease_status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                         (pid, tid, start, end, rent, dep, status))
            conn.commit(); conn.close(); self.load()

    def edit(self):
        rec = self.selected()
        if not rec: return
        conn = get_connection()
        full = conn.execute("SELECT * FROM leases WHERE lease_id=%s", (rec[0],)).fetchone()
        conn.close()
        d = LeaseDialog(self, full)
        self.wait_window(d)
        if d.result:
            pid, tid, start, end, rent, dep, status = d.result
            conn = get_connection()
            conn.execute("UPDATE leases SET property_id=%s,tenant_id=%s,start_date=%s,end_date=%s,monthly_rent=%s,security_deposit=%s,lease_status=%s WHERE lease_id=%s",
                         (pid, tid, start, end, rent, dep, status, rec[0]))
            conn.commit(); conn.close(); self.load()

    def delete(self):
        rec = self.selected()
        if not rec: return
        if messagebox.askyesno("Delete", f"Delete lease #{rec[0]}?"):
            conn = get_connection()
            conn.execute("DELETE FROM leases WHERE lease_id=%s", (rec[0],))
            conn.commit(); conn.close(); self.load()


class PaymentPanel(BasePanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.search_var = tk.StringVar()
        self.make_header("Payments", "Track rent and other payments", self.add)
        self.make_search(self.search_var, self.load)
        cols = ("id","lease","amount","date","method","type","status","notes","recorded")
        heads = ("ID","Lease","Amount","Date","Method","Type","Status","Notes","Recorded")
        widths = [40,200,90,100,110,110,80,160,100]
        self.tree = scrolled_tree(self, cols, heads, widths)
        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.pack(fill="x", padx=16, pady=(0,12))
        make_button(bf, "✏ Edit", self.edit).pack(side="left", padx=(0,6))
        make_button(bf, "🗑 Delete", self.delete, danger=True).pack(side="left")
        self.load()

    def load(self):
        q = self.search_var.get().strip()
        conn = get_connection()
        sql = """SELECT py.payment_id,
                        t.first_name||' '||t.last_name||' — '||p.property_address,
                        py.payment_amount, py.payment_date,
                        pd.payment_method, pd.payment_type, pd.payment_status,
                        py.notes, py.date_recorded
                 FROM payments py
                 JOIN leases l ON py.lease_id=l.lease_id
                 JOIN tenants t ON l.tenant_id=t.tenant_id
                 JOIN properties p ON l.property_id=p.property_id
                 LEFT JOIN payment_description pd ON py.payment_id=pd.payment_id"""
        rows = conn.execute(sql + (" WHERE t.first_name LIKE %s OR t.last_name LIKE %s OR p.property_address LIKE %s" if q else ""),
                            (f"%{q}%", f"%{q}%", f"%{q}%") if q else None).fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            vals = list(r)
            vals[2] = fmt_peso(r[2])
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a record first.")
            return None
        return self.tree.item(sel[0])["values"]

    def add(self):
        d = PaymentDialog(self)
        self.wait_window(d)
        if d.result:
            lid, amount, pay_date, notes, method, ptype, status = d.result
            conn = get_connection()
            cur = conn.execute("INSERT INTO payments (lease_id,payment_amount,payment_date,notes) VALUES (%s,%s,%s,%s)",
                               (lid, amount, pay_date, notes))
            pay_id = cur.lastrowid
            conn.execute("INSERT INTO payment_description (payment_id,payment_method,payment_type,payment_status) VALUES (%s,%s,%s,%s)",
                         (pay_id, method, ptype, status))
            conn.commit(); conn.close(); self.load()

    def edit(self):
        rec = self.selected()
        if not rec: return
        conn = get_connection()
        full = conn.execute("""SELECT py.payment_id, py.lease_id, py.payment_amount, py.payment_date,
                                      py.notes, pd.payment_method, pd.payment_type, pd.payment_status
                               FROM payments py
                               LEFT JOIN payment_description pd ON py.payment_id=pd.payment_id
                               WHERE py.payment_id=%s""", (rec[0],)).fetchone()
        conn.close()
        d = PaymentDialog(self, full)
        self.wait_window(d)
        if d.result:
            lid, amount, pay_date, notes, method, ptype, status = d.result
            conn = get_connection()
            conn.execute("UPDATE payments SET lease_id=%s,payment_amount=%s,payment_date=%s,notes=%s WHERE payment_id=%s",
                         (lid, amount, pay_date, notes, rec[0]))
            conn.execute("UPDATE payment_description SET payment_method=%s,payment_type=%s,payment_status=%s WHERE payment_id=%s",
                         (method, ptype, status, rec[0]))
            conn.commit(); conn.close(); self.load()

    def delete(self):
        rec = self.selected()
        if not rec: return
        if messagebox.askyesno("Delete", f"Delete payment #{rec[0]}?"):
            conn = get_connection()
            conn.execute("DELETE FROM payments WHERE payment_id=%s", (rec[0],))
            conn.commit(); conn.close(); self.load()


class MaintenancePanel(BasePanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.search_var = tk.StringVar()
        self.make_header("Maintenance", "Track maintenance requests", self.add)
        self.make_search(self.search_var, self.load)
        cols = ("id","property","tenant","title","desc","requested","completed","priority","status","est","actual")
        heads = ("ID","Property","Tenant","Title","Description","Requested","Completed","Priority","Status","Est. Cost","Actual Cost")
        widths = [40,160,120,160,180,100,100,80,90,90,90]
        self.tree = scrolled_tree(self, cols, heads, widths)
        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.pack(fill="x", padx=16, pady=(0,12))
        make_button(bf, "✏ Edit", self.edit).pack(side="left", padx=(0,6))
        make_button(bf, "🗑 Delete", self.delete, danger=True).pack(side="left")
        self.load()

    def load(self):
        q = self.search_var.get().strip()
        conn = get_connection()
        sql = """SELECT mr.request_id, p.property_address, t.first_name||' '||t.last_name,
                        mr.request_title, mr.description, mr.date_requested, mr.date_completed,
                        mrd.priority, mrd.request_status, mrd.estimated_cost, mrd.actual_cost
                 FROM maintenance_request mr
                 JOIN properties p ON mr.property_id=p.property_id
                 JOIN tenants t ON mr.tenant_id=t.tenant_id
                 LEFT JOIN maintenance_request_description mrd ON mr.request_id=mrd.request_id"""
        rows = conn.execute(sql + (" WHERE p.property_address LIKE %s OR t.first_name LIKE %s OR mr.request_title LIKE %s" if q else ""),
                            (f"%{q}%", f"%{q}%", f"%{q}%") if q else None).fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            vals = list(r)
            vals[9]  = fmt_peso(r[9])  if r[9]  else "—"
            vals[10] = fmt_peso(r[10]) if r[10] else "—"
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a record first.")
            return None
        return self.tree.item(sel[0])["values"]

    def add(self):
        d = MaintenanceDialog(self)
        self.wait_window(d)
        if d.result:
            pid, tid, title, desc, priority, status, est, act = d.result
            conn = get_connection()
            cur = conn.execute("INSERT INTO maintenance_request (property_id,tenant_id,request_title,description) VALUES (%s,%s,%s,%s)",
                               (pid, tid, title, desc))
            rid = cur.lastrowid
            conn.execute("INSERT INTO maintenance_request_description (request_id,priority,request_status,estimated_cost,actual_cost) VALUES (%s,%s,%s,%s,%s)",
                         (rid, priority, status, est, act))
            conn.commit(); conn.close(); self.load()

    def edit(self):
        rec = self.selected()
        if not rec: return
        conn = get_connection()
        full = conn.execute("""SELECT mr.request_id, mr.property_id, mr.tenant_id,
                                      mr.request_title, mr.description, mr.date_requested, mr.date_completed,
                                      mrd.priority, mrd.request_status, mrd.estimated_cost, mrd.actual_cost
                               FROM maintenance_request mr
                               LEFT JOIN maintenance_request_description mrd ON mr.request_id=mrd.request_id
                               WHERE mr.request_id=%s""", (rec[0],)).fetchone()
        conn.close()
        d = MaintenanceDialog(self, full)
        self.wait_window(d)
        if d.result:
            pid, tid, title, desc, priority, status, est, act = d.result
            conn = get_connection()
            conn.execute("UPDATE maintenance_request SET property_id=%s,tenant_id=%s,request_title=%s,description=%s WHERE request_id=%s",
                         (pid, tid, title, desc, rec[0]))
            conn.execute("UPDATE maintenance_request_description SET priority=%s,request_status=%s,estimated_cost=%s,actual_cost=%s WHERE request_id=%s",
                         (priority, status, est, act, rec[0]))
            conn.commit(); conn.close(); self.load()

    def delete(self):
        rec = self.selected()
        if not rec: return
        if messagebox.askyesno("Delete", f"Delete request '{rec[3]}'?"):
            conn = get_connection()
            conn.execute("DELETE FROM maintenance_request WHERE request_id=%s", (rec[0],))
            conn.commit(); conn.close(); self.load()


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
class DashboardPanel(BasePanel):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Label(self, text="Dashboard", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 4))
        tk.Label(self, text="Overview of your housing management system",
                 font=("Segoe UI", 9), bg=COLORS["bg"], fg=COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 16))
        self.cards_frame = tk.Frame(self, bg=COLORS["bg"])
        self.cards_frame.pack(fill="x", padx=16)
        self.load()

    def load(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        conn = get_connection()
        stats = {
            "Landlords":   conn.execute("SELECT COUNT(*) FROM landlords").fetchone()[0],
            "Properties":  conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0],
            "Tenants":     conn.execute("SELECT COUNT(*) FROM tenants").fetchone()[0],
            "Active Leases": conn.execute("SELECT COUNT(*) FROM leases WHERE lease_status='active'").fetchone()[0],
            "Payments":    conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0],
            "Open Requests": conn.execute("SELECT COUNT(*) FROM maintenance_request_description WHERE request_status='open'").fetchone()[0],
        }
        total_rent = conn.execute("SELECT SUM(payment_amount) FROM payments").fetchone()[0] or 0
        conn.close()

        icons = {"Landlords":"👤","Properties":"🏠","Tenants":"🧑","Active Leases":"📋","Payments":"💳","Open Requests":"🔧"}
        colors = [COLORS["blue_bg"], COLORS["green_bg"], COLORS["amber_bg"],
                  COLORS["blue_bg"], COLORS["green_bg"], COLORS["red_bg"]]
        fgs    = [COLORS["blue_fg"], COLORS["green_fg"], COLORS["amber_fg"],
                  COLORS["blue_fg"], COLORS["green_fg"], COLORS["red_fg"]]

        for i, (label, val) in enumerate(stats.items()):
            card = tk.Frame(self.cards_frame, bg=colors[i], bd=0, relief="flat",
                            padx=16, pady=12, cursor="arrow")
            card.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="ew")
            self.cards_frame.columnconfigure(i%3, weight=1)
            tk.Label(card, text=icons[label], font=("Segoe UI", 22), bg=colors[i]).pack(anchor="w")
            tk.Label(card, text=str(val), font=("Segoe UI", 20, "bold"), bg=colors[i], fg=fgs[i]).pack(anchor="w")
            tk.Label(card, text=label, font=("Segoe UI", 9), bg=colors[i], fg=fgs[i]).pack(anchor="w")

        rev_frame = tk.Frame(self, bg=COLORS["white"], relief="solid", bd=1)
        rev_frame.pack(fill="x", padx=24, pady=(8, 0))
        tk.Label(rev_frame, text=f"💰  Total Revenue Collected:   {fmt_peso(total_rent)}",
                 font=("Segoe UI", 12, "bold"), bg=COLORS["white"], fg=COLORS["green_fg"],
                 pady=14).pack(anchor="w", padx=20)


# ---------------------------------------------------------
# Login Window
# ---------------------------------------------------------
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vanguard HMS — Login")
        self.resizable(False, False)
        self.configure(bg=COLORS["white"])
        w, h = 380, 340
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")

        tk.Frame(self, bg=COLORS["primary"], height=6).pack(fill="x")
        body = tk.Frame(self, bg=COLORS["white"])
        body.pack(fill="both", expand=True, padx=40, pady=30)

        tk.Label(body, text="🏠", font=("Segoe UI", 32), bg=COLORS["white"]).pack()
        tk.Label(body, text="Vanguard HMS", font=("Segoe UI", 14, "bold"), bg=COLORS["white"], fg=COLORS["text"]).pack()
        tk.Label(body, text="Housing Management System", font=("Segoe UI", 9), bg=COLORS["white"], fg=COLORS["text_muted"]).pack(pady=(0,20))

        tk.Label(body, text="Username", font=("Segoe UI", 9), bg=COLORS["white"], fg=COLORS["text_muted"], anchor="w").pack(fill="x")
        self.username = styled_entry(body, width=35)
        self.username.pack(fill="x", pady=(2,10))

        tk.Label(body, text="Password", font=("Segoe UI", 9), bg=COLORS["white"], fg=COLORS["text_muted"], anchor="w").pack(fill="x")
        self.password = styled_entry(body, width=35, show="•")
        self.password.pack(fill="x", pady=(2,16))

        make_button(body, "Login", self.login, primary=True).pack(fill="x", ipady=4)
        self.username.focus()
        self.bind("<Return>", lambda _: self.login())

    def login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p)).fetchone()
        conn.close()
        if row:
            self.destroy()
            MainApp().mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


# ---------------------------------------------------------
# Main Application
# ---------------------------------------------------------
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vanguard Housing Management System")
        self.state("zoomed")
        self.configure(bg=COLORS["bg"])
        self._build_ui()

    def _build_ui(self):
        # Sidebar
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🏠 Vanguard", font=("Segoe UI", 12, "bold"),
                 bg=COLORS["sidebar"], fg=COLORS["sidebar_text_active"], pady=20).pack(fill="x", padx=12)
        tk.Frame(sidebar, bg=COLORS["sidebar_active"], height=1).pack(fill="x")

        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        self.panels = {}
        nav_items = [
            ("📊 Dashboard",    "dashboard",    DashboardPanel),
            ("👤 Landlords",    "landlords",    LandlordPanel),
            ("🏠 Properties",   "properties",   PropertyPanel),
            ("🧑 Tenants",      "tenants",      TenantPanel),
            ("📋 Leases",       "leases",       LeasePanel),
            ("💳 Payments",     "payments",     PaymentPanel),
            ("🔧 Maintenance",  "maintenance",  MaintenancePanel),
        ]

        self.nav_buttons = {}
        for label, key, PanelClass in nav_items:
            panel = PanelClass(self.content)
            self.panels[key] = panel
            btn = tk.Button(sidebar, text=label, font=("Segoe UI", 10),
                            bg=COLORS["sidebar"], fg=COLORS["sidebar_text"],
                            activebackground=COLORS["sidebar_active"],
                            activeforeground=COLORS["sidebar_text_active"],
                            relief="flat", anchor="w", padx=16, pady=10,
                            cursor="hand2", bd=0,
                            command=lambda k=key: self.show(k))
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

        # Logout
        tk.Frame(sidebar, bg=COLORS["sidebar_active"], height=1).pack(fill="x", side="bottom", pady=4)
        tk.Button(sidebar, text="⎋ Logout", font=("Segoe UI", 10),
                  bg=COLORS["sidebar"], fg=COLORS["sidebar_text"],
                  activebackground=COLORS["red_bg"], activeforeground=COLORS["red_fg"],
                  relief="flat", anchor="w", padx=16, pady=10,
                  cursor="hand2", bd=0, command=self.logout).pack(fill="x", side="bottom")

        self.show("dashboard")

    def show(self, key):
        for k, p in self.panels.items():
            p.pack_forget()
            self.nav_buttons[k].configure(bg=COLORS["sidebar"], fg=COLORS["sidebar_text"])
        self.panels[key].pack(fill="both", expand=True)
        self.nav_buttons[key].configure(bg=COLORS["sidebar_active"], fg=COLORS["sidebar_text_active"])
        # Refresh dashboard on switch
        if key == "dashboard":
            self.panels[key].load()

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            LoginWindow().mainloop()


# ---------------------------------------------------------
# Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()