from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import time



app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

DB_FILE = os.path.join('static', 'techhub_users_db.json')

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
        # Update last login
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
        "name": name,
        "email": email,
        "password": password, 
        "createdAt": int(time.time() * 1000),
        "about": "",
        "lastLogin": int(time.time() * 1000)
    }

    users[email] = new_user
    save_users(users)
    
    # Auto login after register
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



if __name__ == '__main__':
    app.run(debug=True)
