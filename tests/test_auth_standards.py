import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from src.main import create_app
from src.config import settings


@pytest.fixture(autouse=True)
def preserve_settings():
	orig_key = settings.api_key
	orig_sim = settings.pixoo_simulated
	yield
	settings.api_key = orig_key
	settings.pixoo_simulated = orig_sim


def test_auth_unconfigured_api_key_returns_403():
	settings.api_key = None
	settings.pixoo_simulated = True
	app = create_app()
	with TestClient(app) as client:
		resp = client.post("/api/v1/channel/switch", params={"app_id": "test"})
		assert resp.status_code == 403
		assert "Admin features disabled" in resp.json()["detail"]


def test_auth_missing_or_invalid_key_returns_401():
	settings.api_key = "secret123"
	settings.pixoo_simulated = True
	app = create_app()
	with TestClient(app) as client:
		resp = client.post("/api/v1/channel/switch", params={"app_id": "test"})
		assert resp.status_code == 401
		resp = client.post("/api/v1/channel/switch", params={"app_id": "test"}, headers={"X-API-Key": "wrong"})
		assert resp.status_code == 401


def test_admin_command_unauthorized_returns_403():
	settings.api_key = "secret123"
	settings.pixoo_simulated = True
	app = create_app()
	with TestClient(app) as client:
		payload = {
			"app_id": "admin_app",
			"functions": [{"name": "set_brightness", "args": [50]}],
			"duration": 5
		}
		resp = client.post("/api/v1/request", json=payload)
		assert resp.status_code == 403
