
import asyncio
from main import FrameRequest
import requests
import asyncio
class PixooClient:
		def __init__(self, appid: str, host: str, port: int):
				self.appid = appid
				self.host = host
				self.port = port
				self.base_url = f"http://{host}:{port}"
				self.buffer = []

		def add_to_buffer(self, frame: FrameRequest):
				self.buffer.append(frame)

		def send_buffered_frames(self):
				results = []
				for frame in self.buffer:
					result = asyncio.run(self.send_frame(frame))
					results.append(result)
				self.buffer = []
				return results


		async def send_frame(self, frame: FrameRequest):
				# Simulate sending the frame to the Pixoo64 device
				response = requests.post(f"{self.base_url}/api/v1/frame", json=frame.model_dump())
				return response.status_code, response.text,frame.app_id


