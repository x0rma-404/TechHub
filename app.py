from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import time
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# --- TOOL IMPORTLARI ---
try:
    from tools.logical_evaluator.algo import lex_and_consider_adjacents, create_ast
    from tools.logical_evaluator.truth_table import TruthTable, TooLongError
    from tools.logical_evaluator.register import reg_global
    from tools.LinuxSimulator.linux_simulator import LinuxTerminal
except ImportError as e:
    print(f"Xəbərdarlıq: Bəzi modullar tapılmadı: {e}")

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'

# Qovluqlar
UPLOAD_FOLDER = os.path.join('static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Fayl yolları
USER_DB_FILE = os.path.join('static', 'techhub_users_db.json')
QA_DB_FILE = os.path.join('static', 'techhub_qa_db.json')

# Linux Simulator Initialization
try:
    linux_simulator = LinuxTerminal()
except:
    linux_simulator = None

# --- DATABASE FUNKSİYALARI ---
def load_json(file_path):
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

def load_users(): return load_json(USER_DB_FILE)
def save_users(users): save_json(USER_DB_FILE, users)

def get_timestamp(): return int(time.time() * 1000)

def format_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime('%d.%m.%Y %H:%M')

app.jinja_env.filters['format_time'] = format_time

# --- ROL MƏNTİQİ ---
def update_role_logic(user_data):
    current_role = user_data.get('role', 'Yeni')
    if current_role in ["Staff", "Moderator", "Administrator"]:
        return current_role
    count = user_data.get('answerCount', 0)
    if count >= 700: return "Professional"
    elif count >= 300: return "Çoxbilmiş"
    elif count >= 50: return "Üzv"
    return "Yeni"

# --- CORE ROUTES ---
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
    return jsonify(session.get('user'))

# --- AUTH SYSTEM ---
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email, password = data.get('email'), data.get('password')
        users = load_users()

        if email in users and users[email]['password'] == password:
            user = users[email]
            user.setdefault('role', 'Yeni')
            user.setdefault('answerCount', 0)
            user['lastLogin'] = get_timestamp()
            session['user'] = user
            save_users(users)
            return jsonify({'success': True, 'user': user})
        return jsonify({'success': False, 'message': 'Email və ya şifrə yanlışdır'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    users = load_users()
    if email in users:
        return jsonify({'success': False, 'message': 'Email artıq mövcuddur'}), 400
    
    new_user = {
        "name": data.get('name'), "email": email, "password": data.get('password'),
        "createdAt": get_timestamp(), "lastLogin": get_timestamp(),
        "role": "Yeni", "queryCount": 0, "answerCount": 0, "about": "",
        "location": "", "photo": "../static/images/profile-placeholder.png", "banner": ""
    }
    users[email] = new_user
    save_users(users)
    session['user'] = new_user
    return jsonify({'success': True, 'user': new_user})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

# --- PROFILE & TOOLS ---
@app.route('/profile')
def profile():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('profile.html', user=session['user'])

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({'success': False}), 401
    users = load_users()
    u_email = session['user']['email']
    user_data = users.get(u_email)

    if not user_data: return jsonify({'success': False}), 404

    # Məlumat yeniləmə
    user_data['location'] = request.form.get('location', user_data.get('location'))
    
    # Şifrə dəyişmə
    old_p = request.form.get('old_password')
    new_p = request.form.get('new_password')
    if new_p and user_data['password'] == old_p:
        user_data['password'] = new_p

    # Şəkil yükləmə
    safe_name = secure_filename(user_data['name'])
    for key in ['profile_photo', 'banner_photo']:
        if key in request.files:
            file = request.files[key]
            if file and file.filename != '':
                ext = os.path.splitext(file.filename)[1]
                suffix = 'profile' if 'profile' in key else 'banner'
                fname = f"{safe_name}_{suffix}{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                user_data['photo' if suffix == 'profile' else 'banner'] = f"../static/images/uploads/{fname}"

    users[u_email] = user_data
    save_users(users)
    session['user'] = user_data
    return jsonify({'success': True})

# --- Q&A SYSTEM ---
@app.route('/Q&A')
def Q_and_A():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('Q&A.html', user=session['user'])

@app.route('/Q&A/<category>')
def Q_and_A_cat(category):
    if 'user' not in session: return redirect(url_for('home'))
    all_q = load_json(QA_DB_FILE)
    filtered = [q for q in all_q if q.get('category') == category]
    return render_template(f'Q&A_{category}.html', questions=filtered, user=session['user'])

@app.route('/api/add_answer', methods=['POST'])
def add_answer():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    questions = load_json(QA_DB_FILE)
    users = load_users()
    u_email = session['user']['email']

    for q in questions:
        if q['id'] == data.get('question_id'):
            ans = {
                "id": str(uuid.uuid4()), "text": data.get('text'),
                "author_email": u_email, "author_name": session['user']['name'],
                "timestamp": get_timestamp(), "votes": 0
            }
            q['answers'].append(ans)
            break
    
    save_json(QA_DB_FILE, questions)
    
    # Rol yeniləmə
    users[u_email]['answerCount'] = users[u_email].get('answerCount', 0) + 1
    users[u_email]['role'] = update_role_logic(users[u_email])
    save_users(users)
    session['user'] = users[u_email]
    
    return jsonify({'success': True, 'new_role': users[u_email]['role']})

# --- LOGIC EVALUATOR API ---
@app.route('/api/logic/evaluate', methods=['POST'])
def evaluate_logic():
    if 'user' not in session: return jsonify({'success': False}), 401
    try:
        data = request.get_json()
        expr = data.get('expression', '').replace("->", "$").replace("<=>", "#")
        reg_global.reset()
        tokens = lex_and_consider_adjacents(expr)
        ast = create_ast(tokens)
        tt = TruthTable(reg_global.get_headers(), reg_global.objs, ast)
        tt.generate()
        tt.simplify()
        
        rows = [[1 if v else 0 for v in r.ls] + [1 if r.value else 0] for r in tt.rows]
        return jsonify({'success': True, 'headers': tt.headers + ['X'], 'rows': rows, 'simplified': tt.simplified_str})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/linux-sim', methods=['POST'])
def linux_sim_cmd():
    if not linux_simulator: return jsonify({"output": "Error"})
    data = request.get_json()
    output = linux_simulator.run_command(data.get("command", ""))
    return jsonify({"output": output, "path": linux_simulator.current_path})

if __name__ == '__main__':
    app.run(debug=True)