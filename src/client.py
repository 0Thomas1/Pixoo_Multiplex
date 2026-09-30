import requests
from dataclasses import dataclass
from typing import Any

from .models import PixooRequest


@dataclass
class ClientResult:
	"""Result of a client operation.

	Args:
		success: True if the HTTP response was 2xx.
		status_code: HTTP status code.
		data: Parsed JSON dict, or raw text if not JSON.
	"""
	success: bool
	status_code: int
	data: Any


class PixooClient:
	"""Client for interacting with the Pixoo server.

	Args:
		appid: Identifier for this client's app.
		host: Server hostname or IP.
		port: Server port.
		api_key: Optional API key sent as X-API-Key header on every request.
	"""

	def __init__(self, appid: str, host: str, port: int, api_key: str | None = None):
		self.appid = appid
		self.host = host
		self.port = port
		self.base_url = f"http://{host}:{port}"
		self.api_key = api_key

	def _request(self, method: str, path: str, json: dict | None = None, params: dict | None = None) -> ClientResult:
		"""Make an HTTP request to the server.

		Args:
			method: HTTP method (GET, POST, etc.).
			path: URL path (appended to base_url).
			json: Optional JSON body.
			params: Optional query parameters.

		Returns:
			ClientResult with success, status_code, and data.
		"""
		headers = {}
		if self.api_key:
			headers["X-API-Key"] = self.api_key
		response = requests.request(method, f"{self.base_url}{path}", json=json, params=params, headers=headers)
		try:
			data = response.json()
		except Exception:
			data = response.text
		return ClientResult(success=response.ok, status_code=response.status_code, data=data)

	def send(self, request: PixooRequest) -> ClientResult:
		"""Send a PixooRequest to the server.

		Args:
			request: The PixooRequest to send.

		Returns:
			ClientResult with the server response.
		"""
		return self._request("POST", "/api/v1/request", json=request.model_dump())

	def get_status(self) -> ClientResult:
		"""Get current server status.

		Returns:
			ClientResult with channels, carousel, and urgent queue info.
		"""
		return self._request("GET", "/api/v1/status")

	def switch_channel(self, app_id: str) -> ClientResult:
		"""Switch to a specific app (manual mode). Requires API key.

		Args:
			app_id: The app_id to switch to.

		Returns:
			ClientResult with switch confirmation.
		"""
		return self._request("POST", "/api/v1/channel/switch", params={"app_id": app_id})

	def set_mode(self, mode: str) -> ClientResult:
		"""Set the display mode. Requires API key.

		Args:
			mode: "carousel" or "manual".

		Returns:
			ClientResult with mode confirmation.
		"""
		return self._request("POST", "/api/v1/mode/set", params={"mode": mode})

	def _send_command(self, name: str, *args, **kwargs) -> ClientResult:
		"""Build and send a single-function PixooRequest.

		Args:
			name: Command name from the server's command registry.
			*args: Positional arguments for the command.
			**kwargs: Keyword arguments for the command.

		Returns:
			ClientResult with the server response.
		"""
		from .models import Function
		request = PixooRequest(
			app_id=self.appid,
			functions=[Function(name=name, args=list(args), kwargs=kwargs)],
		)
		return self.send(request)

	def clear(self) -> ClientResult:
		"""Clear the display.

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("clear")

	def push(self) -> ClientResult:
		"""Push the current buffer to the display.

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("push")

	def fill_rgb(self, r: int, g: int, b: int) -> ClientResult:
		"""Fill the entire display with a color.

		Args:
			r: Red component (0-255).
			g: Green component (0-255).
			b: Blue component (0-255).

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("fill_rgb", r, g, b)

	def draw_text(self, text: str, x: int, y: int, r: int, g: int, b: int) -> ClientResult:
		"""Draw text at a location.

		Args:
			text: Text to draw.
			x: X coordinate.
			y: Y coordinate.
			r: Red component (0-255).
			g: Green component (0-255).
			b: Blue component (0-255).

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("draw_text_at_location_rgb", text, x, y, r, g, b)

	def draw_pixel(self, x: int, y: int, r: int, g: int, b: int) -> ClientResult:
		"""Draw a single pixel.

		Args:
			x: X coordinate.
			y: Y coordinate.
			r: Red component (0-255).
			g: Green component (0-255).
			b: Blue component (0-255).

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("draw_pixel_at_location_rgb", x, y, r, g, b)

	def draw_line(self, x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int) -> ClientResult:
		"""Draw a line between two points.

		Args:
			x1: Start X coordinate.
			y1: Start Y coordinate.
			x2: End X coordinate.
			y2: End Y coordinate.
			r: Red component (0-255).
			g: Green component (0-255).
			b: Blue component (0-255).

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("draw_line_from_start_to_stop_rgb", x1, y1, x2, y2, r, g, b)

	def draw_filled_rectangle(self, x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int) -> ClientResult:
		"""Draw a filled rectangle.

		Args:
			x1: Top-left X coordinate.
			y1: Top-left Y coordinate.
			x2: Bottom-right X coordinate.
			y2: Bottom-right Y coordinate.
			r: Red component (0-255).
			g: Green component (0-255).
			b: Blue component (0-255).

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("draw_filled_rectangle_from_top_left_to_bottom_right_rgb", x1, y1, x2, y2, r, g, b)

	def draw_character(self, char: str, x: int, y: int, r: int, g: int, b: int) -> ClientResult:
		"""Draw a single character at a location.

		Args:
			char: Character to draw.
			x: X coordinate.
			y: Y coordinate.
			r: Red component (0-255).
			g: Green component (0-255).
			b: Blue component (0-255).

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("draw_character_at_location_rgb", char, x, y, r, g, b)

	def draw_image(self, image_data: str, x: int = 0, y: int = 0) -> ClientResult:
		"""Draw an image at a location.

		Args:
			image_data: Base64-encoded image data.
			x: X coordinate (default 0).
			y: Y coordinate (default 0).

		Returns:
			ClientResult with the server response.
		"""
		return self._send_command("draw_image_at_location", image_data, x, y)
