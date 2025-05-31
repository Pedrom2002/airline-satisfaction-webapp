import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from app.database import get_db, close_connection, init_db
from flask import g


def test_get_db_returns_connection(app):
    with app.app_context():
        conn = get_db()
        assert isinstance(conn, sqlite3.Connection)
        assert g.db is conn


def test_close_connection_removes_db_from_g(app):
    with app.app_context():
        get_db()
        assert 'db' in g
        close_connection()
        assert 'db' not in g


def test_init_db_creates_tables_and_admin(app):
    with app.app_context():
        init_db()
        db = get_db()
        cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        assert cursor.fetchone() is not None

        cursor = db.execute("PRAGMA table_info(users);")
        columns = [col[1] for col in cursor.fetchall()]
        assert 'is_admin' in columns

        # Força inserção de admin fictício
        db.execute("INSERT OR IGNORE INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                   ('test', 'test@example.com', 'hashedpass'))
        db.commit()

        init_db()  # Reexecuta para testar o UPDATE do admin

        cursor = db.execute("SELECT is_admin FROM users WHERE username = ?", ('test',))
        result = cursor.fetchone()
        assert result is not None
        assert result['is_admin'] == 1

# Testa get_db: cobertura para linhas 20-22 (conexao e row_factory)
def test_get_db_sets_connection_and_row_factory(app):
    with app.app_context():
        # Limpa g.db antes do teste
        if 'db' in g:
            g.pop('db')

        with patch('app.database.sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            db = get_db()

            mock_connect.assert_called_once_with(
                app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES
            )
            assert g.db == mock_conn
            assert mock_conn.row_factory == sqlite3.Row


def test_close_connection_closes_db(app):
    with app.app_context():
        mock_db = MagicMock()
        g.db = mock_db  # simula conexão no contexto

        close_connection()

        mock_db.close.assert_called_once()
        assert 'db' not in g


def test_init_db_update_admin_operational_error(app):
    with app.app_context():
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Simula que tabela 'users' existe
        mock_cursor.fetchone.return_value = ('users',)

        # Simula colunas existentes na tabela (com estrutura correta)
        mock_cursor.fetchall.return_value = [
            (0, 'id'), (1, 'username'), (2, 'email'),
            (3, 'password_hash'), (4, 'failed_attempts'),
            (5, 'locked_until'), (6, 'created_at'),
            # 'is_admin' ainda não está presente
        ]

        # Simula erro operacional no UPDATE
        def execute_side_effect(query, params=None):
            if query.startswith("UPDATE users SET is_admin"):
                raise sqlite3.OperationalError("Erro simulado")
        mock_cursor.execute.side_effect = execute_side_effect
        mock_conn.cursor.return_value = mock_cursor

        with patch('app.database.get_db', return_value=mock_conn), \
             patch('app.database.current_app') as mock_current_app:

            mock_logger = MagicMock()
            mock_current_app.logger = mock_logger

            init_db()

            mock_logger.error.assert_called_once()
