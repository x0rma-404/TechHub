import os
import json
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.utils import secure_filename
import ollama

# --- ARAÇ IMPORTLARI ---
from tools.logical_evaluator.algo import lex_and_consider_adjacents, create_ast
from tools.logical_evaluator.truth_table import TruthTable, TooLongError
from tools.logical_evaluator.register import reg_global
from tools.LinuxSimulator.linux_simulator import LinuxTerminal
from tools.CsvJson_Converter.csv_json_converter import CsvJsonConverter
from tools.floating_point.floating_point import FloatingPoint
from tools.ip_subnet.subcalc import SubnetCalculator

# --- DASTAN AI ---
from dastan.ai_logic import get_ai_config, get_ai_response

# --- GITHUB ---
from github import Github, GithubException
from cryptography.fernet import Fernet

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'
import threading
db_lock = threading.Lock()

#Ollama pull llama3.2:3b
ollama.pull("llama3.2:3b")

UPLOAD_FOLDER = os.path.join('static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Local JSON file paths
USERS_DB_FILE = os.path.join('static', 'techhub_users_db.json')
QA_DB_FILE = os.path.join('static', 'techhub_qa_db.json')
PROJECTS_DB_FILE = os.path.join('static', 'techhub_projects.json')

# Initialize tools
linux_simulator = LinuxTerminal()
floating_point_converter = FloatingPoint()

# --- GITHUB ENCRYPTION ---
# ⚠️ PRODUCTION'DA BUNU ENVIRONMENT VARIABLE YAPMANIZ GEREKİYOR!
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_token(token):
    """GitHub token'ı şifrele"""
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    """GitHub token'ı çöz"""
    try:
        return cipher_suite.decrypt(encrypted_token.encode()).decode()
    except:
        return None

# --- 📡 LOCAL JSON FUNCTIONS ---

def load_json(db_type_key):
    """Load data from local JSON file"""
    if 'user' in str(db_type_key).lower():
        db_file = USERS_DB_FILE
        default_data = {}
    elif 'project' in str(db_type_key).lower():
        db_file = PROJECTS_DB_FILE
        default_data = []
    else:
        db_file = QA_DB_FILE
        default_data = []
    
    if not os.path.exists(db_file):
        return default_data
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_data

def save_json(db_type_key, data):
    """Save data to local JSON file"""
    if 'user' in str(db_type_key).lower():
        db_file = USERS_DB_FILE
    elif 'project' in str(db_type_key).lower():
        db_file = PROJECTS_DB_FILE
    else:
        db_file = QA_DB_FILE
    
    try:
        with db_lock:
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Save Error: {e}")
        return False

# Yardımcılar
def load_users(): return load_json("users")
def save_users(users): return save_json("users", users)
def load_projects(): return load_json("projects")
def save_projects(projects): return save_json("projects", projects)
def get_timestamp(): return int(time.time() * 1000)
def format_time(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime('%d.%m.%Y %H:%M')

app.jinja_env.filters['format_time'] = format_time

def strip_html(text):
    import re
    if not text: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

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
    all_questions = load_json("qa")
    sorted_questions = sorted(all_questions, key=lambda x: x['timestamp'], reverse=True)
    recent_activity = sorted_questions[:3]
    return render_template('index.html', recent_activity=recent_activity)

@app.route('/api/user')
def get_user():
    if 'user' in session: return jsonify(session['user'])
    return jsonify(None)

@app.route('/api/qa-count')
def get_qa_count():
    all_questions = load_json("qa")
    return jsonify({'count': len(all_questions)})

@app.route('/profile')
def profile():
    if 'user' not in session: return redirect(url_for('home'))
    
    # Get user's projects
    projects = load_projects()
    user_projects = [p for p in projects if p.get('author_email') == session['user']['email']]
    
    return render_template('profile.html', user=session['user'], projects=user_projects)

@app.route('/tools')
def tools():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('tools.html')

@app.route('/github')
def github():
    if 'user' not in session: return redirect(url_for('home'))
    return redirect(url_for('github_settings'))

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
        "photo": "", "about": "", "location": "", "github_token": None, "github_username": None
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
    if category not in ['python', 'linux', 'web', 'java', 'cpp', 'go', 'ruby', 'db', 'security', 'mobile']: return "Kategoriya tapılmadı", 404
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

    # --- AUTO AI ANSWER (ASYNCHRONOUS) ---
    def generate_async_answer(q_id, title, content, category):
        import threading
        def worker():
            try:
                config = get_ai_config()
                clean_content = strip_html(content)
                ai_content = f"Question Title: {title}\nCategory: {category}\nContent: {clean_content}"
                ai_response_text = get_ai_response(ai_content)
                
                if ai_response_text:
                    ai_ans = {
                        "id": str(uuid.uuid4()), 
                        "text": ai_response_text,
                        "reply_to": None,
                        "author_email": "ai@techhub.com", 
                        "author_name": "Dastan",
                        "author_photo": "/static/images/logo.png",
                        "role": "AI Assistant",
                        "timestamp": get_timestamp() + 1000, 
                        "votes": 0
                    }
                    current_questions = load_json("qa")
                    for q in current_questions:
                        if q['id'] == q_id:
                            q['answers'].append(ai_ans)
                            break
                    save_json("qa", current_questions)
            except Exception as e:
                print(f"⚠️ Auto-answer error: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    generate_async_answer(new_q['id'], new_q['title'], new_q['content'], new_q['category'])

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
    
    # --- AUTO AI REPLY (IF MENTIONED OR REPLIED TO) ---
    ans_text = data.get('text', '')
    parent_id = data.get('reply_to')
    
    should_reply = "dastan" in ans_text.lower()
    
    if not should_reply and parent_id:
        for q in questions:
            for a in q.get('answers', []):
                if a['id'] == parent_id and a.get('author_email') == "ai@techhub.com":
                    should_reply = True
                    break
            if should_reply: break

    if should_reply:
        def worker():
            try:
                context_q = next((q for q in load_json("qa") if q['id'] == q_id), None)
                if not context_q: return
                
                parent_text = ""
                if parent_id:
                    parent_ans = next((a for a in context_q.get('answers', []) if a['id'] == parent_id), None)
                    if parent_ans: parent_text = strip_html(parent_ans['text'])

                prompt_context = f"Topic/Question: {context_q['title']}\n"
                if parent_text:
                    prompt_context += f"You said earlier: {parent_text}\n"
                prompt_context += f"User ({session['user']['name']}) says: {strip_html(ans_text)}"
                
                ai_response = get_ai_response(prompt_context, system_prompt_override="You are Dastan. A user mentioned you or replied to your comment in a Q&A thread. Provide a short, direct, and helpful reply based on the context.")
                
                if ai_response:
                    ai_ans = {
                        "id": str(uuid.uuid4()), "text": ai_response, "reply_to": new_ans['id'],
                        "author_email": "ai@techhub.com", "author_name": "Dastan",
                        "author_photo": "/static/images/logo.png", "role": "AI Assistant",
                        "timestamp": get_timestamp() + 1000, "votes": 0
                    }
                    curr_q = load_json("qa")
                    for q in curr_q:
                        if q['id'] == q_id:
                            q['answers'].append(ai_ans)
                            break
                    save_json("qa", curr_q)
            except Exception as e:
                print(f"❌ Auto-reply error: {e}")
        import threading
        threading.Thread(target=worker, daemon=True).start()

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

# --- 🔗 GITHUB INTEGRATION ---

@app.route('/github/settings')
def github_settings():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    github_connected = user.get('github_token') is not None
    github_username = user.get('github_username', '')
    
    return render_template('github_settings.html', 
                         github_connected=github_connected,
                         github_username=github_username)

@app.route('/api/github/save-token', methods=['POST'])
def save_github_token():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş yapmalısınız'}), 401
    
    data = request.get_json()
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Token boş olamaz'}), 400
    
    try:
        # Token'ı doğrula
        g = Github(token)
        user = g.get_user()
        github_username = user.login
        
        # Kullanıcı bilgilerini güncelle
        users = load_users()
        user_email = session['user']['email']
        
        users[user_email]['github_token'] = encrypt_token(token)
        users[user_email]['github_username'] = github_username
        
        save_users(users)
        session['user'] = users[user_email]
        
        return jsonify({
            'success': True,
            'message': f'GitHub hesabınız ({github_username}) başarıyla bağlandı!',
            'username': github_username
        })
        
    except GithubException as e:
        return jsonify({
            'success': False,
            'message': 'Geçersiz GitHub token! Lütfen kontrol edin.'
        }), 400

@app.route('/api/github/remove-token', methods=['POST'])
def remove_github_token():
    if 'user' not in session:
        return jsonify({'success': False}), 401
    
    users = load_users()
    user_email = session['user']['email']
    
    users[user_email]['github_token'] = None
    users[user_email]['github_username'] = None
    
    save_users(users)
    session['user'] = users[user_email]
    
    return jsonify({'success': True, 'message': 'GitHub bağlantısı kaldırıldı'})

@app.route('/api/github/repos')
def get_github_repos():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş yapmalısınız'}), 401
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    encrypted_token = user.get('github_token')
    if not encrypted_token:
        return jsonify({'success': False, 'message': 'GitHub token bulunamadı'}), 400
    
    token = decrypt_token(encrypted_token)
    if not token:
        return jsonify({'success': False, 'message': 'Token çözülemedi'}), 400
    
    try:
        g = Github(token)
        gh_user = g.get_user()
        repos = gh_user.get_repos()
        
        # Mevcut projeleri al (hangisi zaten import edilmiş)
        projects = load_projects()
        imported_repos = {p.get('github_repo') for p in projects if p.get('author_email') == user_email}
        
        repo_list = []
        for repo in repos:
            repo_list.append({
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'private': repo.private,
                'html_url': repo.html_url,
                'created_at': repo.created_at.strftime('%Y-%m-%d'),
                'updated_at': repo.updated_at.strftime('%Y-%m-%d'),
                'imported': repo.full_name in imported_repos
            })
        
        return jsonify({'success': True, 'repos': repo_list})
        
    except GithubException as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/github/import', methods=['POST'])
def import_from_github():
    if 'user' not in session:
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    repo_full_name = data.get('repo_full_name')
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    encrypted_token = user.get('github_token')
    if not encrypted_token:
        return jsonify({'success': False, 'message': 'GitHub token bulunamadı'}), 400
    
    token = decrypt_token(encrypted_token)
    
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        
        # Proje listesini yükle
        projects = load_projects()
        
        # Yeni proje oluştur
        new_project = {
            'id': str(uuid.uuid4()),
            'title': repo.name,
            'description': repo.description or 'GitHub\'dan içe aktarıldı',
            'tech_stack': repo.language or 'Unknown',
            'demo_url': repo.homepage or '',
            'github_url': repo.html_url,
            'github_repo': repo.full_name,
            'author_email': user_email,
            'author_name': user.get('name', 'Adsız'),
            'author_photo': user.get('photo', ''),
            'timestamp': get_timestamp(),
            'stars': repo.stargazers_count,
            'synced': True
        }
        
        projects.append(new_project)
        save_projects(projects)
        
        return jsonify({
            'success': True,
            'message': f'{repo.name} başarıyla içe aktarıldı!'
        })
        
    except GithubException as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/github/push', methods=['POST'])
def push_to_github():
    if 'user' not in session:
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    project_id = data.get('project_id')
    repo_name = data.get('repo_name')
    is_private = data.get('is_private', False)
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    encrypted_token = user.get('github_token')
    if not encrypted_token:
        return jsonify({'success': False, 'message': 'GitHub token bulunamadı'}), 400
    
    token = decrypt_token(encrypted_token)
    
    # Projeyi bul
    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return jsonify({'success': False, 'message': 'Proje bulunamadı'}), 404
    
    try:
        g = Github(token)
        gh_user = g.get_user()
        
        # Yeni repo oluştur
        repo = gh_user.create_repo(
            name=repo_name,
            description=project.get('description', ''),
            private=is_private,
            auto_init=True
        )
        
        # README.md oluştur
        readme_content = f"""# {project['title']}

{project.get('description', '')}

## 🛠️ Tech Stack
{project.get('tech_stack', 'N/A')}

## 🔗 Links
- **Demo**: {project.get('demo_url', 'N/A')}

---
*This project was created on TechHub platform.*
"""
        
        repo.create_file(
            "README.md",
            "Initial commit from TechHub",
            readme_content
        )
        
        # Projeyi güncelle
        for p in projects:
            if p['id'] == project_id:
                p['github_url'] = repo.html_url
                p['github_repo'] = repo.full_name
                p['synced'] = True
                break
        
        save_projects(projects)
        
        return jsonify({
            'success': True,
            'repo_url': repo.html_url,
            'message': f'Proje {repo.html_url} adresine yüklendi!'
        })
        
    except GithubException as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/github/sync/<project_id>', methods=['POST'])
def sync_from_github(project_id):
    if 'user' not in session:
        return jsonify({'success': False}), 401
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    encrypted_token = user.get('github_token')
    if not encrypted_token:
        return jsonify({'success': False, 'message': 'GitHub token bulunamadı'}), 400
    
    token = decrypt_token(encrypted_token)
    
    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return jsonify({'success': False, 'message': 'Proje bulunamadı'}), 404
    
    github_repo = project.get('github_repo')
    if not github_repo:
        return jsonify({'success': False, 'message': 'Bu proje GitHub ile bağlantılı değil'}), 400
    
    try:
        g = Github(token)
        repo = g.get_repo(github_repo)
        
        # Projeyi güncelle
        for p in projects:
            if p['id'] == project_id:
                p['title'] = repo.name
                p['description'] = repo.description or p.get('description', '')
                p['tech_stack'] = repo.language or p.get('tech_stack', 'Unknown')
                p['stars'] = repo.stargazers_count
                break
        
        save_projects(projects)
        
        return jsonify({
            'success': True,
            'message': 'Proje başarıyla güncellendi!'
        })
        
    except GithubException as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/github/projects')
def github_projects():
    """Display all synced GitHub projects from all users"""
    if 'user' not in session:
        return redirect(url_for('home'))
    
    # Get all projects synced from GitHub (from all users)
    projects = load_projects()
    github_projects = [p for p in projects if p.get('synced')]  # Just check if synced is truthy
    
    # Sort by timestamp (newest first)
    github_projects.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    return render_template('github_projects.html', projects=github_projects, current_user=session['user'])

@app.route('/api/github/repo/<path:repo_full_name>/contents')
def get_repo_contents(repo_full_name):
    """Get repository directory contents"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş yapmalısınız'}), 401
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    encrypted_token = user.get('github_token')
    if not encrypted_token:
        return jsonify({'success': False, 'message': 'GitHub token bulunamadı'}), 400
    
    token = decrypt_token(encrypted_token)
    path = request.args.get('path', '')
    
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        
        contents = repo.get_contents(path) if path else repo.get_contents('')
        
        items = []
        # Ensure contents is always a list
        if not isinstance(contents, list):
            contents = [contents]
            
        for item in contents:
            items.append({
                'name': item.name,
                'path': item.path,
                'type': item.type,  # 'file' or 'dir'
                'size': item.size if item.type == 'file' else 0
            })
        
        # Sort: directories first, then files
        items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        
        return jsonify({'success': True, 'items': items, 'path': path})
        
    except GithubException as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/github/repo/<path:repo_full_name>/file')
def get_repo_file(repo_full_name):
    """Get specific file content from repository"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş yapmalısınız'}), 401
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    encrypted_token = user.get('github_token')
    if not encrypted_token:
        return jsonify({'success': False, 'message': 'GitHub token bulunamadı'}), 400
    
    token = decrypt_token(encrypted_token)
    file_path = request.args.get('path', '')
    
    if not file_path:
        return jsonify({'success': False, 'message': 'Dosya yolu belirtilmedi'}), 400
    
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        
        file_content = repo.get_contents(file_path)
        
        # Decode content
        import base64
        content = base64.b64decode(file_content.content).decode('utf-8')
        
        return jsonify({
            'success': True,
            'content': content,
            'name': file_content.name,
            'path': file_content.path,
            'size': file_content.size
        })
        
    except UnicodeDecodeError:
        return jsonify({'success': False, 'message': 'Bu dosya binary dosya (görüntülemek için uygun değil)'}), 400
    except GithubException as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/github/create-project', methods=['POST'])
def create_github_project():
    """Create a new GitHub repository and save to local projects"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş yapmalısınız'}), 401
    
    data = request.get_json()
    repo_name = data.get('repo_name', '').strip()
    description = data.get('description', '').strip()
    tech_stack = data.get('tech_stack', 'Not specified').strip()
    is_private = data.get('is_private', False)
    
    if not repo_name:
        return jsonify({'success': False, 'message': 'Repository name is required'}), 400
    
    users = load_users()
    user_email = session['user']['email']
    user = users.get(user_email, {})
    
    encrypted_token = user.get('github_token')
    if not encrypted_token:
        return jsonify({'success': False, 'message': 'GitHub token not found. Please connect GitHub first.'}), 400
    
    token = decrypt_token(encrypted_token)
    
    try:
        g = Github(token)
        gh_user = g.get_user()
        
        # Create new repository
        repo = gh_user.create_repo(
            name=repo_name,
            description=description or f"Project created on TechHub",
            private=is_private,
            auto_init=True
        )
        
        # Create README.md
        readme_content = f"""# {repo_name}

{description or 'A project created on TechHub'}

## 🛠️ Tech Stack
{tech_stack}

---
*This project was created on TechHub platform.*
"""
        
        # Wait a bit for auto_init
        import time
        time.sleep(2)
        
        try:
            repo.create_file(
                "README.md",
                "Initial commit from TechHub",
                readme_content
            )
        except:
            # README might already exist from auto_init
            pass
        
        # Save project to local database
        projects = load_projects()
        
        new_project = {
            'id': str(uuid.uuid4()),
            'title': repo_name,
            'description': description or 'Created on TechHub',
            'tech_stack': tech_stack,
            'demo_url': '',
            'github_url': repo.html_url,
            'github_repo': repo.full_name,
            'author_email': user_email,
            'author_name': user.get('name', 'Unknown'),
            'author_photo': user.get('photo', ''),
            'timestamp': get_timestamp(),
            'stars': 0,
            'synced': True
        }
        
        projects.append(new_project)
        save_projects(projects)
        
        return jsonify({
            'success': True,
            'message': f'Repository "{repo_name}" created successfully!',
            'repo_url': repo.html_url
        })
        
    except GithubException as e:
        error_msg = str(e)
        if 'name already exists' in error_msg.lower():
            return jsonify({'success': False, 'message': 'A repository with this name already exists'}), 400
        return jsonify({'success': False, 'message': error_msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/github/delete-project/<project_id>', methods=['POST'])
def delete_github_project(project_id):
    """Delete a project from database and optionally from GitHub"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş yapmalısınız'}), 401
    
    data = request.get_json() or {}
    delete_from_github = data.get('delete_from_github', False)
    
    projects = load_projects()
    project = None
    project_index = None
    
    # Find the project
    for i, p in enumerate(projects):
        if p.get('id') == project_id:
            project = p
            project_index = i
            break
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Check authorization - only owner can delete
    if project.get('author_email') != session['user']['email']:
        return jsonify({'success': False, 'message': 'You can only delete your own projects'}), 403
    
    github_delete_error = None
    
    # Delete from GitHub if requested
    if delete_from_github and project.get('github_repo'):
        users = load_users()
        user_email = session['user']['email']
        user = users.get(user_email, {})
        encrypted_token = user.get('github_token')
        
        if encrypted_token:
            try:
                token = decrypt_token(encrypted_token)
                if not token:
                    github_delete_error = 'GitHub token is invalid'
                else:
                    g = Github(token)
                    # Verify token works
                    try:
                        gh_user = g.get_user()
                        gh_user.login
                    except GithubException as e:
                        if '401' in str(e):
                            github_delete_error = 'GitHub token is expired. Please reconnect GitHub in Settings.'
                        else:
                            raise
                    
                    repo = g.get_repo(project['github_repo'])
                    repo.delete()
            except GithubException as e:
                # Check if it's a permission error
                if '403' in str(e) or 'admin rights' in str(e).lower():
                    github_delete_error = 'GitHub token lacks delete_repo permission. Repository kept on GitHub.'
                else:
                    github_delete_error = f'Failed to delete from GitHub: {str(e)}'
            except Exception as e:
                github_delete_error = f'Error deleting from GitHub: {str(e)}'
    
    # Remove from database even if GitHub deletion failed
    projects.pop(project_index)
    save_projects(projects)
    
    # Return appropriate message
    if github_delete_error:
        return jsonify({
            'success': True,
            'message': f'Project "{project["title"]}" removed from TechHub. Note: {github_delete_error}',
            'warning': github_delete_error
        })
    else:
        message = f'Project "{project["title"]}" deleted successfully'
        if delete_from_github:
            message += ' (from TechHub and GitHub)'
        return jsonify({
            'success': True,
            'message': message
        })

@app.route('/api/github/upload-code', methods=['POST'])
def upload_code_to_github():
    """Upload code files to a GitHub repository"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Giriş yapmalısınız'}), 401
    
    try:
        project_id = request.form.get('project_id')
        file_path = request.form.get('file_path', '').strip()
        commit_message = request.form.get('commit_message', 'Upload from TechHub').strip()
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Find project
        projects = load_projects()
        project = None
        for p in projects:
            if p.get('id') == project_id:
                project = p
                break
        
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404
        
        # Check authorization
        if project.get('author_email') != session['user']['email']:
            return jsonify({'success': False, 'message': 'You can only upload to your own projects'}), 403
        
        if not project.get('github_repo'):
            return jsonify({'success': False, 'message': 'Project not connected to GitHub'}), 400
        
        # Get GitHub token
        users = load_users()
        user_email = session['user']['email']
        user = users.get(user_email, {})
        encrypted_token = user.get('github_token')
        
        if not encrypted_token:
            return jsonify({'success': False, 'message': 'GitHub token not found'}), 400
        
        try:
            token = decrypt_token(encrypted_token)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Failed to decrypt GitHub token: {str(e)}'}), 400
        
        if not token:
            return jsonify({'success': False, 'message': 'Invalid GitHub token'}), 400
        
        try:
            g = Github(token)
            # Verify token is valid by making a simple API call
            gh_user = g.get_user()
            gh_user.login  # This will fail if token is invalid
        except GithubException as e:
            if '401' in str(e):
                return jsonify({'success': False, 'message': 'GitHub token is invalid or expired. Please reconnect your GitHub account in Settings.'}), 401
            return jsonify({'success': False, 'message': f'GitHub authentication error: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error connecting to GitHub: {str(e)}'}), 400
        
        try:
            repo = g.get_repo(project['github_repo'])
        except GithubException as e:
            return jsonify({'success': False, 'message': f'Repository not found or access denied: {str(e)}'}), 404
        
        # Read file content
        file_content = file.read()
        
        # Determine file path
        if file_path:
            full_path = f"{file_path.strip('/')}/{file.filename}"
        else:
            full_path = file.filename
        
        # Try to update existing file or create new one
        try:
            # Check if file exists
            contents = repo.get_contents(full_path)
            repo.update_file(
                full_path,
                commit_message,
                file_content,
                contents.sha
            )
            action = 'updated'
        except:
            # File doesn't exist, create it
            repo.create_file(
                full_path,
                commit_message,
                file_content
            )
            action = 'created'
        
        return jsonify({
            'success': True,
            'message': f'File "{file.filename}" {action} successfully',
            'file_path': full_path
        })
        
    except GithubException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# --- 🛠️ DİĞER ARAÇLAR ---
@app.route('/linux-sim', methods=["POST"])
def linux_sim():
    data = request.get_json()
    output = linux_simulator.run_command(data.get("command", ""))
    
    if isinstance(output, dict):
        return jsonify(output)
        
    return jsonify({"output": output, "path": linux_simulator.current_path})

@app.route('/linux-sim/save', methods=["POST"])
def linux_sim_save():
    data = request.get_json()
    full_path = data.get("full_path")
    content = data.get("content")
    
    if full_path:
        linux_simulator.fs[full_path] = content
        linux_simulator.change_dict["modified"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Missing path"}), 400

@app.route('/tools/floating-point')
def floating_point_page():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('floating.html')

@app.route('/tools/ipsub')
def ipsub_page():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('ipsub.html')

@app.route('/tools/bst')
def bst_page():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('bst.html')

@app.route('/tools/sorting-vis')
def sorting_vis():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('sorting_vis.html')

@app.route('/tools/py-visualizer')
def py_visualizer():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('py_visualizer.html')

@app.route('/api/evaluate-floating', methods=['POST'])
def evaluate_floating():
    if 'user' not in session: 
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    number = data.get('number', '').strip()
    
    if not number:
        return jsonify({'success': False, 'message': 'Please enter a number'})
    
    try:
        result = floating_point_converter.convert_to_floating_point(number)
        
        if isinstance(result, dict):
            return jsonify({
                'success': True,
                'binary': result['formatted'],
                'raw_binary': result['binary'],
                'details': {
                    'sign': 'Negative' if result['sign'] == '1' else 'Positive',
                    'exponent_bits': result['exponent'],
                    'exponent_value': result['actual_exponent'],
                    'mantissa': result['mantissa'],
                    'decimal_binary': result['decimal_binary']
                }
            })
        else:
            return jsonify({'success': True, 'binary': result})
            
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/floating-to-decimal', methods=['POST'])
def floating_to_decimal():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    binary = data.get('binary', '').strip()
    
    if not binary:
        return jsonify({'success': False, 'message': 'Please enter a binary number'})
    
    try:
        decimal = floating_point_converter.convert_from_floating_point(binary)
        return jsonify({
            'success': True,
            'decimal': decimal
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/ipsub', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        ip = data.get('ip')
        prefix = int(data.get('prefix'))

        calc = SubnetCalculator(ip, prefix)
        nw, bc, first, last = calc.get_network_details()
        
        return jsonify({
            'success': True,
            'subnet_mask': calc.get_mask(),
            'max_hosts': calc.get_max_hosts(),
            'network_address': nw,
            'broadcast_address': bc,
            'first_usable_ip': first,
            'last_usable_ip': last,
            'host_bits': calc.get_host_bits()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/tools/python3')
def python_comp():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('py_comp.html')

@app.route('/tools/logic')
def logic():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('logic.html')

@app.route('/tools/matrix')
def matrix():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('matrix.html')

@app.route('/tools/boolencircuit')
def boolencircuit():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('boolencircuit.html')

@app.route('/tools/terminal')
def terminal():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('terminal.html')

@app.route('/tools/converter')
def converter():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('converter.html')

@app.route('/tools/c++')
def cpp_playground():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('cpp_comp.html')

@app.route('/tools/ruby')
def ruby_playground():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('ruby.html')

@app.route('/tools/go')
def go_playground():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('go.html')

@app.route('/tools/java')
def java_playground():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('java.html')

@app.route('/run-cpp', methods=['POST'])
def run_cpp():
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    GODBOLD_API_URL = "https://godbolt.org/api/compiler/g141/compile"
    
    payload = {
        "source": code,
        "options": {
            "userArguments": "",
            "compilerOptions": {
                "executorRequest": True
            },
            "filters": {
                "execute": True
            },
            "tools": [],
            "libraries": []
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(GODBOLD_API_URL, json=payload, headers=headers)
        result = response.json()
        
        if result.get('code') != 0 and not result.get('didExecute'):
            error_msg = ""
            for line in result.get('stderr', []):
                error_msg += line.get('text', '') + "\n"
            return jsonify({'success': False, 'error': error_msg or "Compilation failed"})
            
        if result.get('didExecute'):
            output = ""
            for line in result.get('stdout', []):
                output += line.get('text', '') + "\n"
            
            stderr_out = ""
            for line in result.get('stderr', []):
                stderr_out += line.get('text', '') + "\n"
                
            final_output = output + ("\nRuntime Error:\n" + stderr_out if stderr_out else "")
            return jsonify({'success': True, 'output': final_output or "Program executed successfully (no output)."})
        else:
             return jsonify({'success': False, 'error': "Compilation successful, but execution failed or was not returned."})

    except Exception as e:
        return jsonify({'success': False, 'error': "API Error: " + str(e)})

@app.route('/run-ruby', methods=['POST'])
def run_ruby():
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    GODBOLD_API_URL = "https://godbolt.org/api/compiler/ruby334/compile"
    
    payload = {
        "source": code,
        "options": {
            "userArguments": "",
            "compilerOptions": {
                "executorRequest": True
            },
            "filters": {
                "execute": True
            },
            "tools": [],
            "libraries": []
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(GODBOLD_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
             return jsonify({'success': False, 'error': f"Godbolt API Error ({response.status_code}): {response.text}"})

        result = response.json()
        
        if result.get('code') != 0 and not result.get('didExecute'):
            error_msg = ""
            for line in result.get('stderr', []):
                error_msg += line.get('text', '') + "\n"
            return jsonify({'success': False, 'error': error_msg or "Execution failed"})
            
        if result.get('didExecute'):
            output = ""
            for line in result.get('stdout', []):
                output += line.get('text', '') + "\n"
            
            stderr_out = ""
            for line in result.get('stderr', []):
                stderr_out += line.get('text', '') + "\n"
                
            final_output = output + ("\nRuntime Error:\n" + stderr_out if stderr_out else "")
            return jsonify({'success': True, 'output': final_output or "Program executed successfully."})
        else:
             return jsonify({'success': False, 'error': "Execution failed or returned no output."})

    except Exception as e:
        return jsonify({'success': False, 'error': "API Error: " + str(e)})

@app.route('/run-go', methods=['POST'])
def run_go():
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    GODBOLT_API_URL = "https://godbolt.org/api/compiler/gl12212/compile"
    
    payload = {
        "source": code,
        "options": {
            "userArguments": "",
            "compilerOptions": {
                "executorRequest": True
            },
            "filters": {
                "execute": True
            },
            "tools": [],
            "libraries": []
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(GODBOLT_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
             return jsonify({'success': False, 'error': f"Godbolt API Error ({response.status_code}): {response.text}"})

        result = response.json()
        
        if result.get('code') != 0 and not result.get('didExecute'):
            error_msg = ""
            for line in result.get('stderr', []):
                error_msg += line.get('text', '') + "\n"
            return jsonify({'success': False, 'error': error_msg or "Execution failed"})
            
        if result.get('didExecute'):
            output = ""
            for line in result.get('stdout', []):
                output += line.get('text', '') + "\n"
            
            stderr_out = ""
            for line in result.get('stderr', []):
                stderr_out += line.get('text', '') + "\n"
                
            final_output = output + ("\nRuntime Error:\n" + stderr_out if stderr_out else "")
            return jsonify({'success': True, 'output': final_output or "Program executed successfully."})
        else:
             return jsonify({'success': False, 'error': "Execution failed or returned no output."})

    except Exception as e:
        return jsonify({'success': False, 'error': "API Error: " + str(e)})

@app.route('/run-java', methods=['POST'])
def run_java():
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    GODBOLT_API_URL = "https://godbolt.org/api/compiler/java2301/compile"
    
    payload = {
        "source": code,
        "options": {
            "userArguments": "",
            "compilerOptions": {
                "executorRequest": True
            },
            "filters": {
                "execute": True
            },
            "tools": [],
            "libraries": []
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(GODBOLT_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
             return jsonify({'success': False, 'error': f"Godbolt API Error ({response.status_code}): {response.text}"})

        result = response.json()
        
        if result.get('code') != 0 and not result.get('didExecute'):
            error_msg = ""
            for line in result.get('stderr', []):
                error_msg += line.get('text', '') + "\n"
            return jsonify({'success': False, 'error': error_msg or "Execution failed"})
            
        if result.get('didExecute'):
            output = ""
            for line in result.get('stdout', []):
                output += line.get('text', '') + "\n"
            
            stderr_out = ""
            for line in result.get('stderr', []):
                stderr_out += line.get('text', '') + "\n"
                
            final_output = output + ("\nRuntime Error:\n" + stderr_out if stderr_out else "")
            return jsonify({'success': True, 'output': final_output or "Program executed successfully."})
        else:
             return jsonify({'success': False, 'error': "Execution failed or returned no output."})

    except Exception as e:
        return jsonify({'success': False, 'error': "API Error: " + str(e)})

@app.route('/api/logic/evaluate', methods=['POST'])
def evaluate_logic():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    raw_expr = data.get('expression', '')
    
    import re
    expression = raw_expr
    expression = expression.replace("Ā", "!A").replace("B̄", "!B").replace("C̄", "!C").replace("D̄", "!D")
    expression = expression.replace("Ē", "!E").replace("F̄", "!F").replace("Ḡ", "!G").replace("H̄", "!H")
    expression = expression.replace("Ī", "!I").replace("J̄", "!J").replace("K̄", "!K").replace("L̄", "!L")
    expression = expression.replace("M̄", "!M").replace("N̄", "!N").replace("Ō", "!O").replace("P̄", "!P")
    expression = expression.replace("Q̄", "!Q").replace("R̄", "!R").replace("S̄", "!S").replace("T̄", "!T")
    expression = expression.replace("Ū", "!U").replace("V̄", "!V").replace("W̄", "!W").replace("X̄", "!X")
    expression = expression.replace("Ȳ", "!Y").replace("Z̄", "!Z")
    expression = expression.replace("ā", "!a").replace("b̄", "!b").replace("c̄", "!c").replace("d̄", "!d").replace("ē", "!e")
    
    COMB_OVER = '\u0304'
    expression = re.sub(r'([a-zA-Z0-9])' + COMB_OVER, r'!\1', expression)
    
    expression = expression.replace("→", "$").replace("↔", "#").replace("⊕", "^")
    expression = expression.replace("->", "$").replace("<=>", "#")
    
    try:
        reg_global.reset()
        tokens = lex_and_consider_adjacents(expression)
        ast = create_ast(tokens)
        tt = TruthTable(reg_global.get_headers(), reg_global.objs, ast)
        tt.generate()
        tt.simplify()
        
        def format_pretty(s):
            if not s: return s
            s = s.replace("$", "→").replace("#", "↔").replace("^", "⊕")
            s = s.replace("!A", "Ā").replace("!B", "B̄").replace("!C", "C̄").replace("!D", "D̄")
            s = s.replace("!E", "Ē").replace("!F", "F̄").replace("!G", "Ḡ").replace("!H", "H̄")
            s = s.replace("!I", "Ī").replace("!J", "J̄").replace("!K", "K̄").replace("!L", "L̄")
            s = s.replace("!M", "M̄").replace("!N", "N̄").replace("!O", "Ō").replace("!P", "P̄")
            s = s.replace("!Q", "Q̄").replace("!R", "R̄").replace("!S", "S̄").replace("!T", "T̄")
            s = s.replace("!U", "Ū").replace("!V", "V̄").replace("!W", "W̄").replace("!X", "X̄")
            s = s.replace("!Y", "Ȳ").replace("!Z", "Z̄")
            s = s.replace("!a", "ā").replace("!b", "b̄").replace("!c", "c̄").replace("!d", "d̄").replace("!e", "ē")
            COMB_OVER = '\u0304'
            s = re.sub(r'!([a-zA-Z0-9])', r'\1' + COMB_OVER, s)
            return s

        pretty_headers = [format_pretty(h) for h in tt.headers] + ['X']
        pretty_simplified = format_pretty(tt.simplified_str)
        
        rows = [[(1 if val else 0) for val in row.ls] + [1 if row.value else 0] for row in tt.rows]
        return jsonify({
            'success': True, 
            'headers': pretty_headers, 
            'rows': rows, 
            'simplified': pretty_simplified
        })
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

@app.route('/chatbot')
def chatbot():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template('chatbot.html', user=session['user'])

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        ai_response = get_ai_response(user_message)
        
        if ai_response:
            return jsonify({'response': ai_response})
        else:
            return jsonify({'response': 'Sorry, I am currently unavailable. Please check if Ollama is running.'}), 500
            
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    try:
        user_message = request.json.get('message')
        config = get_ai_config()
        
        def generate():
            try:
                response = ollama.chat(
                    model=config.get('model', 'llama3.2:3b'),
                    messages=[
                        {'role': 'system', 'content': config.get('system_prompt')},
                        {'role': 'user', 'content': user_message}
                    ],
                    options={'temperature': config.get('temperature', 0.7)},
                    stream=True
                )
                for chunk in response:
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        yield f"data: {json.dumps({'content': content})}\n\n"
            except Exception as stream_error:
                print(f"❌ Stream Generation Error: {stream_error}")
                yield f"data: {json.dumps({'error': str(stream_error)})}\n\n"
            
        return Response(generate(), mimetype='text/event-stream')
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({'success': False}), 401
    users = load_users()
    user_data = users.get(session['user']['email'])
    if not user_data: return jsonify({'success': False}), 404
    
    if location := request.form.get('location'): user_data['location'] = location
    if about := request.form.get('about'): user_data['about'] = about
    
    if phone := request.form.get('phone'): user_data['phone'] = phone
    if website := request.form.get('website'): user_data['website'] = website
    
    if github := request.form.get('github'): user_data['github'] = github
    if linkedin := request.form.get('linkedin'): user_data['linkedin'] = linkedin
    if twitter := request.form.get('twitter'): user_data['twitter'] = twitter
    if instagram := request.form.get('instagram'): user_data['instagram'] = instagram
    
    old_p, new_p, conf_p = request.form.get('old_password'), request.form.get('new_password'), request.form.get('confirm_password')
    if new_p:
        if user_data['password'] == old_p and new_p == conf_p: user_data['password'] = new_p
        else: return jsonify({'success': False, 'message': 'Şifrə xətası'}), 400

    if 'profile_photo' in request.files:
        file = request.files['profile_photo']
        if file.filename:
            filename = secure_filename(f"{user_data['name']}_profile_{str(uuid.uuid4())[:8]}{os.path.splitext(file.filename)[1]}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user_data['photo'] = f"/static/images/uploads/{filename}"

    if 'banner_photo' in request.files:
        file = request.files['banner_photo']
        if file.filename:
            filename = secure_filename(f"{user_data['name']}_banner_{str(uuid.uuid4())[:8]}{os.path.splitext(file.filename)[1]}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user_data['banner'] = f"/static/images/uploads/{filename}"

    users[user_data['email']] = user_data
    save_users(users)
    session['user'] = user_data
    return jsonify({'success': True})

if __name__ == '__main__':
    print(f"\n🚀 SİSTEM BAŞLIYOR...")
    print(f"📁 LOCAL MODE - Using JSON files")
    
    # Ensure projects file exists
    if not os.path.exists(PROJECTS_DB_FILE):
        with open(PROJECTS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    app.run(host='0.0.0.0', port=5000, debug=True)