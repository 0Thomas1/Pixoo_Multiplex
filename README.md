# Pixoo Multiplex

FastAPI service that multiplexes multiple client applications onto a single 64x64 Pixoo64 LED display.

## Why This Exists

The Divoom Pixoo 64 is a popular 64x64 pixel display for homelabs and smart home setups. While Divoom's mobile app provides proprietary cloud channels, developers building custom integrations must use the device's **local HTTP WebAPI (`http://<device-ip>/post`)**.

However, the native local WebAPI is **single-tenant, unbuffered, and non-transactional**:

- **No Multi-Source Coordination**: The device exposes a single, shared frame buffer in memory with no transaction boundaries. If multiple independent scripts or services (e.g., Home Assistant, a crypto ticker, and a weather widget) send draw commands concurrently, their network calls interleave. Pixels, text coordinates, and buffer clears collide, resulting in visual tearing, broken fonts, and screen flicker.
- **No Native Scheduling or Queueing**: The hardware has no concept of app rotation, display duration, or frame buffering. Whichever client makes an HTTP request last simply hijacks the display.
- **No Priority Preemption**: Critical real-time events (such as a smart doorbell ring, security sensor trigger, or CI/CD build failure) cannot temporarily interrupt passive ambient dashboards without permanently breaking their update loops.

**Pixoo Multiplex** solves this by acting as a smart display server and arbitration middleware between your microservices and the physical screen:

- **Isolated Virtual Channels**: Every client application connects to its own dedicated, bounded FIFO queue (`MAX_QUEUE_SIZE = 100` with drop-oldest backpressure).
- **Fair Carousel Scheduling**: Automatically round-robins across active applications, allocating screen time according to each app's requested display duration.
- **Atomic Frame Transactions**: The client library buffers drawing commands locally and transmits them across the network as a single atomic `PixooRequest`, guaranteeing zero draw command interleaving across apps.
- **Priority Preemption**: High-priority urgent requests (gated via API key) immediately wake the active sleep timer, render the alert for its duration, and cleanly advance the carousel to the next app in sequence to prevent stale re-renders.
- **Manual Mode Locking**: Lock the display onto a single app on demand (via REST endpoint or client method) and resume carousel rotation whenever ready.

---

## Features

- **Multi-App Scheduling**: Display multiple applications on a single screen via round-robin carousel or lock onto a single app using manual mode.
- **Atomic Frame Buffering**: Fluent `PixooClient` accumulates drawing operations locally and transmits them across the network as a single atomic frame upon calling `push()`.
- **Urgent Priority Preemption**: High-priority alerts (doorbell, emergency notifications) immediately interrupt active display sleep, show their message, and resume the carousel cleanly on the next app in sequence.
- **Hermetic Simulation Mode**: Run offline, in headless CI runners, or on hardware-free development machines using `PIXOO_SIMULATED=true` (bypasses LAN scans and eliminates GUI/Tkinter window dependencies).
- **Hardened REST Security**: Strict HTTP status codes (`401 Unauthorized` for missing/bad API keys, `403 Forbidden` for unauthorized admin or urgent commands, with fail-closed security when server `API_KEY` is unconfigured).
- **Liveness Monitoring**: Built-in root `GET /health` endpoint for process monitors, orchestrators, and container healthchecks.

---

## Requirements

- Python 3.10+
- A Pixoo64 device on your LAN (or use simulated mode)

---

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy config template
cp .env.example .env
```

---

## Configuration

Edit `.env` to configure your device connection and security settings:

| Variable | Default | Description |
|---|---|---|
| `PIXOO_IP` | `None` | Device IP address on LAN. If unset and `PIXOO_SIMULATED=false`, auto-discovers via ARP/UDP subnet scan. |
| `PIXOO_SIMULATED` | `false` | When `true`, runs in headless simulation mode without physical hardware or GUI windows. |
| `API_KEY` | `None` | Secret key required for admin endpoints, urgent frames, and device controls. If unset on server, admin endpoints fail closed with 403. |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins list. |
| `LOG_LEVEL` | `"INFO"` | Logging verbosity level. |

---

## Running the Server

```bash
# Start server in production mode
./.venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Start server in development mode (auto-reload)
./.venv/bin/python -m uvicorn src.main:app --port 8000 --reload

# Start server in simulated mode without hardware
PIXOO_SIMULATED=true ./.venv/bin/python -m uvicorn src.main:app --port 8000

# Smoke check (import only)
./.venv/bin/python -c "from src.main import app"
```

---

## Using the Python Client

### 1. Fluent Frame Assembly (Drawing Commands)

Drawing commands (`clear`, `fill_rgb`, `draw_text`, `draw_pixel`, etc.) buffer locally. Calling `push()` transmits all commands as one atomic frame, preventing carousel interleaving or screen flicker.

```python
from src.client import PixooClient

client = PixooClient("weather_app", "localhost", 8000)

# Build and push a frame atomically
result = (
    client
    .clear()
    .fill_rgb(12, 28, 30)
    .draw_text("TORONTO", 8, 14, 255, 140, 0)
    .draw_text("21.5 C", 12, 38, 0, 230, 255)
    .push(duration=4)
)

print(result.status_code, result.data)
```

### 2. High-Priority Urgent Notification (Preemption)

Urgent requests preempt whatever is actively on screen and require `api_key`:

```python
admin_client = PixooClient("doorbell_app", "localhost", 8000, api_key="your-secret-key")

# Preempts the active frame immediately for 3 seconds
admin_client.clear().fill_rgb(255, 0, 0).draw_text("DOORBELL!", 6, 24, 255, 255, 255).push(duration=3, urgent=True)
```

### 3. Immediate Device Controls & Mode Switching

Administrative device actions execute immediately without buffering:

```python
admin_client = PixooClient("admin", "localhost", 8000, api_key="your-secret-key")

# Hardware control
admin_client.set_brightness(50)
admin_client.set_screen(True)

# Display mode switching
admin_client.set_mode("manual")
admin_client.switch_channel("weather_app")  # Locks screen to weather_app
admin_client.set_mode("carousel")           # Resumes round-robin
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Liveness healthcheck for process monitors and orchestrators. Returns `{"status": "ok"}`. |
| GET | `/api/v1/status` | No | Returns active channels, carousel order, display mode, and urgent queue size. |
| POST | `/api/v1/request` | Optional | Enqueue a `PixooRequest`. Set `urgent: true` or include device control commands (requires `X-API-Key`). |
| POST | `/api/v1/channel/switch` | `X-API-Key` | Switch display to a specific `app_id` in manual mode. |
| POST | `/api/v1/mode/set` | `X-API-Key` | Set display mode: `"carousel"` or `"manual"`. |

---

## Demos

```bash
# 1. Automated end-to-end simulated workflow (spawns and tears down server automatically)
./.venv/bin/python examples/simulated_demo.py

# 2. Interactive physical dual-app demo (CAD/USD rate & Temperature in °C)
# Connects to running server and supports live switching between Carousel, Manual, and Urgent alerts:
./.venv/bin/python examples/physical_demo.py
```

---

## Running Tests

```bash
# Run unit tests (runs offline without live server)
./.venv/bin/pytest -v

# Run integration tests (requires dev server running on localhost:8000)
./.venv/bin/python tests/test_endpoints.py
./.venv/bin/python tests/test_channel_switch.py
./.venv/bin/python tests/test_mode.py
./.venv/bin/python tests/client_test.py
```

---

## Project Structure

```
src/
  main.py              # Application factory and lifespan management
  router.py            # API endpoints (/status, /request, /channel/switch, /mode/set)
  models.py            # Pydantic schemas (PixooRequest, Function)
  client.py            # PixooClient with fluent buffering & immediate controls
  commands.py          # Allowlist registries (DRAWING_COMMANDS, DEVICE_CONTROL_COMMANDS)
  config.py            # Settings loader (env-based via pydantic-settings)
  dependencies.py      # Dependency injection & API key verification
  services/
    channel_manager.py # State machine, queue manager, worker loop, HeadlessSimulator
examples/
  simulated_demo.py    # Self-contained automated demonstration
  physical_demo.py     # Interactive dual-app demonstration (CAD/USD & Temp C)
  demo.py              # Minimal example
tests/
  test_auth_standards.py     # 401/403 status code verification
  test_urgent_preemption.py  # Urgent priority preemption verification
  test_client_buffering.py   # Client buffering & frame atomicity verification
  test_resilience.py         # Worker loop crash resilience verification
  test_simulation.py         # Simulation mode LAN bypass verification
  test_health.py             # Root /health endpoint verification
  test_endpoints.py          # Integration tests
  test_channel_switch.py     # Channel switching integration tests
  test_mode.py               # Carousel/manual mode integration tests
  client_test.py             # ThreadPoolExecutor multi-client load generator
docs/
  architecture.md      # Detailed system design
  api.md               # API reference & payload specifications
  development.md       # Developer guide
```

---

## License

MIT
