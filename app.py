from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import psycopg2
import os
import csv
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

    c.execute('''
    CREATE TABLE IF NOT EXISTS personnel (
        id SERIAL PRIMARY KEY,
        Sr_no TEXT,
        Ps_Outpost TEXT,
        Rank TEXT,
        Name TEXT,
        Posting_Date DATE,
        Posting_Tenure TEXT,
        Work_Profile TEXT,
        Mobile_number TEXT,
        Remark TEXT
)
''')

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
        village TEXT,
        submitted_by TEXT
    )
    ''')
    try:
        c.execute("ALTER TABLE observations ADD COLUMN submitted_by TEXT")
        conn.commit()
    except:
        conn.rollback()



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

def bulk_insert_villages():
    conn = get_db_connection()
    c = conn.cursor()

    file_path = os.path.join(os.path.dirname(__file__), 'villages.csv')

    with open(file_path, 'r', encoding='utf-8') as file:

        reader = csv.DictReader(file)

        for row in reader:
            village_name = row['village'].strip().lower()

            # 🔍 check already exists
            c.execute("SELECT 1 FROM beatbook WHERE LOWER(TRIM(village))=%s", (village_name,))
            exists = c.fetchone()

            if not exists:
                c.execute("""
                    INSERT INTO beatbook 
                    (police_station, village, beat_officer, beat_constable, population, caste, sarpanch, school)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    "Lanji",
                    row['village'],
                    row['beat_officer'],
                    row['beat_constable'],
                    row['population'],
                    row['caste'],
                    row['sarpanch'],
                    row['school']
                ))

    conn.commit()
    c.close()
    conn.close()

    print("✅ All new villages inserted successfully")
def bulk_insert_personnel_safe():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS personnel (
            id SERIAL PRIMARY KEY,
            Sr_no TEXT,
            Ps_Outpost TEXT,
            Rank TEXT,
            Name TEXT,
            Posting_Date DATE,
            Posting_Tenure TEXT,
            Work_Profile TEXT,
            Mobile_number TEXT,
            Remark TEXT
        )
    """)
    conn.commit()

    file_path = os.path.join(os.path.dirname(__file__), 'personnel.csv')

    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            name = row.get('Name')

            if not name:
               continue
            c.execute("SELECT 1 FROM personnel WHERE Name=%s", (row['Name'],))
            exists = c.fetchone()

            if not exists:
                from datetime import datetime

                raw_date = row['Posting_Date']
                date_obj = datetime.strptime(raw_date.strip(), "%d-%m-%Y").date()
                
                c.execute("""
                    INSERT INTO personnel 
                    (Sr_no, Ps_Outpost, Rank, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    row['Sr_no'],
                    row['Ps_Outpost'],
                    row['Rank'],
                    row['Name'],
                    date_obj,
                    row['Posting_Tenure'],
                    row['Work_Profile'],
                    row['Mobile_number'],
                    row['Remark']
                ))

    conn.commit()
    c.close()
    conn.close()


# 🔹 Dummy Users (same)
users = {
    "beat_1": {
    "password": "123",
    "rank": "SI",
    "villages": ["lanji", "bisoni", "katangi", "rampura", "sogalpur","manpur","tekri","thanegaon","purvatola","khandafari","dulhapur","satitola","chichtola","saheki","bagdi","peepalgaon khurd","pouni","kosmara","kholmara","kosamdehi","kashitola","bakramundi","neemtola","kalimati",]   # example
},
"beat_2": {
    "password": "123",
    "rank": "SI",
    "villages": ["paldongri", "ameda", "sadra", "borikhurd", "fofsa", "siregaon", "ladsa", "jivnara", "dahegaon", "keregaon", "kareja", "devalgaon", "kumarikhurd", "kumarikalan", "singola", "dighori", "savrikala", "umri", "kulpa", "karanja", "bapdi", "parsodi", "paraswada", "chichamtola",]       # example
},
"beat_3": {
    "password": "123",
    "rank": "SI",
    "villages": ["bolegaon", "benegaon", "ghoti-ghusmara", "kochewahi", "bhimodi", "mohara", "mohjhari", "bhanegaon", "temni (choundhatola)", "chikhlamali", "sihari", "aava", "churli", "dorli", "tedva", "binjhalgaon", "pipalgaon kala", "sirri", "atariya", "mendra", "bhakkutola", "borikala", "itora", "kakodi", "khajri", "kalpathri", "pathargaon", "badhgaon", "pondi",]              # example
},

     "hc_narendra": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["manpur","tekri","thanegaon","purvatola","khandafari"]
    },
     "hc_dhanlal": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["lanji","bisoni","katangi","rampura","sogalpur"]
    },
     "c_mohshin": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["dulhapur","satitola","chichtola","saheki","bagdi"]
    },
     "c_surendra": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["peepalgaon khurd","pouni","kosmara","kholmara","kosamdehi"]
    },
     "c_nemichand": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["kashitola","bakramundi","neemtola","kalimati"]
    },
     "hc_pawan": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["paldongri","ameda","sadra","borikhurd"]
    },
     "c_anil": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["fofsa","siregaon","ladsa"]
    },
     "c_manohar": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["jivnara","dahegaon","keregaon","kharegaon","kareja","devalgaon"]
    },
    "c_vijay": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["kumhari khurd","kumhari kala","singola","dighori","savrikala","umri"]
    },
    "c_dilip": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["kulpa","karanja","bapdi","parsodi","paraswada","chichamtola"]
    },
    "c_ashutosh": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["bolegaon","benegaon","ghoti-ghusmara","kochewahi","bhimodi"]
    },
    "c_sujeet": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["mohara","mohjhari","manegaon","temni (choundhatola)","chikhlamali"]
    },
    "c_roopsingh": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["sihari","aava","churli","dorli","tedwa","binjhalgaon"]
    },
    "c_jitendra": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["pipalgaon kala","sirri","atariya","mendra","bhakkutola","borikala"]
    },
    "c_pawan": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["itora","sunarkakodi","khajri","kalpathri","pathargaon","badhgaon","pondi"]
    },
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

            if users[username]["rank"] in ["CONSTABLE", "SI"]:
                session["assigned_villages"] = users[username].get("villages", [])

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
    if session.get("rank") in ["CONSTABLE", "SI"]:
        villages = session.get("assigned_villages", [])
    else:
        c.execute("SELECT village FROM beatbook")
        villages = [row[0] for row in c.fetchall()]

   
    c.close()
    conn.close()

    return render_template('dashboard.html', villages=villages)

@app.route('/personnel')
def personnel():
    conn = get_db_connection()
    c = conn.cursor()

    search = request.args.get('search', '')
    rank = request.args.get('rank', '')
    ps = request.args.get('ps', '')

    query = "SELECT * FROM personnel WHERE 1=1"
    values = []

    if search:
        query += " AND Name ILIKE %s"
        values.append(f"%{search}%")

    if rank and rank != "ALL":
        query += " AND Rank = %s"
        values.append(rank)

    if ps:
        query += " AND Ps_Outpost = %s"
        values.append(ps)

    query += " ORDER BY id DESC"

    c.execute(query, values)
    data = c.fetchall()

    c.close()
    conn.close()

    return render_template('personnel.html', data=data)


@app.route('/add_personnel', methods=['POST'])
def add_personnel():
    Sr_no = request.form.get('Sr_no')
    Ps_Outpost = request.form.get('Ps_Outpost')
    Rank = request.form.get('Rank')
    Name = request.form.get('Name')
    Posting_Date = request.form.get('Posting_Date')
    Posting_Tenure = request.form.get('Posting_Tenure')
    Work_Profile = request.form.get('Work_Profile')
    Mobile_number = request.form.get('Mobile_number')
    Remark = request.form.get('Remark')

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO personnel 
        (Sr_no, Ps_Outpost, Rank, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (Sr_no, Ps_Outpost, Rank, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/personnel')

    Sr_no = request.form.get('Sr_no')
    Ps_Outpost = request.form.get('Ps_Outpost')
    Rank = request.form.get('Rank')
    Name = request.form.get('Name')
    Posting_Date = request.form.get('Posting_Date')
    Posting_Tenure = request.form.get('Posting_Tenure')
    Work_Profile = request.form.get('Work_Profile')
    Mobile_number = request.form.get('Mobile_number')
    Remark = request.form.get('Remark')

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO personnel 
        (Sr_no, Ps_Outpost, Rank, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (Sr_no, Ps_Outpost, Rank, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/personnel')

    conn = get_db_connection()
    c = conn.cursor()

    search = request.args.get('search', '')
    rank = request.args.get('rank', '')
    ps = request.args.get('ps', '')

    query = "SELECT * FROM personnel WHERE 1=1"
    values = []

    if search:
        query += " AND Name ILIKE %s"
        values.append(f"%{search}%")

    if rank and rank != "ALL":
        query += " AND Rank = %s"
        values.append(rank)

    if ps:
        query += " AND Ps_Outpost = %s"
        values.append(ps)

    query += " ORDER BY id DESC"

    c.execute(query, values)
    data = c.fetchall()

    c.close()
    conn.close()

    return render_template('personnel.html', data=data)



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
    return redirect("/") 

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
        INSERT INTO observations (text, created_at, village, submitted_by) 
        VALUES (%s, NOW() + INTERVAL '5 hours 30 minutes', %s, %s)
    """, (observation, village, submitted_by))

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
    return redirect("/")

@app.route('/load-personnel')
def load_personnel():
    init_db()
    bulk_insert_personnel_safe()
    return "Personnel Loaded ✅"

@app.route('/init-db')
def force_init_db():
    init_db()
    return "DB Created ✅"

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
init_db_safe()
if os.path.exists("villages.csv"):
    bulk_insert_villages()   # 🔥 IMPORTANT (1 बार चलाना है)

if __name__ == '__main__':    
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
