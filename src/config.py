from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	"""Application configuration loaded from environment variables.

	Args:
		pixoo_ip: IP address of the Pixoo64 device. If None, auto-discovers.
		cors_origins: Allowed origins for CORS middleware.
		log_level: Logging level for the application.
	"""
	pixoo_ip: str | None = None
	pixoo_simulated: bool = Field(
		default=False,
		validation_alias=AliasChoices(
			"pixoo_simulated",
			"simulation",
			"simulated",
			"pixoo_simulation",
		),
	)
	cors_origins: list[str] = ["*"]
	log_level: str = "INFO"
	api_key: str | None = None
	manual_mode_timeout: int = 30
	app_inactivity_timeout: int = 30

	class Config:
		env_file = ".env"


settings = Settings()
