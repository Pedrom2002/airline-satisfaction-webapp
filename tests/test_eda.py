import pandas as pd
import numpy as np
import pytest
from utils import eda

# Criação de um DataFrame fictício de exemplo
@pytest.fixture
def sample_df():
    data = {
        'Age': [25, 40, 35, 60, 50],
        'Flight Distance': [200, 400, 300, 500, 600],
        'Departure Delay in Minutes': [5, 0, 10, 20, 15],
        'Arrival Delay in Minutes': [5, 0, 0, 10, 15],
        'Inflight wifi service': [3, 4, 5, 2, 1],
        'Food and drink': [4, 3, 2, 5, 1],
        'Seat comfort': [4, 3, 5, 3, 2],
        'Inflight entertainment': [4, 4, 4, 5, 1],
        'On-board service': [4, 3, 5, 2, 2],
        'Leg room service': [3, 3, 4, 4, 1],
        'Baggage handling': [5, 5, 4, 3, 2],
        'Checkin service': [3, 4, 5, 2, 2],
        'Inflight service': [4, 3, 5, 4, 1],
        'Cleanliness': [4, 3, 4, 5, 1],
        'prediction': ['satisfied', 'neutral', 'satisfied', 'neutral', 'satisfied'],
        'probability': [0.9, 0.4, 0.85, 0.6, 0.95],
        'satisfaction': [1, 0, 1, 0, 1],
        'Gender': ['Male', 'Female', 'Male', 'Female', 'Male'],
        'Customer Type': ['Loyal', 'Disloyal', 'Loyal', 'Disloyal', 'Loyal'],
        'Type of Travel': ['Business', 'Personal', 'Business', 'Personal', 'Business'],
        'Class': ['Business', 'Economy', 'Economy', 'Business', 'Economy']
    }
    return pd.DataFrame(data)

# Testa se os gráficos e tabelas principais são gerados
def test_perform_eda_outputs(sample_df):
    result, df_out = eda.perform_eda(sample_df.copy())
    expected_keys = [
        'correlation_table_sorted', 'graph_html', 'prob_html',
        'age_group_html', 'delay_cat_html', 'pizza_imgs'
    ]
    for key in expected_keys:
        assert key in result
        if isinstance(result[key], str):
            assert "<div" in result[key] or "<table" in result[key]  # Verifica se é HTML

# Testa a função generate_summary
def test_generate_summary(sample_df):
    y_true = sample_df['satisfaction']
    y_pred = sample_df['prediction'].apply(lambda x: 1 if x == 'satisfied' else 0)
    y_prob = sample_df['probability']
    summary = eda.generate_summary(sample_df.copy(), y_true, y_pred, y_prob)
    assert 'num_passengers' in summary
    assert isinstance(summary['num_passengers'], int)
    assert summary['entropy'] is not None

# Testa a tabela de correlação ordenada
def test_build_sorted_correlation_table(sample_df):
    table = eda.build_sorted_correlation_table(sample_df)
    assert not table.empty
    assert 'Feature 1' in table.columns
    assert 'Feature 2' in table.columns
    assert 'Correlation' in table.columns
