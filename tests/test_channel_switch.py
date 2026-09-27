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


def test_switch_with_valid_key():
	"""Switch with correct X-API-Key succeeds and reorders carousel."""
	setup_apps()
	response = requests.post(f"{BASE_URL}/channel/switch", params={"app_id": "app_beta"}, headers=HEADERS)
	assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
	data = response.json()
	assert data["status"] == "switched"
	assert data["app_id"] == "app_beta"
	assert data["mode"] == "manual"
	print("PASS: switch with valid key")


def test_switch_without_key():
	"""Switch without X-API-Key header returns 401."""
	response = requests.post(f"{BASE_URL}/channel/switch", params={"app_id": "app_alpha"})
	assert response.status_code == 401, f"Expected 401, got {response.status_code}"
	print("PASS: switch without key")


def test_switch_with_wrong_key():
	"""Switch with incorrect X-API-Key returns 401."""
	response = requests.post(
		f"{BASE_URL}/channel/switch",
		params={"app_id": "app_alpha"},
		headers={"X-API-Key": "wrong_key"},
	)
	assert response.status_code == 401, f"Expected 401, got {response.status_code}"
	print("PASS: switch with wrong key")


def test_switch_to_unknown_app():
	"""Switch to an app not in the carousel returns 404."""
	response = requests.post(
		f"{BASE_URL}/channel/switch",
		params={"app_id": "unknown_app"},
		headers=HEADERS,
	)
	assert response.status_code == 404, f"Expected 404, got {response.status_code}"
	print("PASS: switch to unknown app")


def test_switch_with_empty_app_id():
	"""Switch with empty app_id returns 404 (not found in carousel)."""
	response = requests.post(
		f"{BASE_URL}/channel/switch",
		params={"app_id": ""},
		headers=HEADERS,
	)
	assert response.status_code == 404, f"Expected 404, got {response.status_code}"
	print("PASS: switch with empty app_id")


if __name__ == "__main__":
	test_switch_with_valid_key()
	test_switch_without_key()
	test_switch_with_wrong_key()
	test_switch_to_unknown_app()
	test_switch_with_empty_app_id()
	print("\nAll channel switch tests passed!")
