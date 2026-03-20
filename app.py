from flask import Flask, render_template, request, redirect
import psycopg2
import os

app = Flask(__name__)

# 🔹 Database URL (Render se aayega)
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
            name TEXT,
            message TEXT
        )
    ''')

    # Query table
    c.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id SERIAL PRIMARY KEY,
            name TEXT,
            message TEXT
        )
    ''')

    conn.commit()
    conn.close()


# 🔹 Home page
@app.route('/')
def home():
    return render_template('index.html')


# 🔹 View data (IMPORTANT 🔥)
@app.route('/view')
def view():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM complaints")
    complaints = c.fetchall()

    c.execute("SELECT * FROM queries")
    queries = c.fetchall()

    conn.close()

    return f"<h2>Complaints</h2>{complaints}<br><br><h2>Queries</h2>{queries}"


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
        conn.close()

        return redirect('/')

    except Exception as e:
        return f"Error: {str(e)}"


# 🔹 Run app
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
