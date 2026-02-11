def ensure_guest(client):
    with client.session_transaction() as session:
        session.clear()

    # Clear remember/session cookies across Flask/Werkzeug client versions.
    if hasattr(client, 'cookie_jar'):
        client.cookie_jar.clear()
        return

    cookie_store = getattr(client, '_cookies', None)
    if cookie_store is not None:
        cookie_store.clear()


def test_home_access_behavior_for_guest(client):
    ensure_guest(client)
    response = client.get('/home', follow_redirects=False)

    assert response.status_code == 302, f"Expected redirect for guest, got {response.status_code} with Location={response.headers.get('Location')}"
    assert '/login' in response.headers['Location']


def test_login_with_valid_credentials(client, user):
    response = client.post(
        '/login',
        data={
            'email': 'test.user@example.com',
            'password': 'Secret123!',
            'remember': 'y',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/home' in response.headers['Location']
