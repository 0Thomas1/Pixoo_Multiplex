import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = os.environ.get("API_KEY", "test_key")
HEADERS = {"X-API-Key": API_KEY}


def setup_apps():
	"""Helper: enqueue two apps so the carousel has multiple entries."""
	from src.models import PixooRequest, Function
	for app_id in ["app_alpha", "app_beta"]:
		request = PixooRequest(
			app_id=app_id,
			functions=[Function(name="clear", args=[])],
			duration=5,
		)
		requests.post(f"{BASE_URL}/request", json=request.model_dump())


def test_set_mode_carousel():
	"""Set mode to carousel succeeds."""
	setup_apps()
	resp = requests.post(f"{BASE_URL}/mode/set", params={"mode": "carousel"}, headers=HEADERS)
	assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
	data = resp.json()
	assert data["status"] == "mode set"
	assert data["mode"] == "carousel"
	print("PASS: set mode carousel")


def test_set_mode_manual():
	"""Set mode to manual succeeds."""
	resp = requests.post(f"{BASE_URL}/mode/set", params={"mode": "manual"}, headers=HEADERS)
	assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
	data = resp.json()
	assert data["mode"] == "manual"
	print("PASS: set mode manual")


def test_set_mode_invalid():
	"""Set mode to invalid value returns 400."""
	resp = requests.post(f"{BASE_URL}/mode/set", params={"mode": "invalid"}, headers=HEADERS)
	assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
	print("PASS: set mode invalid")


def test_mode_requires_auth():
	"""Set mode without API key returns 401."""
	resp = requests.post(f"{BASE_URL}/mode/set", params={"mode": "carousel"})
	assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
	print("PASS: mode requires auth")


def test_switch_then_mode():
	"""Switch channel then verify mode changes, then back to carousel."""
	setup_apps()

	# Switch to app_beta
	resp = requests.post(f"{BASE_URL}/channel/switch", params={"app_id": "app_beta"}, headers=HEADERS)
	assert resp.status_code == 200
	assert resp.json()["mode"] == "manual"

	# Back to carousel
	resp = requests.post(f"{BASE_URL}/mode/set", params={"mode": "carousel"}, headers=HEADERS)
	assert resp.status_code == 200
	assert resp.json()["mode"] == "carousel"
	print("PASS: switch then mode")


if __name__ == "__main__":
	test_set_mode_carousel()
	test_set_mode_manual()
	test_set_mode_invalid()
	test_mode_requires_auth()
	test_switch_then_mode()
	print("\nAll mode tests passed!")
