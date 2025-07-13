# import sqlite3
# import os
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from datetime import datetime

# # --- App Setup ---
# app = Flask(__name__)
# CORS(app)
# DATABASE = 'tracker.db'

# # --- Database Setup ---
# def get_db_connection():
#     conn = sqlite3.connect(DATABASE, check_same_thread=False)
#     conn.row_factory = sqlite3.Row
#     return conn

# def init_db():
#     if os.path.exists(DATABASE):
#         return
#     print("Creating new database...")
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('CREATE TABLE employees (id TEXT PRIMARY KEY, name TEXT NOT NULL)')
#     cursor.execute('CREATE TABLE admin_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
#     cursor.execute('''CREATE TABLE logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, employeeName TEXT, employeeId TEXT, eventType TEXT, timestamp TEXT NOT NULL)''')
#     cursor.execute('''CREATE TABLE deliveries (delivery_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, emp_name TEXT, emp_id TEXT, cust_id TEXT, gas_price REAL)''')
#     cursor.execute('''CREATE TABLE expenses (expense_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, emp_name TEXT, emp_id TEXT, expense_category TEXT, expense_price REAL)''')
#     cursor.execute("INSERT INTO employees (id, name) VALUES (?, ?)", ('EMP001', 'John Doe'))
#     cursor.execute("INSERT INTO admin_settings (key, value) VALUES (?, ?)", ('password', 'admin123'))
#     conn.commit()
#     conn.close()
#     print("Database initialized. Default Admin Password: admin123")

# # --- API Endpoints ---
# @app.route('/')
# def index():
#     return "<h1>Expense Tracker API is Running</h1>"

# # ... (login, logout, admin_login functions are correct and unchanged) ...
# @app.route('/api/login', methods=['POST'])
# def login():
#     data = request.json
#     emp_name = data.get('emp_name', '').strip()
#     emp_id = data.get('emp_id', '').strip().upper()
#     conn = get_db_connection()
#     employee = conn.execute("SELECT * FROM employees WHERE LOWER(name) = LOWER(?) AND id = ?", (emp_name, emp_id)).fetchone()
#     if employee:
#         conn.execute("INSERT INTO logs (employeeName, employeeId, eventType, timestamp) VALUES (?, ?, ?, ?)",
#                      (employee['name'], employee['id'], 'login', datetime.now().isoformat()))
#         conn.commit()
#         conn.close()
#         return jsonify(dict(employee))
#     else:
#         conn.close()
#         return jsonify({"error": "Invalid credentials"}), 401
# @app.route('/api/logout', methods=['POST'])
# def logout():
#     data = request.json
#     conn = get_db_connection()
#     conn.execute("INSERT INTO logs (employeeName, employeeId, eventType, timestamp) VALUES (?, ?, ?, ?)",
#                  (data.get('emp_name'), data.get('emp_id'), 'logout', datetime.now().isoformat()))
#     conn.commit()
#     conn.close()
#     return jsonify({"message": "Logout logged"})
# @app.route('/api/admin/login', methods=['POST'])
# def admin_login():
#     password = request.json.get('password')
#     conn = get_db_connection()
#     admin_data = conn.execute("SELECT value FROM admin_settings WHERE key = 'password'").fetchone()
#     conn.close()
#     if admin_data and password == admin_data['value']:
#         return jsonify({"success": True})
#     else:
#         return jsonify({"error": "Incorrect password"}), 401


# @app.route('/api/delivery', methods=['POST'])
# def add_delivery():
#     data = request.json
#     conn = get_db_connection()
#     # FIX: Using standard YYYY-MM-DD for reliable filtering
#     date_str = datetime.now().strftime('%Y-%m-%d')
#     conn.execute("INSERT INTO deliveries (date, emp_name, emp_id, cust_id, gas_price) VALUES (?, ?, ?, ?, ?)",
#                  (date_str, data['emp_name'], data['emp_id'], data['cust_id'], data['gas_price']))
#     conn.commit()
#     conn.close()
#     return jsonify({"message": "Delivery logged."})

# @app.route('/api/expense', methods=['POST'])
# def add_expense():
#     data = request.json
#     conn = get_db_connection()
#     # FIX: Using standard YYYY-MM-DD for reliable filtering
#     date_str = datetime.now().strftime('%Y-%m-%d')
#     conn.execute("INSERT INTO expenses (date, emp_name, emp_id, expense_category, expense_price) VALUES (?, ?, ?, ?, ?)",
#                  (date_str, data['emp_name'], data['emp_id'], data['expense_category'], data['expense_price']))
#     conn.commit()
#     conn.close()
#     return jsonify({"message": "Expense logged."})

# # ... (The rest of the backend code is correct and unchanged) ...
# @app.route('/api/admin/dashboard', methods=['GET'])
# def get_admin_dashboard_data():
#     conn = get_db_connection()
#     logs = [dict(row) for row in conn.execute("SELECT * FROM logs ORDER BY timestamp DESC").fetchall()]
#     deliveries = [dict(row) for row in conn.execute("SELECT * FROM deliveries ORDER BY delivery_id DESC").fetchall()]
#     expenses = [dict(row) for row in conn.execute("SELECT * FROM expenses ORDER BY expense_id DESC").fetchall()]
#     summary = {}
#     all_deliveries_summary = [dict(row) for row in conn.execute("SELECT * FROM deliveries").fetchall()]
#     all_expenses_summary = [dict(row) for row in conn.execute("SELECT * FROM expenses").fetchall()]
#     for d in all_deliveries_summary:
#         key = (d['date'], d['emp_id'], d['emp_name'])
#         summary.setdefault(key, {'gas': 0, 'expense': 0})
#         summary[key]['gas'] += d['gas_price']
#     for e in all_expenses_summary:
#         key = (e['date'], e['emp_id'], e['emp_name'])
#         summary.setdefault(key, {'gas': 0, 'expense': 0})
#         summary[key]['expense'] += e['expense_price']
#     string_key_summary = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in summary.items()}
#     conn.close()
#     return jsonify({"logs": logs, "deliveries": deliveries, "expenses": expenses, "summary": string_key_summary})
# @app.route('/api/admin/employees', methods=['GET', 'POST'])
# def manage_employees():
#     conn = get_db_connection()
#     if request.method == 'GET':
#         employees = [dict(row) for row in conn.execute("SELECT * FROM employees").fetchall()]
#         conn.close()
#         return jsonify(employees)
#     if request.method == 'POST':
#         data = request.json
#         conn.execute("INSERT INTO employees (name, id) VALUES (?, ?)", (data['emp_name'], data['emp_id']))
#         conn.commit()
#         conn.close()
#         return jsonify({"message": "Employee added."})
# @app.route('/api/admin/employees/delete_all', methods=['POST'])
# def delete_all_employees():
#     conn = get_db_connection()
#     conn.execute("DELETE FROM employees")
#     conn.commit()
#     conn.close()
#     return jsonify({"message": "All employees deleted."})
# @app.route('/api/admin/password', methods=['POST'])
# def change_admin_password():
#     data = request.json
#     new_password = data.get('new_password')
#     if not new_password or len(new_password) < 6:
#         return jsonify({"error": "Password must be at least 6 characters."}), 400
#     conn = get_db_connection()
#     conn.execute("UPDATE admin_settings SET value = ? WHERE key = 'password'", (new_password,))
#     conn.commit()
#     conn.close()
#     return jsonify({"message": "Admin password updated."})
# if __name__ == '__main__':
#     init_db()
#     app.run(host='0.0.0.0', port=5001, debug=True)


import sqlite3
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# --- App Setup ---
app = Flask(__name__)
CORS(app)
DATABASE = 'tracker.db'

# --- Database Setup ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DATABASE):
        return
    print("Creating new database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    # Using 'id' and 'name' as column names
    cursor.execute('CREATE TABLE employees (id TEXT PRIMARY KEY, name TEXT NOT NULL)')
    cursor.execute('CREATE TABLE admin_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    cursor.execute('''CREATE TABLE logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, employeeName TEXT, employeeId TEXT, eventType TEXT, timestamp TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE deliveries (delivery_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, emp_name TEXT, emp_id TEXT, cust_id TEXT, gas_price REAL)''')
    cursor.execute('''CREATE TABLE expenses (expense_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, emp_name TEXT, emp_id TEXT, expense_category TEXT, expense_price REAL)''')
    cursor.execute("INSERT INTO employees (id, name) VALUES (?, ?)", ('EMP001', 'John Doe'))
    cursor.execute("INSERT INTO admin_settings (key, value) VALUES (?, ?)", ('password', 'admin123'))
    conn.commit()
    conn.close()
    print("Database initialized. Default Admin Password: admin123")

# --- API Endpoints ---
@app.route('/')
def index():
    return "<h1>Expense Tracker API is Running</h1>"

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    emp_name = data.get('emp_name', '').strip()
    emp_id = data.get('emp_id', '').strip().upper()
    conn = get_db_connection()
    # Using 'id' and 'name' for the query
    employee = conn.execute("SELECT * FROM employees WHERE LOWER(name) = LOWER(?) AND id = ?", (emp_name, emp_id)).fetchone()
    if employee:
        conn.execute("INSERT INTO logs (employeeName, employeeId, eventType, timestamp) VALUES (?, ?, ?, ?)",
                     (employee['name'], employee['id'], 'login', datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify(dict(employee))
    else:
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    data = request.json
    conn = get_db_connection()
    conn.execute("INSERT INTO logs (employeeName, employeeId, eventType, timestamp) VALUES (?, ?, ?, ?)",
                 (data.get('emp_name'), data.get('emp_id'), 'logout', datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"message": "Logout logged"})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    password = request.json.get('password')
    conn = get_db_connection()
    admin_data = conn.execute("SELECT value FROM admin_settings WHERE key = 'password'").fetchone()
    conn.close()
    if admin_data and password == admin_data['value']:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Incorrect password"}), 401

@app.route('/api/delivery', methods=['POST'])
def add_delivery():
    data = request.json
    conn = get_db_connection()
    date_str = datetime.now().strftime('%Y-%m-%d')
    conn.execute("INSERT INTO deliveries (date, emp_name, emp_id, cust_id, gas_price) VALUES (?, ?, ?, ?, ?)",
                 (date_str, data['emp_name'], data['emp_id'], data['cust_id'], data['gas_price']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Delivery logged."})

@app.route('/api/expense', methods=['POST'])
def add_expense():
    data = request.json
    conn = get_db_connection()
    date_str = datetime.now().strftime('%Y-%m-%d')
    conn.execute("INSERT INTO expenses (date, emp_name, emp_id, expense_category, expense_price) VALUES (?, ?, ?, ?, ?)",
                 (date_str, data['emp_name'], data['emp_id'], data['expense_category'], data['expense_price']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Expense logged."})

@app.route('/api/admin/dashboard', methods=['GET'])
def get_admin_dashboard_data():
    conn = get_db_connection()
    logs = [dict(row) for row in conn.execute("SELECT * FROM logs ORDER BY timestamp DESC").fetchall()]
    deliveries = [dict(row) for row in conn.execute("SELECT * FROM deliveries ORDER BY delivery_id DESC").fetchall()]
    expenses = [dict(row) for row in conn.execute("SELECT * FROM expenses ORDER BY expense_id DESC").fetchall()]
    summary = {}
    all_deliveries_summary = [dict(row) for row in conn.execute("SELECT * FROM deliveries").fetchall()]
    all_expenses_summary = [dict(row) for row in conn.execute("SELECT * FROM expenses").fetchall()]
    for d in all_deliveries_summary:
        key = (d['date'], d['emp_id'], d['emp_name'])
        summary.setdefault(key, {'gas': 0, 'expense': 0})
        summary[key]['gas'] += d['gas_price']
    for e in all_expenses_summary:
        key = (e['date'], e['emp_id'], e['emp_name'])
        summary.setdefault(key, {'gas': 0, 'expense': 0})
        summary[key]['expense'] += e['expense_price']
    string_key_summary = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in summary.items()}
    conn.close()
    return jsonify({"logs": logs, "deliveries": deliveries, "expenses": expenses, "summary": string_key_summary})

@app.route('/api/admin/employees', methods=['GET', 'POST'])
def manage_employees():
    conn = get_db_connection()
    if request.method == 'GET':
        employees = [dict(row) for row in conn.execute("SELECT * FROM employees").fetchall()]
        conn.close()
        return jsonify(employees)
    if request.method == 'POST':
        data = request.json
        # Using 'id' and 'name' to match the database schema
        conn.execute("INSERT INTO employees (id, name) VALUES (?, ?)", (data['emp_id'], data['emp_name']))
        conn.commit()
        conn.close()
        return jsonify({"message": "Employee added."})

# --- NEW, CORRECTED FUNCTION ---
@app.route('/api/admin/employees/batch_add', methods=['POST'])
def batch_add_employees():
    data = request.get_json()
    new_employees = data.get('employees')
    if not new_employees or not isinstance(new_employees, list):
        return jsonify({'error': 'Invalid data format'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    added_count = 0
    skipped_count = 0
    
    for emp in new_employees:
        try:
            # THE FIX: Using the correct database column names 'id' and 'name'
            # The Flutter app sends 'id' and 'name', so we use emp['id'] and emp['name']
            cursor.execute('INSERT INTO employees (id, name) VALUES (?, ?)', (emp['id'], emp['name']))
            added_count += 1
        except sqlite3.IntegrityError:
            # This happens if the employee ID already exists. We can just skip it.
            skipped_count += 1
            print(f"Employee ID {emp['id']} already exists. Skipping.")
            pass
        except Exception as e:
            # Catch any other unexpected errors during the loop
            print(f"Error inserting {emp}: {e}")

    conn.commit()
    conn.close()
    
    message = f'{added_count} new employees added.'
    if skipped_count > 0:
        message += f' {skipped_count} duplicates were skipped.'
        
    return jsonify({'message': message})
# -------------------------------

@app.route('/api/admin/employees/delete_all', methods=['POST'])
def delete_all_employees():
    conn = get_db_connection()
    conn.execute("DELETE FROM employees")
    conn.commit()
    conn.close()
    return jsonify({"message": "All employees deleted."})

@app.route('/api/admin/password', methods=['POST'])
def change_admin_password():
    data = request.json
    new_password = data.get('new_password')
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    conn = get_db_connection()
    conn.execute("UPDATE admin_settings SET value = ? WHERE key = 'password'", (new_password,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Admin password updated."})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)