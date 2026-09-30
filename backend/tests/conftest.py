"""pytest 共享配置：独立测试数据库 + 每个测试独立经销商"""
import os
import sys
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DB = BACKEND_DIR / "test_crm.db"

# 在导入 app 前设置测试环境变量（使用独立测试库）
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key"

sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient

from database import Base, engine, SessionLocal
from auth import hash_password
from models import User
import main as main_module


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    if TEST_DB.exists():
        TEST_DB.unlink()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(main_module.app) as c:
        yield c


@pytest.fixture()
def test_dealer(client):
    """每个测试创建独立经销商，保证积分/项目状态互不干扰"""
    db = SessionLocal()
    username = f"dealer_{uuid.uuid4().hex[:10]}"
    user = User(
        name="测试经销商", username=username,
        password_hash=hash_password("Test1234"),
        role="dealer", dealer_name="测试医疗有限公司",
    )
    db.add(user)
    db.commit()
    uid = user.id
    db.close()

    resp = client.post("/api/auth/login", json={"username": username, "password": "Test1234"})
    assert resp.status_code == 200
    return {"token": resp.json()["access_token"], "id": uid, "username": username}
