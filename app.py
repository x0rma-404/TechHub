from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import time
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

DB_FILE = os.path.join('static', 'techhub_users_db.json')
terminal = LinuxTerminal()

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
    output = terminal.run_command(command)
    if output == "__exit__":
        return jsonify({"output": "Closing the terminal... Goodbye!"})
    return jsonify({"output": output})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect(url_for('home'))
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    users = load_users()
    if email in users and users[email]['password'] == password:
        session['user'] = users[email]
        users[email]['lastLogin'] = int(time.time() * 1000)
        save_users(users)
        return jsonify({'success': True, 'user': users[email]})
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

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
        "lastLogin": int(time.time() * 1000)
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