from typing import Any

from pydantic import BaseModel, Field
class Function(BaseModel):
	name: str
	args: list[Any] = Field(default_factory=list)
	kwargs: dict[str, Any] = Field(default_factory=dict)

class PixooRequest(BaseModel):
	"""A series of functions to be executed on the Pixoo."""
	app_id: str
	functions: list[Function] = Field(min_length=1)
	