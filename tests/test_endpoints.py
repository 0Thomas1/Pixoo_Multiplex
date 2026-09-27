import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests

BASE_URL = "http://localhost:8000/api/v1"


def test_status_endpoint():
	"""Test GET /api/v1/status returns server state."""
	response = requests.get(f"{BASE_URL}/status")
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"

	data = response.json()
	assert data["status"] == "running"
	assert "channels" in data
	assert "carousel" in data
	assert "urgent_queue_size" in data
	print("PASS: GET /api/v1/status")


def test_request_endpoint():
	"""Test POST /api/v1/request enqueues a PixooRequest."""
	from src.models import PixooRequest, Function

	request = PixooRequest(
		app_id="test_endpoint",
		functions=[Function(name="clear", args=[])],
		duration=5,
	)

	response = requests.post(f"{BASE_URL}/request", json=request.model_dump())
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"

	data = response.json()
	assert data["status"] == "request added to queue"
	assert data["app_id"] == "test_endpoint"
	assert data["functions_len"] == 1
	print("PASS: POST /api/v1/request")


def test_request_endpoint_invalid():
	"""Test POST /api/v1/request with empty functions list fails validation."""
	response = requests.post(
		f"{BASE_URL}/request",
		json={"app_id": "test", "functions": [], "duration": 5},
	)
	assert response.status_code == 422, f"Expected 422, got {response.status_code}"
	print("PASS: POST /api/v1/request (invalid - empty functions)")


def test_status_reflects_enqueue():
	"""Test that status endpoint shows enqueued app in carousel."""
	from src.models import PixooRequest, Function

	request = PixooRequest(
		app_id="test_reflect",
		functions=[Function(name="clear", args=[])],
		duration=5,
	)
	requests.post(f"{BASE_URL}/request", json=request.model_dump())

	response = requests.get(f"{BASE_URL}/status")
	data = response.json()
	assert "test_reflect" in data["carousel"], "App not found in carousel"
	print("PASS: GET /api/v1/status reflects enqueued app")


if __name__ == "__main__":
	test_status_endpoint()
	test_request_endpoint()
	test_request_endpoint_invalid()
	test_status_reflects_enqueue()
	print("\nAll endpoint tests passed!")
