import os
from datetime import timedelta
from flask import Flask, redirect, url_for
from flask_wtf import CSRFProtect
from flasgger import Swagger

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

    # Garante que a pasta de uploads existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializa proteção CSRF
    csrf = CSRFProtect(app)

    # Inicializa o rate limiter
    limiter.init_app(app)
    app.limiter = limiter

    # Swagger / OpenAPI (somente se não estiver em modo de teste)
    if not testing:
        swagger_config = {
            "headers": [],
            "specs": [
                {
                    "endpoint": "apispec",
                    "route": "/apispec.yaml",
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/apidocs/"
        }

        # Caminho para o template OpenAPI YAML
        template_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            os.pardir,
            'openapi.yaml'
        )

        Swagger(app, config=swagger_config, template_file=template_path)

    # Blueprints
    from app.auth import auth
    from app.prediction import prediction
    from app.history import history_bp
    from app.admin import admin_bp

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(prediction, url_prefix='/prediction')
    app.register_blueprint(history_bp, url_prefix='/history')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Redirecionamento da raiz '/' para '/prediction'
    @app.route('/')
    def index_redirect():
        return redirect(url_for('prediction.index'))

    # Fecha conexão com DB ao encerrar contexto
    app.teardown_appcontext(close_connection)

    return app
