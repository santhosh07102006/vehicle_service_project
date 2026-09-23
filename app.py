from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import date
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(32)

# ── DB CONFIG ──────────────────────────────────────────────
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'vehicle_service_db')
}

# ── AUTO DATABASE SETUP ────────────────────────────────────
def init_db():
    """
    Automatically creates the database, all tables, and seeds
    default data on first run. Safe to call every startup —
    uses IF NOT EXISTS so nothing is overwritten.
    """
    # Connect WITHOUT selecting a database first
    base_cfg = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    try:
        conn = mysql.connector.connect(**base_cfg)
        cur  = conn.cursor()

        # 1. Create database
        cur.execute("CREATE DATABASE IF NOT EXISTS vehicle_service_db "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cur.execute("USE vehicle_service_db;")

        # 2. Create tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id  INT AUTO_INCREMENT PRIMARY KEY,
                name         VARCHAR(100) NOT NULL,
                phone        VARCHAR(15)  NOT NULL UNIQUE,
                email        VARCHAR(100),
                address      TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id   INT AUTO_INCREMENT PRIMARY KEY,
                customer_id  INT NOT NULL,
                reg_number   VARCHAR(20) NOT NULL UNIQUE,
                make         VARCHAR(50) NOT NULL,
                model        VARCHAR(50) NOT NULL,
                year         INT,
                vehicle_type ENUM('Car','Bike','Truck','Van','Other') DEFAULT 'Car',
                color        VARCHAR(30),
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS parts (
                part_id    INT AUTO_INCREMENT PRIMARY KEY,
                part_name  VARCHAR(100) NOT NULL,
                part_code  VARCHAR(50)  UNIQUE,
                category   VARCHAR(50),
                quantity   INT          DEFAULT 0,
                unit_price DECIMAL(10,2) NOT NULL,
                supplier   VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                           ON UPDATE CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS services (
                service_id   INT AUTO_INCREMENT PRIMARY KEY,
                service_name VARCHAR(100) NOT NULL,
                description  TEXT,
                base_price   DECIMAL(10,2) NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                bill_id        INT AUTO_INCREMENT PRIMARY KEY,
                vehicle_id     INT NOT NULL,
                customer_id    INT NOT NULL,
                bill_date      DATE NOT NULL,
                total_amount   DECIMAL(10,2) DEFAULT 0,
                payment_status ENUM('Pending','Paid') DEFAULT 'Pending',
                payment_method ENUM('Cash','Card','UPI','Other') DEFAULT 'Cash',
                notes          TEXT,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id)
                    REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bill_service_items (
                id                  INT AUTO_INCREMENT PRIMARY KEY,
                bill_id             INT NOT NULL,
                service_id          INT,
                custom_service_name VARCHAR(100),
                quantity            INT           DEFAULT 1,
                unit_price          DECIMAL(10,2) NOT NULL,
                subtotal            DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (bill_id)
                    REFERENCES bills(bill_id) ON DELETE CASCADE,
                FOREIGN KEY (service_id)
                    REFERENCES services(service_id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bill_part_items (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                bill_id          INT NOT NULL,
                part_id          INT,
                custom_part_name VARCHAR(100),
                quantity         INT           DEFAULT 1,
                unit_price       DECIMAL(10,2) NOT NULL,
                subtotal         DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (bill_id)
                    REFERENCES bills(bill_id) ON DELETE CASCADE,
                FOREIGN KEY (part_id)
                    REFERENCES parts(part_id) ON DELETE SET NULL
            );
        """)

        # 3. Seed default services (only if table is empty)
        cur.execute("SELECT COUNT(*) FROM services;")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO services (service_name, description, base_price) VALUES (%s, %s, %s);",
                [
                    ('Oil Change',            'Engine oil and filter replacement',              500.00),
                    ('Wheel Alignment',       'Four-wheel alignment check and adjustment',      800.00),
                    ('Brake Service',         'Brake pad inspection and replacement',          1200.00),
                    ('Battery Check & Replace','Battery voltage test and replacement if needed',2500.00),
                    ('AC Service',            'AC gas refill and cooling check',               1500.00),
                    ('General Checkup',       'Full vehicle inspection and diagnostics',        400.00),
                    ('Tyre Rotation',         'Rotate and balance all four tyres',              600.00),
                    ('Engine Tune-up',        'Spark plug, air filter, fuel filter service',   1800.00),
                ]
            )
            print("✔  Seeded default services.")

        # 4. Seed default parts (only if table is empty)
        cur.execute("SELECT COUNT(*) FROM parts;")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO parts (part_name, part_code, category, quantity, unit_price, supplier) "
                "VALUES (%s, %s, %s, %s, %s, %s);",
                [
                    ('Engine Oil (1L)',   'OIL-001', 'Lubricants', 50,  350.00, 'Castrol India'),
                    ('Oil Filter',        'FIL-001', 'Filters',    30,  150.00, 'Bosch India'),
                    ('Air Filter',        'FIL-002', 'Filters',    25,  200.00, 'Bosch India'),
                    ('Brake Pads (Set)',  'BRK-001', 'Brakes',     20,  800.00, 'Brembo India'),
                    ('Wiper Blade',       'WIP-001', 'Accessories',40,  250.00, 'Local Supplier'),
                    ('Spark Plug',        'SPK-001', 'Ignition',   60,  180.00, 'NGK India'),
                    ('Coolant (1L)',      'COL-001', 'Fluids',     35,  220.00, 'Prestone India'),
                    ('Brake Fluid (500ml)','BRF-001','Fluids',     28,  190.00, 'Bosch India'),
                    ('Clutch Plate',      'CLT-001', 'Transmission',15,1200.00, 'LuK India'),
                    ('Headlight Bulb',    'LGT-001', 'Electricals', 45,  120.00, 'Philips India'),
                ]
            )
            print("✔  Seeded default parts.")

        # 5. Seed one sample customer + vehicle for demo (only if empty)
        cur.execute("SELECT COUNT(*) FROM customers;")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO customers (name, phone, email, address) "
                "VALUES ('Rajesh Kumar', '9876543210', 'rajesh@example.com', '12, Anna Nagar, Chennai');"
            )
            cid = cur.lastrowid
            cur.execute(
                "INSERT INTO vehicles (customer_id, reg_number, make, model, year, vehicle_type, color) "
                "VALUES (%s, 'TN01AB1234', 'Maruti', 'Swift', 2021, 'Car', 'White');",
                (cid,)
            )
            print("✔  Seeded demo customer and vehicle.")

        conn.commit()
        cur.close()
        conn.close()
        print("✔  Database initialised successfully.")

    except Error as e:
        print(f"✘  Database init failed: {e}")
        print("   Make sure MySQL is running and DB_HOST/DB_USER/DB_PASSWORD are correct.")


def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"DB Error: {e}")
        return None

def query(sql, params=(), fetchone=False, commit=False):
    conn = get_db()
    if not conn:
        return None
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    if commit:
        conn.commit()
        result = cur.lastrowid
    elif fetchone:
        result = cur.fetchone()
    else:
        result = cur.fetchall()
    cur.close()
    conn.close()
    return result


# ── HOME ───────────────────────────────────────────────────
@app.route('/')
def index():
    total_customers = query("SELECT COUNT(*) AS c FROM customers", fetchone=True)['c']
    total_vehicles  = query("SELECT COUNT(*) AS c FROM vehicles", fetchone=True)['c']
    total_bills     = query("SELECT COUNT(*) AS c FROM bills", fetchone=True)['c']
    revenue         = query("SELECT IFNULL(SUM(total_amount),0) AS r FROM bills WHERE payment_status='Paid'", fetchone=True)['r']
    recent_bills    = query("""
        SELECT b.bill_id, c.name, v.reg_number, b.bill_date, b.total_amount, b.payment_status
        FROM bills b
        JOIN customers c ON c.customer_id = b.customer_id
        JOIN vehicles v  ON v.vehicle_id  = b.vehicle_id
        ORDER BY b.created_at DESC LIMIT 5
    """)
    return render_template('index.html',
        total_customers=total_customers,
        total_vehicles=total_vehicles,
        total_bills=total_bills,
        revenue=revenue,
        recent_bills=recent_bills
    )


# ── CUSTOMERS ──────────────────────────────────────────────
@app.route('/customers')
def customers():
    rows = query("SELECT * FROM customers ORDER BY created_at DESC")
    return render_template('customers.html', customers=rows)

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name    = request.form['name']
        phone   = request.form['phone']
        email   = request.form.get('email', '')
        address = request.form.get('address', '')
        query("INSERT INTO customers (name, phone, email, address) VALUES (%s,%s,%s,%s)",
              (name, phone, email, address), commit=True)
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=None)

@app.route('/customers/edit/<int:cid>', methods=['GET', 'POST'])
def edit_customer(cid):
    customer = query("SELECT * FROM customers WHERE customer_id=%s", (cid,), fetchone=True)
    if request.method == 'POST':
        query("UPDATE customers SET name=%s, phone=%s, email=%s, address=%s WHERE customer_id=%s",
              (request.form['name'], request.form['phone'],
               request.form.get('email',''), request.form.get('address',''), cid), commit=True)
        flash('Customer updated!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=customer)

@app.route('/customers/delete/<int:cid>')
def delete_customer(cid):
    query("DELETE FROM customers WHERE customer_id=%s", (cid,), commit=True)
    flash('Customer deleted.', 'info')
    return redirect(url_for('customers'))


# ── VEHICLES ───────────────────────────────────────────────
@app.route('/vehicles')
def vehicles():
    rows = query("""
        SELECT v.*, c.name AS customer_name, c.phone
        FROM vehicles v JOIN customers c ON c.customer_id = v.customer_id
        ORDER BY v.created_at DESC
    """)
    return render_template('vehicles.html', vehicles=rows)

@app.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    customers_list = query("SELECT customer_id, name, phone FROM customers ORDER BY name")
    if request.method == 'POST':
        query("""INSERT INTO vehicles (customer_id, reg_number, make, model, year, vehicle_type, color)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              (request.form['customer_id'], request.form['reg_number'].upper(),
               request.form['make'], request.form['model'],
               request.form.get('year') or None,
               request.form['vehicle_type'], request.form.get('color','')), commit=True)
        flash('Vehicle registered!', 'success')
        return redirect(url_for('vehicles'))
    return render_template('vehicle_form.html', vehicle=None, customers=customers_list)

@app.route('/vehicles/edit/<int:vid>', methods=['GET', 'POST'])
def edit_vehicle(vid):
    vehicle = query("SELECT * FROM vehicles WHERE vehicle_id=%s", (vid,), fetchone=True)
    customers_list = query("SELECT customer_id, name, phone FROM customers ORDER BY name")
    if request.method == 'POST':
        query("""UPDATE vehicles SET customer_id=%s, reg_number=%s, make=%s, model=%s,
                 year=%s, vehicle_type=%s, color=%s WHERE vehicle_id=%s""",
              (request.form['customer_id'], request.form['reg_number'].upper(),
               request.form['make'], request.form['model'],
               request.form.get('year') or None,
               request.form['vehicle_type'], request.form.get('color',''), vid), commit=True)
        flash('Vehicle updated!', 'success')
        return redirect(url_for('vehicles'))
    return render_template('vehicle_form.html', vehicle=vehicle, customers=customers_list)

@app.route('/vehicles/delete/<int:vid>')
def delete_vehicle(vid):
    query("DELETE FROM vehicles WHERE vehicle_id=%s", (vid,), commit=True)
    flash('Vehicle removed.', 'info')
    return redirect(url_for('vehicles'))


# ── PARTS INVENTORY ────────────────────────────────────────
@app.route('/parts')
def parts():
    rows = query("SELECT * FROM parts ORDER BY category, part_name")
    return render_template('parts.html', parts=rows)

@app.route('/parts/add', methods=['GET', 'POST'])
def add_part():
    if request.method == 'POST':
        query("""INSERT INTO parts (part_name, part_code, category, quantity, unit_price, supplier)
                 VALUES (%s,%s,%s,%s,%s,%s)""",
              (request.form['part_name'], request.form.get('part_code',''),
               request.form.get('category',''), int(request.form.get('quantity',0)),
               float(request.form['unit_price']), request.form.get('supplier','')), commit=True)
        flash('Part added!', 'success')
        return redirect(url_for('parts'))
    return render_template('part_form.html', part=None)

@app.route('/parts/edit/<int:pid>', methods=['GET', 'POST'])
def edit_part(pid):
    part = query("SELECT * FROM parts WHERE part_id=%s", (pid,), fetchone=True)
    if request.method == 'POST':
        query("""UPDATE parts SET part_name=%s, part_code=%s, category=%s,
                 quantity=%s, unit_price=%s, supplier=%s WHERE part_id=%s""",
              (request.form['part_name'], request.form.get('part_code',''),
               request.form.get('category',''), int(request.form.get('quantity',0)),
               float(request.form['unit_price']), request.form.get('supplier',''), pid), commit=True)
        flash('Part updated!', 'success')
        return redirect(url_for('parts'))
    return render_template('part_form.html', part=part)

@app.route('/parts/delete/<int:pid>')
def delete_part(pid):
    query("DELETE FROM parts WHERE part_id=%s", (pid,), commit=True)
    flash('Part deleted.', 'info')
    return redirect(url_for('parts'))


# ── BILLING ────────────────────────────────────────────────
@app.route('/bills')
def bills():
    rows = query("""
        SELECT b.bill_id, c.name, v.reg_number, v.make, v.model,
               b.bill_date, b.total_amount, b.payment_status, b.payment_method
        FROM bills b
        JOIN customers c ON c.customer_id = b.customer_id
        JOIN vehicles v  ON v.vehicle_id  = b.vehicle_id
        ORDER BY b.created_at DESC
    """)
    return render_template('bills.html', bills=rows)

@app.route('/bills/add', methods=['GET', 'POST'])
def add_bill():
    customers_list = query("SELECT customer_id, name, phone FROM customers ORDER BY name")
    services_list  = query("SELECT * FROM services ORDER BY service_name")
    parts_list     = query("SELECT * FROM parts ORDER BY part_name")

    if request.method == 'POST':
        cid    = int(request.form['customer_id'])
        vid    = int(request.form['vehicle_id'])
        pstat  = request.form['payment_status']
        pmeth  = request.form['payment_method']
        notes  = request.form.get('notes', '')
        bdate  = request.form.get('bill_date') or str(date.today())

        bill_id = query(
            "INSERT INTO bills (vehicle_id, customer_id, bill_date, payment_status, payment_method, notes) VALUES (%s,%s,%s,%s,%s,%s)",
            (vid, cid, bdate, pstat, pmeth, notes), commit=True
        )

        total = 0.0

        # Services
        svc_ids   = request.form.getlist('svc_id[]')
        svc_names = request.form.getlist('svc_custom_name[]')
        svc_qtys  = request.form.getlist('svc_qty[]')
        svc_prices= request.form.getlist('svc_price[]')
        for i in range(len(svc_prices)):
            if not svc_prices[i]: continue
            qty = int(svc_qtys[i]) if svc_qtys[i] else 1
            price = float(svc_prices[i])
            sub = qty * price
            total += sub
            sid = int(svc_ids[i]) if svc_ids[i] else None
            cname = svc_names[i] if not sid else None
            query("INSERT INTO bill_service_items (bill_id, service_id, custom_service_name, quantity, unit_price, subtotal) VALUES (%s,%s,%s,%s,%s,%s)",
                  (bill_id, sid, cname, qty, price, sub), commit=True)

        # Parts
        prt_ids   = request.form.getlist('prt_id[]')
        prt_names = request.form.getlist('prt_custom_name[]')
        prt_qtys  = request.form.getlist('prt_qty[]')
        prt_prices= request.form.getlist('prt_price[]')
        for i in range(len(prt_prices)):
            if not prt_prices[i]: continue
            qty = int(prt_qtys[i]) if prt_qtys[i] else 1
            price = float(prt_prices[i])
            sub = qty * price
            total += sub
            pid_val = int(prt_ids[i]) if prt_ids[i] else None
            cname = prt_names[i] if not pid_val else None
            query("INSERT INTO bill_part_items (bill_id, part_id, custom_part_name, quantity, unit_price, subtotal) VALUES (%s,%s,%s,%s,%s,%s)",
                  (bill_id, pid_val, cname, qty, price, sub), commit=True)
            # Deduct stock
            if pid_val:
                query("UPDATE parts SET quantity = quantity - %s WHERE part_id=%s", (qty, pid_val), commit=True)

        query("UPDATE bills SET total_amount=%s WHERE bill_id=%s", (total, bill_id), commit=True)
        flash(f'Bill #{bill_id} created! Total: ₹{total:.2f}', 'success')
        return redirect(url_for('view_bill', bid=bill_id))

    return render_template('bill_form.html',
        customers=customers_list, services=services_list, parts=parts_list)

@app.route('/bills/view/<int:bid>')
def view_bill(bid):
    bill = query("""
        SELECT b.*, c.name, c.phone, c.address, v.reg_number, v.make, v.model, v.vehicle_type
        FROM bills b
        JOIN customers c ON c.customer_id = b.customer_id
        JOIN vehicles v  ON v.vehicle_id  = b.vehicle_id
        WHERE b.bill_id=%s
    """, (bid,), fetchone=True)
    svc_items  = query("""
        SELECT bsi.*, IFNULL(s.service_name, bsi.custom_service_name) AS label
        FROM bill_service_items bsi
        LEFT JOIN services s ON s.service_id = bsi.service_id
        WHERE bsi.bill_id=%s
    """, (bid,))
    part_items = query("""
        SELECT bpi.*, IFNULL(p.part_name, bpi.custom_part_name) AS label
        FROM bill_part_items bpi
        LEFT JOIN parts p ON p.part_id = bpi.part_id
        WHERE bpi.bill_id=%s
    """, (bid,))
    return render_template('bill_view.html', bill=bill, svc_items=svc_items, part_items=part_items)

@app.route('/bills/delete/<int:bid>')
def delete_bill(bid):
    query("DELETE FROM bills WHERE bill_id=%s", (bid,), commit=True)
    flash('Bill deleted.', 'info')
    return redirect(url_for('bills'))

# AJAX: get vehicles for a customer
@app.route('/api/vehicles/<int:cid>')
def api_vehicles(cid):
    rows = query("SELECT vehicle_id, reg_number, make, model FROM vehicles WHERE customer_id=%s", (cid,))
    return jsonify(rows)

# AJAX: get part price
@app.route('/api/part_price/<int:pid>')
def api_part_price(pid):
    row = query("SELECT unit_price FROM parts WHERE part_id=%s", (pid,), fetchone=True)
    return jsonify(row)

# AJAX: get service price
@app.route('/api/service_price/<int:sid>')
def api_service_price(sid):
    row = query("SELECT base_price FROM services WHERE service_id=%s", (sid,), fetchone=True)
    return jsonify(row)


if __name__ == '__main__':
    init_db()          # ← auto-creates DB, tables, and seeds data
    app.run(debug=True)
