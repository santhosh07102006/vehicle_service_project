# Vehicle Service Center Management System
## Flask + MySQL | DBMS Project

---

## 📁 Project Structure

```
vehicle_service/
├── app.py                  ← Flask backend (all routes)
├── schema.sql              ← MySQL database schema + seed data
├── requirements.txt        ← Python dependencies
└── templates/
    ├── base.html           ← Base layout (nav, styles)
    ├── index.html          ← Dashboard
    ├── customers.html      ← Customer list
    ├── customer_form.html  ← Add/Edit customer
    ├── vehicles.html       ← Vehicle list
    ├── vehicle_form.html   ← Add/Edit vehicle
    ├── parts.html          ← Parts inventory
    ├── part_form.html      ← Add/Edit part
    ├── bills.html          ← Bills list
    ├── bill_form.html      ← Create new bill
    └── bill_view.html      ← View/Print bill
```

---

## ⚙️ Setup Instructions

### Step 1 – Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 2 – Set up MySQL database
Open MySQL and run:
```bash
mysql -u root -p < schema.sql
```
This creates the database, all tables, and seeds sample data.

### Step 3 – Configure database access
The app reads database settings from environment variables, so passwords do not need to be stored in the repository.

PowerShell:
```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "your-local-mysql-password"
$env:DB_NAME = "vehicle_service_db"
$env:FLASK_SECRET_KEY = "a-long-random-local-secret"
```

For a local MySQL account with no password, omit `DB_PASSWORD` or set it to an empty string. You can also copy `.env.example` into your shell configuration, but do not commit a file containing real values.

### Step 4 – Run the Flask app
```bash
python app.py
```

### Step 5 – Open in browser
```
http://127.0.0.1:5000
```

---

## ✅ Features

| Module            | What you can do                                      |
|-------------------|------------------------------------------------------|
| Dashboard         | See stats: customers, vehicles, bills, revenue       |
| Customers         | Add, edit, delete customers                          |
| Vehicles          | Register vehicles linked to customers                |
| Parts Inventory   | Manage stock, price, supplier info                   |
| Billing           | Create bills with services + parts, auto-total       |
| Bill View/Print   | Printable invoice view                               |

---

## 🗃️ Database Tables

- `customers` – Customer info
- `vehicles` – Vehicles linked to customers
- `parts` – Spare parts inventory
- `services` – Service catalog (seeded)
- `bills` – Main billing records
- `bill_service_items` – Services per bill
- `bill_part_items` – Parts used per bill
