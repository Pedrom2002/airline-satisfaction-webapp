import io
import pytest
from unittest.mock import patch, MagicMock
from flask import url_for

from unittest.mock import patch, MagicMock

from collections import namedtuple
from unittest.mock import patch, MagicMock

def test_history_route(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    Upload = namedtuple('Upload', ['id', 'original_filename', 'filename', 'upload_date', 'processed', 'num_rows'])
    fake_uploads = [
        Upload(1, 'original.csv', 'file1.csv', '2023-01-01', True, 100),
        Upload(2, 'original2.csv', 'file2.csv', '2023-02-01', False, 50)
    ]

    with patch('app.history.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = fake_uploads
        mock_get_db.return_value = mock_conn

        response = client.get('/history')

        assert response.status_code == 200

        html = response.get_data(as_text=True)
        for upload in fake_uploads:
            assert upload.original_filename in html



import os
from unittest.mock import patch

def test_download_file_exists(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    filename = 'file1.csv'
    expected_path = os.path.join('/fake/path', filename)

    with patch('app.history.current_app') as mock_app, \
         patch('app.history.os.path.exists') as mock_exists, \
         patch('app.history.send_file') as mock_send_file:

        mock_app.config = {'UPLOAD_FOLDER': '/fake/path'}
        mock_exists.return_value = True
        mock_send_file.return_value = MagicMock(name='response')

        response = client.get(f'/download/{filename}')

        mock_exists.assert_called_once_with(expected_path)
        mock_send_file.assert_called_once_with(expected_path, as_attachment=True)
        mock_send_file.assert_called_once_with(expected_path, as_attachment=True)



# Testa o download de arquivo inexistente (404)
def test_download_file_not_found(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    filename = 'missing.csv'

    with patch('app.history.current_app') as mock_app, \
         patch('app.history.os.path.exists') as mock_exists:

        mock_app.config = {'UPLOAD_FOLDER': '/fake/path'}
        mock_exists.return_value = False

        response = client.get(f'/download/{filename}')
        assert response.status_code == 404
        assert 'Página não encontrada' in response.get_data(as_text=True)  # ou texto que seu 404.html tem

# Testa handler customizado 404 (opcional)
def test_custom_404_handler(client):
    response = client.get('/some/invalid/url')
    assert response.status_code == 404
    assert 'Página não encontrada' in response.get_data(as_text=True)  # texto do seu 404.html
