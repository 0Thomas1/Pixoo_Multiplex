from fastapi import Header, HTTPException, Request

from .config import settings
from .services.channel_manager import ChannelManager


def get_manager(request: Request) -> ChannelManager:
	"""Dependency provider for ChannelManager.

	Args:
		request: The incoming FastAPI request.

	Returns:
		The ChannelManager instance stored in app.state.
	"""
	return request.app.state.manager


def verify_api_key(x_api_key: str = Header(None)) -> str | None:
	"""Verify the X-API-Key header against the configured API key.

	Args:
		x_api_key: The API key from the X-API-Key header.

	Returns:
		The verified API key, or None if missing/invalid.
	"""
	if not x_api_key or x_api_key != settings.api_key:
		return None
	return x_api_key
