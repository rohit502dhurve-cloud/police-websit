from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "secret123"

# 🔹 Database URL
DATABASE_URL = os.environ.get("DATABASE_URL")

# 🔹 Connect function
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# 🔹 Database create (tables)
def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Complaint table
    c.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

    # Query table
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

# 🔥 IMPORTANT: har request se pehle table create
@app.before_request
def create_tables():
    init_db()

# 🔹 Home page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "1234":
            session['logged_in'] = True
            return redirect('/view')
        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')    

# 🔹 View data
@app.route('/view')
def view():
    if not session.get('logged_in'):
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM complaints")
    complaints = c.fetchall()

    c.execute("SELECT * FROM queries")
    queries = c.fetchall()

    c.close()
    conn.close()

    return render_template('view.html', complaints=complaints, queries=queries)

    html = "<h2>Complaints</h2><ul>"
    for comp in complaints:
        html += f"<li>ID:{comp[0]} | Name:{comp[1]} | Message:{comp[2]}</li>"
    html += "</ul>"

    html += "<h2>Queries</h2><ul>"
    for q in queries:
        html += f"<li>ID:{q[0]} | Name:{q[1]} | Message:{q[2]}</li>"
    html += "</ul>"

    return html

# 🔹 Form submit
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

        # ✅ Success message
        return redirect('/?success=1')

    except Exception as e:
        return f"Error: {str(e)}"

# 🔹 Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
