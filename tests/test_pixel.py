import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests

from src.models import PixooRequest, Function

request = PixooRequest(
	app_id="test_pixel",
	functions=[
		Function(name="clear", args=[]),
		Function(name="draw_pixel_at_location_rgb", args=[1, 1, 255, 255, 255]),
		Function(name="push", args=[]),
	],
	duration=5,
)

response = requests.post("http://localhost:8000/api/v1/request", json=request.model_dump())
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
