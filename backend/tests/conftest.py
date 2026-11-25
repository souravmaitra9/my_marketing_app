import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    settings = Settings(
        database_url="sqlite+pysqlite://",
        redis_url="",
        llm_base_url="",
        llm_api_key="",
        auto_create_schema=True,
        seed_demo=False,
        cors_origins="http://localhost",
    )
    application = create_app(settings)
    with TestClient(application) as test_client:
        yield test_client
