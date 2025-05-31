from flask import Blueprint, request, render_template, redirect, url_for, session, flash, g
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
from app.database import get_db, init_db
from app.extensions import limiter

auth = Blueprint('auth', __name__)  # Define um blueprint para as rotas de autenticação

# --- Decorador para proteger rotas que precisam de login ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def register():
    init_db()
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if not username or not email or not password or not confirm:
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('As senhas não coincidem.')
            return redirect(url_for('auth.register'))

        if len(password) < 8:
            flash('A senha deve ter pelo menos 8 caracteres.')
            return redirect(url_for('auth.register'))

        import re
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('Formato de e-mail inválido.')
            return redirect(url_for('auth.register'))

        password_hash = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute(
                '''INSERT INTO users (username, email, password_hash, created_at)
                   VALUES (?, ?, ?, datetime('now'))''',
                (username, email, password_hash)
            )
            conn.commit()
            flash('Registro bem-sucedido!')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError as e:
            if 'username' in str(e).lower():
                flash('Nome de usuário já está em uso.')
            elif 'email' in str(e).lower():
                flash('E-mail já cadastrado.')
            else:
                flash('Erro ao registrar usuário.')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    init_db()
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_db()
        user = conn.execute(
            'SELECT id, password_hash, failed_attempts, locked_until, is_admin FROM users WHERE username = ?',
            (username,)
        ).fetchone()

        # Corrigido: verifica se locked_until é válido e diferente de 'None'
        if user and user['locked_until'] and user['locked_until'] != 'None':
            try:
                locked_until = datetime.fromisoformat(user['locked_until'])
            except ValueError:
                # Se a string não for um isoformat válido, trata como None
                locked_until = None
            if locked_until and datetime.utcnow() < locked_until:
                flash('Conta temporariamente bloqueada. Tente novamente mais tarde.')
                return redirect(url_for('auth.login'))
            else:
                # Se bloqueio expirou, zera tentativas e desbloqueia
                conn.execute(
                    'UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?',
                    (user['id'],)
                )
                conn.commit()

        if user and check_password_hash(user['password_hash'], password):
            conn.execute(
                'UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = username
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for('prediction.index'))
        else:
            if user:
                attempts = user['failed_attempts'] + 1
                locked_until = None
                if attempts >= 5:
                    locked_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
                conn.execute(
                    'UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?',
                    (attempts, locked_until, user['id'])
                )
                conn.commit()
            flash('Credenciais inválidas.')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per minute")
def profile():
    conn = get_db()
    user_id = session.get('user_id')

    user = conn.execute(
        'SELECT id, username, email, password_hash FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not check_password_hash(user['password_hash'], current_password):
            flash('Senha atual incorreta.', 'error')
            return redirect(url_for('auth.profile'))

        if new_password != confirm_password:
            flash('As novas senhas não coincidem.', 'error')
            return redirect(url_for('auth.profile'))

        if len(new_password) < 8:
            flash('A nova senha deve ter pelo menos 8 caracteres.', 'error')
            return redirect(url_for('auth.profile'))

        new_hash = generate_password_hash(new_password)
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (new_hash, user_id)
        )
        conn.commit()
        flash('Senha atualizada com sucesso!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('profile.html', user=user)

@auth.route('/logout', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
