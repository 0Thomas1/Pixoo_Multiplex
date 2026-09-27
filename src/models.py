from typing import Any

from pydantic import BaseModel, Field


class Function(BaseModel):
	"""A single Pixoo device command to execute.

	Args:
		name: Command name as defined in ChannelManager.commands allowlist.
		args: Positional arguments for the command.
		kwargs: Keyword arguments for the command.
	"""
	name: str
	args: list[Any] = Field(default_factory=list)
	kwargs: dict[str, Any] = Field(default_factory=dict)


class PixooRequest(BaseModel):
	"""A series of functions to be executed on the Pixoo.

	Args:
		app_id: Identifier for the app sending the request.
		functions: Ordered list of device commands to execute.
		duration: Seconds to display before advancing (default 5).
	"""
	app_id: str
	functions: list[Function] = Field(min_length=1)
	duration: int = 5
