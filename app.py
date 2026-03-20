from flask import Flask, render_template, request, redirect
import psycopg2
import os

app = Flask(__name__)

# 🔹 Database URL (Render / Heroku environment variable)
DATABASE_URL = os.environ.get("DATABASE_URL")

# 🔹 Connect function
def get_db_connection():
    if DATABASE_URL is None:
        raise ValueError("DATABASE_URL environment variable not set!")
    return psycopg2.connect(DATABASE_URL)

# 🔹 Initialize database tables (complaints + queries)
def init_db():
    try:
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
        print("Tables created successfully ✅")

    except Exception as e:
        print("Error creating tables:", e)

# 🔹 Initialize tables before first request (Render compatible)
@app.before_first_request
def initialize():
    init_db()

# 🔹 Home page
@app.route('/')
def home():
    return render_template('index.html')

# 🔹 View data
@app.route('/view')
def view():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("SELECT * FROM complaints")
        complaints = c.fetchall()

        c.execute("SELECT * FROM queries")
        queries = c.fetchall()

        c.close()
        conn.close()

        # Nicely format output
        html = "<h2>Complaints</h2><ul>"
        for comp in complaints:
            html += f"<li>ID:{comp[0]} | Name:{comp[1]} | Message:{comp[2]}</li>"
        html += "</ul>"

        html += "<h2>Queries</h2><ul>"
        for q in queries:
            html += f"<li>ID:{q[0]} | Name:{q[1]} | Message:{q[2]}</li>"
        html += "</ul>"

        return html

    except Exception as e:
        print("DB Fetch Error:", e)
        return f"Error fetching data: {str(e)}"

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
        else:
            return "Invalid form type ❌"

        conn.commit()
        c.close()
        conn.close()

        return redirect('/')

    except Exception as e:
        print("DB Insert Error:", e)
        return f"Error: {str(e)}"

# 🔹 Run app
if __name__ == '__main__':
    app.run(debug=True)
