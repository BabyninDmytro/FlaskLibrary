def login(client, email='test.user@example.com', password='Secret123!'):
    return client.post(
        '/login',
        data={'email': email, 'password': password},
        follow_redirects=False,
    )


def test_root_redirects_guest_to_login(client):
    response = client.get('/', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_root_redirects_authenticated_user_to_home(client, user):
    login_response = login(client)
    assert login_response.status_code == 302

    response = client.get('/', follow_redirects=False)

    assert response.status_code == 302
    assert '/home' in response.headers['Location']



def test_logout_requires_authentication(client):
    response = client.get('/logout', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_logout_redirects_to_login_after_authentication(client, user):
    login_response = login(client)
    assert login_response.status_code == 302

    response = client.get('/logout', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_book_route_returns_404_for_missing_book(client):
    response = client.get('/book/999999', follow_redirects=False)

    assert response.status_code == 404


def test_profile_route_returns_404_for_missing_user(client):
    response = client.get('/profile/999999', follow_redirects=False)

    assert response.status_code == 404


def test_reviews_route_returns_404_for_missing_review(client):
    response = client.get('/reviews/999999', follow_redirects=False)

    assert response.status_code == 404
