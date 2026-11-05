import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from src.main import create_app
from src.config import settings


def test_health_endpoint():
	settings.pixoo_simulated = True
	app = create_app()
	with TestClient(app) as client:
		resp = client.get("/health")
		assert resp.status_code == 200
		assert resp.json() == {"status": "ok"}
