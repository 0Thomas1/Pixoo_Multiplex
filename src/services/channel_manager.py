import asyncio

from pixoo import Pixoo

from ..models import PixooRequest


class ChannelManager:
	"""Owns all display state and dispatches PixooCommands to the device.

	Args:
		pixoo_ip: IP address of the Pixoo64 device. If None, auto-discovers.
	"""

	def __init__(self, pixoo_ip):
		self.pixoo = Pixoo(pixoo_ip)
		self.commands = {
			"clear": self.pixoo.clear,
			"clear_rgb": self.pixoo.clear_rgb,
			"draw_character": self.pixoo.draw_character,
			"draw_character_at_location_rbg": self.pixoo.draw_character_at_location_rgb,
			"draw_pixel_at_location_rgb": self.pixoo.draw_pixel_at_location_rgb,
			"push": self.pixoo.push,
		}
		self.channels = {}       # app_id -> asyncio.Queue[PixooRequest]
		self.channel_0 = []      # Carousel: ordered list of active app_ids
		self.urgent_queue = asyncio.Queue()
		self.interrupt_event = asyncio.Event()

	async def worker_loop(self):
		"""Main loop: drains urgent queue first, then round-robins carousel channels.

		Returns:
			None. Runs indefinitely until cancelled.
		"""
		carousel_index = 0
		while True:
			# 1. Check for urgent notifications first
			if not self.urgent_queue.empty():
				request = await self.urgent_queue.get()
				await self.send_to_pixoo(request)
				await self.sleep_interruptible(request.duration, interruptable=False)
				continue

			# 2. Process Channel
			print(f"channel_0: {self.channel_0}")
			if self.channel_0:
				current_app = self.channel_0[carousel_index]
				queue = self.channels[current_app]
				if not queue.empty():
					request = await queue.get()
					await self.send_to_pixoo(request)

				# interrupted = await self.sleep_interruptible(request.duration, interruptable=True)
				# if not interrupted:
				# 		carousel_index = (carousel_index + 1) % len(self.channel_0)
			else:
				await asyncio.sleep(1)

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
				print(f"Calling {function.name}{tuple(function.args)} for {request.app_id} with {function.kwargs}")
				self.commands[function.name](*function.args, **function.kwargs)
			else:
				print(f"Unknown function: {function.name}")

	async def enqueue_request(self, request: PixooRequest):
		"""Add a PixooRequest to the appropriate app channel.

		Args:
			request: The PixooRequest to enqueue.

		Returns:
			Dict with status message and metadata, or error string.
		"""
		try:
			if request.app_id not in self.channel_0:
				self.channel_0.append(request.app_id)
				self.channels[request.app_id] = asyncio.Queue()

			await self.channels[request.app_id].put(request)
		except Exception as e:
			return f"Error enqueuing request: {e}"
		return {"status": "request added to queue", "app_id": request.app_id, "functions_len": len(request.functions)}
