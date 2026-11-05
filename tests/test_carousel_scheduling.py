import sys, os, pytest, asyncio, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.services.channel_manager import ChannelManager
from src.models import PixooRequest, Function


@pytest.mark.anyio
async def test_carousel_skips_empty_queues():
	manager = ChannelManager("127.0.0.1", simulated=True)
	# Register two apps
	req_b = PixooRequest(app_id="app_b", functions=[Function(name="clear", args=[])], duration=1)
	
	# Only enqueue for app_b, leave app_a with empty queue
	manager.carousel_apps = ["app_a", "app_b"]
	manager.app_queues["app_a"] = asyncio.Queue()
	manager.app_queues["app_b"] = asyncio.Queue()
	await manager.app_queues["app_b"].put(req_b)

	processed = []
	async def mock_send(req):
		processed.append(req.app_id)

	manager.send_to_pixoo = mock_send

	# Start worker loop task
	task = asyncio.create_task(manager.worker_loop())
	await asyncio.sleep(0.3)
	task.cancel()
	try:
		await task
	except asyncio.CancelledError:
		pass

	# app_b must have been processed even though app_a is first and empty!
	assert "app_b" in processed


@pytest.mark.anyio
async def test_manual_mode_auto_reverts_on_idle():
	manager = ChannelManager("127.0.0.1", simulated=True)
	manager.mode = "manual"
	manager.manual_app = "app_manual"
	manager.app_queues["app_manual"] = asyncio.Queue()
	# Set last active time to 35 seconds ago
	manager.last_manual_active_time = time.time() - 35

	task = asyncio.create_task(manager.worker_loop())
	await asyncio.sleep(0.2)
	task.cancel()
	try:
		await task
	except asyncio.CancelledError:
		pass

	assert manager.mode == "carousel"
	assert manager.manual_app is None


@pytest.mark.anyio
async def test_manual_mode_timeout_disabled():
	# 0 disables auto-revert
	manager = ChannelManager("127.0.0.1", simulated=True, manual_mode_timeout=0)
	manager.mode = "manual"
	manager.manual_app = "app_manual"
	manager.app_queues["app_manual"] = asyncio.Queue()
	manager.last_manual_active_time = time.time() - 100

	task = asyncio.create_task(manager.worker_loop())
	await asyncio.sleep(0.2)
	task.cancel()
	try:
		await task
	except asyncio.CancelledError:
		pass

	# Mode should still be manual because timeout is 0
	assert manager.mode == "manual"
	assert manager.manual_app == "app_manual"
