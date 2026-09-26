import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from concurrent.futures import ThreadPoolExecutor

from src.client import PixooClient
from src.models import PixooRequest, Function

if __name__ == "__main__":
	clients = []
	for i in range(3):
		appid = f"app_{i}"
		host = "localhost"
		port = 8000
		client_instance = PixooClient(appid, host, port)
		clients.append(client_instance)
	for i, client_instance in enumerate(clients):
		for j in range(5):
			request = PixooRequest(
				app_id=f"app_{i}",
				functions=[Function(name="clear", args=[])],
				duration=5,
			)
			client_instance.add_to_buffer(request)

	with ThreadPoolExecutor(max_workers=3) as executor:
		futures = []
		for client_instance in clients:
			futures.append(executor.submit(client_instance.send_buffered_requests))

		for future in futures:
			for result in future.result():
				status_code, response_text, app_id = result
				print(f"Client {app_id} received response: {status_code}, {response_text}")
