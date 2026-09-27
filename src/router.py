from fastapi import APIRouter, Depends

from .dependencies import get_manager
from .models import PixooRequest
from .services.channel_manager import ChannelManager

router = APIRouter()


@router.get("/status")
async def get_status(manager: ChannelManager = Depends(get_manager)):
	"""Get current server status.

	Args:
		manager: Injected ChannelManager instance.

	Returns:
		Dict with active channels, carousel order, and urgent queue size.
	"""
	return {
		"status": "running",
		"channels": list(manager.channels.keys()),
		"carousel": manager.channel_0,
		"urgent_queue_size": manager.urgent_queue.qsize(),
	}


@router.post("/request")
async def add_request(
	request: PixooRequest,
	manager: ChannelManager = Depends(get_manager),
):
	"""Accept a PixooRequest and enqueue it for display.

	Args:
		request: The PixooRequest to enqueue.
		manager: Injected ChannelManager instance.

	Returns:
		Dict with status message and metadata.
	"""
	return await manager.enqueue_request(request)
