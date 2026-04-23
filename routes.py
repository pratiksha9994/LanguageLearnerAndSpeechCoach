from flask import Blueprint, render_template, request, redirect, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import difflib

main = Blueprint('main', __name__)

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT
    )
    ''')

    # Progress table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        module TEXT,
        score INTEGER
    )
    ''')

    conn.commit()
    conn.close()


# ---------------- HOME ---------------- #

@main.route('/')
def home():
    return redirect('/login')


# ---------------- REGISTER ---------------- #

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_pw)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists"

        conn.close()
        return redirect('/login')

    return render_template('register.html')


# ---------------- LOGIN ---------------- #

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            session['user'] = username
            return redirect('/language')
        else:
            return "Invalid Credentials"

    return render_template('login.html')


# ---------------- LANGUAGE ---------------- #

@main.route('/language', methods=['GET', 'POST'])
def language():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        session['language'] = request.form['language']
        session['current_level'] = "beginner"
        return redirect('/course')

    return render_template('language.html')


# ---------------- COURSE ---------------- #

@main.route('/course')
def course():
    if 'user' not in session:
        return redirect('/login')

    return render_template('course.html')


# ---------------- LESSON ---------------- #

@main.route('/lesson')
def lesson():
    if 'user' not in session:
        return redirect('/login')

    module = request.args.get('module', '1')

    lessons = {
        "1": ["Hello", "Hi", "Good Morning", "What is your name?"],
        "2": ["How are you?", "I am fine", "Nice to meet you"],
        "3": ["I am a student", "I live in India", "I am 20 years old"],
        "4": ["One, Two, Three", "What time is it?"],
        "5": ["Food", "Water", "Go", "Come"],
        "6": ["I am", "You are", "This is"]
    }

    content = lessons.get(module, [])

    return render_template('lesson.html', content=content, module=module)


# ---------------- QUIZ ---------------- #

@main.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user' not in session:
        return redirect('/login')

    module = request.args.get('module', '1')

    questions = {
        "1": {"What is Hello?": "hello"},
        "2": {"How are you?": "fine"},
        "3": {"I am a ___": "student"},
        "4": {"1,2,3... next?": "4"},
        "5": {"Drink ___": "water"},
        "6": {"I ___ a student": "am"}
    }

    module_questions = questions.get(module, {})

    if request.method == 'POST':
        score = 0

        for q, ans in module_questions.items():
            user_ans = request.form.get(q)

            if user_ans and user_ans.lower() == ans:
                score += 1

        # SAVE PROGRESS
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO progress (username, module, score) VALUES (?, ?, ?)",
            (session['user'], module, score)
        )

        conn.commit()
        conn.close()

        return render_template("result.html", score=score)

    return render_template("quiz.html", questions=module_questions, module=module)


# ---------------- SPEECH ---------------- #

@main.route('/speech')
def speech():
    if 'user' not in session:
        return redirect('/login')

    return render_template('speech.html')


# ---------------- AI SPEECH ---------------- #

@main.route('/evaluate_speech', methods=['POST'])
def evaluate_speech():
    data = request.get_json()

    spoken = data['speech'].lower()
    expected = data['expected'].lower()

    score = difflib.SequenceMatcher(None, spoken, expected).ratio()
    score = round(score * 100, 2)

    return jsonify({"score": score})


# ---------------- DASHBOARD ---------------- #

@main.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT module, score FROM progress WHERE username=?",
        (session['user'],)
    )

    data = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', data=data)


# ---------------- LOGOUT ---------------- #

@main.route('/logout')
def logout():
    session.clear()
    return redirect('/login')