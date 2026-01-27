from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import time
import uuid # Bunu unutma!
from datetime import datetime
from werkzeug.utils import secure_filename
from tools.logical_evaluator.algo import lex_and_consider_adjacents, create_ast
from tools.logical_evaluator.truth_table import TruthTable, TooLongError
from tools.logical_evaluator.register import reg_global
from tools.LinuxSimulator.linux_simulator import LinuxTerminal
# Initialize Flask app
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = os.path.join('static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

USER_DB_FILE = os.path.join('static', 'techhub_users_db.json')
QA_DB_FILE = os.path.join('static', 'techhub_qa_db.json')
linux_simulator = LinuxTerminal()

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users):
    with open(DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)


# --- KÖMƏKÇİ FUNKSİYALAR (DATABASE) ---
def load_json(file_path):
    # Fayl yoxdursa və ya tamamilə boşdursa (0 byte)
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return {} if 'users' in file_path else []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"JSON oxuma xətası: {e}")
        return {} if 'users' in file_path else []


def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_timestamp():
    return int(time.time() * 1000)


def format_time(timestamp):
    # Millisaniyəni oxunaqlı tarixə çevirir
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime('%d.%m.%Y %H:%M')


# Jinja2 üçün tarix filteri
app.jinja_env.filters['format_time'] = format_time


# --- ROL SİSTEMİ MƏNTİQİ ---
def update_role_logic(user_data):
    current_role = user_data.get('role', 'Yeni')
    # Toxunulmaz rollar
    if current_role in ["Staff", "Moderator", "Administrator"]:
        return current_role

    count = user_data.get('answerCount', 0)

    if count >= 700:
        return "Professional"
    elif count >= 300:
        return "Çoxbilmiş"
    elif count >= 50:
        return "Üzv"
    else:
        return "Yeni"

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('menu.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/api/user')
def get_user():
    if 'user' in session:
        return jsonify(session['user'])
    return jsonify(None)

@app.route("/linux-sim", methods=["POST"])
def linux_sim():
    data = request.get_json()
    command = data.get("command", "")
    output = linux_simulator.run_command(command)
    if output == "__exit__":
        return jsonify({"output": "Closing the terminal... Goodbye!"})
    return jsonify({
        "output": output,
        "path": linux_simulator.current_path
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect(url_for('home'))
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    users = load_users()

    if email in users and users[email]['password'] == password:
        # Rol yoxlaması və ya dataların tamlığı üçün update
        user = users[email]
        # Əgər yeni sistemə keçmisənsə, köhnə userlərdə bu sahələr yoxdursa əlavə edirik
        if 'role' not in user: user['role'] = 'Yeni'
        if 'answerCount' not in user: user['answerCount'] = 0

        user['lastLogin'] = get_timestamp()
        session['user'] = user
        save_json(USER_DB_FILE, users)
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'message': 'Email və ya şifrə yanlışdır'}), 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return redirect(url_for('home'))
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    users = load_users()
    if email in users:
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    new_user = {
        "name": name, "email": email, "password": password, 
        "createdAt": int(time.time() * 1000), "about": "",
        "lastLogin": int(time.time() * 1000),
        # YENİ SİSTEM SAHƏLƏRİ
        "role": "Yeni",
        "queryCount": 0,
        "answerCount": 0,
        "location": "",
        "photo": "../static/images/profile-placeholder.png",  # Default şəkil
        "banner": ""
    }
    users[email] = new_user
    save_users(users)
    session['user'] = new_user
    return jsonify({'success': True, 'user': new_user})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('profile.html', user=session['user'])

@app.route('/tools')
def tools():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('tools.html')


# --- Q&A SİSTEMİ (TƏKMİLLƏŞDİRİLMİŞ) ---

@app.route('/Q&A')
def Q_and_A():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('Q&A.html', user=session['user'])


# Kateqoriyalar üçün tək bir funksiya istifadə edə bilərik, amma sənin strukturunu qoruyuram
@app.route('/Q&A/python')
def Q_and_A_python():
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)
    # Yalnız Python suallarını filterləyirik
    py_questions = [q for q in all_questions if q['category'] == 'python']
    return render_template('Q&A_python.html', questions=py_questions, user=session['user'])


@app.route('/Q&A/linux')
def Q_and_A_linux():
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)
    linux_questions = [q for q in all_questions if q['category'] == 'linux']
    return render_template('Q&A_linux.html', questions=linux_questions, user=session['user'])


@app.route('/Q&A/web')
def Q_and_A_web():
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)
    web_questions = [q for q in all_questions if q['category'] == 'web']
    return render_template('Q&A_web.html', questions=web_questions, user=session['user'])


# Sual Detalları (Dinamik ID ilə)
@app.route('/Q&A/view/<question_id>')
def view_question(question_id):
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)

    # Sualları axtar
    question = next((q for q in all_questions if q['id'] == question_id), None)
    if not question:
        return "Sual tapılmadı", 404

    return render_template('Q&A_detail.html', question=question, user=session['user'])


# --- API ENDPOINTS (Yeni Sual və Cavab) ---

@app.route('/api/new_question', methods=['POST'])
def new_question():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş edilməyib'}), 401

    try:
        data = request.get_json()
        users = load_json(USER_DB_FILE)
        user_email = session['user']['email']

        questions = load_json(QA_DB_FILE)

        # Əgər questions hər hansı səbəbdən siyahı deyilsə, onu siyahı et
        if not isinstance(questions, list):
            questions = []

        new_q = {
            "id": str(uuid.uuid4()),
            "title": data.get('title'),
            "content": data.get('content'),
            "category": data.get('category'),
            "tags": data.get('tags', []),
            "author_email": user_email,
            "author_name": session['user'].get('name', 'Adsız'),
            "author_photo": session['user'].get('photo', ''),
            "timestamp": get_timestamp(),
            "views": 0,
            "answers": []
        }

        questions.insert(0, new_q)
        save_json(QA_DB_FILE, questions)

        return jsonify({'success': True, 'id': new_q['id']})
    except Exception as e:
        # Xətanı terminalda görə bilmək üçün
        print(f"SERVER ERROR: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/add_answer', methods=['POST'])
def add_answer():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    q_id = data.get('question_id')
    text = data.get('text')

    questions = load_json(QA_DB_FILE)
    users = load_json(USER_DB_FILE)
    user_email = session['user']['email']

    # Sualı tap
    for q in questions:
        if q['id'] == q_id:
            new_ans = {
                "id": str(uuid.uuid4()),
                "text": text,
                "author_email": user_email,
                "author_name": session['user']['name'],
                "author_photo": session['user'].get('photo', ''),
                "role": users[user_email].get('role', 'Yeni'),  # Cavab verənin o anki rolu
                "timestamp": get_timestamp(),
                "votes": 0
            }
            q['answers'].append(new_ans)
            break
    else:
        return jsonify({'success': False, 'message': 'Sual tapılmadı'}), 404

    save_json(QA_DB_FILE, questions)

    # Userin cavab sayını artır və ROLU HESABLA
    if user_email in users:
        user = users[user_email]
        user['answerCount'] = user.get('answerCount', 0) + 1

        # Rolu yoxla və dəyiş
        new_role = update_role_logic(user)
        role_changed = (new_role != user.get('role', 'Yeni'))
        user['role'] = new_role

        save_json(USER_DB_FILE, users)
        session['user'] = user  # Sessiyanı yenilə

        return jsonify({
            'success': True,
            'new_role': new_role,
            'role_changed': role_changed
        })

    return jsonify({'success': True})

@app.route('/python-compiler')
def python_comp():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('py_comp.html')

@app.route('/tools/logic')
def logic():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('logic.html')
@app.route('/tools/terminal')
def terminal():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('terminal.html')
@app.route('/logic')
def old_logic():
    return redirect(url_for('logic'))

@app.route('/api/logic/evaluate', methods=['POST'])
def evaluate_logic():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Daxil olmamısınız'}), 401
    data = request.get_json()
    expression = data.get('expression', '')
    if not expression:
        return jsonify({'success': False, 'message': 'İfadə daxil edilməyib'}), 400
    expression = expression.replace("->", "$")
    expression = expression.replace("<=>", "#")
    try:
        reg_global.reset()
        tokens = lex_and_consider_adjacents(expression)
        ast = create_ast(tokens)
        tt = TruthTable(reg_global.get_headers(), reg_global.objs, ast)
        tt.generate()
        tt.simplify()
        headers = tt.headers + ['X']
        rows = []
        for row in tt.rows:
            row_data = [1 if val else 0 for val in row.ls]
            row_data.append(1 if row.value else 0)
            rows.append(row_data)
        return jsonify({
            'success': True,
            'headers': headers,
            'rows': rows,
            'simplified': tt.simplified_str
        })
    except TooLongError:
        return jsonify({'success': False, 'message': 'Çox sayda dəyişən! Limit 6-dır.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Xəta: {str(e)}'}), 400

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Daxil olmamısınız'}), 401
    users = load_users()
    current_email = session['user']['email']
    user_data = users.get(current_email)
    if not user_data:
        return jsonify({'success': False, 'message': 'İstifadəçi tapılmadı'}), 404
    location = request.form.get('location')
    if location:
        user_data['location'] = location
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    if new_password:
        if not old_password:
             return jsonify({'success': False, 'message': 'Şifrəni dəyişmək üçün köhnə şifrəni yazmalısınız'}), 400
        if user_data['password'] != old_password:
            return jsonify({'success': False, 'message': 'Köhnə şifrə yanlışdır'}), 400
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Yeni şifrələr uyğun gəlmir'}), 400
        user_data['password'] = new_password
    safe_name = secure_filename(user_data['name'])
    if 'profile_photo' in request.files:
        file = request.files['profile_photo']
        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1]
            filename = f"{safe_name}_profile{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user_data['photo'] = f"../static/images/uploads/{filename}"
    if 'banner_photo' in request.files:
        file = request.files['banner_photo']
        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1]
            filename = f"{safe_name}_banner{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user_data['banner'] = f"../static/images/uploads/{filename}"
    users[current_email] = user_data
    save_users(users)
    session['user'] = user_data
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)