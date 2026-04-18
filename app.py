from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import psycopg2
from datetime import datetime

def calculate_tenure(posting_date):

    if not posting_date:
        return ""

    # 🔥 अगर string है तो convert करो
    if isinstance(posting_date, str):
        try:
            posting_date = datetime.strptime(posting_date, "%Y-%m-%d").date()
        except:
            try:
                posting_date = datetime.strptime(posting_date, "%d-%m-%Y").date()
            except:
                return "Invalid Date"

    # अगर datetime है तो date बनाओ
    if isinstance(posting_date, datetime):
        posting_date = posting_date.date()

    today = datetime.today().date()
    diff = today - posting_date

    years = diff.days // 365
    months = (diff.days % 365) // 30
    days = (diff.days % 365) % 30

    return f"{years} Years {months} Months {days} Days"


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
        Police_Station TEXT,
        Outpost TEXT,
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

    file_path = os.path.join(os.path.dirname(__file__), 'personnel.csv')

    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:   # ✅ FIX: अंदर लाओ
            try:
                name = row.get('Name', '').strip()

                if not name:
                    continue

                raw_date = row.get('Posting_Date', '').strip()

                if raw_date == "":
                    date_obj = None
                else:
                    try:
                        date_obj = datetime.strptime(raw_date, "%d-%m-%Y").date()
                    except:
                        try:
                            date_obj = datetime.strptime(raw_date, "%d-%m-%y").date()
                        except:
                            try:
                                date_obj = datetime.strptime(raw_date, "%Y-%m-%d").date()
                            except:
                                date_obj = None

                # 🔍 Check exists
                c.execute("SELECT 1 FROM personnel WHERE Name=%s", (name,))
                exists = c.fetchone()

                if exists:
                    c.execute("""
                        UPDATE personnel SET
                        Sr_no=%s,
                        Police_Station=%s,
                        Outpost=%s,
                        Rank=%s,
                        Posting_Date=%s,
                        Work_Profile=%s,
                        Mobile_number=%s,
                        Remark=%s
                        WHERE Name=%s
                    """, (
                        row['Sr_no'],
                        row['Police_Station'],
                        row['Outpost'],
                        row['Rank'],
                        date_obj,
                        row['Work_Profile'],
                        row['Mobile_number'],
                        row['Remark'],
                        name
                    ))
                else:
                    c.execute("""
                        INSERT INTO personnel 
                        (Sr_no, Police_Station, Outpost, Rank, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        row['Sr_no'],
                        row['Police_Station'],
                        row['Outpost'],
                        row['Rank'],
                        name,
                        date_obj,
                        "",
                        row['Work_Profile'],
                        row['Mobile_number'],
                        row['Remark']
                    ))

            except Exception as e:
                print("Row Error:", e)
                continue

    conn.commit()
    c.close()
    conn.close()

    print("✅ Personnel Updated Successfully")




# 🔹 Dummy Users (same)
users = {
    "beat_lanji": {
        "password": "123",
        "rank": "SI",
        "villages": ["lanji", "bisoni", "katangi", "rampura", "sogalpur","manpur","tekri","thanegaon","purvatola","khandafari","dulhapur","satitola","chichtola","saheki","bagdi","peepalgaon khurd","pouni","kosmara","kholmara","kosamdehi","kashitola","bakramundi","neemtola","kalimati"]
    },
    "beat_kulpa.karanja": {
        "password": "123",
        "rank": "SI",
        "villages": ["paldongri", "ameda", "sadra", "borikhurd", "fofsa", "siregaon", "ladsa", "jivnara", "dahegaon", "keregaon", "kareja", "devalgaon", "kumarikhurd", "kumarikalan", "singola", "dighori", "savrikala", "umri", "kulpa", "karanja", "bapdi", "parsodi", "paraswada", "chichamtola"]
    },
    "beat_bhanegaon.mohjhari": {
        "password": "123",
        "rank": "SI",
        "villages": ["bolegaon", "benegaon", "ghoti-ghusmara", "kochewahi", "bhimodi", "mohara", "mohjhari", "bhanegaon", "temni (choundhatola)", "chikhlamali", "sihari", "aava", "churli", "dorli", "tedva", "binjhalgaon", "pipalgaon kala", "sirri", "atariya", "mendra", "bhakkutola", "borikala", "itora", "kakodi", "khajri", "kalpathri", "pathargaon", "badhgaon", "pondi"]
    },
    "8225946160": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Narendra Sonve",
        "villages": ["manpur","tekri","thanegaon","purvatola","khandafari"]
    },
    "9424943406": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Dhanlal Lilhare",
        "villages": ["lanji","bisoni","katangi","rampura","sogalpur"]
    },
    "9806644195": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Mohshin Khan",
        "villages": ["dulhapur","satitola","chichtola","saheki","bagdi"]
    },
    "9669000629": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Surendra Panche",
        "villages": ["peepalgaon khurd","pouni","kosmara","kholmara","kosamdehi"]
    },
    "9340530959": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Nemichand Sepat",
        "villages": ["kashitola","bakramundi","neemtola","kalimati"]
    },
    "9425140102": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Pawan Marskole",
        "villages": ["paldongri","ameda","sadra","borikhurd"]
    },
    "c_anil": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["fofsa","siregaon","ladsa"]
    },
    "9691744570": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Manohar Jhadekar",
        "villages": ["jivnara","dahegaon","keregaon","kharegaon","kareja","devalgaon"]
    },
    "9340549440": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Vijay Sisodiya",
        "villages": ["kumhari khurd","kumhari kala","singola","dighori","savrikala","umri"]
    },
    "8815001286": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Dilip Yadav",
        "villages": ["kulpa","karanja","bapdi","parsodi","paraswada","chichamtola"]
    },
    "7000502578": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Ashutosh Singh",
        "villages": ["bolegaon","benegaon","ghoti-ghusmara","kochewahi","bhimodi"]
    },
    "7999412916": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Sujeet Pal",
        "villages": ["mohara","mohjhari","manegaon","temni (choundhatola)","chikhlamali"]
    },
    "9826336422": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Roopsingh Rawat",
        "villages": ["sihari","aava","churli","dorli","tedwa","binjhalgaon"]
    },
    "c_jitendra": {
        "password": "123",
        "rank": "CONSTABLE",
        "villages": ["pipalgaon kala","sirri","atariya","mendra","bhakkutola","borikala"]
    },
    "7694048643": {
        "password": "123",
        "rank": "CONSTABLE",
        "name": "Pawan Dhakad",
        "villages": ["itora","sunarkakodi","khajri","kalpathri","pathargaon","badhgaon","pondi"]
    },
    "sho_lanji": {
        "password": "123",
        "rank": "SHO",
        "name": "Thana Prabhari Lanji"
    }
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
            session["name"] = users[username].get("name", username)

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
    if session.get("rank") == "CONSTABLE":
        villages = session.get("assigned_villages", [])

    elif session.get("rank") == "SI":
        villages = session.get("assigned_villages", [])

    elif session.get("rank") == "SHO":
        c.execute("SELECT village FROM beatbook")
        villages = [row[0] for row in c.fetchall()]

    else:
        villages = []


   
    c.close()
    conn.close()

    return render_template('dashboard.html', villages=villages)

@app.route('/sho/report', methods=['GET'])
def sho_report():
    if "user" not in session or session.get("rank") != "SHO":
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()

    # 🔹 Filters
    village_filter = request.args.get("village", "").strip().lower()
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    query = "SELECT village, text, submitted_by, created_at FROM observations WHERE 1=1"
    params = []

    if village_filter:
        query += " AND LOWER(TRIM(village)) = %s"
        params.append(village_filter)

    if start_date:
        start_obj = datetime.strptime(start_date, "%Y-%m-%d")
        query += " AND created_at >= %s"
        params.append(start_obj)

    if end_date:
        end_obj = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(hours=23, minutes=59, seconds=59)
        query += " AND created_at <= %s"
        params.append(end_obj)


    query += " ORDER BY created_at DESC"

    c.execute(query, params)
    observations = c.fetchall()

    # 🔹 Fetch all villages for filter dropdown
    c.execute("SELECT village FROM beatbook ORDER BY village")
    villages = [row[0] for row in c.fetchall()]

    c.close()
    conn.close()

    return render_template('sho_report.html', observations=observations, villages=villages, selected_village=village_filter, start_date=start_date, end_date=end_date)

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
        query += " AND (Police_Station = %s OR Outpost = %s)"
        values.append(ps)
        values.append(ps)

    query += " ORDER BY id ASC"

    c.execute(query, values)
    data = c.fetchall()

    new_data = []
    for row in data:
        row = list(row)
        posting_date = row[6]

        if posting_date:
            row[7] = calculate_tenure(posting_date)

        new_data.append(row)

    c.close()
    conn.close()

    return render_template('personnel.html', data=new_data)



@app.route('/delete_personnel/<int:id>')
def delete_personnel(id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("DELETE FROM personnel WHERE id=%s", (id,))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/personnel')

@app.route('/add_personnel', methods=['POST'])
def add_personnel():
    Sr_no = request.form.get('Sr_no')
    Police_Station = request.form.get('Police_Station')
    Outpost = request.form.get('Outpost')
    Rank = request.form.get('Rank')
    Name = request.form.get('Name')
    Posting_Date = request.form.get('Posting_Date')

    if Posting_Date:
        Posting_Date = datetime.strptime(Posting_Date, "%Y-%m-%d").date()
    else:
        Posting_Date = None
    Posting_Tenure = ""
    Work_Profile = request.form.get('Work_Profile')
    Mobile_number = request.form.get('Mobile_number')
    Remark = request.form.get('Remark')

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO personnel 
        (Sr_no, Police_Station, Outpost, Rank, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        Sr_no, Police_Station, Outpost, Rank, Name,
        Posting_Date, Posting_Tenure, Work_Profile,
        Mobile_number, Remark
    ))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/personnel')


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
    submitted_by = session.get("name")

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

@app.route('/fix-personnel')
def fix_personnel():
    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE personnel ADD COLUMN Police_Station TEXT;")
    except:
        pass

    try:
        c.execute("ALTER TABLE personnel ADD COLUMN Outpost TEXT;")
    except:
        pass

    conn.commit()
    c.close()
    conn.close()

    return "Columns Fixed ✅"


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
