from flask import Blueprint, render_template, abort, request, g
from functools import wraps
import math
from app.database import get_db
from app.auth import login_required
from flask import redirect, url_for, flash
from app.extensions import limiter


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Decorator para garantir que o usuário seja admin ---
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user or not bool(user['is_admin']):
            abort(403)
        return f(*args, **kwargs)
    return decorated

# Define quais tabelas o admin pode gerenciar
ALLOWED_TABLES = ['users', 'uploads', 'predictions', 'logs', 'user_settings']

@admin_bp.route('/')
@login_required
@admin_required
def admin_index():
    return render_template('admin/index.html', tables=ALLOWED_TABLES)

@admin_bp.route('/table/<table>/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@limiter.limit("50 per minute")
def admin_edit(table, record_id):
    if table not in ALLOWED_TABLES:
        abort(403)

    db = get_db()
    cursor = db.cursor()

    # Pega colunas da tabela
    cursor.execute(f"PRAGMA table_info({table})")
    columns_info = cursor.fetchall()
    columns = [col[1] for col in columns_info if col[5] == 0]  # ignora PK autoincremento

    if request.method == 'POST':
        data = {col: request.form.get(col) for col in columns if col in request.form}
        update_clause = ', '.join(f"{key}=?" for key in data.keys())
        values = list(data.values()) + [record_id]

        cursor.execute(
            f"UPDATE {table} SET {update_clause} WHERE id = ?",
            values
        )
        db.commit()

        # ✅ Mensagem flash + redirecionamento para admin_table
        flash("Alteração concluída!", "success")
        return redirect(url_for('admin.admin_table', table=table))

    # GET: carrega dados do registro
    cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
    record = cursor.fetchone()
    if not record:
        abort(404)

    return render_template(
        'admin/edit.html',
        table=table,
        row=record,
        columns=columns
    )


@admin_bp.route('/table/<table>')
@login_required
@limiter.limit("50 per minute")
@admin_required
def admin_table(table):
    if table not in ALLOWED_TABLES:
        abort(403)

    db = get_db()
    cursor = db.cursor()

    # Pega colunas da tabela para mostrar no template
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]

    # Parâmetros da busca
    search = request.args.get('search', '').strip()
    column = request.args.get('column', columns[0] if columns else 'id')

    # Paginação
    page = max(int(request.args.get('page', 1)), 1)
    per_page = 50
    offset = (page - 1) * per_page

    # Consulta com filtro de busca, se informado
    if search and column:
        like = f"%{search}%"
        cursor.execute(
            f"SELECT * FROM {table} WHERE {column} LIKE ? LIMIT ? OFFSET ?",
            (like, per_page, offset)
        )
        rows = cursor.fetchall()
        cursor.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {column} LIKE ?",
            (like,)
        )
        total = cursor.fetchone()[0]
    else:
        cursor.execute(
            f"SELECT * FROM {table} LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        rows = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total = cursor.fetchone()[0]

    total_pages = math.ceil(total / per_page) if total else 1

    return render_template(
        'admin/table.html',
        table=table,
        columns=columns,
        rows=rows,
        search=search,
        column=column,
        page=page,
        total_pages=total_pages
    )

from flask import flash, redirect, url_for

@admin_bp.route('/table/<table>/delete/<int:record_id>', methods=['POST'])
@login_required
@limiter.limit("50 per minute")
@admin_required
def admin_delete(table, record_id):
    if table not in ALLOWED_TABLES:
        abort(403)

    db = get_db()
    cursor = db.cursor()

    cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
    record = cursor.fetchone()
    if not record:
        abort(404)

    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    db.commit()

    flash('Registro deletado com sucesso!', 'success')
    return redirect(url_for('admin.admin_table', table=table))
