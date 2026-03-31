from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import psycopg2
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret123"

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

    c.execute('''
    CREATE TABLE IF NOT EXISTS observations (
        id SERIAL PRIMARY KEY,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ✅ Add village column if not exists
    c.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='observations' AND column_name='village'
        ) THEN
            ALTER TABLE observations ADD COLUMN village TEXT;
        END IF;
    END$$;
    """)
 
    
    # Check if data exists
    c.execute("SELECT COUNT(*) FROM beatbook")
    count = c.fetchone()[0]

    c.execute("SELECT village FROM beatbook")
    existing = [row[0] for row in c.fetchall()]
    if "Bisoni" not in existing:
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

   
    villages_to_add = [
        ("Bisoni", "SI Sundar Lal Pawar", "Surendra Panche", "Approx 2500", "Lodhi, Kalar, Marar, Gowara", "Smt. Varsha Vare (9424937724)", "Govt. High School Bisoni"),
        ("Chichtola", "SI Verma", "Constable A", "1500", "General", "Mr Rajesh Yadav", "School Chichtola"),
        ("Rampura", "SI Singh", "Constable B", "1200", "OBC", "Mr Suresh Patel", "School Rampura"),
        ("Lanji", "SI Khan", "Constable C", "1800", "SC", "Mr Vijay Sharma", "School Lanji"),
        ("Sogalpur", "SI Patel", "Constable D", "1400", "ST", "Mr Ramesh Tiwari", "School Sogalpur"),
        ("Itora", "SI Ram", "Constable E", "1900", "ST", "Mr Anand Kumar", "School Itora"),
        ("Bhandara", "SI Sharma", "Constable F", "1600", "OBC", "Mr Deepak Singh", "School Bhandara"),
        ("Kachari", "SI Gupta", "Constable G", "1700", "General", "Mr Manoj Joshi", "School Kachari"),
        ("Mandwa", "SI Joshi", "Constable H", "1300", "SC", "Mr Sunil Reddy", "School Mandwa"),
        ("Chandrapur", "SI Reddy", "Constable I", "2000", "ST", "Mr Prakash Rao", "School Chandrapur")
    ]

    for v in villages_to_add:
        if v[0] not in existing:
            c.execute("""
                INSERT INTO beatbook 
                (police_station, village, beat_officer, beat_constable, population, caste, sarpanch, school)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, ("Lanji", v[0], v[1], v[2], v[3], v[4], v[5], v[6]))

    conn.commit()
    c.close()
    conn.close()

 # 🔹 Dummy Users
users = {
    "si": {"password": "123", "rank": "SI"},
    "const_bisoni": {"password": "123", "rank": "CONSTABLE", "village": "Bisoni"},
    "const_chichtola": {"password": "123", "rank": "CONSTABLE", "village": "Chichtola"},
    "const_rampura": {"password": "123", "rank": "CONSTABLE", "village": "Rampura"},
    "const_lanji": {"password": "123", "rank": "CONSTABLE", "village": "Lanji"},
    "const_sogalpur": {"password": "123", "rank": "CONSTABLE", "village": "Sogalpur"},
    "const_itora": {"password": "123", "rank": "CONSTABLE", "village": "Itora"},
}

# 🔹 Rank wise village mapping
village_mapping = {
    "SI": ["Bisoni", "Chichtola", "Rampura", "Lanji", "Sogalpur", "Itora"],
    "CONSTABLE": ["Bisoni"]
    }


# 🔥 IMPORTANT: har request se pehle table create
def init_db_safe():
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print("❌ DB Error:", e)

# 🔹 Home page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users and users[username]["password"] == password:
            session["user"] = username
            session["rank"] = users[username]["rank"]

            # Constable के लिए village save करो
            if users[username]["rank"] == "CONSTABLE":
                session["village"] = users[username]["village"]

            return redirect('/dashboard')
        else:
            return "Invalid Login ❌"

    # GET request के लिए login page render
    return render_template('login.html')

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            return "Invalid Admin Login"

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()
    cur = conn.cursor()

    # 🔹 Complaints
    cur.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = cur.fetchall()

    # 🔹 Queries
    cur.execute("SELECT * FROM queries ORDER BY id DESC")
    queries = cur.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        queries=queries
    )
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

    
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect('/login')

    rank = session.get("rank")

    if rank == "CONSTABLE":
        villages = [session.get("village")]
    else:
        villages = village_mapping.get(rank, [])

    return render_template('dashboard.html', villages=villages)

@app.route("/logout")
def logout():
    session.clear()   # 🔴 login खत्म
    return redirect(url_for("login"))  # login page पर भेजो

@app.route('/village/<name>')
def village(name):
    if "user" not in session:
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()

    # Beatbook data
    c.execute("SELECT * FROM beatbook WHERE village=%s", (name,))
    beat = c.fetchone()

    # Observations
    c.execute("SELECT * FROM observations WHERE village=%s ORDER BY id DESC", (name,))
    observations = c.fetchall()

    c.close()
    conn.close()
    
    now = datetime.now() + timedelta(hours=5, minutes=30)
    
    return render_template(
    'village_detail.html',
    beat=beat,
    observations=observations,
    village=name,
    now=now
)

@app.route('/')
def home():    
    return render_template('index.html')
        
@app.route('/health')
def health():
    return "OK", 200

@app.route('/beatbook')
def beatbook():
    if "user" not in session:
        return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM beatbook")
    data = c.fetchall()

    c.execute("SELECT * FROM observations ORDER BY id DESC")
    observations = c.fetchall()

    c.close()
    conn.close()

    return render_template('beatbook.html', data=data, observations=observations)

@app.route('/delete_observation/<int:id>', methods=['POST'])
def delete_observation(id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM observations WHERE id=%s", (id,))
        conn.commit()
        c.close()
        conn.close()
        return redirect(request.referrer)
    except Exception as e:
        return f"Error: {str(e)}"
        
@app.route("/delete/<string:type>/<int:id>", methods=["POST"])
def delete(type, id):
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()
    cur = conn.cursor()

    if type == "complaint":
        cur.execute("DELETE FROM complaints WHERE id=%s", (id,))
    elif type == "query":
        cur.execute("DELETE FROM queries WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")


@app.route('/save_observation', methods=['POST'])
def save_observation():
    observation = request.form['observation']
    village = request.form.get('village')
    if not observation:
        return "Observation required ❗"

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
    INSERT INTO observations (text, created_at, village) 
    VALUES (%s, NOW() + INTERVAL '5 hours 30 minutes', %s)
    """, (observation, village))
    conn.commit()
    c.close()
    conn.close()

    return redirect(request.referrer + "?success=1")

@app.route('/edit/<int:id>')
def edit(id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM beatbook WHERE id=%s", (id,))
    row = c.fetchone()

    c.close()
    conn.close()

    return render_template('edit.html', row=row)

@app.route("/update_row/<int:id>", methods=["POST"])
def update_row(id):
    try:
        data = request.get_json()  # JS से भेजा गया JSON पढ़ो
        field = data.get("field")
        value = data.get("value")
        allowed_fields = ["police_station","village","beat_officer","beat_constable",
                          "population","caste","sarpanch","school"]
        if field not in allowed_fields:
            return jsonify({"status": "error", "message": "Invalid field"}), 400

        conn = get_db_connection()
        c = conn.cursor()

        query = f"UPDATE beatbook SET {field}=%s WHERE id=%s"
        c.execute(query, (value, id))
        conn.commit()
        c.close()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        print("Update error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
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
    init_db_safe()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
