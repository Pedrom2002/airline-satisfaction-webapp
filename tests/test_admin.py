import pytest
import logging
from werkzeug.security import generate_password_hash
from app.database import get_db, init_db
from app import create_app

# Configura logger para DEBUG
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        logger.info("Inicializando banco de dados no setup do teste")
        init_db()  # Cria as tabelas no banco in-memory antes dos testes

        # Verifica se a tabela 'users' foi criada com sucesso
        db = get_db()
        table_exists = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
        ).fetchone()
        if table_exists:
            logger.info("Tabela 'users' existe no banco de dados de teste")
        else:
            logger.error("Tabela 'users' NÃO encontrada no banco de dados de teste")

    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_admin_access_requires_login(client):
    response = client.get('/admin/', follow_redirects=False)
    assert response.status_code == 302  # Deve redirecionar para login

def test_admin_access_forbidden_for_non_admin(client):
    # Registra e loga um usuário normal
    logger.info("Registrando usuário normal para teste de acesso proibido")
    register_resp = client.post('/auth/register', data={
        'username': 'normaluser',
        'email': 'normal@example.com',
        'password': 'pass1234',
        'confirm_password': 'pass1234'
    })
    logger.debug(f"Status do registro: {register_resp.status_code}")
    login_resp = client.post('/auth/login', data={
        'username': 'normaluser',
        'password': 'pass1234'
    })
    logger.debug(f"Status do login: {login_resp.status_code}")

    response = client.get('/admin/', follow_redirects=False)
    logger.debug(f"Status do acesso admin por usuário normal: {response.status_code}")
    # Pode ser 403 ou mensagem Forbidden
    assert response.status_code == 403 or b'Forbidden' in response.data

import tempfile
import os
import pytest
from app import create_app
from app.database import init_db, get_db

@pytest.fixture
def app():
    # Cria arquivo temporário para banco de dados SQLite
    db_fd, db_path = tempfile.mkstemp()

    app = create_app(testing=True)
    app.config['DATABASE'] = db_path  # Aponta para o arquivo temporário

    with app.app_context():
        init_db()  # Cria as tabelas no banco temporário

    yield app

    # Cleanup após teste: fecha e remove arquivo temporário
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()

def test_tables_created(app):
    with app.app_context():
        db = get_db()
        # Verifica se a tabela 'users' existe
        table_exists = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
        ).fetchone()
        assert table_exists is not None

def test_admin_access_granted_for_admin_user(client, app):
    # Registra usuário
    client.post('/auth/register', data={
        'username': 'test',
        'email': 'test@example.com',
        'password': 'test',
        'confirm_password': 'test'
    }, content_type='application/x-www-form-urlencoded')

    with app.app_context():
        db = get_db()
        # Promove usuário para admin
        db.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('test',))
        db.commit()

    # Faz login do usuário admin
    client.post('/auth/login', data={
        'username': 'test',
        'password': 'test'
    }, content_type='application/x-www-form-urlencoded')

    # Acessa rota admin
    response = client.get('/admin/')
    assert response.status_code == 200
    assert b'users' in response.data or b'table' in response.data

def test_admin_required_decorator_forbids_non_admin(client, app):
    # Registrar usuário comum
    client.post('/auth/register', data={
        'username': 'normaluser',
        'email': 'normal@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    client.post('/auth/login', data={
        'username': 'normaluser',
        'password': 'password123'
    })

    # Tentativa de acessar rota admin protegida
    response = client.get('/admin/')
    assert response.status_code == 403

def test_admin_index_access_granted_for_admin(client, app):
    # Registrar usuário e tornar admin diretamente no banco
    client.post('/auth/register', data={
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': 'adminpass',
        'confirm_password': 'adminpass'
    })
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('adminuser',))
        db.commit()

    # Login admin
    client.post('/auth/login', data={
        'username': 'adminuser',
        'password': 'adminpass'
    })

    # Acesso admin
    response = client.get('/admin/')
    assert response.status_code == 200
    for table in ['users', 'uploads', 'predictions', 'logs', 'user_settings']:
        assert table.encode() in response.data

def test_admin_edit_get_post(client, app):
    # Cria usuário admin
    client.post('/auth/register', data={
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': 'adminpass',
        'confirm_password': 'adminpass'
    })
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('adminuser',))
        db.execute("INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                   ('edituser', 'edit@example.com', 'hash', 0))
        db.commit()

    client.post('/auth/login', data={'username': 'adminuser', 'password': 'adminpass'})

    with app.app_context():
        db = get_db()
        user_id = db.execute("SELECT id FROM users WHERE username = ?", ('edituser',)).fetchone()[0]

    # GET edição registro existente
    response = client.get(f'/admin/table/users/edit/{user_id}')
    assert response.status_code == 200
    assert b'edituser' in response.data

    # POST para editar registro — agora deve redirecionar (302)
    response = client.post(f'/admin/table/users/edit/{user_id}', data={
        'username': 'edituserupdated',
        'email': 'editupdated@example.com',
        'password_hash': 'hash',
        'is_admin': '0'
    }, follow_redirects=False)
    assert response.status_code == 302  # redirecionamento após update

    # Opcional: seguir o redirecionamento para verificar a mensagem flash
    response = client.post(f'/admin/table/users/edit/{user_id}', data={
        'username': 'edituserupdated',
        'email': 'editupdated@example.com',
        'password_hash': 'hash',
        'is_admin': '0'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        updated = db.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        assert updated == 'edituserupdated'

    # GET edição registro inexistente
    response = client.get('/admin/table/users/edit/9999999')
    assert response.status_code == 404

    # Tentativa editar tabela não permitida
    response = client.get('/admin/table/notallowed/edit/1')
    assert response.status_code == 403

def test_admin_table(client, app):
    # Configura usuário admin
    client.post('/auth/register', data={
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': 'adminpass',
        'confirm_password': 'adminpass'
    })
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('adminuser',))
        # Cria dados para tabela 'users'
        db.execute("INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                   ('testuser1', 'test1@example.com', 'hash1', 0))
        db.execute("INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                   ('testuser2', 'test2@example.com', 'hash2', 0))
        db.commit()

    # Login admin
    client.post('/auth/login', data={'username': 'adminuser', 'password': 'adminpass'})

    # Acesso a tabela válida (GET)
    response = client.get('/admin/table/users')
    assert response.status_code == 200
    assert b'username' in response.data  # header coluna
    assert b'testuser1' in response.data
    assert b'testuser2' in response.data

    # Busca com filtro (search na coluna username)
    response = client.get('/admin/table/users?search=testuser1&column=username')
    assert response.status_code == 200
    assert b'testuser1' in response.data
    assert b'testuser2' not in response.data  # só um resultado

    # Tabela inválida (não permitida)
    response = client.get('/admin/table/notallowed')
    assert response.status_code == 403

    # Testa paginação - página 1 (default)
    response = client.get('/admin/table/users?page=1')
    assert response.status_code == 200

    # Página 0 (menor que 1) deve ser tratada como 1
    response = client.get('/admin/table/users?page=0')
    assert response.status_code == 200



def test_admin_delete(client, app):
    # Cria e promove usuário admin
    client.post('/auth/register', data={
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': 'adminpass',
        'confirm_password': 'adminpass'
    })
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('adminuser',))
        # Cria um segundo usuário para deletar
        db.execute("INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                   ('todelete', 'todelete@example.com', 'hash', 0))
        db.commit()
        user_id = db.execute("SELECT id FROM users WHERE username = ?", ('todelete',)).fetchone()[0]

    # Login como admin
    client.post('/auth/login', data={'username': 'adminuser', 'password': 'adminpass'})

    # Deleta usuário existente
    response = client.post(f'/admin/table/users/delete/{user_id}', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        result = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        assert result is None  # Confirmar que foi realmente deletado

    # Deleta registro inexistente
    response = client.post('/admin/table/users/delete/999999', follow_redirects=True)
    assert response.status_code == 404

    # Tenta deletar de tabela não permitida
    response = client.post('/admin/table/invalid/edit/1', follow_redirects=True)
    assert response.status_code == 403
