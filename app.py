from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# 🔹 Database create
def init_db():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()

        # Complaint table
        c.execute('''CREATE TABLE IF NOT EXISTS complaints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        message TEXT
                    )''')

        # Query table
        c.execute('''CREATE TABLE IF NOT EXISTS queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        message TEXT
                    )''')

# 🔹 Home page
@app.route('/')
def home():
    return render_template('index.html')


# 🔹 Form submit
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    message = request.form.get('message')
    form_type = request.form.get('type')

    print("Form Type:", form_type)  # 🔥 debug ke liye

    if not name or not message:
        return "Please fill all fields ❗"

    try:
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()

            if form_type == "complaint":
                c.execute("INSERT INTO complaints (name, message) VALUES (?, ?)", (name, message))
            else:
                c.execute("INSERT INTO queries (name, message) VALUES (?, ?)", (name, message))

        return '''
<script>
alert("Submitted Successfully ✅");
window.location.href = "/";
</script>
'''

    except Exception as e:
        return f"Error: {str(e)}"


# 🔹 Run app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
