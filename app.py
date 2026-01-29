import os
import json
import time
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.utils import secure_filename

# --- ARAÇ IMPORTLARI ---
from tools.logical_evaluator.algo import lex_and_consider_adjacents, create_ast
from tools.logical_evaluator.truth_table import TruthTable, TooLongError
from tools.logical_evaluator.register import reg_global
from tools.LinuxSimulator.linux_simulator import LinuxTerminal
from tools.CsvJson_Converter import CsvJsonConverter

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = os.path.join('static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Local JSON file paths
USERS_DB_FILE = os.path.join('static', 'techhub_users_db.json')
QA_DB_FILE = os.path.join('static', 'techhub_qa_db.json')

# Linux Simulator
linux_simulator = LinuxTerminal()

# --- 📡 LOCAL JSON FUNCTIONS ---

def load_json(db_type_key):
    """Load data from local JSON file"""
    db_type = 'users' if 'user' in str(db_type_key).lower() else 'qa'
    db_file = USERS_DB_FILE if db_type == 'users' else QA_DB_FILE
    
    if not os.path.exists(db_file):
        return {} if db_type == 'users' else []
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {} if db_type == 'users' else []

def save_json(db_type_key, data):
    """Save data to local JSON file"""
    db_type = 'users' if 'user' in str(db_type_key).lower() else 'qa'
    db_file = USERS_DB_FILE if db_type == 'users' else QA_DB_FILE
    
    try:
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Save Error: {e}")
        return False

# Yardımcılar
def load_users(): return load_json("users")
def save_users(users): return save_json("users", users)
def get_timestamp(): return int(time.time() * 1000)
def format_time(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime('%d.%m.%Y %H:%M')

app.jinja_env.filters['format_time'] = format_time

# --- 🖼️ LOGGING ---
@app.before_request
def log_request_info():
    if request.path.startswith('/static'): return
    print(f"\n--- 📥 {request.method} {request.path} ---")
    if request.is_json:
        try:
            data = request.get_json()
            if data and 'password' in data: 
                safe_data = data.copy()
                safe_data['password'] = '******'
                print(f"JSON: {json.dumps(safe_data, indent=2)}")
            else:
                print(f"JSON: {json.dumps(data, indent=2)}")
        except: pass

@app.after_request
def log_response_info(response):
    if not request.path.startswith('/static'):
        print(f"--- 📤 Status: {response.status} ---")
    return response

# --- 🎖️ ROL MƏNTİQİ ---
def update_role_logic(user_data):
    current_role = user_data.get('role', 'Yeni')
    if current_role in ["Staff", "Moderator", "Administrator"]: return current_role
    count = user_data.get('answerCount', 0)
    if count >= 700: return "Professional"
    elif count >= 300: return "Çoxbilmiş"
    elif count >= 50: return "Üzv"
    else: return "Yeni"

# --- 🔐 AUTH VE ANA SAYFALAR ---
@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template('menu.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/api/user')
def get_user():
    if 'user' in session: return jsonify(session['user'])
    return jsonify(None)

@app.route('/profile')
def profile():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('profile.html', user=session['user'])

@app.route('/tools')
def tools():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('tools.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    users = load_users()
    email, pwd = data.get('email'), data.get('password')
    if email in users and users[email]['password'] == pwd:
        users[email]['lastLogin'] = get_timestamp()
        session['user'] = users[email]
        save_users(users)
        return jsonify({'success': True, 'user': users[email]})
    return jsonify({'success': False, 'message': 'Hatalı giriş'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    users = load_users()
    if email in users: return jsonify({'success': False, 'message': 'Email already registered'}), 400
    new_user = {
        "name": data.get('name'), "email": email, "password": data.get('password'),
        "createdAt": get_timestamp(), "role": "Yeni", "answerCount": 0, "queryCount": 0,
        "photo": "../static/images/profile-placeholder.png", "about": "", "location": ""
    }
    users[email] = new_user
    save_users(users)
    session['user'] = new_user
    return jsonify({'success': True, 'user': new_user})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

# --- ❓ Q&A SİSTEMİ ---
@app.route('/Q&A')
def Q_and_A():
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json("qa")
    sorted_questions = sorted(all_questions, key=lambda x: x['timestamp'], reverse=True)
    return render_template('Q&A.html', user=session['user'], recent_activity=sorted_questions[:10])

@app.route('/Q&A/<category>')
def Q_and_A_category(category):
    if 'user' not in session: return redirect(url_for('home'))
    if category not in ['python', 'linux', 'web']: return "Kategoriya tapılmadı", 404
    all_questions = load_json("qa")
    cat_questions = [q for q in all_questions if q.get('category') == category]
    return render_template(f'Q&A_{category}.html', questions=cat_questions, user=session['user'])

@app.route('/Q&A/view/<question_id>')
def view_question(question_id):
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json("qa")
    question = next((q for q in all_questions if q['id'] == question_id), None)
    if not question: return "Sual tapılmadı", 404
    return render_template('Q&A_detail.html', question=question, user=session['user'])

@app.route('/api/new_question', methods=['POST'])
def new_question():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    questions = load_json("qa")
    new_q = {
        "id": str(uuid.uuid4()), "title": data.get('title'), "content": data.get('content'),
        "category": data.get('category'), "author_email": session['user']['email'],
        "author_name": session['user'].get('name', 'Adsız'), 
        "author_photo": session['user'].get('photo', ''),
        "timestamp": get_timestamp(), "views": 0, "answers": []
    }
    questions.insert(0, new_q)
    save_json("qa", questions)
    return jsonify({'success': True, 'id': new_q['id']})

@app.route('/api/add_answer', methods=['POST'])
def add_answer():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    questions = load_json("qa")
    users = load_users()
    user_email = session['user']['email']
    q_id = data.get('question_id')
    
    for q in questions:
        if q['id'] == q_id:
            new_ans = {
                "id": str(uuid.uuid4()), "text": data.get('text'),
                "reply_to": data.get('reply_to'),
                "author_email": user_email, "author_name": session['user']['name'],
                "author_photo": session['user'].get('photo', ''),
                "role": users[user_email].get('role', 'Yeni'),
                "timestamp": get_timestamp(), "votes": 0
            }
            q['answers'].append(new_ans)
            break
    else: return jsonify({'success': False, 'message': 'Sual tapılmadı'}), 404
    
    save_json("qa", questions)
    user = users[user_email]
    user['answerCount'] = user.get('answerCount', 0) + 1
    user['role'] = update_role_logic(user)
    save_users(users)
    session['user'] = user
    return jsonify({'success': True, 'new_role': user['role']})

@app.route('/api/get_filtered_questions', methods=['POST'])
def get_filtered_questions():
    data = request.get_json()
    filter_type = data.get('filter', 'categories')
    page = int(data.get('page', 1))
    limit, skip = 10, (page - 1) * 10
    all_questions = load_json("qa")
    filtered_data = []
    if filter_type == 'populyar':
        filtered_data = sorted(all_questions, key=lambda x: x.get('votes', 0), reverse=True)
    elif filter_type == 'cavabsiz':
        filtered_data = [q for q in all_questions if len(q.get('answers', [])) == 0]
        filtered_data.sort(key=lambda x: x['timestamp'], reverse=True)
    elif filter_type == 'yeni-sorgu':
        filtered_data = sorted(all_questions, key=lambda x: x['timestamp'], reverse=True)
    
    total = len(filtered_data)
    paginated = filtered_data[skip: skip + limit]
    return jsonify({'success': True, 'data': paginated, 'has_more': (skip + limit) < total})

@app.route('/api/delete_question', methods=['POST'])
def delete_question():
    if 'user' not in session: return jsonify({'success': False, 'message': 'Giriş edilməyib'}), 401
    data = request.get_json()
    q_id = data.get('id')
    questions = load_json("qa")
    users = load_users()
    current_user = session['user']
    user_role = users.get(current_user['email'], {}).get('role', 'Yeni')
    q_to_delete = next((q for q in questions if q['id'] == q_id), None)
    if not q_to_delete: return jsonify({'success': False, 'message': 'Sual tapılmadı'}), 404
    if current_user['email'] == q_to_delete['author_email'] or user_role in ['Moderator', 'Administrator', 'Staff']:
        questions = [q for q in questions if q['id'] != q_id]
        save_json("qa", questions)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'İcazəniz yoxdur'}), 403

@app.route('/api/delete_answer', methods=['POST'])
def delete_answer():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    q_id, ans_id = data.get('question_id'), data.get('answer_id')
    questions = load_json("qa")
    users = load_users()
    current_user = session['user']
    user_role = users.get(current_user['email'], {}).get('role', 'Yeni')
    question = next((q for q in questions if q['id'] == q_id), None)
    if not question: return jsonify({'success': False}), 404
    answer = next((a for a in question['answers'] if a['id'] == ans_id), None)
    if not answer: return jsonify({'success': False}), 404
    if current_user['email'] == answer['author_email'] or user_role in ['Moderator', 'Administrator', 'Staff']:
        question['answers'] = [a for a in question['answers'] if a['id'] != ans_id]
        save_json("qa", questions)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'İcazəniz yoxdur'}), 403

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    if 'user' not in session: return jsonify({'success': False}), 401
    if 'image' not in request.files: return jsonify({'success': False}), 400
    file = request.files['image']
    if file.filename == '': return jsonify({'success': False}), 400
    filename = secure_filename(str(uuid.uuid4()) + "_" + file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    return jsonify({'success': True, 'url': f'../static/images/uploads/{filename}'})

# --- 🛠️ DİĞER ARAÇLAR ---
@app.route('/linux-sim', methods=["POST"])
def linux_sim():
    data = request.get_json()
    output = linux_simulator.run_command(data.get("command", ""))
    return jsonify({"output": output, "path": linux_simulator.current_path})

@app.route('/python-compiler')
@app.route('/tools/python3')
def python_comp():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('py_comp.html')

@app.route('/tools/logic')
def logic():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('logic.html')

@app.route('/tools/terminal')
def terminal():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('terminal.html')

@app.route('/tools/converter')
def converter():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('converter.html')

@app.route('/api/logic/evaluate', methods=['POST'])
def evaluate_logic():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    expression = data.get('expression', '').replace("->", "$").replace("<=>", "#")
    try:
        reg_global.reset()
        tokens = lex_and_consider_adjacents(expression)
        ast = create_ast(tokens)
        tt = TruthTable(reg_global.get_headers(), reg_global.objs, ast)
        tt.generate()
        tt.simplify()
        headers = tt.headers + ['X']
        rows = [[(1 if val else 0) for val in row.ls] + [1 if row.value else 0] for row in tt.rows]
        return jsonify({'success': True, 'headers': headers, 'rows': rows, 'simplified': tt.simplified_str})
    except TooLongError: return jsonify({'success': False, 'message': 'Limit 6 dəyişəndir.'}), 400
    except Exception as e: return jsonify({'success': False, 'message': str(e)}), 400

@app.route("/convert", methods=["POST"])
def convert_file():
    f = request.files.get("file")
    if not f or not f.filename: return jsonify({"error": "File is required."}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    delimiter = request.form.get("delimiter") or None
    conv = CsvJsonConverter()
    try:
        if ext == ".csv":
            result = conv.csv_to_json(f.stream, delimiter=delimiter)
            return Response(result, mimetype="application/json", headers={"Content-Disposition": "attachment; filename=converted.json"})
        if ext == ".json":
            result = conv.json_to_csv(f.stream)
            return Response(result, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=converted.csv"})
        return jsonify({"error": "Only .csv and .json are supported."}), 400
    except Exception as e: return jsonify({"error": str(e)}), 400

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({'success': False}), 401
    users = load_users()
    user_data = users.get(session['user']['email'])
    if not user_data: return jsonify({'success': False}), 404
    
    if location := request.form.get('location'): user_data['location'] = location
    if about := request.form.get('about'): user_data['about'] = about
    
    old_p, new_p, conf_p = request.form.get('old_password'), request.form.get('new_password'), request.form.get('confirm_password')
    if new_p:
        if user_data['password'] == old_p and new_p == conf_p: user_data['password'] = new_p
        else: return jsonify({'success': False, 'message': 'Şifrə xətası'}), 400

    if 'profile_photo' in request.files:
        file = request.files['profile_photo']
        if file.filename:
            filename = secure_filename(f"{user_data['name']}_profile_{str(uuid.uuid4())[:8]}{os.path.splitext(file.filename)[1]}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user_data['photo'] = f"../static/images/uploads/{filename}"
            
    users[user_data['email']] = user_data
    save_users(users)
    session['user'] = user_data
    return jsonify({'success': True})

if __name__ == '__main__':
    print(f"\n🚀 SİSTEM BAŞLIYOR...")
    print(f"📁 LOCAL MODE - Using JSON files")
    app.run(host='0.0.0.0', port=5000, debug=True)
