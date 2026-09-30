from fastapi import APIRouter, Depends, HTTPException

from .dependencies import get_manager, verify_api_key
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
	api_key: str | None = Depends(verify_api_key),
):
	"""Accept a PixooRequest and enqueue it for display.

	Args:
		request: The PixooRequest to enqueue.
		manager: Injected ChannelManager instance.
		api_key: Verified API key from X-API-Key header, if provided.

	Returns:
		Dict with status message and metadata.
	"""
	if api_key:
		request.is_admin = True
	return await manager.enqueue_request(request)


@router.post("/channel/switch")
async def switch_channel(
	app_id: str,
	manager: ChannelManager = Depends(get_manager),
	_api_key: str = Depends(verify_api_key),
):
	"""Switch to a specific app (manual mode). Requires authentication.

	Args:
		app_id: The app_id to switch to.
		manager: Injected ChannelManager instance.
		_api_key: Verified API key from X-API-Key header.

	Returns:
		Dict with switch confirmation and current mode.

	Raises:
		HTTPException: 404 if the app_id is not in the carousel.
	"""
	try:
		return await manager.switch_channel(app_id)
	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))


@router.post("/mode/set")
async def set_mode(
	mode: str,
	manager: ChannelManager = Depends(get_manager),
	_api_key: str = Depends(verify_api_key),
):
	"""Set the display mode (carousel or manual). Requires authentication.

	Args:
		mode: "carousel" or "manual".
		manager: Injected ChannelManager instance.
		_api_key: Verified API key from X-API-Key header.

	Returns:
		Dict with mode confirmation.

	Raises:
		HTTPException: 400 if mode is invalid.
	"""
	try:
		return await manager.set_mode(mode)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
