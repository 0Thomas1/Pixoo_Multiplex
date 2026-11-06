import sys, os, pytest, asyncio, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from src.services.channel_manager import ChannelManager
from src.models import PixooRequest, Function
from src.client import PixooClient
from src.main import create_app
from src.config import settings


@pytest.mark.anyio
async def test_disconnect_purges_queue_and_unregisters():
	manager = ChannelManager("127.0.0.1", simulated=True)
	# Enqueue multiple requests
	for i in range(5):
		req = PixooRequest(app_id="app_purge", functions=[Function(name="clear", args=[])], duration=2)
		await manager.enqueue_request(req)

	assert "app_purge" in manager.carousel_apps
	assert manager.app_queues["app_purge"].qsize() == 5

	# Now disconnect
	res = await manager.disconnect_app("app_purge", clear_screen=False)
	assert res["status"] == "disconnected"
	assert res["purged_frames"] == 5
	assert "app_purge" not in manager.carousel_apps
	assert "app_purge" not in manager.app_queues
	assert "app_purge" not in manager.last_app_activity


@pytest.mark.anyio
async def test_auto_prune_inactive_app():
	manager = ChannelManager("127.0.0.1", simulated=True, app_inactivity_timeout=2)
	req = PixooRequest(app_id="stale_app", functions=[Function(name="clear", args=[])], duration=1)
	await manager.enqueue_request(req)

	# Set last activity to 10 seconds ago (exceeding timeout of 2s)
	manager.last_app_activity["stale_app"] = time.time() - 10

	task = asyncio.create_task(manager.worker_loop())
	await asyncio.sleep(0.3)
	task.cancel()
	try:
		await task
	except asyncio.CancelledError:
		pass

	# Stale app should have been automatically pruned from carousel
	assert "stale_app" not in manager.carousel_apps


def test_client_disconnect_api_and_context_manager():
	orig_sim = settings.pixoo_simulated
	try:
		settings.pixoo_simulated = True
		app = create_app()
		with TestClient(app) as test_client:
			# 1. Enqueue via API
			payload = {
				"app_id": "client_app",
				"functions": [{"name": "clear", "args": []}],
				"duration": 2
			}
			r1 = test_client.post("/api/v1/request", json=payload)
			assert r1.status_code == 200

			status = test_client.get("/api/v1/status").json()
			assert "client_app" in status["carousel"]

			# 2. Call disconnect endpoint
			r2 = test_client.post("/api/v1/channel/disconnect", params={"app_id": "client_app"})
			assert r2.status_code == 200
			assert r2.json()["status"] == "disconnected"

			status2 = test_client.get("/api/v1/status").json()
			assert "client_app" not in status2["carousel"]
			assert "client_app" not in status2["channels"]
	finally:
		settings.pixoo_simulated = orig_sim


def test_client_disconnect_warns_on_failure(caplog):
	import logging
	client = PixooClient("fail_app", "localhost", 59999)  # unreachable port
	with caplog.at_level(logging.WARNING):
		res = client.disconnect()
		assert not res.success
		assert any("disconnect failed" in record.message.lower() for record in caplog.records)

