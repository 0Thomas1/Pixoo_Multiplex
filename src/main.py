import asyncio
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .router import router
from .services.channel_manager import ChannelManager

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Start the worker loop on startup and cancel on shutdown.

	Args:
		app: The FastAPI application instance.

	Returns:
		Async context manager yielding control to the app.
	"""
	manager = ChannelManager(settings.pixoo_ip)
	app.state.manager = manager
	task = asyncio.create_task(manager.worker_loop())
	logger.info("Worker loop started")
	yield
	task.cancel()
	logger.info("Worker loop stopped")


def create_app() -> FastAPI:
	"""Application factory.

	Returns:
		Configured FastAPI application instance.
	"""
	app = FastAPI(lifespan=lifespan)
	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.cors_origins,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	app.include_router(router, prefix="/api/v1")
	return app


app = create_app()
