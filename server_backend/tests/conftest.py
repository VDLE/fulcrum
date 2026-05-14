import pytest

from app import create_app


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    client = app.test_client()
    client.post("/testing_reset_db")
    return app.test_client()
