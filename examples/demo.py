import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time

from src.client import PixooClient
from src.models import PixooRequest, Function


def make_frame(text: str, bg: tuple[int, int, int], fg: tuple[int, int, int], duration: int = 2) -> PixooRequest:
	"""Build a single frame: fill background, draw text, push to display.

	Args:
		text: Character to display.
		bg: Background color (r, g, b).
		fg: Foreground color (r, g, b).
		duration: Seconds to display the frame.

	Returns:
		PixooRequest with fill_rgb, draw_text, and push functions.
	"""
	return PixooRequest(
		app_id="demo",
		functions=[
			Function(name="fill_rgb", args=list(bg)),
			Function(name="draw_text_at_location_rgb", args=[text, 20, 24, *fg]),
			Function(name="push", args=[]),
		],
		duration=duration,
	)


if __name__ == "__main__":
	client = PixooClient("demo", "localhost", 8000)

	frames = [
		make_frame("1", bg=(255, 0, 0), fg=(255, 255, 255)),
		make_frame("2", bg=(255, 0, 0), fg=(255, 255, 255)),
	]

	try:
		while True:
			for i, frame in enumerate(frames):
				result = client.send(frame)
				print(f"Frame {i + 1}: status={result.status_code}, success={result.success}, data={result.data}")
				time.sleep(frame.duration)
	except KeyboardInterrupt:
		print("\nDemo interrupted by user.")
