from flask import Blueprint, render_template, session, send_file, abort, current_app
from flask_restx import Namespace, Resource
import os
from app.database import get_db
from app.auth import login_required
from app.extensions import limiter

# Blueprint para rotas da interface web
history_bp = Blueprint('history', __name__)

# Página de histórico de uploads (interface web)
@history_bp.route('/history')
@login_required
@limiter.limit("10 per minute")
def history():
    user_id = session.get('user_id')
    conn = get_db()
    uploads = conn.execute(
        '''SELECT id, original_filename, filename, upload_date, processed, num_rows
           FROM uploads WHERE user_id = ? ORDER BY upload_date DESC''',
        (user_id,)
    ).fetchall()
    return render_template('history.html', uploads=uploads)

# Rota de download (interface web)
@history_bp.route('/download/<filename>')
@login_required
@limiter.limit("10 per minute")
def download_file(filename):
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    abort(404)

# Página personalizada de erro 404
@history_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
from flask import Blueprint, render_template, session, send_file, abort, current_app
import os
from app.database import get_db  # Importa função para conectar ao banco de dados
from app.auth import login_required  # Decorator para proteger rotas, exige login

# Cria um blueprint chamado 'history' para organizar as rotas relacionadas ao histórico de uploads
history_bp = Blueprint('history', __name__)

# Rota para a página de histórico de uploads do usuário
@history_bp.route('/history')
@login_required  # Protege a rota, só permite acesso se o usuário estiver logado
def history():
    user_id = session.get('user_id')  # Pega o id do usuário logado na sessão
    conn = get_db()  # Abre conexão com o banco de dados
    # Busca no banco todos os uploads feitos por esse usuário, ordenados pela data mais recente
    uploads = conn.execute(
        '''SELECT id, original_filename, filename, upload_date, processed, num_rows
           FROM uploads WHERE user_id = ? ORDER BY upload_date DESC''',
        (user_id,)
    ).fetchall()

    # Renderiza a página history.html, enviando a lista de uploads para exibição
    return render_template('history.html', uploads=uploads)

# Rota para download do arquivo CSV processado pelo usuário
@history_bp.route('/download/<filename>')
@login_required  # Também protege o download, só usuários logados podem baixar
def download_file(filename):
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)  # Caminho completo do arquivo
    if os.path.exists(path):  # Verifica se o arquivo existe no servidor
        return send_file(path, as_attachment=True)  # Envia o arquivo para download
    abort(404)  # Se não existir, retorna erro 404 (arquivo não encontrado)

# Tratador de erro 404 para o blueprint, renderiza uma página customizada
@history_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
