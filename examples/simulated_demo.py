import sys, os, time, subprocess, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.client import PixooClient

API_KEY = os.environ.get("API_KEY", "test_key")
PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}/api/v1"


def run_demo():
	print("=" * 60)
	print("   PIXOO MULTIPLEX - SIMULATED INTERACTIVE DEMO")
	print("=" * 60)

	# 1. Start server process in simulated mode
	print("\n[1/6] Starting simulated server on port 8000...")
	env = os.environ.copy()
	env["PIXOO_SIMULATED"] = "true"
	env["API_KEY"] = API_KEY
	env["LOG_LEVEL"] = "INFO"

	server_proc = subprocess.Popen(
		[sys.executable, "-m", "uvicorn", "src.main:app", "--port", str(PORT)],
		env=env,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
	)

	# Wait for server ready
	ready = False
	for _ in range(30):
		time.sleep(0.2)
		try:
			resp = requests.get(f"{BASE_URL}/status", timeout=1)
			if resp.status_code == 200:
				ready = True
				break
		except Exception:
			pass

	if not ready:
		print("❌ Failed to connect to server.")
		server_proc.kill()
		return

	print("✅ Server running in Hermetic Simulation Mode (No hardware / GUI required)!")

	try:
		# 2. Client Fluent Buffering Demo
		print("\n[2/6] Connecting 2 apps using atomic frame buffering (PixooClient)...")
		clock_client = PixooClient("clock_app", "127.0.0.1", PORT, api_key=API_KEY)
		weather_client = PixooClient("weather_app", "127.0.0.1", PORT, api_key=API_KEY)

		print("  -> clock_app: buffering clear() + fill_rgb(0, 0, 80) + draw_text('12:00') + push(duration=2)")
		res1 = (
			clock_client
			.clear()
			.fill_rgb(0, 0, 80)
			.draw_text("12:00", 10, 24, 255, 255, 255)
			.push(duration=2)
		)
		print(f"     Result: status={res1.status_code}, data={res1.data}")

		print("  -> weather_app: buffering clear() + fill_rgb(0, 80, 0) + draw_text('72F SUN') + push(duration=2)")
		res2 = (
			weather_client
			.clear()
			.fill_rgb(0, 80, 0)
			.draw_text("72F SUN", 8, 24, 255, 255, 0)
			.push(duration=2)
		)
		print(f"     Result: status={res2.status_code}, data={res2.data}")

		# 3. Inspect Carousel
		print("\n[3/6] Inspecting server carousel status...")
		status = requests.get(f"{BASE_URL}/status").json()
		print(f"  Status response: {status}")
		assert "clock_app" in status["carousel"]
		assert "weather_app" in status["carousel"]

		# Set Carousel Mode
		requests.post(f"{BASE_URL}/mode/set", params={"mode": "carousel"}, headers={"X-API-Key": API_KEY})
		print("  Display mode set to: carousel")
		time.sleep(2.5)

		# 4. Manual Channel Switch Demo
		print("\n[4/6] Switching to Manual Mode (locking display to weather_app)...")
		switch_res = requests.post(f"{BASE_URL}/channel/switch", params={"app_id": "weather_app"}, headers={"X-API-Key": API_KEY}).json()
		print(f"  Switch confirmation: {switch_res}")
		assert switch_res["mode"] == "manual"
		assert switch_res["app_id"] == "weather_app"

		# Queue another frame for weather_app
		weather_client.clear().fill_rgb(80, 40, 0).draw_text("75F WARM", 8, 24, 255, 200, 0).push(duration=2)
		time.sleep(1.5)

		# 5. Urgent Preemption Demo
		print("\n[5/6] Triggering High-Priority Urgent Notification (Doorbell Alert)...")
		urgent_client = PixooClient("doorbell_app", "127.0.0.1", PORT, api_key=API_KEY)
		print("  -> Sending urgent request: clear() + fill_rgb(255, 0, 0) + draw_text('DOORBELL!') + push(duration=2, urgent=True)")
		start_urgent = time.time()
		urgent_res = (
			urgent_client
			.clear()
			.fill_rgb(255, 0, 0)
			.draw_text("DOORBELL!", 4, 24, 255, 255, 255)
			.push(duration=2, urgent=True)
		)
		print(f"     Urgent enqueue response: {urgent_res.status_code}, data={urgent_res.data}")
		assert urgent_res.status_code == 200

		# Allow urgent frame to display and resume
		time.sleep(2.5)
		print("  -> Urgent notification completed. Carousel scheduling safely resumed.")

		# 6. Admin Command Execution Demo
		print("\n[6/6] Executing immediate admin device control command...")
		bright_res = clock_client.set_brightness(60)
		print(f"  -> set_brightness(60): status={bright_res.status_code}, data={bright_res.data}")

		# Final Status Check
		final_status = requests.get(f"{BASE_URL}/status").json()
		print(f"\nFinal Server Status: {final_status}")

		print("\n" + "=" * 60)
		print("   🎉 ALL SIMULATED DEMO PHASES COMPLETED SUCCESSFULLY!")
		print("=" * 60)

	finally:
		print("\nCleaning up server process...")
		server_proc.terminate()
		server_proc.wait(timeout=3)
		print("Server stopped cleanly.")


if __name__ == "__main__":
	run_demo()
