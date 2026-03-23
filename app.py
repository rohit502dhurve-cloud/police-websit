from flask import Flask, render_template, request, redirect
import psycopg2
import os

app = Flask(__name__)

# 🔹 Database URL
DATABASE_URL = os.environ.get("DATABASE_URL")

# 🔹 Connect function
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, connect_timeout=3)
    
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

    # Beatbook table
    c.execute('''
        CREATE TABLE IF NOT EXISTS beatbook (
            id SERIAL PRIMARY KEY,
            police_station TEXT,
            village TEXT,
            beat_officer TEXT,
            beat_constable TEXT,
            population TEXT,
            caste TEXT,
            sarpanch TEXT,
            school TEXT
        )
    ''')

    # Check if data exists
    c.execute("SELECT COUNT(*) FROM beatbook")
    count = c.fetchone()[0]

    if count == 0:
        c.execute("""
            INSERT INTO beatbook 
            (police_station, village, beat_officer, beat_constable, population, caste, sarpanch, school)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            "Lanji",
            "Bisoni",
            "SI Sundar Lal Pawar",
            "Surendra Panche",
            "Approx 2500",
            "Lodhi, Kalar, Marar, Gowara",
            "Smt. Varsha Vare (9424937724)",
            "Govt. High School Bisoni"
        ))

    conn.commit()
    c.close()
    conn.close()

# 🔥 IMPORTANT: har request se pehle table create
def init_db_safe():
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print("❌ DB Error:", e)

# 🔹 Home page
@app.route('/')
def home():
    try:
        init_db()
    except:
        pass
    return render_template('index.html')
    
@app.route('/health')
def health():
    return "OK", 200

@app.route('/beatbook')
def beatbook():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM beatbook")
    data = c.fetchall()

    c.close()
    conn.close()

    return render_template('beatbook.html', data=data)

@app.route('/save_observation', methods=['POST'])
def save_observation():
    observation = request.form['observation']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("INSERT INTO observations (text) VALUES (?)", (observation,))
    conn.commit()
    conn.close()

    return redirect('/beatbook')

c.execute('''CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT
)''')

@app.route('/edit/<int:id>')
def edit(id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM beatbook WHERE id=%s", (id,))
    row = c.fetchone()

    c.close()
    conn.close()

    return render_template('edit.html', row=row)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    police_station = request.form.get('police_station')
    village = request.form.get('village')
    beat_officer = request.form.get('beat_officer')
    beat_constable = request.form.get('beat_constable')
    population = request.form.get('population')
    caste = request.form.get('caste')
    sarpanch = request.form.get('sarpanch')
    school = request.form.get('school')

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE beatbook SET
        police_station=%s,
        village=%s,
        beat_officer=%s,
        beat_constable=%s,
        population=%s,
        caste=%s,
        sarpanch=%s,
        school=%s
        WHERE id=%s
    """, (
        police_station, village, beat_officer,
        beat_constable, population, caste,
        sarpanch, school, id
    ))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/beatbook')

# 🔹 View data
@app.route('/view')
def view():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM complaints")
    complaints = c.fetchall()

    c.execute("SELECT * FROM queries")
    queries = c.fetchall()

    c.close()
    conn.close()

    return render_template('view.html', complaints=complaints, queries=queries)

 
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
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
