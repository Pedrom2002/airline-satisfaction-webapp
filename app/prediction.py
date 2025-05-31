from flask import Blueprint, request, session, redirect, url_for, render_template, flash, current_app as app
from markupsafe import Markup
import os
import uuid
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, roc_auc_score
from werkzeug.utils import secure_filename

# Importações do próprio projeto
from app.extensions import limiter
from app.auth import login_required
from app.eda import (
    perform_eda,
    build_sorted_correlation_table,
    generate_prediction_distribution_plot,
    generate_probability_distribution_plot,
    generate_age_group_distribution,
    generate_delay_category_plot,
    generate_pizza_charts,
    load_model_assets
)
from app.database import get_db

# Criação do blueprint para rotas de predição
prediction = Blueprint('prediction', __name__)

# Carregamento dos artefatos do modelo (modelo, pre-processador, codificador e nomes das features)
model, preprocessor, label_encoder, feature_columns = load_model_assets()

# Função auxiliar para verificar se o ficheiro é CSV
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

@prediction.route('/', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per minute")  # Limite de 10 requisições por minuto por usuário
def index():
    if request.method == 'POST':
        user_id = session.get('user_id')
        action = request.form.get('action')

        if action == 'use_sample':
            # Usar CSV de exemplo local
            test_path = os.path.join('static', 'test.csv')
            if not os.path.exists(test_path):
                flash('Arquivo de exemplo não encontrado.', 'error')
                return redirect(request.url)
            df = pd.read_csv(test_path)
            original_filename = 'test.csv'

        elif action == 'upload':
            file = request.files.get('file')

            if not file or file.filename == '':
                flash('Por favor, envie um arquivo CSV para processar.', 'error')
                return redirect(request.url)

            if not allowed_file(file.filename):
                flash('Por favor, envie um arquivo CSV válido.', 'error')
                return redirect(request.url)

            try:
                df = pd.read_csv(file)
                original_filename = file.filename
            except Exception as e:
                flash(f'Erro ao ler o CSV: {e}', 'error')
                return redirect(request.url)
        else:
            flash('Ação inválida.', 'error')
            return redirect(request.url)

        # ------------------- Engenharia de features -------------------

        df['total_delay'] = df['Departure Delay in Minutes'].fillna(0) + df['Arrival Delay in Minutes'].fillna(0)
        df['delay_ratio'] = df['total_delay'] / (df['Flight Distance'] + 1)
        df['delay_indicator'] = (df['total_delay'] > 0).astype(int)

        service_cols = [
            'Inflight wifi service', 'Departure/Arrival time convenient', 'Ease of Online booking',
            'Gate location', 'Food and drink', 'Online boarding', 'Seat comfort',
            'Inflight entertainment', 'On-board service', 'Leg room service',
            'Baggage handling', 'Checkin service', 'Inflight service', 'Cleanliness'
        ]

        df['service_score'] = df[service_cols].mean(axis=1)
        df['service_consistency'] = df[service_cols].std(axis=1)

        eps = 1e-9
        total_service = df[service_cols].sum(axis=1) + eps
        probs = df[service_cols].div(total_service, axis=0)
        df['service_entropy'] = - (probs * np.log(probs + eps)).sum(axis=1)

        df['age_group'] = pd.cut(df['Age'], bins=[0,18,35,60,120], labels=['Child','Young','Adult','Senior'])

        bins = [-1,0,15,60,np.inf]
        labels = ['No Delay','Short','Moderate','Severe']
        df['delay_category'] = pd.cut(df['total_delay'], bins=bins, labels=labels)

        kmeans = KMeans(n_clusters=3, random_state=42)
        df['cluster'] = kmeans.fit_predict(df[['service_score', 'total_delay']])

        df_model = df.drop(columns=['id', 'satisfaction', 'age_group', 'delay_category', 'cluster'], errors='ignore')

        X_proc = preprocessor.transform(df_model)
        df_proc = pd.DataFrame(X_proc, columns=feature_columns)

        preds = model.predict(df_proc)
        probas = model.predict_proba(df_proc)[:, 1]

        df['prediction'] = label_encoder.inverse_transform(preds)
        df['probability'] = probas

        if 'satisfaction' in df.columns:
            true_labels = label_encoder.transform(df['satisfaction'])
            accuracy = round(accuracy_score(true_labels, preds) * 100, 2)
            roc_auc = round(roc_auc_score(true_labels, probas) * 100, 2)
        else:
            accuracy = None
            roc_auc = None

        if 'satisfaction_flag' not in df.columns and 'satisfaction' in df.columns:
            df['satisfaction_flag'] = (df['satisfaction'] == 'satisfied').astype(int)

        # ------------------- EDA e visualizações -------------------

        eda_html, df = perform_eda(df)
        corr_df = build_sorted_correlation_table(df)
        corr_table_html = corr_df.to_html(classes='data correlation-sorted', index=False)

        graph_html       = generate_prediction_distribution_plot(df)
        prob_html        = generate_probability_distribution_plot(probas)
        age_group_html   = generate_age_group_distribution(df)
        delay_cat_html   = generate_delay_category_plot(df)

        pizza_imgs = generate_pizza_charts(df, [
            'Online boarding', 'Inflight entertainment', 'Seat comfort', 'On-board service', 'Cleanliness', 'Leg room service',
            'Inflight wifi service', 'Baggage handling', 'Checkin service', 'Inflight service', 'Food and drink',
            'Ease of Online booking', 'Flight Distance_grupo', 'Age_grupo'
        ])

        df_display = df.copy()
        if 'satisfaction_flag' in df_display.columns:
            df_display = df_display.drop(columns=['satisfaction_flag'])
        cols_to_move = ['satisfaction', 'prediction', 'probability']
        cols_to_move = [c for c in cols_to_move if c in df_display.columns]
        cols = [c for c in df_display.columns if c not in cols_to_move] + cols_to_move
        df_display = df_display[cols]
        df_display_limited = df_display.head(100)
        df_table_html = df_display_limited.to_html(classes='data', index=False)

        metrics = {
            'avg_total_delay': round(df['total_delay'].mean(), 2),
            'avg_delay_ratio': round(df['delay_ratio'].mean(), 4),
            'delay_indicator_rate': round(df['delay_indicator'].mean() * 100, 2),
            'avg_service_score': round(df['service_score'].mean(), 2),
            'avg_service_consistency': round(df['service_consistency'].mean(), 2),
            'avg_service_entropy': round(df['service_entropy'].mean(), 4)
        }

        out_csv = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4().hex}_predictions.csv")
        df.to_csv(out_csv, index=False)

        conn = get_db()
        cursor = conn.execute(
            '''INSERT INTO uploads (user_id, filename, original_filename, processed, num_rows)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, os.path.basename(out_csv), original_filename, 1, len(df))
        )
        conn.commit()
        upload_id = cursor.lastrowid

        for idx, row in df.iterrows():
            passenger_id = str(row.get('id', ''))
            conn.execute(
                '''INSERT INTO predictions (upload_id, passenger_id, prediction, probability)
                   VALUES (?, ?, ?, ?)''',
                (upload_id, passenger_id, row['prediction'], float(row['probability']))
            )
        conn.commit()

        flash('Arquivo processado com sucesso!', 'success')

        return render_template(
            'results.html',
            eda_html=eda_html,
            num_passengers=len(df),
            satisfaction_rate=round((preds == 1).mean() * 100, 2),
            avg_proba=round(probas.mean() * 100, 2),
            accuracy=accuracy,
            roc_auc=roc_auc,
            avg_total_delay=metrics['avg_total_delay'],
            avg_delay_ratio=metrics['avg_delay_ratio'],
            delay_indicator_rate=metrics['delay_indicator_rate'],
            avg_service_score=metrics['avg_service_score'],
            avg_service_consistency=metrics['avg_service_consistency'],
            avg_service_entropy=metrics['avg_service_entropy'],
            graph_html=graph_html,
            prob_html=prob_html,
            age_group_html=age_group_html,
            delay_cat_html=delay_cat_html,
            pizza_imgs=pizza_imgs,
            df_table_html=Markup(df_table_html),
            tables=[Markup(corr_table_html)],
            filename=os.path.basename(out_csv)
        )

    # GET renderiza página de upload
    return render_template('index.html')
