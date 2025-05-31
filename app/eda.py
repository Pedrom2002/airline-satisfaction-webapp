import pandas as pd
import plotly.express as px
import plotly.io as pio
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, roc_auc_score
import numpy as np
from scipy.stats import entropy
import joblib

# --- Função para carregar os modelos e objetos necessários para predição ---
def load_model_assets():
    # Carrega o modelo final treinado (XGBoost neste caso)
    model = joblib.load('models/xgb_final_model.pkl')
    # Carrega o pré-processador usado para preparar os dados (ex: transformação, codificação)
    preprocessor = joblib.load('models/preprocessor.pkl')
    # Carrega o codificador de labels para transformar rótulos em números e vice-versa
    label_encoder = joblib.load('models/label_encoder.pkl')
    # Carrega a lista/ordem das colunas usadas como features no modelo
    feature_columns = pd.read_json('models/feature_columns.json')

    # Retorna todos os objetos para usar na aplicação
    return model, preprocessor, label_encoder, feature_columns

# --- Função para criar tabelas HTML para EDA (Análise Exploratória de Dados) ---
def generate_eda_tables(df):
    tables = {}
    # Seleciona só colunas numéricas para análise
    numeric_cols = df.select_dtypes(include='number')
    # Se existir a coluna 'satisfaction', calcula correlações com outras variáveis numéricas
    if 'satisfaction' in numeric_cols.columns:
        corr = numeric_cols.corr()['satisfaction'].drop('satisfaction').sort_values(ascending=False)
        corr_df = pd.DataFrame({'Variável': corr.index, 'Correlação': corr.values})
        # Filtra para mostrar só correlações acima de 0.1 (em módulo)
        corr_df = corr_df[abs(corr_df['Correlação']) >= 0.1]
        # Transforma a tabela em HTML para ser exibida na web
        tables['correlation_table_sorted'] = corr_df.to_html(classes='data', index=False)
    return tables

# --- Função para construir tabela detalhada de correlações entre todas variáveis numéricas ---
def build_sorted_correlation_table(df, threshold=0.1):
    # Pega só as colunas numéricas
    num_cols = df.select_dtypes(include=['number']).columns
    # Calcula matriz de correlação absoluta arredondada
    corr = df[num_cols].corr().abs().round(2)
    # Transforma a matriz em formato "long" para listar pares de features e suas correlações
    corr_long = (
        corr
        .stack()
        .reset_index()
        .rename(columns={'level_0': 'Feature 1', 'level_1': 'Feature 2', 0: 'Correlation'})
    )
    # Remove pares iguais e filtra só correlações acima do limite (threshold)
    corr_long = corr_long[
        (corr_long['Feature 1'] != corr_long['Feature 2']) &
        (corr_long['Correlation'] >= threshold)
    ]
    # Cria um par ordenado para evitar duplicatas (ex: (A,B) == (B,A))
    corr_long['pair'] = corr_long.apply(
        lambda row: tuple(sorted([row['Feature 1'], row['Feature 2']])),
        axis=1
    )
    # Remove pares repetidos e ordena pela correlação decrescente
    corr_long = corr_long.drop_duplicates('pair').drop(columns='pair')
    corr_long = corr_long.sort_values(by='Correlation', ascending=False).reset_index(drop=True)
    return corr_long

# --- Função que gera um resumo estatístico e métricas do dataframe e resultados de predição ---
def generate_summary(df, y_true=None, y_pred=None, y_prob=None):
    summary = {}
    # Total de passageiros analisados
    summary['num_passengers'] = len(df)
    # Percentual de passageiros classificados como satisfeitos na predição
    summary['satisfaction_rate'] = round(df['prediction'].value_counts(normalize=True).get('satisfied', 0) * 100, 2)
    # Média das probabilidades previstas (confiança do modelo)
    summary['avg_proba'] = round(y_prob.mean() * 100, 2) if y_prob is not None else 0
    # Acurácia da predição (se houver dados verdadeiros)
    summary['accuracy'] = round(accuracy_score(y_true, y_pred) * 100, 2) if y_true is not None else None
    # AUC ROC para avaliar qualidade da predição probabilística
    summary['roc_auc'] = round(roc_auc_score(y_true, y_prob) * 100, 2) if y_true is not None else None

    # Calcula o atraso total somando atraso de partida e chegada (considerando valores ausentes como zero)
    df['total_delay'] = df['Departure Delay in Minutes'].fillna(0) + df['Arrival Delay in Minutes'].fillna(0)
    # Média do atraso total
    summary['avg_total_delay'] = round(df['total_delay'].mean(), 1)
    # Percentual de passageiros com atraso acima de 10 minutos
    summary['delay_indicator_rate'] = round((df['total_delay'] > 10).mean() * 100, 2)

    # Lista das colunas relacionadas a serviço a bordo
    service_cols = [
        'Inflight wifi service', 'Food and drink', 'Seat comfort', 'Inflight entertainment',
        'On-board service', 'Leg room service', 'Baggage handling', 'Checkin service',
        'Inflight service', 'Cleanliness'
    ]
    # Média geral da nota dos serviços (em todas as colunas de serviço)
    summary['avg_service_score'] = round(df[service_cols].mean().mean(), 2)
    # Consistência das avaliações de serviço (desvio padrão médio por passageiro)
    summary['avg_service_consistency'] = round(df[service_cols].std(axis=1).mean(), 2)
    # Média de idade dos passageiros
    summary['avg_age'] = round(df['Age'].mean(), 1)
    # Desvio padrão das probabilidades previstas
    summary['std_proba'] = round(y_prob.std() * 100, 2) if y_prob is not None else None

    # Calcula a entropia média das probabilidades para medir a incerteza do modelo
    if y_prob is not None:
        clipped_probs = y_prob.clip(1e-15, 1 - 1e-15)
        entropies = - (clipped_probs * np.log2(clipped_probs) + (1 - clipped_probs) * np.log2(1 - clipped_probs))
        summary['entropy'] = round(entropies.mean(), 3)
    else:
        summary['entropy'] = None

    # Proporção do atraso em relação à distância do voo
    df['delay_ratio'] = df['total_delay'] / (df['Flight Distance'] + 1)
    summary['avg_delay_ratio'] = round(df['delay_ratio'].mean(), 4)

    return summary

# --- Função para criar gráfico da distribuição das previsões (satisfeito x insatisfeito) ---
def generate_prediction_distribution_plot(df):
    fig = px.histogram(df, x='prediction', color='prediction', title='Distribuição das Previsões')
    fig.update_layout(template='plotly_dark')  # tema escuro para o gráfico
    return pio.to_html(fig, full_html=False)

# --- Função para criar gráfico da distribuição das probabilidades previstas ---
def generate_probability_distribution_plot(y_prob):
    fig = px.histogram(x=y_prob, nbins=50, title='Distribuição das Probabilidades de Satisfação')
    fig.update_layout(template='plotly_dark', xaxis_title='Probabilidade', yaxis_title='Frequência')
    return pio.to_html(fig, full_html=False)

# --- Função para gerar gráfico de distribuição por faixas etárias ---
def generate_age_group_distribution(df):
    if 'Age' in df.columns:
        bins = [0, 18, 30, 45, 60, 100]
        labels = ['0–17', '18–30', '31–45', '46–60', '60+']
        # Cria uma nova coluna categorizando as idades em grupos
        df['age_group'] = pd.cut(df['Age'], bins=bins, labels=labels, include_lowest=True)
        fig = px.histogram(df, x='age_group', color='prediction', barmode='group', title='Distribuição por Faixa Etária')
        fig.update_layout(template='plotly_dark', xaxis_title='Faixa Etária', yaxis_title='Contagem')
        return pio.to_html(fig, full_html=False)
    return None

# --- Função para gerar gráfico de distribuição por categoria de atraso ---
def generate_delay_category_plot(df):
    if 'total_delay' in df.columns:
        # Função auxiliar para categorizar o atraso em faixas qualitativas
        def categorize_delay(x):
            if x <= 0:
                return 'Sem Atraso'
            elif x <= 10:
                return 'Leve'
            elif x <= 30:
                return 'Moderado'
            else:
                return 'Grave'
        # Aplica a categorização ao dataframe
        df['delay_category'] = df['total_delay'].apply(categorize_delay)
        fig = px.histogram(df, x='delay_category', color='prediction', barmode='group', title='Distribuição por Categoria de Atraso')
        fig.update_layout(template='plotly_dark', xaxis_title='Categoria de Atraso', yaxis_title='Contagem')
        return pio.to_html(fig, full_html=False)
    return None

import plotly.express as px
import plotly.io as pio

# --- Função para gerar vários gráficos estilo “pizza” (barras horizontais) para variáveis categóricas ---
def generate_pizza_charts(df, vars_to_plot):
    pizza_imgs = {}

    # Cria faixas agrupadas para distância do voo (se ainda não existirem)
    if 'Flight Distance' in df.columns and 'Flight Distance_grupo' not in df.columns:
        df['Flight Distance_grupo'] = pd.cut(
            df['Flight Distance'], 5,
            labels=['Muito Curto','Curto','Médio','Longo','Muito Longo']
        )
    # Cria faixas agrupadas para idade (se ainda não existirem)
    if 'Age' in df.columns and 'Age_grupo' not in df.columns:
        df['Age_grupo'] = pd.cut(
            df['Age'], [0,25,40,55,70,100],
            labels=['<=25','26-40','41-55','56-70','70+']
        )

    # Escolhe qual coluna usar para calcular percentual de satisfeitos:
    # Prioriza a coluna com valor real ('satisfaction_flag'), senão usa a predita
    if 'satisfaction_flag' in df.columns:
        flag_col = 'satisfaction_flag'
    elif 'prediction' in df.columns:
        # Cria uma coluna binária para predição: 1 se satisfeito, 0 caso contrário
        df['prediction_flag'] = (df['prediction'] == 'satisfied').astype(int)
        flag_col = 'prediction_flag'
    else:
        # Se não tiver como calcular, retorna vazio
        return pizza_imgs

    # Para cada variável categórica, gera gráfico de barras horizontais mostrando % de satisfeitos por categoria
    for var in vars_to_plot:
        if var not in df.columns:
            continue
        s = df.groupby(var)[flag_col].mean().reset_index()
        s['pct'] = (s[flag_col] * 100).round(1)
        s = s.dropna()
        fig = px.bar(
            s,
            y=var,
            x='pct',
            orientation='h',
            title=f'% Satisfeitos por {var}',
            template='plotly_dark',
            text='pct'
        )
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(
            width=350,
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            title_x=0.5,
            xaxis=dict(range=[0,100], title='% Satisfeitos'),
            yaxis=dict(title=var)
        )
        # Salva o gráfico em formato HTML dentro do dicionário
        pizza_imgs[var] = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

    return pizza_imgs

# --- Função principal que reúne toda análise exploratória e gráficos para retornar para frontend ---
def perform_eda(df):
    eda_html = {}
    # Gera as tabelas em HTML da análise básica (correlações, etc)
    eda_html.update(generate_eda_tables(df))
    # Gráfico da distribuição das previsões
    eda_html['graph_html']     = generate_prediction_distribution_plot(df)
    # Gráfico da distribuição das probabilidades previstas
    eda_html['prob_html']      = generate_probability_distribution_plot(df['probability'])
    # Gráfico de distribuição por faixa etária
    eda_html['age_group_html'] = generate_age_group_distribution(df)
    # Gráfico de distribuição por categoria de atraso
    eda_html['delay_cat_html'] = generate_delay_category_plot(df)
    # Gera gráficos para variáveis categóricas principais
    vars_to_plot = ['Gender', 'Customer Type', 'Type of Travel', 'Class']
    eda_html['pizza_imgs'] = generate_pizza_charts(df, vars_to_plot)
    # Retorna o dicionário com todo HTML dos gráficos e tabelas, junto com o dataframe para uso posterior
    return eda_html, df
