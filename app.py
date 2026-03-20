from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "secret123"

# 🔹 Database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# 🔹 Function to get DB connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# 🔹 Initialize database tables once
def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Complaints table
    c.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

    # Queries table
    c.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

    conn.commit()
    c.close()
    conn.close()

init_db()  # Run once on startup

# 🔹 Public homepage (form only, no submissions shown)
@app.route('/')
def home():
    return render_template('public_home.html')  # templates/public_home.html

# 🔹 Admin login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "1234":
            session['logged_in'] = True
            return redirect(url_for('admin_view'))
        else:
            return render_template('login.html', error="Invalid Credentials ❌")

    return render_template('login.html', error=None)

# 🔹 Admin logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# 🔹 Admin view (login required)
@app.route('/admin')
def admin_view():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = c.fetchall()

    c.execute("SELECT * FROM queries ORDER BY id DESC")
    queries = c.fetchall()

    c.close()
    conn.close()

    return render_template('admin_view.html', complaints=complaints, queries=queries)

# 🔹 Form submit (public can submit, data goes to DB)
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    message = request.form.get('message')
    form_type = request.form.get('type')

    if not name or not message:
        return "Please fill all fields ❗"

    try:
        conn = get_db_connection()
        c = conn.cursor()

        if form_type == "complaint":
            c.execute(
                "INSERT INTO complaints (name, message) VALUES (%s, %s)",
                (name, message)
            )
        elif form_type == "query":
            c.execute(
                "INSERT INTO queries (name, message) VALUES (%s, %s)",
                (name, message)
            )

        conn.commit()
        c.close()
        conn.close()

        # Redirect public back to home after submit
        return redirect(url_for('home'))

    except Exception as e:
        return f"Error: {str(e)}"

# 🔹 Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
