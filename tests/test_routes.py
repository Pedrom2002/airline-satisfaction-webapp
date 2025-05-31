import io
def test_protected_route_requires_login(client):
    protected_url = '/prediction/'  # rota protegida que exige login

    response = client.get(protected_url, follow_redirects=False)
    assert response.status_code == 302  # deve redirecionar para login quando não autenticado

