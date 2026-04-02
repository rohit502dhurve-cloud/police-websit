from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import psycopg2
import os
from datetime import datetime, timedelta
from urllib.parse import unquote   # ✅ NEW (URL fix)

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

    # Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        village TEXT
    )
    ''')

    # 🔥 FIX: existing villages (clean)
    c.execute("SELECT LOWER(TRIM(village)) FROM beatbook")
    existing = [row[0] for row in c.fetchall()]

    # 🔹 Villages list
    villages_to_add = [
        ("Itora","SI Ramesh","Constable J","2100","SC","Mr F","School J"),
        ("Dulhapur","SI Naresh","Constable K","2200","ST","Mr G","School K"),
        ("Khajri","SI Deepak","Constable L","2300","General","Mr H","School L"),
        ("Bhimodi","SI Karan","Constable M","2400","OBC","Mr I","School M"),
        ("Sunarkakodi","SI Arjun","Constable N","2500","SC","Mr J","School N")
    ]

    # 🔥 FIX: safe insert + update existing list
    for v in villages_to_add:
        name = v[0].strip().lower()

        if name not in existing:
            c.execute("""
                INSERT INTO beatbook 
                (police_station, village, beat_officer, beat_constable, population, caste, sarpanch, school)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, ("Lanji", v[0].strip(), v[1], v[2], v[3], v[4], v[5], v[6]))

            existing.append(name)  # 🔥 IMPORTANT

    conn.commit()
    c.close()
    conn.close()


# 🔹 Dummy Users (same)
users = {
    "si": {"password": "123", "rank": "SI"},
    "const_bisoni": {"password": "123", "rank": "CONSTABLE", "village": "Bisoni"},
    "const_rampura": {"password": "123", "rank": "CONSTABLE", "village": "Rampura"},
    "const_lanji": {"password": "123", "rank": "CONSTABLE", "village": "Lanji"},
    "const_sogalpur": {"password": "123", "rank": "CONSTABLE", "village": "Sogalpur"},
    "const_chichtola": {"password": "123", "rank": "CONSTABLE", "village": "Chichtola"},
    "const_itora": {"password": "123", "rank": "CONSTABLE", "village": "Itora"},
    "const_dulhapur": {"password": "123", "rank": "CONSTABLE", "village": "Dulhapur"},
    "const_khajri": {"password": "123", "rank": "CONSTABLE", "village": "Khajri"},
    "const_bhimodi": {"password": "123", "rank": "CONSTABLE", "village": "Bhimodi"},
    "const_sunarkakodi": {"password": "123", "rank": "CONSTABLE", "village": "Sunarkakodi"}
}

village_mapping = {
    "SI": [],
    "CONSTABLE": ["Bisoni"]
}

# 🔥 Safe init
def init_db_safe():
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print("❌ DB Error:", e)

# 🔹 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users and users[username]["password"] == password:
            session["user"] = username
            session["rank"] = users[username]["rank"]

            if users[username]["rank"] == "CONSTABLE":
                session["village"] = users[username]["village"]

            return redirect('/dashboard')

        return "Invalid Login ❌"

    return render_template('login.html')

# 🔹 Dashboard (🔥 dynamic)
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()
    if session.get("rank") == "CONSTABLE":
        villages = [session.get("village")]   # 🔥 सिर्फ अपना village
    else:
        c.execute("SELECT village FROM beatbook")
        villages = [row[0] for row in c.fetchall()]
   
    c.close()
    conn.close()

    return render_template('dashboard.html', villages=villages)

# 🔹 Village page (🔥 FIXED)
@app.route('/village/<name>')
def village(name):
    if "user" not in session:
        return redirect('/login')

    original_name = unquote(name).strip()
    name = original_name.lower()

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        SELECT * FROM beatbook 
        WHERE LOWER(TRIM(village)) = %s
    """, (name,))
    beat = c.fetchone()

    c.execute("""
        SELECT * FROM observations 
        WHERE LOWER(TRIM(village)) = %s 
        ORDER BY id DESC
    """, (name,))
    observations = c.fetchall()

    c.close()
    conn.close()

    now = datetime.now() + timedelta(hours=5, minutes=30)

    return render_template(
        'village_detail.html',
        beat=beat,
        observations=observations,
        village=original_name,
        now=now
    )

# 🔹 बाकी routes SAME (no change)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check_db')
def check_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM beatbook")
    data = c.fetchall()
    c.close()
    conn.close()
    return str(data)

@app.route('/health')
def health():
    return "OK", 200

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/save_observation', methods=['POST'])
def save_observation():
    observation = request.form.get('observation')
    village = request.form.get('village')

    if not observation:
        return "Observation required ❗"

    village = village.strip().lower()   # 🔥 FIX

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO observations (text, created_at, village) 
        VALUES (%s, NOW() + INTERVAL '5 hours 30 minutes', %s)
    """, (observation, village))

    conn.commit()
    c.close()
    conn.close()

    return redirect(request.referrer)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    message = request.form.get('message')
    form_type = request.form.get('type')  # "complaint" या "query"

    if not name or not message:
        return "Please fill all fields ❗"

    conn = get_db_connection()
    c = conn.cursor()

    if form_type == "complaint":
        c.execute("INSERT INTO complaints (name, message) VALUES (%s, %s)", (name, message))
    elif form_type == "query":
        c.execute("INSERT INTO queries (name, message) VALUES (%s, %s)", (name, message))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/?success=1')  # या अपनी पसंद का page
@app.route("/update_row/<int:id>", methods=["POST"])
def update_row(id):
    try:
        data = request.get_json()
        field = data.get("field")
        value = data.get("value")

        allowed_fields = [
            "police_station","village","beat_officer",
            "beat_constable","population","caste",
            "sarpanch","school"
        ]

        if field not in allowed_fields:
            return jsonify({"status": "error"}), 400

        conn = get_db_connection()
        c = conn.cursor()

        c.execute(f"UPDATE beatbook SET {field}=%s WHERE id=%s", (value, id))

        conn.commit()
        c.close()
        conn.close()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    admins = {"admin": "1234"}  # future-proof
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in admins and password == admins[username]:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            return render_template("admin_login.html", error="Invalid Admin Login")

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = cur.fetchall()

    cur.execute("SELECT * FROM queries ORDER BY id DESC")
    queries = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin_dashboard.html", complaints=complaints, queries=queries)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

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
    cur.close()   # ✅ cursor close जरूरी
    conn.close()

    return redirect("/admin/dashboard")


# 🔹 Run
if __name__ == '__main__':
    init_db_safe()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
