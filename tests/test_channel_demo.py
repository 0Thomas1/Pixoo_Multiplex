import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = os.environ.get("API_KEY", "test_key")
HEADERS = {"X-API-Key": API_KEY}

RED = (255, 0, 0)
BLUE = (0, 0, 255)
POSITIONS = [(63, 1), (63, 2)]


def make_frame(app_id, positions, color):
	"""Build a PixooRequest for a frame.

	Args:
		app_id: The app identifier.
		positions: List of (x, y) pixel coordinates.
		color: (r, g, b) tuple.

	Returns:
		PixooRequest with clear, draw pixels, and push commands.
	"""
	from src.models import PixooRequest, Function

	functions = [Function(name="clear", args=[])]
	for x, y in positions:
		functions.append(Function(name="draw_pixel_at_location_rgb", args=[x, y, *color]))
	functions.append(Function(name="push", args=[]))
	return PixooRequest(app_id=app_id, functions=functions, duration=2)


def send_frames():
	"""Background thread: continuously send frames for both apps, alternating every 2s.

	Args:
		None.

	Returns:
		None. Runs forever until the main thread exits.
	"""
	while True:
		# Frame 1: 1 pixel
		for app_id, color in [("app_red", RED), ("app_blue", BLUE)]:
			req = make_frame(app_id, POSITIONS[:1], color)
			try:
				requests.post(f"{BASE_URL}/request", json=req.model_dump(), timeout=5)
			except Exception as e:
				print(f"Send error: {e}")
		time.sleep(2)

		# Frame 2: 2 pixels
		for app_id, color in [("app_red", RED), ("app_blue", BLUE)]:
			req = make_frame(app_id, POSITIONS[:2], color)
			try:
				requests.post(f"{BASE_URL}/request", json=req.model_dump(), timeout=5)
			except Exception as e:
				print(f"Send error: {e}")
		time.sleep(2)


def switch_channel(target_app):
	"""Switch to a specific app (manual mode).

	Args:
		target_app: The app_id to switch to.

	Returns:
		None.
	"""
	try:
		resp = requests.post(
			f"{BASE_URL}/channel/switch",
			params={"app_id": target_app},
			headers=HEADERS,
			timeout=5,
		)
		print(f"Switched to {target_app}: {resp.status_code}")
	except Exception as e:
		print(f"Switch error: {e}")


def set_mode(mode):
	"""Set the display mode.

	Args:
		mode: "carousel" or "manual".

	Returns:
		None.
	"""
	try:
		resp = requests.post(
			f"{BASE_URL}/mode/set",
			params={"mode": mode},
			headers=HEADERS,
			timeout=5,
		)
		print(f"Mode set to {mode}: {resp.status_code}")
	except Exception as e:
		print(f"Mode error: {e}")


if __name__ == "__main__":
	threading.Thread(target=send_frames, daemon=True).start()

	print("Channel demo running.")
	print("  Enter → switch to other app (manual mode)")
	print("  C → back to carousel mode")
	print("  Ctrl+C → quit")

	current_app = "app_red"
	while True:
		user_input = input().strip().lower()
		if user_input == "c":
			set_mode("carousel")
		elif user_input == "":
			current_app = "app_blue" if current_app == "app_red" else "app_red"
			switch_channel(current_app)
