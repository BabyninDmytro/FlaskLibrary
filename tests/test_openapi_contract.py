from pathlib import Path


def _read_openapi():
    return Path('openapi.yaml').read_text(encoding='utf-8')


def test_openapi_documents_core_v1_paths():
    spec_text = _read_openapi()

    expected_paths = (
        '/api/v1/auth/login:',
        '/api/v1/auth/refresh:',
        '/api/v1/auth/logout:',
        '/api/v1/auth/me:',
        '/api/v1/books:',
        '/api/v1/books/{book_id}:',
        '/api/v1/books/{book_id}/reviews:',
        '/api/v1/books/{book_id}/annotations:',
        '/api/v1/books/{book_id}/toggle-hidden:',
        '/api/v1/reviews/{review_id}:',
        '/api/v1/annotations/{annotation_id}:',
        '/api/v1/readers/{user_id}:',
    )

    for path in expected_paths:
        assert path in spec_text


def test_openapi_documents_expected_toggle_hidden_responses():
    spec_text = _read_openapi()
    toggle_hidden_block_start = spec_text.index('/api/v1/books/{book_id}/toggle-hidden:')
    reviews_block_start = spec_text.index('/api/v1/reviews/{review_id}:')
    toggle_hidden_block = spec_text[toggle_hidden_block_start:reviews_block_start]

    assert "'200':" in toggle_hidden_block
    assert "'401':" in toggle_hidden_block
    assert "'403':" in toggle_hidden_block
    assert "'404':" in toggle_hidden_block


def test_openapi_documents_bearer_auth_scheme():
    spec_text = _read_openapi()

    assert 'bearerAuth:' in spec_text
    assert 'scheme: bearer' in spec_text
    assert 'bearerFormat: JWT' in spec_text
