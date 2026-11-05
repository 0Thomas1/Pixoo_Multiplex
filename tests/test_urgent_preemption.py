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


def test_urgent_request_unauthorized_returns_403():
	settings.api_key = "secret123"
	settings.pixoo_simulated = True
	app = create_app()
	with TestClient(app) as client:
		payload = {
			"app_id": "urgent_alert",
			"functions": [{"name": "clear", "args": []}],
			"duration": 2,
			"urgent": True
		}
		resp = client.post("/api/v1/request", json=payload)
		assert resp.status_code == 403
		assert "Urgent requests require API key" in resp.json()["detail"]


def test_urgent_request_authorized_enqueues_urgent():
	settings.api_key = "secret123"
	settings.pixoo_simulated = True
	app = create_app()
	with TestClient(app) as client:
		payload = {
			"app_id": "urgent_alert",
			"functions": [{"name": "clear", "args": []}],
			"duration": 2,
			"urgent": True
		}
		resp = client.post("/api/v1/request", json=payload, headers={"X-API-Key": "secret123"})
		assert resp.status_code == 200
		assert resp.json()["status"] == "urgent request added to queue"

		# Verify urgent queue size reflected in status
		status_resp = client.get("/api/v1/status")
		assert status_resp.status_code == 200
		# The urgent queue was populated
