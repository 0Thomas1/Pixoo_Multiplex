# Pixoo Worker

FastAPI service that multiplexes multiple "apps" onto a single 64x64 Pixoo64 LED display.
Apps submit frames (ordered lists of device commands) and a worker loop schedules them
round-robin, with optional manual override and device-control commands gated behind an API key.

## Features

- **Multi-app carousel**: Multiple apps share one display via round-robin scheduling
- **Manual mode**: Switch to a specific app on demand, or return to carousel
- **Function-based API**: Send ordered lists of device commands (clear, draw, push)
- **Admin commands**: Device control (brightness, channel, reboot, etc.) gated behind `X-API-Key`
- **Python client**: `PixooClient` with low-level `send()` and convenience methods
- **Pydantic validation**: Request/response models with automatic validation
- **Simulated mode**: Run without hardware using the pixoo library's simulator
- **CORS support**: Configurable allowed origins

## Requirements

- Python 3.10+
- A Pixoo64 device on your LAN (or use simulated mode)

## Installation

```powershell
# Create virtual environment
python -m venv .venv

# Install dependencies
.\.venv\Scripts\pip.exe install -r requirements.txt

# Copy config template
copy .env.example .env
```

## Configuration

Edit `.env` to set your device IP and optional API key:

```env
PIXOO_IP=192.168.1.100
API_KEY=your-secret-key
```

| Variable | Description |
|---|---|
| `PIXOO_IP` | IP address of the Pixoo64 device. If unset, auto-discovers via `find_local_device_ip()`. |
| `API_KEY` | Optional key for device-control commands. If set, clients must send it via the `X-API-Key` header. |

Additional settings (in `src/config.py`):

| Setting | Default | Description |
|---|---|---|
| `cors_origins` | `["*"]` | Allowed CORS origins |
| `log_level` | `"INFO"` | Logging level |

## Running the Server

```powershell
# Start the server
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000

# Smoke check (import only)
.\.venv\Scripts\python.exe -c "from src.main import app"
```

The server starts a background `worker_loop` task on startup and cancels it on shutdown.

## Using the Python Client

### Low-level `send()`

```python
from src.client import PixooClient
from src.models import PixooRequest, Function

client = PixooClient("my_app", "localhost", 8000)

request = PixooRequest(
    app_id="my_app",
    functions=[
        Function(name="clear", args=[]),
        Function(name="draw_text_at_location_rgb", args=["Hello!", 10, 24, 255, 255, 255]),
        Function(name="push", args=[]),
    ],
    duration=5,
)
result = client.send(request)
print(result.success, result.status_code, result.data)
```

### Convenience Methods

```python
client = PixooClient("my_app", "localhost", 8000)

client.clear()
client.fill_rgb(255, 0, 0)
client.draw_text("Hi!", 20, 24, 255, 255, 255)
client.push()
```

Available convenience methods: `clear()`, `push()`, `fill_rgb(r, g, b)`,
`draw_text(text, x, y, r, g, b)`, `draw_pixel(x, y, r, g, b)`,
`draw_line(x1, y1, x2, y2, r, g, b)`,
`draw_filled_rectangle(x1, y1, x2, y2, r, g, b)`,
`draw_character(char, x, y, r, g, b)`,
`draw_image(image_data, x=0, y=0)`.

### Admin Commands (require API key)

```python
client = PixooClient("my_app", "localhost", 8000, api_key="your-secret-key")

# Device control commands (from DEVICE_CONTROL_COMMANDS allowlist)
client.send(PixooRequest(
    app_id="my_app",
    functions=[Function(name="set_brightness", args=[50])],
))
```

Admin commands include: `set_brightness`, `set_channel`, `set_clock`, `set_face`,
`set_screen`, `set_screen_on`, `set_screen_off`, `reboot`, `sound_buzzer`,
`play_local_gif`, `play_net_gif`, `send_text`, `set_visualizer`, and more.
See `src/commands.py` for the full list.

### Status and Mode Control

```python
# Get server status
status = client.get_status()
print(status.data)  # {"status": "running", "channels": [...], "carousel": [...], "urgent_queue_size": 0}

# Switch to a specific app (manual mode)
client.switch_channel("my_app")

# Set display mode
client.set_mode("carousel")  # or "manual"
```

## API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/status` | Server status and active channels | No |
| POST | `/api/v1/request` | Submit a PixooRequest for display | No* |
| POST | `/api/v1/channel/switch` | Switch to a specific app (manual mode) | Yes |
| POST | `/api/v1/mode/set` | Set display mode: `carousel` or `manual` | Yes |

\* Requests containing device-control commands require a valid `X-API-Key` header.

### GET /api/v1/status

**Response:**

```json
{
  "status": "running",
  "channels": ["app_0", "app_1"],
  "carousel": ["app_0", "app_1"],
  "urgent_queue_size": 0
}
```

### POST /api/v1/request

**Request Body:**

```json
{
  "app_id": "my_app",
  "functions": [
    {"name": "clear", "args": [], "kwargs": {}},
    {"name": "draw_pixel_at_location_rgb", "args": [1, 1, 255, 255, 255], "kwargs": {}},
    {"name": "push", "args": [], "kwargs": {}}
  ],
  "duration": 5,
  "is_admin": false
}
```

**Response:**

```json
{
  "status": "request added to queue",
  "app_id": "my_app",
  "functions_len": 3
}
```

### POST /api/v1/channel/switch

Switch to a specific app (manual mode). Requires `X-API-Key` header.

**Query Parameters:** `app_id` (string, required)

**Response:**

```json
{"status": "switched", "app_id": "my_app", "mode": "manual"}
```

**Errors:** 404 if `app_id` is not in the carousel.

### POST /api/v1/mode/set

Set the display mode. Requires `X-API-Key` header.

**Query Parameters:** `mode` (string, required) — `"carousel"` or `"manual"`

**Response:**

```json
{"status": "mode set", "mode": "carousel"}
```

**Errors:** 400 if mode is invalid.

## Demo

```powershell
# Run the demo (server must be running)
.\.venv\Scripts\python.exe examples\demo.py
```

The demo sends two alternating frames (red background with "1" and "2") via `PixooClient.send()`.

## Project Structure

```
src/
  __init__.py
  main.py              # FastAPI app factory + lifespan
  router.py            # API endpoints (4 routes)
  models.py            # PixooRequest, Function (Pydantic models)
  client.py            # PixooClient (low-level + convenience + admin)
  commands.py          # DRAWING_COMMANDS + DEVICE_CONTROL_COMMANDS allowlists
  config.py            # Settings (env-based, pydantic-settings)
  dependencies.py      # FastAPI dependencies (get_manager, verify_api_key)
  utils.py             # WorkerQueue (priority queue, currently unused)
  services/
    __init__.py
    channel_manager.py # ChannelManager: queues, worker_loop, mode, dispatch
tests/
  client_test.py       # Multi-client load generator (3 clients x 5 frames)
  test_endpoints.py    # Status + request endpoint tests
  test_channel_switch.py  # Channel switch auth + behavior tests
  test_mode.py         # Mode set/switch tests
  test_channel_demo.py # Interactive channel switching demo
  test_pixel.py        # Single-pixel draw test
examples/
  demo.py              # fill_rgb + draw_text demo
docs/
  architecture.md      # System design
  api.md               # API reference
  development.md       # Dev guide
```

## Known Issues

- **Urgent queue**: No producer exists; `interrupt_event` is never set — preemption path is dead code
- **API key enforcement gap**: `/channel/switch` and `/mode/set` declare `verify_api_key` as a dependency but assign it to `_api_key` (unused), so the key is not actually validated on those endpoints
- **WorkerQueue unused**: `src/utils.py` defines a priority queue that is not wired into the worker loop

## License

MIT
