import sqlite3
from flask import g, current_app

# Função para obter conexão com o banco de dados, respeitando configuração em current_app

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


import pytest

@pytest.fixture(autouse=True)
def initialize_database(app):
    with app.app_context():
        init_db()
    yield

# Função para fechar a conexão ao fim da requisição
def close_connection(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
def init_db():
    db = get_db()
    cursor = db.cursor()

    # Verifica se a tabela 'users' existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    table_exists = cursor.fetchone()

    if table_exists:
        # Verifica se a coluna 'is_admin' existe
        cursor.execute("PRAGMA table_info(users);")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_admin' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;")
            db.commit()
    else:
        # Cria as tabelas, já que não existe a tabela 'users'
        cursor.executescript('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                failed_attempts INTEGER DEFAULT 0,
                locked_until DATETIME,
                created_at DATETIME,
                is_admin BOOLEAN DEFAULT 0
            );

            CREATE TABLE uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                num_rows INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER NOT NULL,
                passenger_id TEXT,
                prediction TEXT,
                probability REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (upload_id) REFERENCES uploads(id)
            );

            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                preference_name TEXT NOT NULL,
                preference_value TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        db.commit()

    # Atualiza o usuário 'test' para admin, se existir
    try:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('test',))
        db.commit()
    except sqlite3.OperationalError as e:
        current_app.logger.error(f"Erro ao definir admin: {e}")
