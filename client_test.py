from concurrent.futures import ThreadPoolExecutor
import client
from main import FrameRequest
from PixooRequest import PixooRequest
if __name__ == "__main__":
	clients = []
	for i in range(3):
		appid = f"app_{i}"
		host = "localhost"
		port = 8000
		client_instance = client.PixooClient(appid, host, port)
		clients.append(client_instance)
	for i, client_instance in enumerate(clients):
		for j in range(5):
			frame = FrameRequest(app_id=f"app_{i}", duration=5, pic_data=f"image_data_{i}_{j}")
			client_instance.add_to_buffer(frame)
		request = PixooRequest(
			app_id=f"app_{i}",
			duration=5,
			function="set_brightness",
			args=[50],
		)
		client_instance.add_to_buffer(request)

	with ThreadPoolExecutor(max_workers=3) as executor:
		futures = []
		for client_instance in clients:
			futures.append(executor.submit(client_instance.send_buffered_frames))

		for future in futures:
			for result in future.result():
				status_code, response_text, app_id = result
				print(f"Client {app_id} received response: {status_code}, {response_text}")