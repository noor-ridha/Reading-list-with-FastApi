import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models import ExportJob, Item, List, User  # noqa: F401

engine = create_engine(settings.test_database_url)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def register_and_login(client):
    def _do(email: str, password: str = "test1234") -> dict[str, str]:
        client.post("/auth/register", json={"email": email, "password": password})
        resp = client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _do