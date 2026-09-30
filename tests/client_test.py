import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from concurrent.futures import ThreadPoolExecutor

from src.client import PixooClient
from src.models import PixooRequest, Function


def send_frames(client: PixooClient, app_id: str, count: int):
	"""Send count frames from a client."""
	results = []
	for _ in range(count):
		request = PixooRequest(
			app_id=app_id,
			functions=[Function(name="clear", args=[])],
			duration=5,
		)
		results.append(client.send(request))
	return results


if __name__ == "__main__":
	clients = []
	for i in range(3):
		appid = f"app_{i}"
		host = "localhost"
		port = 8000
		client_instance = PixooClient(appid, host, port)
		clients.append(client_instance)

	with ThreadPoolExecutor(max_workers=3) as executor:
		futures = []
		for i, client_instance in enumerate(clients):
			futures.append(executor.submit(send_frames, client_instance, f"app_{i}", 5))

		for future in futures:
			for result in future.result():
				print(f"Client received response: {result.status_code}, success={result.success}, data={result.data}")
