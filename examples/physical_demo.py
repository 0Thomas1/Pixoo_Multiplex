import sys, os, time, threading, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.client import PixooClient

API_KEY = os.environ.get("API_KEY", "test_key")
SERVER_HOST = os.environ.get("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))

# Colors (R, G, B)
NAVY = (10, 15, 35)
GOLD = (255, 215, 0)
CYAN = (0, 230, 255)
TEAL_BG = (12, 28, 30)
ORANGE = (255, 140, 0)
WHITE = (255, 255, 255)
GREY = (70, 85, 110)
RED_BG = (90, 0, 0)


_LAST_CAD_FETCH = 0.0
_CACHED_CAD_RATE = 0.7215

_LAST_TEMP_FETCH = 0.0
_CACHED_TEMP = 20.0


def get_cad_to_usd_rate() -> float:
	"""Fetch live CAD to USD exchange rate with cache and offline fallback.

	Returns:
		CAD to USD exchange rate (e.g. 0.72).
	"""
	global _LAST_CAD_FETCH, _CACHED_CAD_RATE
	now = time.time()
	if now - _LAST_CAD_FETCH < 60:
		return _CACHED_CAD_RATE

	try:
		resp = requests.get("https://open.er-api.com/v6/latest/CAD", timeout=1.0)
		if resp.ok:
			data = resp.json()
			rate = data.get("rates", {}).get("USD")
			if rate:
				_CACHED_CAD_RATE = float(rate)
				_LAST_CAD_FETCH = now
				return _CACHED_CAD_RATE
	except Exception:
		pass
	return _CACHED_CAD_RATE


def get_temperature_c() -> float:
	"""Fetch live temperature in Celsius with cache and offline fallback.

	Returns:
		Temperature in Celsius (e.g. 21.5).
	"""
	global _LAST_TEMP_FETCH, _CACHED_TEMP
	now = time.time()
	if now - _LAST_TEMP_FETCH < 60:
		return _CACHED_TEMP

	try:
		resp = requests.get(
			"https://api.open-meteo.com/v1/forecast?latitude=43.65&longitude=-79.38&current=temperature_2m",
			timeout=1.0,
		)
		if resp.ok:
			data = resp.json()
			temp = data.get("current", {}).get("temperature_2m")
			if temp is not None:
				_CACHED_TEMP = float(temp)
				_LAST_TEMP_FETCH = now
				return _CACHED_TEMP
	except Exception:
		pass
	return _CACHED_TEMP


class PhysicalDemoRunner:
	"""Multiplex demo runner feeding CAD/USD and Temperature apps to Pixoo."""

	def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT, api_key: str = API_KEY):
		self.host = host
		self.port = port
		self.api_key = api_key
		self.cad_client = PixooClient("cad_usd_app", host, port, api_key=api_key)
		self.temp_client = PixooClient("temp_c_app", host, port, api_key=api_key)
		self.admin_client = PixooClient("admin_demo", host, port, api_key=api_key)
		self.running = True
		self.feed_thread: threading.Thread | None = None

	def send_cad_usd_frame(self):
		"""Assemble and send atomic CAD/USD exchange rate frame."""
		rate = get_cad_to_usd_rate()
		rate_str = f"{rate:.4f}"

		(
			self.cad_client
			.clear()
			.fill_rgb(*NAVY)
			.draw_line(4, 26, 60, 26, *GREY)
			.draw_text("CAD / USD", 6, 12, *GOLD)
			.draw_text(f"${rate_str}", 8, 38, *CYAN)
			.push(duration=4)
		)

	def send_temperature_frame(self):
		"""Assemble and send atomic Temperature in Celsius frame."""
		temp = get_temperature_c()
		temp_str = f"{temp:.1f} C"

		(
			self.temp_client
			.clear()
			.fill_rgb(*TEAL_BG)
			.draw_line(4, 26, 60, 26, *ORANGE)
			.draw_text("TEMP", 20, 12, *ORANGE)
			.draw_text(temp_str, 12, 38, *WHITE)
			.push(duration=4)
		)

	def background_feed_loop(self):
		"""Continuously feed updated frames to both app channels."""
		while self.running:
			try:
				self.send_cad_usd_frame()
				self.send_temperature_frame()
			except Exception as e:
				print(f"[Feed Error]: {e}")
			# Sleep between frame submissions to allow carousel display cycle
			for _ in range(40):
				if not self.running:
					break
				time.sleep(0.1)

	def send_urgent_alert(self):
		"""Trigger an urgent high-priority notification preempting active frame."""
		print("  -> Dispatching Urgent Notification (Preempting active frame)...")
		(
			self.admin_client
			.clear()
			.fill_rgb(*RED_BG)
			.draw_text("! ALERT !", 6, 18, *WHITE)
			.draw_text("HIGH PRIORITY", 4, 38, *GOLD)
			.push(duration=3, urgent=True)
		)

	def start(self):
		"""Start the demo and interactive control loop."""
		print("=" * 60)
		print("       PIXOO MULTIPLEX PHYSICAL DEMO")
		print("=" * 60)
		print(f"Connecting to Multiplex server at {self.host}:{self.port}...")

		# Pre-flight check: verify server is running
		try:
			resp = requests.get(f"http://{self.host}:{self.port}/health", timeout=1.5)
			if not resp.ok:
				raise ConnectionError()
		except Exception:
			print(f"\n❌ [ERROR] Cannot connect to Pixoo Multiplex server at http://{self.host}:{self.port}")
			print("Please start the server first in another terminal:")
			print("    ./.venv/bin/python -m uvicorn src.main:app --port 8000")
			print("Or in simulated mode:")
			print("    SIMULATION=true ./.venv/bin/python -m uvicorn src.main:app --port 8000\n")
			return

		print("App 1: CAD to USD Exchange Rate ('cad_usd_app')")
		print("App 2: Current Temperature in °C ('temp_c_app')")
		print("-" * 60)

		# Initial registration of both apps
		print("Sending initial frames for both apps...")
		self.send_cad_usd_frame()
		self.send_temperature_frame()

		# Ensure server starts in carousel mode
		self.admin_client.set_mode("carousel")
		print("Display mode set to: Carousel (alternating every 4s)")

		# Start background producer
		self.feed_thread = threading.Thread(target=self.background_feed_loop, daemon=True)
		self.feed_thread.start()

		print("\nInteractive Controls:")
		print("  [C] Carousel Mode (Round-robin both apps)")
		print("  [1] Manual Mode -> Lock on CAD/USD App")
		print("  [2] Manual Mode -> Lock on Temperature App")
		print("  [U] Urgent Notification -> Send 3s Alert (Preempts active app)")
		print("  [S] Server Status -> View active channels & mode")
		print("  [Q] Quit Demo")
		print("=" * 60)

		try:
			while self.running:
				cmd = input("\nEnter Command [C, 1, 2, U, S, Q]: ").strip().upper()
				if cmd == "C":
					res = self.admin_client.set_mode("carousel")
					print(f"Mode set to CAROUSEL: {res.data}")
				elif cmd == "1":
					res = self.admin_client.switch_channel("cad_usd_app")
					print(f"MANUAL MODE: Switched to CAD/USD app: {res.data}")
				elif cmd == "2":
					res = self.admin_client.switch_channel("temp_c_app")
					print(f"MANUAL MODE: Switched to Temperature app: {res.data}")
				elif cmd == "U":
					self.send_urgent_alert()
					print("Urgent alert dispatched!")
				elif cmd == "S":
					status = self.admin_client.get_status()
					print(f"Server Status: {status.data}")
				elif cmd == "Q":
					print("Exiting demo...")
					self.running = False
					break
				else:
					print("Unknown command. Options: C (Carousel), 1 (CAD/USD), 2 (Temp), U (Urgent), S (Status), Q (Quit)")
		except KeyboardInterrupt:
			print("\nDemo interrupted by user.")
		finally:
			self.running = False
			if self.feed_thread and self.feed_thread.is_alive():
				self.feed_thread.join(timeout=1.5)
			print("Disconnecting apps, purging pending queues, and restoring clock face...")
			try:
				r1 = self.cad_client.disconnect()
				r2 = self.temp_client.disconnect(clear_screen=True)
				if not (r1.success and r2.success):
					print(f"⚠️ Warning: Server did not acknowledge disconnect (CAD: {r1.status_code}, Temp: {r2.status_code})")
			except Exception as e:
				print(f"Disconnect error: {e}")
			print("Demo ended.")


if __name__ == "__main__":
	runner = PhysicalDemoRunner()
	runner.start()
