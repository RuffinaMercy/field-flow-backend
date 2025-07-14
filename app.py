# --- IMPORTS ---
# Switched from sqlite3 to psycopg2 for PostgreSQL
import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# --- App Setup ---
app = Flask(__name__)
CORS(app)
# The DATABASE constant for the local file is no longer needed.

# --- Database Setup (MODIFIED FOR POSTGRESQL) ---
def get_db_connection():
    """Connects to the PostgreSQL database using the DATABASE_URL from the environment."""
    # Render.com and other hosts provide the database connection string as an environment variable.
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise RuntimeError("FATAL: DATABASE_URL environment variable is not set.")
    
    conn = psycopg2.connect(db_url)
    # Use DictCursor to access columns by name (like dictionary keys), similar to sqlite3.Row
    conn.cursor_factory = psycopg2.extras.DictCursor
    return conn

def init_db():
    """
    Initializes the PostgreSQL database with the required tables and default data.
    This function should be run manually once on the server.
    It creates tables only if they do not already exist.
    """
    print("Connecting to the database to initialize tables...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("Creating tables if they don't exist...")

        # PostgreSQL uses SERIAL for auto-incrementing primary keys.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY, 
                name TEXT NOT NULL
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY, 
                value TEXT NOT NULL
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                log_id SERIAL PRIMARY KEY, 
                employeeName TEXT, 
                employeeId TEXT, 
                eventType TEXT, 
                timestamp TEXT NOT NULL
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deliveries (
                delivery_id SERIAL PRIMARY KEY, 
                date TEXT, 
                emp_name TEXT, 
                emp_id TEXT, 
                cust_id TEXT, 
                gas_price REAL
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id SERIAL PRIMARY KEY, 
                date TEXT, 
                emp_name TEXT, 
                emp_id TEXT, 
                expense_category TEXT, 
                expense_price REAL
            )''')

        # Check for default admin before inserting to prevent duplicates.
        cursor.execute("SELECT 1 FROM admin_settings WHERE key = 'password'")
        if cursor.fetchone() is None:
            print("Inserting default admin password...")
            # PostgreSQL uses %s for parameter placeholders.
            cursor.execute("INSERT INTO admin_settings (key, value) VALUES (%s, %s)", ('password', 'admin123'))

        # Check for default employee before inserting.
        cursor.execute("SELECT 1 FROM employees WHERE id = 'EMP001'")
        if cursor.fetchone() is None:
            print("Inserting default employee...")
            cursor.execute("INSERT INTO employees (id, name) VALUES (%s, %s)", ('EMP001', 'John Doe'))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialization complete.")
    except Exception as e:
        print(f"An error occurred during DB initialization: {e}")


# --- API Endpoints ---
# All endpoints are updated to use get_db_connection() which now connects to PostgreSQL.
# All SQL parameters are now using %s instead of ?.

@app.route('/')
def index():
    return "<h1>Field Flow API is Running (Cloud Version)</h1>"

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    emp_name = data.get('emp_name', '').strip()
    emp_id = data.get('emp_id', '').strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE LOWER(name) = LOWER(%s) AND id = %s", (emp_name, emp_id))
    employee = cursor.fetchone()
    
    if employee:
        cursor.execute("INSERT INTO logs (employeeName, employeeId, eventType, timestamp) VALUES (%s, %s, %s, %s)",
                     (employee['name'], employee['id'], 'login', datetime.now().isoformat()))
        conn.commit()
        cursor.close()
        conn.close()
        # dict() is needed because DictRow is not directly JSON serializable
        return jsonify(dict(employee))
    else:
        cursor.close()
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (employeeName, employeeId, eventType, timestamp) VALUES (%s, %s, %s, %s)",
                 (data.get('emp_name'), data.get('emp_id'), 'logout', datetime.now().isoformat()))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Logout logged"})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    password = request.json.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM admin_settings WHERE key = 'password'")
    admin_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if admin_data and password == admin_data['value']:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Incorrect password"}), 401

@app.route('/api/delivery', methods=['POST'])
def add_delivery():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO deliveries (date, emp_name, emp_id, cust_id, gas_price) VALUES (%s, %s, %s, %s, %s)",
                 (date_str, data['emp_name'], data['emp_id'], data['cust_id'], data['gas_price']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Delivery logged."})

@app.route('/api/expense', methods=['POST'])
def add_expense():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO expenses (date, emp_name, emp_id, expense_category, expense_price) VALUES (%s, %s, %s, %s, %s)",
                 (date_str, data['emp_name'], data['emp_id'], data['expense_category'], data['expense_price']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Expense logged."})

@app.route('/api/admin/dashboard', methods=['GET'])
def get_admin_dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
    logs = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM deliveries ORDER BY delivery_id DESC")
    deliveries = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM expenses ORDER BY expense_id DESC")
    expenses = [dict(row) for row in cursor.fetchall()]

    summary = {}
    cursor.execute("SELECT * FROM deliveries")
    all_deliveries_summary = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM expenses")
    all_expenses_summary = [dict(row) for row in cursor.fetchall()]
    
    for d in all_deliveries_summary:
        key = (d['date'], d['emp_id'], d['emp_name'])
        summary.setdefault(key, {'gas': 0, 'expense': 0})
        summary[key]['gas'] += d['gas_price']
    for e in all_expenses_summary:
        key = (e['date'], e['emp_id'], e['emp_name'])
        summary.setdefault(key, {'gas': 0, 'expense': 0})
        summary[key]['expense'] += e['expense_price']
    
    string_key_summary = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in summary.items()}
    cursor.close()
    conn.close()
    return jsonify({"logs": logs, "deliveries": deliveries, "expenses": expenses, "summary": string_key_summary})

@app.route('/api/admin/employees', methods=['GET', 'POST'])
def manage_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'GET':
        cursor.execute("SELECT * FROM employees ORDER BY name")
        employees = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(employees)
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO employees (name, id) VALUES (%s, %s)", (data['emp_name'], data['emp_id']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Employee added."})

@app.route('/api/admin/employees/delete_all', methods=['POST'])
def delete_all_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees")
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "All employees deleted."})

@app.route('/api/admin/password', methods=['POST'])
def change_admin_password():
    data = request.json
    new_password = data.get('new_password')
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE admin_settings SET value = %s WHERE key = 'password'", (new_password,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Admin password updated."})

# --- Main Execution (MODIFIED FOR CLOUD) ---
if __name__ == '__main__':
    # The init_db() call is removed from here. It should be run manually.
    # The app will run on the port provided by the environment, or 5001 if not set.
    # In production on Render, Gunicorn is used instead of app.run().
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False) # Debug should be False in production