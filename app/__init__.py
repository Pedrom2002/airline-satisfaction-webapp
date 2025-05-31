from datetime import timedelta
from flask import Flask, redirect, url_for
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
import os

from app.database import init_db, close_connection
from app.extensions import limiter  # Rate limiter


def create_app(testing=False):
    app = Flask(__name__)

    # Configurações gerais
    app.config['SECRET_KEY'] = 'test123'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    app.config['DATABASE'] = 'users.db'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    if testing:
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DATABASE'] = ':memory:'
        app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'tests', 'uploads')

    # Detecta ambiente pela variável FLASK_ENV (default: development)
    env = os.getenv('FLASK_ENV', 'development')  # <-- aqui foi alterado para 'development'

    # Configurações importantes para cookies de sessão (segurança)
    app.config.update(
        SESSION_COOKIE_SECURE=(env != 'development'),  # True em produção, False em dev/local
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict'
    )

    # Garante que a pasta de uploads existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializa proteção CSRF
    csrf = CSRFProtect(app)

    # Inicializa o rate limiter
    limiter.init_app(app)
    app.limiter = limiter

    # Aplica Talisman APENAS se estiver em produção
    if env == 'production':
        Talisman(app,
                 force_https=True,
                 strict_transport_security=True,
                 strict_transport_security_max_age=31536000,  # 1 ano em segundos
                 strict_transport_security_include_subdomains=True)

    # Swagger / OpenAPI (somente se não estiver em modo de teste)
    if not testing:
        template_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            os.pardir,
            'openapi.yaml'
        )
        # Pode carregar o template ou configurar aqui

    # Importa blueprints e registra
    from app.auth import auth
    from app.prediction import prediction
    from app.history import history_bp
    from app.admin import admin_bp

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(prediction, url_prefix='/prediction')
    app.register_blueprint(history_bp, url_prefix='/history')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Redireciona '/' para '/prediction'
    @app.route('/')
    def index_redirect():
        return redirect(url_for('prediction.index'))

    # Fecha conexão com DB ao encerrar contexto
    app.teardown_appcontext(close_connection)

    return app
