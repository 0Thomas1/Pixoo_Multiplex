import requests

from .models import PixooRequest


class PixooClient:
	"""Client for sending PixooRequests to the server.

	Args:
		appid: Identifier for this client's app.
		host: Server hostname or IP.
		port: Server port.
	"""

	def __init__(self, appid: str, host: str, port: int):
		self.appid = appid
		self.host = host
		self.port = port
		self.base_url = f"http://{host}:{port}"
		self.buffer = []

	def add_to_buffer(self, request: PixooRequest):
		"""Add a PixooRequest to the send buffer.

		Args:
			request: The PixooRequest to buffer.

		Returns:
			None.
		"""
		self.buffer.append(request)

	def send_buffered_requests(self):
		"""Send all buffered requests to the server.

		Returns:
			List of (status_code, response_text, app_id) tuples.
		"""
		results = []
		for request in self.buffer:
			response = requests.post(
				f"{self.base_url}/api/v1/request", json=request.model_dump()
			)
			results.append((response.status_code, response.text, request.app_id))
		self.buffer = []
		return results
