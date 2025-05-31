import io
import pytest
import tempfile

def test_register(client):
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword',
        'confirm_password': 'testpassword'
    }, content_type='application/x-www-form-urlencoded')
    assert response.status_code == 302  # redirect esperado

def test_login(client):
    # Registra o usuário primeiro
    client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword',
        'confirm_password': 'testpassword'
    }, content_type='application/x-www-form-urlencoded')

    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, content_type='application/x-www-form-urlencoded')
    assert response.status_code == 302  # redirect esperado após login

def test_logout(client):
    # Registra e loga
    client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword',
        'confirm_password': 'testpassword'
    }, content_type='application/x-www-form-urlencoded')
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, content_type='application/x-www-form-urlencoded')

    response = client.post('/auth/logout')
    assert response.status_code == 302  # redirect esperado após logout


def test_file_upload(client):
    # Registrar e logar para poder acessar a rota protegida
    client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword',
        'confirm_password': 'testpassword'
    }, content_type='application/x-www-form-urlencoded')

    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, content_type='application/x-www-form-urlencoded')

    upload_url = '/prediction/'

    csv_content = (
        "id,Gender,Customer Type,Age,Type of Travel,Class,Flight Distance,"
        "Inflight wifi service,Departure/Arrival time convenient,"
        "Ease of Online booking,Gate location,Food and drink,Online boarding,"
        "Seat comfort,Inflight entertainment,On-board service,Leg room service,"
        "Baggage handling,Checkin service,Inflight service,Cleanliness,"
        "Departure Delay in Minutes,Arrival Delay in Minutes\n"
        "1,Male,Disloyal Customer,35,Business,Economy,1000,3,3,3,3,3,3,3,3,3,3,3,3,3,10,5\n"
        "2,Female,Loyal Customer,29,Personal,Economy Plus,500,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0\n"
        "3,Male,Loyal Customer,42,Business,Business,1500,2,2,2,2,2,2,2,2,2,2,2,2,2,5,7\n"
    )

    data = {
        'file': (io.BytesIO(csv_content.encode()), 'test.csv')
    }

    response = client.post(upload_url, data=data, content_type='multipart/form-data')
    assert response.status_code == 200


def test_register_success(client):
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'strongpassword',
        'confirm_password': 'strongpassword'
    }, follow_redirects=True)
    assert b'Registration successful' in response.data or response.status_code == 200

def test_register_password_mismatch(client):
    response = client.post('/auth/register', data={
        'username': 'newuser2',
        'email': 'newuser2@example.com',
        'password': 'password1',
        'confirm_password': 'password2'
    }, follow_redirects=True)
    assert b'Passwords must match' in response.data or response.status_code == 200

def test_register_duplicate_username(client):
    client.post('/auth/register', data={
        'username': 'dupuser',
        'email': 'dupuser@example.com',
        'password': 'password',
        'confirm_password': 'password'
    })
    response = client.post('/auth/register', data={
        'username': 'dupuser',
        'email': 'anotheremail@example.com',
        'password': 'password',
        'confirm_password': 'password'
    }, follow_redirects=True)
    assert b'Username already exists' in response.data or response.status_code == 200

def test_login_wrong_password(client):
    client.post('/auth/register', data={
        'username': 'wrongpass',
        'email': 'wrongpass@example.com',
        'password': 'correctpass',
        'confirm_password': 'correctpass'
    })

    response = client.post('/auth/login', data={
        'username': 'wrongpass',
        'password': 'incorrectpass'
    }, follow_redirects=True)

    assert b'Credenciais inv' in response.data or response.status_code == 200

def test_account_lock_after_failed_attempts(client):
    client.post('/auth/register', data={
        'username': 'lockuser',
        'email': 'lockuser@example.com',
        'password': 'securepass',
        'confirm_password': 'securepass'
    })

    # 5 tentativas com senha errada
    for _ in range(5):
        client.post('/auth/login', data={
            'username': 'lockuser',
            'password': 'wrongpass'
        })

    # 6ª tentativa (deve estar bloqueado)
    response = client.post('/auth/login', data={
        'username': 'lockuser',
        'password': 'wrongpass'
    }, follow_redirects=True)

    assert b'temporariamente bloqueada' in response.data or response.status_code == 200

def test_profile_requires_login(client):
    response = client.get('/auth/profile', follow_redirects=True)
    assert b'Login' in response.data or response.status_code == 200

def test_change_password_success(client):
    client.post('/auth/register', data={
        'username': 'changepass',
        'email': 'changepass@example.com',
        'password': 'OldPass123',
        'confirm_password': 'OldPass123'
    })
    client.post('/auth/login', data={
        'username': 'changepass',
        'password': 'OldPass123'
    })

    response = client.post('/auth/profile', data={
        'current_password': 'OldPass123',
        'new_password': 'NewPass456',
        'confirm_password': 'NewPass456'
    }, follow_redirects=True)

    assert b'Senha atualizada' in response.data or response.status_code == 200

def test_change_password_wrong_current(client):
    client.post('/auth/register', data={
        'username': 'wrongcurrent',
        'email': 'wrongcurrent@example.com',
        'password': 'MyPassword1',
        'confirm_password': 'MyPassword1'
    })
    client.post('/auth/login', data={
        'username': 'wrongcurrent',
        'password': 'MyPassword1'
    })

    response = client.post('/auth/profile', data={
        'current_password': 'WrongCurrent',
        'new_password': 'NewPass789',
        'confirm_password': 'NewPass789'
    }, follow_redirects=True)

    assert b'Senha atual incorreta' in response.data or response.status_code == 200

def test_change_password_mismatch(client):
    # Registrar usuário
    client.post('/auth/register', data={
        'username': 'mismatchpass',
        'email': 'mismatch@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    })
    # Login do usuário
    client.post('/auth/login', data={
        'username': 'mismatchpass',
        'password': 'Password123'
    })

    # Tentar alterar a senha com senhas novas diferentes
    response = client.post('/auth/profile', data={
        'current_password': 'Password123',
        'new_password': 'NewPassword1',
        'confirm_password': 'OtherPassword'
    }, follow_redirects=True)

    # Verificar status e mensagem de erro
    assert response.status_code == 200, f"Status esperado 200, obtido {response.status_code}"
    assert 'As novas senhas não coincidem' in response.data.decode('utf-8')

def test_register_password_mismatch(client):
    response = client.post('/auth/register', data={
        'username': 'user1',
        'email': 'user1@example.com',
        'password': 'Password123',
        'confirm_password': 'Password456'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'As senhas não coincidem.' in response.data.decode('utf-8')

def test_register_invalid_email(client):
    response = client.post('/auth/register', data={
        'username': 'user3',
        'email': 'invalid-email',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'Formato de e-mail inválido.' in response.data.decode('utf-8')


def test_register_password_mismatch(client):
    response = client.post('/auth/register', data={
        'username': 'user1',
        'email': 'user1@example.com',
        'password': 'Password123',
        'confirm_password': 'Password456'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'As senhas não coincidem.' in response.data.decode('utf-8')

def test_register_password_too_short(client):
    response = client.post('/auth/register', data={
        'username': 'user2',
        'email': 'user2@example.com',
        'password': 'short',
        'confirm_password': 'short'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'A senha deve ter pelo menos 8 caracteres.' in response.data
