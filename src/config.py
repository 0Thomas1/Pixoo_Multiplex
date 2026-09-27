from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	"""Application configuration loaded from environment variables.

	Args:
		pixoo_ip: IP address of the Pixoo64 device. If None, auto-discovers.
		cors_origins: Allowed origins for CORS middleware.
		log_level: Logging level for the application.
	"""
	pixoo_ip: str | None = None
	cors_origins: list[str] = ["*"]
	log_level: str = "INFO"
	api_key: str | None = None

	class Config:
		env_file = ".env"


settings = Settings()
