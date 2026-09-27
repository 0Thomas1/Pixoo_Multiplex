from fastapi import Request

from .services.channel_manager import ChannelManager


def get_manager(request: Request) -> ChannelManager:
	"""Dependency provider for ChannelManager.

	Args:
		request: The incoming FastAPI request.

	Returns:
		The ChannelManager instance stored in app.state.
	"""
	return request.app.state.manager
