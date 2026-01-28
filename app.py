from flask import Flask, render_template, request, jsonify, session, redirect, url_for,Response
import json
import os
import time
import uuid
from datetime import datetime
from datetime import datetime, timedelta # timedelta lazımdır
from werkzeug.utils import secure_filename
from flask_login import login_required
from tools.CsvJson_Converter import CsvJsonConverter


# --- TOOL IMPORTLARI ---
# Bu faylların tools/ qovluğunda olduğundan əmin ol
from tools.logical_evaluator.algo import lex_and_consider_adjacents, create_ast
from tools.logical_evaluator.truth_table import TruthTable, TooLongError
from tools.logical_evaluator.register import reg_global
from tools.LinuxSimulator.linux_simulator import LinuxTerminal

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'

# Qovluq Ayarları
UPLOAD_FOLDER = os.path.join('static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Fayl Bazaları
USER_DB_FILE = os.path.join('static', 'techhub_users_db.json')
QA_DB_FILE = os.path.join('static', 'techhub_qa_db.json')

# Linux Simulator Initialization
linux_simulator = LinuxTerminal()

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

def load_users():
    return load_json(USER_DB_FILE)

def save_users(users):
    save_json(USER_DB_FILE, users)

def get_timestamp():
    return int(time.time() * 1000)

def format_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime('%d.%m.%Y %H:%M')

app.jinja_env.filters['format_time'] = format_time

# --- ROL SİSTEMİ MƏNTİQİ ---
def update_role_logic(user_data):
    current_role = user_data.get('role', 'Yeni')
    if current_role in ["Staff", "Moderator", "Administrator"]:
        return current_role
    count = user_data.get('answerCount', 0)
    if count >= 700: return "Professional"
    elif count >= 300: return "Çoxbilmiş"
    elif count >= 50: return "Üzv"
    else: return "Yeni"

# --- ƏSAS SƏHİFƏLƏR ---
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

# --- AUTH SİSTEMİ ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET': return redirect(url_for('home'))
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET': return redirect(url_for('home'))
    data = request.get_json()
    email = data.get('email')
    users = load_users()
    if email in users:
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    new_user = {
        "name": data.get('name'), "email": email, "password": data.get('password'),
        "createdAt": get_timestamp(), "about": "", "lastLogin": get_timestamp(),
        "role": "Yeni", "queryCount": 0, "answerCount": 0, "location": "",
        "photo": "../static/images/profile-placeholder.png", "banner": ""
    }
    users[email] = new_user
    save_users(users)
    session['user'] = new_user
    return jsonify({'success': True, 'user': new_user})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

# --- Q&A BÖLMƏSİ (Kateqoriyalar və Detallar) ---
@app.route('/Q&A')
def Q_and_A():
    if 'user' not in session: return redirect(url_for('home'))

    all_questions = load_json(QA_DB_FILE)

    # 1. Son Aktivliklər (Silinməmiş, ən son yaradılan 10 sorğu)
    # Sort edirik: ən yenidən köhnəyə
    sorted_questions = sorted(all_questions, key=lambda x: x['timestamp'], reverse=True)
    recent_activity = sorted_questions[:10]

    return render_template('Q&A.html', user=session['user'], recent_activity=recent_activity)

@app.route('/Q&A/python')
def Q_and_A_python():
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)
    py_questions = [q for q in all_questions if q.get('category') == 'python']
    return render_template('Q&A_python.html', questions=py_questions, user=session['user'])

@app.route('/Q&A/linux')
def Q_and_A_linux():
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)
    linux_questions = [q for q in all_questions if q.get('category') == 'linux']
    return render_template('Q&A_linux.html', questions=linux_questions, user=session['user'])

@app.route('/Q&A/web')
def Q_and_A_web():
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)
    web_questions = [q for q in all_questions if q.get('category') == 'web']
    return render_template('Q&A_web.html', questions=web_questions, user=session['user'])

@app.route('/Q&A/view/<question_id>')
def view_question(question_id):
    if 'user' not in session: return redirect(url_for('home'))
    all_questions = load_json(QA_DB_FILE)
    question = next((q for q in all_questions if q['id'] == question_id), None)
    if not question: return "Sual tapılmadı", 404
    return render_template('Q&A_detail.html', question=question, user=session['user'])

# --- API ENDPOINTS (New Question/Answer) ---
@app.route('/api/new_question', methods=['POST'])
def new_question():
    if 'user' not in session: return jsonify({'success': False}), 401
    try:
        data = request.get_json()
        questions = load_json(QA_DB_FILE)
        new_q = {
            "id": str(uuid.uuid4()), "title": data.get('title'), "content": data.get('content'),
            "category": data.get('category'), "tags": data.get('tags', []),
            "author_email": session['user']['email'], "author_name": session['user'].get('name', 'Adsız'),
            "author_photo": session['user'].get('photo', ''), "timestamp": get_timestamp(),
            "views": 0, "answers": []
        }
        questions.insert(0, new_q)
        save_json(QA_DB_FILE, questions)
        return jsonify({'success': True, 'id': new_q['id']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/add_answer', methods=['POST'])
def add_answer():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    questions = load_json(QA_DB_FILE)
    users = load_users()
    user_email = session['user']['email']

    # Cavabın mətni (HTML formatında gələcək)
    content = data.get('text')
    reply_info = data.get('reply_to', None) # Kimə cavab verilir?

    for q in questions:
        if q['id'] == data.get('question_id'):
            new_ans = {
                "id": str(uuid.uuid4()),
                "text": content, # Artıq HTML olacaq
                "reply_to": reply_info, # Yeni hissə: {name: 'Ali', id: '...'}
                "author_email": user_email,
                "author_name": session['user']['name'],
                "author_photo": session['user'].get('photo', ''),
                "role": users[user_email].get('role', 'Yeni'),
                "timestamp": get_timestamp(),
                "votes": 0
            }
            q['answers'].append(new_ans)
            break
    else: return jsonify({'success': False, 'message': 'Sual tapılmadı'}), 404

    save_json(QA_DB_FILE, questions)
    user = users[user_email]
    user['answerCount'] = user.get('answerCount', 0) + 1
    user['role'] = update_role_logic(user)
    save_users(users)
    session['user'] = user
    return jsonify({'success': True, 'new_role': user['role']})


# --- main.py FAYLINA ƏLAVƏ EDİLƏCƏKLƏR ---

# Editor üçün şəkil yükləmə API-si
@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    if 'user' not in session: return jsonify({'success': False}), 401
    if 'image' not in request.files: return jsonify({'success': False}), 400

    file = request.files['image']
    if file.filename == '': return jsonify({'success': False}), 400

    if file:
        filename = secure_filename(str(uuid.uuid4()) + "_" + file.filename)
        # Yükləmə qovluğunu yoxlayaq
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        # Frontend-ə şəklin URL-ni qaytarırıq
        return jsonify({'success': True, 'url': f'../static/images/uploads/{filename}'})


# Sorğunu silmək (Point 2)
@app.route('/api/delete_question', methods=['POST'])
def delete_question():
    if 'user' not in session: return jsonify({'success': False, 'message': 'Giriş edilməyib'}), 401
    data = request.get_json()
    q_id = data.get('id')

    questions = load_json(QA_DB_FILE)
    users = load_users()
    current_user = session['user']
    user_role = users.get(current_user['email'], {}).get('role', 'Yeni')

    # Silinəcək sualı tapırıq
    q_to_delete = next((q for q in questions if q['id'] == q_id), None)
    if not q_to_delete: return jsonify({'success': False, 'message': 'Sual tapılmadı'}), 404

    # İcazə yoxlanışı: Sahibi, Moderator və ya Administrator
    if current_user['email'] == q_to_delete['author_email'] or user_role in ['Moderator', 'Administrator', 'Staff']:
        questions = [q for q in questions if q['id'] != q_id]
        save_json(QA_DB_FILE, questions)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'İcazəniz yoxdur'}), 403


# Cavabı silmək (Point 3)
@app.route('/api/delete_answer', methods=['POST'])
def delete_answer():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    q_id = data.get('question_id')
    ans_id = data.get('answer_id')

    questions = load_json(QA_DB_FILE)
    users = load_users()
    current_user = session['user']
    user_role = users.get(current_user['email'], {}).get('role', 'Yeni')

    question = next((q for q in questions if q['id'] == q_id), None)
    if not question: return jsonify({'success': False}), 404

    # Cavabı tapırıq
    answer = next((a for a in question['answers'] if a['id'] == ans_id), None)
    if not answer: return jsonify({'success': False}), 404

    # İcazə yoxlanışı
    if current_user['email'] == answer['author_email'] or user_role in ['Moderator', 'Administrator', 'Staff']:
        question['answers'] = [a for a in question['answers'] if a['id'] != ans_id]
        save_json(QA_DB_FILE, questions)
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'İcazəniz yoxdur'}), 403

# --- TOOLS API (Logic & Linux) ---
@app.route('/linux-sim', methods=["POST"])
def linux_sim():
    data = request.get_json()
    output = linux_simulator.run_command(data.get("command", ""))
    if output == "__exit__": return jsonify({"output": "Closing terminal..."})
    return jsonify({"output": output, "path": linux_simulator.current_path})

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

"""
    DEPRECATED - Yeni func asagida(init_interpreter)
"""
@app.route('/python-compiler')
def python_comp():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('py_comp.html')

@app.route('/tools/python3')
#@login_required 
def init_interpreter(): 
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

@app.route('/logic')
def old_logic(): return redirect(url_for('logic'))

# --- PROFILE UPDATE ---
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({'success': False}), 401
    users = load_users()
    user_data = users.get(session['user']['email'])
    
    if location := request.form.get('location'): user_data['location'] = location
    
    old_p, new_p, conf_p = request.form.get('old_password'), request.form.get('new_password'), request.form.get('confirm_password')
    if new_p:
        if user_data['password'] == old_p and new_p == conf_p: user_data['password'] = new_p
        else: return jsonify({'success': False, 'message': 'Şifrə xətası'}), 400

    safe_name = secure_filename(user_data['name'])
    if 'profile_photo' in request.files:
        file = request.files['profile_photo']
        if file.filename:
            path = f"{safe_name}_profile{os.path.splitext(file.filename)[1]}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], path))
            user_data['photo'] = f"../static/images/uploads/{path}"
            
    users[user_data['email']] = user_data
    save_users(users)
    session['user'] = user_data
    return jsonify({'success': True})

@app.route("/convert", methods=["POST"])
def convert_file():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "File is required (form-data field name: file)."}), 400

    ext = os.path.splitext(f.filename)[1].lower()

    delimiter = request.form.get("delimiter")
    if delimiter in ("", None):
        delimiter = None
    elif delimiter not in (",", ";", "\t", "|"):
        return jsonify({"error": "Invalid delimiter. Use one of: , ; tab |"}), 400

    conv = CsvJsonConverter()

    try:
        if ext == ".csv":
            result = conv.csv_to_json(f.stream, delimiter=delimiter)
            return Response(
                result,
                mimetype="application/json",
                headers={"Content-Disposition": "attachment; filename=converted.json"},
            )

        if ext == ".json":
            result = conv.json_to_csv(f.stream)
            return Response(
                result,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=converted.csv"},
            )

        return jsonify({"error": "Only .csv and .json are supported."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# --- YENİ FUNKSİONALLIQLAR ÜÇÜN API-LƏR ---

# 1. TƏKMİLLƏŞDİRİLMİŞ FİLTRLƏMƏ API-Sİ (5-ci bənd üçün)
# Səhifələmə və Filtrləmə API-si
@app.route('/api/get_filtered_questions', methods=['POST'])
def get_filtered_questions():
    data = request.get_json()
    filter_type = data.get('filter', 'categories')
    page = int(data.get('page', 1))

    limit = 10
    skip = (page - 1) * limit

    all_questions = load_json(QA_DB_FILE)
    filtered_data = []

    if filter_type == 'populyar':
        # Votes sayına görə çoxdan aza
        filtered_data = sorted(all_questions, key=lambda x: x.get('votes', 0), reverse=True)

    elif filter_type == 'cavabsiz':
        # Cavabı 0 olanlar, yeni tarixdən köhnəyə
        filtered_data = [q for q in all_questions if len(q.get('answers', [])) == 0]
        filtered_data.sort(key=lambda x: x['timestamp'], reverse=True)

    elif filter_type == 'yeni-sorgu':
        # Son 24 saat (86400000 ms)
        now_ms = int(time.time() * 1000)
        filtered_data = [q for q in all_questions if (now_ms - q['timestamp']) < 86400000]
        filtered_data.sort(key=lambda x: x['timestamp'], reverse=True)

    # Pagination
    total = len(filtered_data)
    paginated = filtered_data[skip: skip + limit]
    has_more = (skip + limit) < total

    return jsonify({'success': True, 'data': paginated, 'has_more': has_more})


if __name__ == '__main__':
    app.run(debug=True)