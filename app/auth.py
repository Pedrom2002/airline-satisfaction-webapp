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
        # Se não estiver logado (não existir user_id na sessão), redireciona para login
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# Rota para registro de usuários
@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Limite: 10 registros por minuto por IP
def register():
    init_db()  # Inicializa o banco (cria tabelas se necessário)
    if request.method == 'POST':
        # Coleta os dados do formulário
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm_password']

        # Validações básicas dos campos
        if not username or not email or not password or not confirm:
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('As senhas não coincidem.')
            return redirect(url_for('auth.register'))

        if len(password) < 8:
            flash('A senha deve ter pelo menos 8 caracteres.')
            return redirect(url_for('auth.register'))

        # Validação simples de formato de e-mail com regex
        import re
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('Formato de e-mail inválido.')
            return redirect(url_for('auth.register'))

        # Gera o hash da senha para salvar seguro no banco
        password_hash = generate_password_hash(password)
        conn = get_db()
        try:
            # Tenta inserir novo usuário na tabela
            conn.execute(
                '''INSERT INTO users (username, email, password_hash, created_at)
                   VALUES (?, ?, ?, datetime('now'))''',
                (username, email, password_hash)
            )
            conn.commit()
            flash('Registro bem-sucedido!')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError as e:
            # Captura erro de username/email duplicados
            if 'username' in str(e).lower():
                flash('Nome de usuário já está em uso.')
            elif 'email' in str(e).lower():
                flash('E-mail já cadastrado.')
            else:
                flash('Erro ao registrar usuário.')
            return redirect(url_for('auth.register'))
    # Se GET, renderiza o formulário de registro
    return render_template('register.html')

# Rota para login
@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Limite: 10 tentativas de login por minuto por IP
def login():
    init_db()  # Inicializa o banco para garantir estrutura
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_db()
        user = conn.execute(
            'SELECT id, password_hash, failed_attempts, locked_until, is_admin FROM users WHERE username = ?',
            (username,)
        ).fetchone()

        # Verifica se a conta está bloqueada temporariamente
        if user and user['locked_until']:
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.utcnow() < locked_until:
                flash('Conta temporariamente bloqueada. Tente novamente mais tarde.')
                return redirect(url_for('auth.login'))
            else:
                # Se bloqueio expirou, zera tentativas e desbloqueia
                conn.execute(
                    'UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?',
                    (user['id'],)
                )
                conn.commit()

        # Se usuário existe e senha bate
        if user and check_password_hash(user['password_hash'], password):
            # Reseta tentativas falhas e bloqueios no banco
            conn.execute(
                'UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            # Cria sessão com dados do usuário
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = username
            session['is_admin'] = bool(user['is_admin'])  # ← ADICIONADO
            return redirect(url_for('prediction.index'))  # Redireciona para página principal da predição
        else:
            # Caso senha errada ou usuário não exista
            if user:
                # Incrementa tentativas falhas
                attempts = user['failed_attempts'] + 1
                locked_until = None
                # Bloqueia a conta por 15 min após 5 tentativas
                if attempts >= 5:
                    locked_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
                conn.execute(
                    'UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?',
                    (attempts, locked_until, user['id'])
                )
                conn.commit()
            flash('Credenciais inválidas.')
            return redirect(url_for('auth.login'))
    
    # Se GET, renderiza formulário de login
    return render_template('login.html')


# Rota para perfil do usuário, onde pode trocar senha
@auth.route('/profile', methods=['GET', 'POST'])
@login_required  # Só acessa quem está logado
@limiter.limit("10 per minute")  # Limite: 10 mudanças de senha por minuto por usuário
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

        # Verifica se a senha atual está correta
        if not check_password_hash(user['password_hash'], current_password):
            flash('Senha atual incorreta.', 'error')
            return redirect(url_for('auth.profile'))

        # Confirmação da nova senha
        if new_password != confirm_password:
            flash('As novas senhas não coincidem.', 'error')
            return redirect(url_for('auth.profile'))

        # Valida o tamanho mínimo da nova senha
        if len(new_password) < 8:
            flash('A nova senha deve ter pelo menos 8 caracteres.', 'error')
            return redirect(url_for('auth.profile'))

        # Atualiza o hash da nova senha no banco
        new_hash = generate_password_hash(new_password)
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (new_hash, user_id)
        )
        conn.commit()
        flash('Senha atualizada com sucesso!', 'success')
        return redirect(url_for('auth.profile'))

    # Se GET, renderiza o formulário com dados do usuário
    return render_template('profile.html', user=user)

# Rota para logout - destrói a sessão do usuário
@auth.route('/logout', methods=['POST'])
@login_required
@limiter.limit("10 per minute")  # Limite para logout por segurança
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# Função que carrega o usuário logado antes de cada requisição
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
