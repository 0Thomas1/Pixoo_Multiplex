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


def verify_api_key(x_api_key: str | None = Header(None)) -> str:
	"""Verify the X-API-Key header against the configured API key.

	Args:
		x_api_key: The API key from the X-API-Key header.

	Returns:
		The verified API key.

	Raises:
		HTTPException: 403 if server API_KEY is unconfigured, 401 if missing/invalid.
	"""
	if not settings.api_key:
		raise HTTPException(status_code=403, detail="Admin features disabled: server API_KEY not configured")
	if not x_api_key or x_api_key != settings.api_key:
		raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing API key")
	return x_api_key


def get_optional_api_key(x_api_key: str | None = Header(None)) -> str | None:
	"""Optionally verify the X-API-Key header.

	Args:
		x_api_key: The API key from the X-API-Key header.

	Returns:
		The verified API key if valid, else None.
	"""
	if settings.api_key and x_api_key == settings.api_key:
		return x_api_key
	return None
