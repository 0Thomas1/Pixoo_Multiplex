import sys, os, pytest, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.services.channel_manager import ChannelManager
from src.models import PixooRequest, Function


@pytest.mark.anyio
async def test_send_to_pixoo_handles_exception_without_crashing():
	manager = ChannelManager("127.0.0.1", simulated=True)

	def bad_command(*args, **kwargs):
		raise RuntimeError("Simulated device failure")

	manager.commands["bad_cmd"] = bad_command

	request = PixooRequest(
		app_id="test_app",
		functions=[Function(name="bad_cmd", args=[])],
		duration=1
	)
	# Must not raise exception
	await manager.send_to_pixoo(request)
