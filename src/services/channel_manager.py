import asyncio
import logging
import time
from fastapi import HTTPException

from pixoo import Pixoo

from ..commands import DRAWING_COMMANDS, DEVICE_CONTROL_COMMANDS
from ..models import PixooRequest

logger = logging.getLogger(__name__)

MAX_QUEUE_SIZE = 100


class HeadlessSimulator:
	"""Headless replacement for Pixoo's GUI Simulator to avoid Tkinter blocking in server/CI."""

	def __init__(self, pixoo=None, config=None):
		pass

	def display(self, buffer, counter):
		pass


class ChannelManager:
	"""Owns all display state and dispatches PixooCommands to the device.

	Args:
		pixoo_ip: IP address of the Pixoo64 device. If None, auto-discovers.
		simulated: Whether to run in simulated mode without hardware.
	"""

	def __init__(self, pixoo_ip: str | None = None, simulated: bool = False, manual_mode_timeout: int = 30):
		self.simulated = simulated
		self.manual_mode_timeout = manual_mode_timeout
		target_ip = pixoo_ip if pixoo_ip else None
		if self.simulated:
			import pixoo.objects.pixoo
			pixoo.objects.pixoo.Simulator = HeadlessSimulator
			target_ip = "127.0.0.1"  # Simulation strictly overrides any physical IP
		self.pixoo = Pixoo(target_ip, simulated=simulated)
		all_commands = DRAWING_COMMANDS + DEVICE_CONTROL_COMMANDS
		self.commands = {name: getattr(self.pixoo, name) for name in all_commands}
		self.admin_commands = set(DEVICE_CONTROL_COMMANDS)
		self.app_queues = {}     # app_id -> asyncio.Queue[PixooRequest]
		self.carousel_apps = []  # Ordered list of app_ids in carousel rotation
		self.urgent_queue = asyncio.Queue()
		self.interrupt_event = asyncio.Event()
		self.mode = "carousel"   # "carousel" or "manual"
		self.manual_app = None   # selected app in manual mode
		self.last_manual_active_time = time.time()

	# Backward-compatibility property aliases
	@property
	def channels(self):
		return self.app_queues

	@property
	def channel_0(self):
		return self.carousel_apps

	async def worker_loop(self):
		"""Main loop: drains urgent queue first, then processes channels based on mode.

		In carousel mode, round-robins through all apps, skipping idle queues.
		In manual mode, only processes the selected app, auto-reverting to carousel on idle timeout.

		Returns:
			None. Runs indefinitely until cancelled.
		"""
		carousel_index = 0
		while True:
			# 1. Check for urgent notifications first
			if not self.urgent_queue.empty():
				request = await self.urgent_queue.get()
				self.urgent_queue.task_done()
				await self.send_to_pixoo(request)
				await self.sleep_interruptible(request.duration, interruptable=False)
				if self.carousel_apps:
					carousel_index = (carousel_index + 1) % len(self.carousel_apps)
				continue

			# 2. Manual mode: only process the selected app
			if self.mode == "manual" and self.manual_app:
				queue = self.app_queues.get(self.manual_app)
				if queue and not queue.empty():
					request = await queue.get()
					queue.task_done()
					self.last_manual_active_time = time.time()
					await self.send_to_pixoo(request)
					await self.sleep_interruptible(request.duration, interruptable=True)
					continue
				else:
					# Check manual lease timeout (0 disables auto-revert)
					if self.manual_mode_timeout > 0 and time.time() - self.last_manual_active_time > self.manual_mode_timeout:
						logger.info(f"Manual mode lease expired for '{self.manual_app}'. Reverting to carousel.")
						self.mode = "carousel"
						self.manual_app = None
					else:
						await asyncio.sleep(0.2)
						continue

			# 3. Carousel mode: round-robin through all apps, skipping idle apps
			if self.carousel_apps:
				found = False
				for _ in range(len(self.carousel_apps)):
					current_app = self.carousel_apps[carousel_index]
					carousel_index = (carousel_index + 1) % len(self.carousel_apps)
					queue = self.app_queues.get(current_app)
					if queue and not queue.empty():
						request = await queue.get()
						queue.task_done()
						await self.send_to_pixoo(request)
						await self.sleep_interruptible(request.duration, interruptable=True)
						found = True
						break
				if not found:
					await asyncio.sleep(0.5)
			else:
				await asyncio.sleep(0.5)

	async def sleep_interruptible(self, duration: int, interruptable: bool):
		"""Sleep for a duration, optionally waking early on interrupt.

		Args:
			duration: Seconds to sleep.
			interruptable: If True, wake early when interrupt_event is set.

		Returns:
			True if interrupted, False if the full duration elapsed.
		"""
		if not interruptable:
			await asyncio.sleep(duration)
			return False
		try:
			await asyncio.wait_for(self.interrupt_event.wait(), timeout=duration)
			self.interrupt_event.clear()
			return True
		except asyncio.TimeoutError:
			return False

	async def send_to_pixoo(self, request: PixooRequest):
		"""Execute all functions in a PixooRequest against the device.

		Args:
			request: The PixooRequest containing functions to execute.

		Returns:
			None.
		"""

		for function in request.functions:
			if function.name in self.commands:
				print(f"[{request.app_id}] {function.name}(args={function.args}, kwargs={function.kwargs})")
				try:
					cmd = self.commands[function.name]
					if function.name == "push" or function.name in self.admin_commands:
						await asyncio.to_thread(cmd, *function.args, **function.kwargs)
					else:
						cmd(*function.args, **function.kwargs)
				except Exception as e:
					logger.error(f"[{request.app_id}] Error executing {function.name}: {e}")
			else:
				print(f"[{request.app_id}] Unknown function: {function.name}")

		if self.simulated:
			logger.info(f"[{request.app_id}] Rendered simulated frame (duration={request.duration}s, functions={len(request.functions)})")


	async def enqueue_request(self, request: PixooRequest):
		"""Add a PixooRequest to the appropriate app channel.

		Args:
			request: The PixooRequest to enqueue.

		Returns:
			Dict with status message and metadata, or error string.
		"""
		has_admin = any(f.name in self.admin_commands for f in request.functions)
		if has_admin and not request.is_admin:
			raise HTTPException(status_code=403, detail="Device control commands require API key")

		try:
			if request.app_id not in self.carousel_apps:
				self.carousel_apps.append(request.app_id)
				self.app_queues[request.app_id] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

			try:
				self.app_queues[request.app_id].put_nowait(request)
			except asyncio.QueueFull:
				self.app_queues[request.app_id].get_nowait()
				self.app_queues[request.app_id].task_done()
				self.app_queues[request.app_id].put_nowait(request)
		except Exception as e:
			return f"Error enqueuing request: {e}"
		return {"status": "request added to queue", "app_id": request.app_id, "functions_len": len(request.functions)}

	async def enqueue_urgent_request(self, request: PixooRequest):
		"""Enqueue an urgent request to preempt active frames.

		Args:
			request: The PixooRequest to enqueue urgently.

		Returns:
			Dict with status confirmation and metadata.
		"""
		await self.urgent_queue.put(request)
		self.interrupt_event.set()
		return {"status": "urgent request added to queue", "app_id": request.app_id, "functions_len": len(request.functions)}

	async def switch_channel(self, app_id: str):
		"""Switch to a specific app (manual mode).

		Args:
			app_id: The app_id to switch to.

		Returns:
			Dict with switch confirmation and current mode.

		Raises:
			ValueError: If the app_id is not in the carousel.
		"""
		if app_id not in self.carousel_apps:
			raise ValueError(f"App '{app_id}' not in carousel")
		self.mode = "manual"
		self.manual_app = app_id
		self.last_manual_active_time = time.time()
		return {"status": "switched", "app_id": app_id, "mode": self.mode}

	async def set_mode(self, mode: str):
		"""Set the display mode.

		Args:
			mode: "carousel" or "manual".

		Returns:
			Dict with mode confirmation.

		Raises:
			ValueError: If mode is not "carousel" or "manual".
		"""
		if mode not in ("carousel", "manual"):
			raise ValueError(f"Invalid mode: {mode}")
		self.mode = mode
		self.manual_app = None if mode == "carousel" else self.manual_app
		return {"status": "mode set", "mode": self.mode}
