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
