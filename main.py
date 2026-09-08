from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from pixoo import Pixoo
import asyncio
from PixooRequest import PixooRequest

class FrameRequest(BaseModel):
	app_id: str
	duration: int
	pic_data: str

class ChannelManager:
	def __init__(self, pixoo_ip):
		self.commands = {
			"clear": self.pixoo.clear,
			"clear_rgb": self.pixoo.clear_rgb,
			"draw_character": self.pixoo.draw_character,
			"draw_character_at_location_rbg": self.pixoo.draw_character_at_location_rgb,
		}
		self.channels = {}       # Channels 1-n: app_id -> FrameRequestQueue
		self.channel_0 = []      # The Carousel: list of active app_ids
		self.urgent_queue = asyncio.Queue() #
		self.interrupt_event = asyncio.Event() #[cite: 1]
		self.pixoo = Pixoo(pixoo_ip)
	async def worker_loop(self):
		carousel_index = 0
		while True:
			# 1. Check for urgent notifications first[cite: 1]
			if not self.urgent_queue.empty():
				frame = await self.urgent_queue.get()
				await self.send_to_pixoo(frame)
				await self.sleep_interruptible(frame.duration, interruptable=False) #[cite: 1]
				continue

			# 2. Process Channel 
			print(f"channel_0: {self.channel_0}")
			if self.channel_0:
				current_app = self.channel_0[carousel_index]
				
				await self.send_to_pixoo(current_app)
				
				# interrupted = await self.sleep_interruptible(frame.duration, interruptable=True) #[cite: 1]
				# if not interrupted:
				# 		# Advance Channel 0 naturally
				# 		carousel_index = (carousel_index + 1) % len(self.channel_0)
			else:
				await asyncio.sleep(1)

	async def sleep_interruptible(self, duration: int, interruptable: bool):
		if not interruptable:
			await asyncio.sleep(duration)
			return False   
		try:
				await asyncio.wait_for(self.interrupt_event.wait(), timeout=duration) #[cite: 1]
				self.interrupt_event.clear() #[cite: 1]
				return True
		except asyncio.TimeoutError:
				return False
            
	async def send_to_pixoo(self, current_app: str):
		queue = self.channels[current_app]
		if queue.empty():
			print("Queue is empty, nothing to send.")
			self.channel_0.remove(current_app)
			del self.channels[current_app]
			return
		frame = await queue.get()

		for function_name, args, kwargs in frame.functions:
			if function_name in self.commands:
				print(f"Calling {function_name}{tuple(args)} for {current_app} with {kwargs}")
				self.commands[function_name](*args, **kwargs)
			else:
				print(f"Unknown function: {function_name}")
		if isinstance(frame, PixooRequest):
			print(f"Calling {frame.function}{tuple(frame.args)} for {frame.app_id} with {frame.kwargs}")
		else:
			print(f"Pushing {frame.app_id}, {frame.duration}, {frame.pic_data} to Pixoo64")

	async def enqueue_request(self,request: PixooRequest):
		try:
			if request.app_id not in self.channel_0:
				self.channel_0.append(request.app_id)
				self.channels[request.app_id] = asyncio.Queue()
			queue_item = request.functions
		
			await self.channels[request.app_id].put(queue_item)
		except Exception as e:
			return(f"Error enqueuing request: {e}")
		return {"status": "request added to queue", "app_id": request.app_id, "functions_len": len(request.functions)}
manager = ChannelManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
	print("Starting worker loop...")
	task = asyncio.create_task(manager.worker_loop())
	yield
	task.cancel()

app = FastAPI(lifespan=lifespan)
@app.get("/api/v1/status")
async def get_status():
	return {"status": "running",
				 "channels": list(manager.channels.keys()),
				 "carousel": manager.channel_0,
				 "urgent_queue_size": manager.urgent_queue.qsize()}

@app.post("/api/v1/frame")
async def add_carousel_frame(frame: FrameRequest):
	# Add to carousel if not already present
	if frame.app_id not in manager.channel_0:
		manager.channel_0.append(frame.app_id)
		manager.channels[frame.app_id] = asyncio.Queue()
	# Add to channels
	await manager.channels[frame.app_id].put(frame)
	print(f"Added frame for {frame.app_id} to carousel with duration {frame.duration} and pic_data {frame.pic_data}")
	

	return {"status": "frame added to carousel"}

@app.post("/api/v1/request")
async def add_request(request: PixooRequest):
	return await manager.enqueue_request(request)
