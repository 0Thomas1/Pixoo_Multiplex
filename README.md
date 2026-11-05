# Pixoo Multiplex

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-e92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Hardware](https://img.shields.io/badge/hardware-Divoom%20Pixoo%2064-orange.svg)](https://www.divoom.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

> A high-performance FastAPI display server and multiplexer for the 64x64 Divoom Pixoo 64 LED display. Enables multiple applications, home automations, and scripts to share a single display through round-robin carousel scheduling, manual channel locking, and priority alert preemption.

---

## Quickstart

```bash
# 1. Clone & setup
git clone https://github.com/0Thomas1/Pixoo_Multiplex.git
cd Pixoo_Multiplex
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the self-contained simulated demo (no physical device required)
python examples/simulated_demo.py
```

---

## Why Pixoo Multiplex?

The Divoom Pixoo 64 is a popular display for homelabs and desktop dashboards. However, its local HTTP WebAPI (`http://<device-ip>/post`) is **single-tenant and unbuffered**:

| Native Pixoo 64 WebAPI Limitation | How Pixoo Multiplex Solves It |
|---|---|
| **No Multi-Source Support**: Multiple apps sending draw calls interleave and tear pixels. | **Virtual Channels**: Each app gets its own isolated, bounded queue (`maxsize=100`). |
| **No Scheduling**: Last HTTP request wins; no native app rotation or display duration. | **Fair Carousel**: Round-robins across active apps based on requested duration. |
| **No Preemption**: Can't show urgent alerts (doorbells, alarms) without killing background scripts. | **Instant Preemption**: Priority alerts immediately preempt the screen and resume carousel. |
| **Torn Frames**: Drawing happens command-by-command over the network. | **Atomic Frame Pushes**: `PixooClient` buffers commands locally and pushes full frames at once. |
| **Requires Hardware for Dev**: Startup blocks on LAN discovery if hardware is unreachable. | **Hermetic Simulation**: Run offline in CI or local dev without hardware or GUI popups. |

---

## Running the Server

### With Physical Hardware
Configure `.env`:
```env
PIXOO_IP=192.168.1.100  # Leave empty for automatic LAN discovery
API_KEY=your-secret-key
```
Start the service:
```bash
./.venv/bin/python -m uvicorn src.main:app --port 8000
```

### Offline / Simulation Mode (No Hardware Needed)
Run completely offline with our headless mock (no network scans, no Tkinter GUI windows):
```bash
PIXOO_SIMULATED=true ./.venv/bin/python -m uvicorn src.main:app --port 8000
```

---

## Python Client (`PixooClient`)

### 1. Build and Push Frames Atomically
```python
from src.client import PixooClient

client = PixooClient("weather_app", "localhost", 8000)

# Chain commands into a local buffer, then push as one atomic frame
client.clear().fill_rgb(12, 28, 30).draw_text("21.5 C", 12, 38, 0, 230, 255).push(duration=4)
```

### 2. High-Priority Urgent Alerts (Preemption)
```python
admin = PixooClient("doorbell", "localhost", 8000, api_key="your-secret-key")

# Interrupts active display immediately for 3 seconds, then advances carousel
admin.clear().fill_rgb(255, 0, 0).draw_text("DOORBELL!", 6, 24, 255, 255, 255).push(duration=3, urgent=True)
```

### 3. Immediate Hardware and Mode Control
```python
admin = PixooClient("admin", "localhost", 8000, api_key="your-secret-key")

admin.set_brightness(50)                    # 0-100%
admin.switch_channel("weather_app")         # Lock display to weather_app (Manual Mode)
admin.set_mode("carousel")                  # Resume round-robin rotation
```

---

## Included Demos

```bash
# 1. Automated Simulated Demo (runs full workflow and tears down cleanly)
./.venv/bin/python examples/simulated_demo.py

# 2. Interactive Physical Demo (CAD/USD Exchange Rate & Temperature in °C)
# Live keyboard controls: [C] Carousel, [1] CAD/USD, [2] Temp, [U] Urgent Alert
./.venv/bin/python examples/physical_demo.py
```

---

## REST API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Liveness healthcheck (`{"status": "ok"}`). |
| `GET` | `/api/v1/status` | None | Active channels, carousel order, display mode, queue size. |
| `POST` | `/api/v1/request` | Optional | Enqueue a frame. Set `urgent: true` for preemption (requires key). |
| `POST` | `/api/v1/channel/switch` | `X-API-Key` | Lock display to a specific `app_id` in manual mode. |
| `POST` | `/api/v1/mode/set` | `X-API-Key` | Set mode to `"carousel"` or `"manual"`. |

---

## Testing

```bash
# Unit test suite (runs offline without dev server)
./.venv/bin/pytest -v

# Integration tests (requires dev server running on localhost:8000)
./.venv/bin/python tests/test_endpoints.py
./.venv/bin/python tests/test_channel_switch.py
./.venv/bin/python tests/test_mode.py
./.venv/bin/python tests/client_test.py
```

---

## Project Structure

```
src/
  main.py              # Application factory, lifespan, and /health
  router.py            # API routes (/status, /request, /channel/switch, /mode/set)
  models.py            # Pydantic schemas (PixooRequest, Function)
  client.py            # PixooClient with fluent buffering & immediate controls
  commands.py          # Command allowlists (DRAWING_COMMANDS, DEVICE_CONTROL_COMMANDS)
  config.py            # Settings loader (PIXOO_IP, PIXOO_SIMULATED, API_KEY)
  dependencies.py      # Dependency injection & API key verification
  services/
    channel_manager.py # State machine, queue manager, worker loop, HeadlessSimulator
examples/
  simulated_demo.py    # Self-contained automated demonstration
  physical_demo.py     # Interactive dual-app demonstration (CAD/USD & Temp C)
tests/
  test_auth_standards.py     # 401/403 status code verification
  test_urgent_preemption.py  # Urgent priority preemption verification
  test_client_buffering.py   # Client buffering & frame atomicity verification
  test_resilience.py         # Worker loop crash resilience verification
  test_simulation.py         # Simulation mode LAN bypass verification
  test_health.py             # Root /health endpoint verification
docs/
  architecture.md      # Detailed system architecture
  api.md               # API reference & payload specifications
  development.md       # Developer guide
```

---

## License

MIT
