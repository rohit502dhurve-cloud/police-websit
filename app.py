from flask import Flask, render_template, request, redirect, jsonify, session, url_for, send_file
import psycopg2
import pandas as pd
from datetime import datetime, timedelta

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
        Batch_No TEXT,
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS personnel_history (
        id SERIAL PRIMARY KEY,
        personnel_id INT,
        posting_station TEXT,
        outpost TEXT,
        rank TEXT,
        from_date DATE,
        to_date DATE
    )
    """)
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS beatbook (
            id SERIAL PRIMARY KEY,
            police_station TEXT,
            village TEXT,
            beat_officer TEXT,
            sector_officer TEXT,  
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
    conn.commit()
   
    # 🔥 FIX: existing villages (clean)
    try:
        c.execute("SELECT LOWER(TRIM(village)) FROM beatbook")
        existing = [row[0] for row in c.fetchall()]
    except:
        existing = []

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

    file_path = "villages.csv"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    village_name = row.get('village', '').strip().lower()

                    if not village_name:
                        continue

                    # 🔍 Already exists check
                    c.execute(
                        "SELECT 1 FROM beatbook WHERE LOWER(TRIM(village))=%s",
                        (village_name,)
                    )
                    exists = c.fetchone()

                    if not exists:
                        c.execute("""
                            INSERT INTO beatbook 
                            (police_station, village, beat_officer, sector_officer, beat_constable, population, caste, sarpanch, school)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """, (
                            "Lanji",
                            row.get('village', '').strip(),
                            row.get('beat_officer', '').strip(),
                            row.get('sector_officer', '').strip(),   # ✅ NEW
                            row.get('beat_constable', '').strip(),
                            row.get('population', '').strip(),
                            row.get('caste', '').strip(),
                            row.get('sarpanch', '').strip(),
                            row.get('school', '').strip()
                        ))

                except Exception as row_error:
                    print("❌ Row Error:", row_error)
                    continue

        conn.commit()
        print("✅ Villages inserted successfully")

    except Exception as e:
        print("❌ File Error:", e)

    finally:
        c.close()
        conn.close()
def bulk_insert_personnel_safe():
    conn = get_db_connection()
    c = conn.cursor()

    file_path = os.path.join(os.path.dirname(_file_), 'personnel.csv')

    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:   # ✅ FIX: अंदर लाओ
            try:
                name = row.get('Name', '').strip()

                if not name:
                    continue

                raw_date = row.get('Posting_Date', '').strip()

                date_obj = None

                if raw_date:
                    try:
                        date_obj = datetime.strptime(raw_date, "%Y-%m-%d").date()
                    except:
                        try:
                            date_obj = datetime.strptime(raw_date, "%d-%m-%Y").date()
                        except:
                            try:
                                date_obj = datetime.strptime(raw_date, "%d/%m/%Y").date()
                            except:
                                try:
                                    date_obj = datetime.strptime(raw_date, "%d-%m-%y").date()   # ✅ ADD THIS
                                except:
                                    print("❌ Invalid Date Format:", raw_date)
                                    date_obj = None

                               
                c.execute("""
                    INSERT INTO personnel 
                    (Sr_no, Police_Station, Outpost, Rank, Batch_No, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    row['Sr_no'],
                    row['Police_Station'],
                    row['Outpost'],
                    row['Rank'],
                    row['Batch_No'],
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
    outpost = request.args.get('outpost', '')
    work = request.args.get('work', '')
    tenure = request.args.get('tenure', '')


    query = """
    SELECT
        id,
        Sr_no,
        Police_Station,
        Outpost,
        Rank,
        Batch_No,
        Name,
        Posting_Date,
        Posting_Tenure,
        Work_Profile,
        Mobile_number,
        Remark
    FROM personnel
    WHERE 1=1
    """
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

    if outpost:
        query += " AND Outpost = %s"
        values.append(outpost)

    if work:
        query += " AND LOWER(TRIM(Work_Profile)) = %s"
        values.append(work.strip().lower())

    if tenure == "0-1":
        query += " AND Posting_Date >= CURRENT_DATE - INTERVAL '1 year'"

    elif tenure == "1-2":
        query += " AND Posting_Date BETWEEN CURRENT_DATE - INTERVAL '2 year' AND CURRENT_DATE - INTERVAL '1 year'"

    elif tenure == "3+":
        query += " AND Posting_Date <= CURRENT_DATE - INTERVAL '3 year'"



    query += " ORDER BY id ASC"

    c.execute(query, values)

    rows = c.fetchall()

    columns = [desc[0] for desc in c.description]

    data = []
    for row in rows:
        row_dict = dict(zip(columns, row))

        posting_date = row_dict.get("Posting_Date")

        try:
            if posting_date:
                row_dict["posting_tenure"] = calculate_tenure(posting_date)
            else:
                row_dict["posting_tenure"] = ""
        except:
            row_dict["posting_tenure"] = "Invalid"

        data.append(row_dict)


    # 🔽 Dropdown lists
    c.execute("SELECT DISTINCT Police_Station FROM personnel ORDER BY Police_Station")
    ps_list = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT Outpost FROM personnel ORDER BY Outpost")
    outpost_list = [row[0] for row in c.fetchall()]

    c.execute("""
    SELECT DISTINCT TRIM(Work_Profile) 
    FROM personnel 
    ORDER BY TRIM(Work_Profile)
    """)
    work_list = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT Rank FROM personnel ORDER BY Rank")
    rank_list = [row[0] for row in c.fetchall()]

    c.close()
    conn.close()

    return render_template(
        'personnel.html',
        data=data,
        ps_list=ps_list,
        outpost_list=outpost_list,
        work_list=work_list,
        rank_list=rank_list
    )

@app.route('/export_personnel_excel')
def export_personnel_excel():
    conn = get_db_connection()

    query = """
        SELECT Sr_no, Police_Station, Outpost, Rank,
               Batch_No, Name, Posting_Date,
               Work_Profile, Mobile_number, Remark
        FROM personnel
        ORDER BY id ASC
    """

    df = pd.read_sql(query, conn)
    conn.close()

    file_name = "personnel_data.xlsx"
    df.to_excel(file_name, index=False)

    return send_file(file_name, as_attachment=True)


@app.route('/edit_personnel/<int:id>', methods=['GET', 'POST'])
def edit_personnel(id):
    if not session.get("personnel_admin"):
        return redirect("/personnel")
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        Sr_no = request.form['Sr_no']
        Police_Station = request.form['Police_Station']
        Outpost = request.form['Outpost']
        Rank = request.form['Rank']
        Batch_No = request.form['Batch_No']
        Name = request.form['Name']
        Posting_Date = request.form['Posting_Date']

        if Posting_Date:
            Posting_Date = datetime.strptime(Posting_Date, "%d/%m/%Y").date()
        else:
            Posting_Date = None

        tenure = calculate_tenure(Posting_Date) if Posting_Date else ""

        Work_Profile = request.form['Work_Profile']
        Mobile_number = request.form['Mobile_number']
        Remark = request.form['Remark']

        c.execute("""
            UPDATE personnel SET
            Sr_no=%s,
            Police_Station=%s,
            Outpost=%s,
            Rank=%s,
            Batch_No=%s,
            Name=%s,
            Posting_Date=%s,
            Posting_Tenure=%s,
            Work_Profile=%s,
            Mobile_number=%s,
            Remark=%s
            WHERE id=%s
        """, (
            Sr_no, Police_Station, Outpost, Rank, Batch_No,
            Name, Posting_Date, tenure, Work_Profile, Mobile_number, Remark, id
        ))

        conn.commit()
        c.close()
        conn.close()

        return redirect('/personnel')

    c.execute("""
    SELECT
        id,
        Sr_no,
        Police_Station,
        Outpost,
        Rank,
        Batch_No,
        Name,
        Posting_Date,
        Work_Profile,
        Mobile,
        Remark
    FROM personnel
    WHERE id=%s
    """, (id,))

    row = c.fetchone()

    columns = [desc[0].lower() for desc in c.description]
    row = dict(zip(columns, row))


    c.close()
    conn.close()

    return render_template('edit_personnel.html', row=row)

@app.route('/delete_personnel/<int:id>', methods=['POST'])
def delete_personnel(id):
    if not session.get("personnel_admin"):
        return redirect("/personnel")

    conn = get_db_connection()

    c.execute("DELETE FROM personnel WHERE id=%s", (id,))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/personnel')

@app.route('/add_personnel_page')
def add_personnel_page():
    if not session.get("personnel_admin"):
        return redirect("/personnel")

    return render_template('add_personnel.html')

@app.route('/personnel_history/<int:id>')
def personnel_history(id):    
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        SELECT posting_station, outpost, rank, from_date, to_date
        FROM personnel_history
        WHERE personnel_id = %s
        ORDER BY from_date DESC
    """, (id,))

    history = c.fetchall()

    c.close()
    conn.close()

    return render_template('personnel_history.html', history=history, personnel_id=id)

@app.route('/add_posting/<int:personnel_id>', methods=['GET', 'POST'])
def add_posting(personnel_id):
    if request.method == 'POST':
        station = request.form.get('station')
        outpost = request.form.get('outpost')
        rank = request.form.get('rank')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        conn = get_db_connection()
        c = conn.cursor()

        c.execute("""
            INSERT INTO personnel_history
            (personnel_id, posting_station, outpost, rank, from_date, to_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (personnel_id, station, outpost, rank, from_date, to_date))

        conn.commit()
        c.close()
        conn.close()

        return redirect(f'/personnel_history/{personnel_id}')

    return render_template('add_posting.html', personnel_id=personnel_id)

@app.route('/add_personnel', methods=['POST'])
def add_personnel():
    if not session.get("admin"):
        return redirect("/personnel")
    Sr_no = request.form.get('Sr_no')
    Police_Station = request.form.get('Police_Station')
    Outpost = request.form.get('Outpost')
    Rank = request.form.get('Rank')
    Batch_No = request.form.get('Batch_No')
    Name = request.form.get('Name')
    Posting_Date = request.form.get('Posting_Date')

    if Posting_Date:
        try:
            Posting_Date = datetime.strptime(Posting_Date, "%Y-%m-%d").date()
        except:
            try:
                Posting_Date = datetime.strptime(Posting_Date, "%d/%m/%Y").date()
            except:
                Posting_Date = None
    else:
        Posting_Date = None

    Posting_Tenure = calculate_tenure(Posting_Date) if Posting_Date else ""

    Work_Profile = request.form.get('Work_Profile')
    Mobile_number = request.form.get('Mobile_number')
    Remark = request.form.get('Remark')

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO personnel 
        (Sr_no, Police_Station, Outpost, Rank, Batch_No, Name, Posting_Date, Posting_Tenure, Work_Profile, Mobile_number, Remark)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        Sr_no, Police_Station, Outpost, Rank, Batch_No, Name,
        Posting_Date, Posting_Tenure, Work_Profile,
        Mobile_number, Remark
    ))

    conn.commit()
    c.close()
    conn.close()

    return redirect('/personnel')

@app.route('/fix-all-ranks')
def fix_all_ranks():
    conn = get_db_connection()
    c = conn.cursor()

    # 🔹 HEAD CONSTABLE → HC
    c.execute("""
        UPDATE personnel
        SET Rank = 'HC'
        WHERE Rank = 'HEAD CONSTABLE'
    """)

    # 🔹 CONSTABLE → Constable
    c.execute("""
        UPDATE personnel
        SET Rank = 'Constable'
        WHERE Rank = 'CONSTABLE'
    """)

    # 🔹 INSPECTOR → Inspector
    c.execute("""
        UPDATE personnel
        SET Rank = 'Inspector'
        WHERE Rank = 'INSPECTOR'
    """)

    cursor.execute("""
        UPDATE personnel
        SET Police_Station = 'SDOP Office Lanji'
        WHERE Police_Station = 'Sdop Office Lanji'
    """)
   
    conn.commit()
    c.close()
    conn.close()

    return "All Ranks Standardized Successfully ✅"


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

    try:
        c.execute("""
            SELECT * FROM observations 
            WHERE LOWER(TRIM(village)) = %s 
            ORDER BY id DESC
        """, (name,))
        observations = c.fetchall()
    except Exception as e:
        print("Observation Error:", e)
        observations = []

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

@app.route('/debug-personnel')
def debug():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM personnel")
    count = c.fetchone()
    c.close()
    conn.close()
    return str(count)

@app.route('/fix-beatbook')
def fix_beatbook():
    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE beatbook ADD COLUMN sector_officer TEXT;")
    except:
        pass

    conn.commit()
    c.close()
    conn.close()

    return "Sector Officer Column Added ✅"

@app.route('/load-villages')
def load_villages():
    bulk_insert_villages()
    return "Villages Loaded ✅"

@app.route('/health')
def health():
    return "OK", 200
@app.route('/fix-cctns')
def fix_cctns():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE personnel
        SET Work_Profile = 'CCTNS'
        WHERE LOWER(TRIM(Work_Profile)) = 'cctns duty'
    """)

    conn.commit()
    c.close()
    conn.close()

    return "CCTNS Fixed ✅"

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

@app.route("/personnel-admin", methods=["GET", "POST"])
def personnel_admin_login():
    admins = {"personnel_admin": "1234"}

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in admins and admins[username] == password:
            session["personnel_admin"] = True
            return redirect("/personnel")

        return render_template("personnel_admin_login.html", error="Invalid Login")

    return render_template("personnel_admin_login.html")

@app.route("/personnel-admin/logout")
def personnel_admin_logout():
    session.pop("personnel_admin", None)
    return redirect(url_for('home'))

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

@app.route('/fix-personnel-batch')
def fix_personnel_batch():
    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE personnel ADD COLUMN batch_no TEXT;")
        conn.commit()
    except Exception as e:
        print("Error:", e)

    c.close()
    conn.close()

    return "Batch_No column added ✅"

@app.route('/delete-all-personnel')
def delete_all_personnel():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("DELETE FROM personnel")

    conn.commit()
    c.close()
    conn.close()

    return "All Personnel Deleted ✅"

@app.route('/init-db')
def force_init_db():
    init_db_safe()
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

import os

print("📂 Current Directory:", os.getcwd())
print("📁 Files in directory:", os.listdir())

# 🔹 Run
init_db_safe()

# 🔥 FORCE CSV LOAD (no condition)
try:
    print("🚀 Loading villages from CSV...")
    bulk_insert_villages()
    print("✅ CSV LOAD DONE")
except Exception as e:
    print("❌ CSV ERROR:", e)
   
# if os.path.exists("personnel.csv"):
    # bulk_insert_personnel_safe()

if __name__ == '__main__':    
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
