import os
import json
import time
import uuid
from datetime import datetime, timedelta
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

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'
import threading
db_lock = threading.Lock()

UPLOAD_FOLDER = os.path.join('static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Local JSON file paths
USERS_DB_FILE = os.path.join('static', 'techhub_users_db.json')
QA_DB_FILE = os.path.join('static', 'techhub_qa_db.json')

# Initialize tools
linux_simulator = LinuxTerminal()
floating_point_converter = FloatingPoint()

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
        "photo": "", "about": "", "location": ""
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

    # --- AUTO AI ANSWER (ASYNCHRONOUS) ---
    def generate_async_answer(q_id, title, content):
        import threading
        def worker():
            try:
                ai_content = f"Question Title: {title}\nContent: {content}"
                ai_response_text = get_ai_response(ai_content, system_prompt_override="You are Dastan. Provide a helpful, concise answer to this user question on our platform.")
                
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
                    # We need a fresh load because DB might have changed
                    current_questions = load_json("qa")
                    for q in current_questions:
                        if q['id'] == q_id:
                            q['answers'].append(ai_ans)
                            break
                    save_json("qa", current_questions)
            except Exception as e:
                print(f"⚠️ Auto-answer error: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    generate_async_answer(new_q['id'], new_q['title'], new_q['content'])

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
    
    # --- AUTO AI REPLY (IF MENTIONED) ---
    ans_text = data.get('text', '')
    if "dastan" in ans_text.lower():
        def worker():
            try:
                ai_response = get_ai_response(ans_text, system_prompt_override="You are Dastan. A user mentioned you in a comment. Provide a short, helpful reply.")
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
            except: pass
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

# --- 🛠️ DİĞER ARAÇLAR ---
@app.route('/linux-sim', methods=["POST"])
def linux_sim():
    data = request.get_json()
    output = linux_simulator.run_command(data.get("command", ""))
    
    # Check if output is a dictionary (internal signal)
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
def floating_point_page():  # ✅ RENAMED TO AVOID CONFLICT
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
        # ✅ USE THE GLOBAL INSTANCE
        result = floating_point_converter.convert_to_floating_point(number)
        
        # Check if result is a dict (new version) or string (old version)
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
            # Old version compatibility
            return jsonify({'success': True, 'binary': result})
            
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/floating-to-decimal', methods=['POST'])
def floating_to_decimal():
    """Convert 8-bit floating point back to decimal"""
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

        # Sinifdən obyekt yaradırıq
        calc = SubnetCalculator(ip, prefix)
        
        # Məlumatları alırıq
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
    # if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    # Godbolt API Configuration
    # Using GCC 14.1.0 (g141) as a stable, modern choice
    GODBOLD_API_URL = "https://godbolt.org/api/compiler/g141/compile"
    
    payload = {
        "source": code,
        "options": {
            "userArguments": "",
            "compilerOptions": {
                "executorRequest": True  # Enable execution
            },
            "filters": {
                "execute": True  # THIS IS KEY: Request execution of the compiled code
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
        
        # Check for compilation errors first
        if result.get('code') != 0 and not result.get('didExecute'):
            # Combine stdout and stderr from compilation
            error_msg = ""
            for line in result.get('stderr', []):
                error_msg += line.get('text', '') + "\n"
            return jsonify({'success': False, 'error': error_msg or "Compilation failed"})
            
        # If execution happened
        if result.get('didExecute'):
            # Combine execution stdout
            output = ""
            for line in result.get('stdout', []):
                output += line.get('text', '') + "\n"
            
            # Combine execution stderr (e.g. runtime errors)
            stderr_out = ""
            for line in result.get('stderr', []):
                stderr_out += line.get('text', '') + "\n"
                
            final_output = output + ("\nRuntime Error:\n" + stderr_out if stderr_out else "")
            return jsonify({'success': True, 'output': final_output or "Program executed successfully (no output)."})
        else:
             # Fallback if execution flag was ignored or failed silently
             return jsonify({'success': False, 'error': "Compilation successful, but execution failed or was not returned."})

    except Exception as e:
        return jsonify({'success': False, 'error': "API Error: " + str(e)})

@app.route('/run-ruby', methods=['POST'])
def run_ruby():
    # if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    # Godbolt API Configuration for Ruby
    # Using Ruby 3.3.4
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
        
        # Check for compilation/execution errors
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
    # if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    # Godbolt API Configuration for Go
    # Using Go 1.22.12 (gl12212) - Stable x86-64 gc
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
        
        # Check for compilation/execution errors
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
    # if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    code = request.json.get('code')
    if not code: return jsonify({'error': 'No code provided'}), 400

    import requests

    # Godbolt API Configuration for Java
    # Using JDK 23.0.1 (java2301)
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
        
        # Check for compilation/execution errors
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
    
    # Normalize Unicode symbols to Internal tokens
    import re
    expression = raw_expr
    # Handle precomposed overline characters (Ā, B̄, etc.)
    expression = expression.replace("Ā", "!A").replace("B̄", "!B").replace("C̄", "!C").replace("D̄", "!D")
    expression = expression.replace("Ē", "!E").replace("F̄", "!F").replace("Ḡ", "!G").replace("H̄", "!H")
    expression = expression.replace("Ī", "!I").replace("J̄", "!J").replace("K̄", "!K").replace("L̄", "!L")
    expression = expression.replace("M̄", "!M").replace("N̄", "!N").replace("Ō", "!O").replace("P̄", "!P")
    expression = expression.replace("Q̄", "!Q").replace("R̄", "!R").replace("S̄", "!S").replace("T̄", "!T")
    expression = expression.replace("Ū", "!U").replace("V̄", "!V").replace("W̄", "!W").replace("X̄", "!X")
    expression = expression.replace("Ȳ", "!Y").replace("Z̄", "!Z")
    expression = expression.replace("ā", "!a").replace("b̄", "!b").replace("c̄", "!c").replace("d̄", "!d").replace("ē", "!e")
    
    # Handle generic combining overlines
    COMB_OVER = '\u0304'
    expression = re.sub(r'([a-zA-Z0-9])' + COMB_OVER, r'!\1', expression)
    
    expression = expression.replace("→", "$").replace("↔", "#").replace("⊕", "^")
    # Compatibility for old symbols if they were pasted
    expression = expression.replace("->", "$").replace("<=>", "#")
    
    try:
        reg_global.reset()
        tokens = lex_and_consider_adjacents(expression)
        ast = create_ast(tokens)
        tt = TruthTable(reg_global.get_headers(), reg_global.objs, ast)
        tt.generate()
        tt.simplify()
        
        # Format output headers and simplified string with PRETTY symbols
        def format_pretty(s):
            if not s: return s
            s = s.replace("$", "→").replace("#", "↔").replace("^", "⊕")
            # Convert !A back to Ā (precomposed if possible)
            s = s.replace("!A", "Ā").replace("!B", "B̄").replace("!C", "C̄").replace("!D", "D̄")
            s = s.replace("!E", "Ē").replace("!F", "F̄").replace("!G", "Ḡ").replace("!H", "H̄")
            s = s.replace("!I", "Ī").replace("!J", "J̄").replace("!K", "K̄").replace("!L", "L̄")
            s = s.replace("!M", "M̄").replace("!N", "N̄").replace("!O", "Ō").replace("!P", "P̄")
            s = s.replace("!Q", "Q̄").replace("!R", "R̄").replace("!S", "S̄").replace("!T", "T̄")
            s = s.replace("!U", "Ū").replace("!V", "V̄").replace("!W", "W̄").replace("!X", "X̄")
            s = s.replace("!Y", "Ȳ").replace("!Z", "Z̄")
            s = s.replace("!a", "ā").replace("!b", "b̄").replace("!c", "c̄").replace("!d", "d̄").replace("!e", "ē")
            # Generic fallback for !
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
    app.run(host='0.0.0.0', port=5000, debug=True)