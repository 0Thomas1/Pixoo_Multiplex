import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.config import Settings
from src.services.channel_manager import ChannelManager
from src.main import create_app


def test_simulation_alias_resolution(monkeypatch):
	# Test various alias forms
	monkeypatch.setenv("simulation", "true")
	assert Settings().pixoo_simulated is True

	monkeypatch.delenv("simulation")
	monkeypatch.setenv("SIMULATION", "1")
	assert Settings().pixoo_simulated is True

	monkeypatch.delenv("SIMULATION")
	monkeypatch.setenv("simulated", "yes")
	assert Settings().pixoo_simulated is True

	monkeypatch.delenv("simulated")
	monkeypatch.setenv("PIXOO_SIMULATED", "on")
	assert Settings().pixoo_simulated is True


def test_simulation_overrides_physical_ip():
	# Even if a physical IP is provided, simulation mode must force 127.0.0.1
	with patch("src.services.channel_manager.Pixoo") as mock_pixoo:
		manager = ChannelManager(pixoo_ip="192.168.0.103", simulated=True)
		mock_pixoo.assert_called_once_with("127.0.0.1", simulated=True)
		assert manager.simulated is True


def test_status_endpoint_reports_simulated():
	from src.config import settings
	orig = settings.pixoo_simulated
	try:
		settings.pixoo_simulated = True
		app = create_app()
		with TestClient(app) as client:
			resp = client.get("/api/v1/status")
			assert resp.status_code == 200
			assert resp.json()["simulated"] is True
	finally:
		settings.pixoo_simulated = orig
