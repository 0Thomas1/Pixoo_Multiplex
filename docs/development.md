# Development Guide

## Setup

```powershell
# Create virtual environment
python -m venv .venv

# Install dependencies
.\.venv\Scripts\pip.exe install -r requirements.txt

# Configure
copy .env.example .env
# Edit .env with your Pixoo64 IP address and optional API key
```

### Environment Variables

| Variable     | Description                                                        |
| ------------ | ------------------------------------------------------------------ |
| `PIXOO_IP`   | Pixoo64 device IP address. If unset, the server auto-discovers.    |
| `API_KEY`    | Optional API key for device-control commands. If set, clients must send it via the `X-API-Key` header. |

## Running

```powershell
# Dev server
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000

# Smoke check (import only)
.\.venv\Scripts\python.exe -c "from src.main import app"
```

## Testing

All tests are standalone scripts (not pytest). Start the server first, then run:

```powershell
# Single pixel draw test
.\.venv\Scripts\python.exe tests/test_pixel.py

# Load test (3 clients x 5 frames via ThreadPoolExecutor)
.\.venv\Scripts\python.exe tests/client_test.py

# Endpoint tests (status, request enqueue, validation, carousel reflection)
.\.venv\Scripts\python.exe tests/test_endpoints.py

# Channel switch tests (auth, valid/invalid key, unknown app)
.\.venv\Scripts\python.exe tests/test_channel_switch.py

# Mode tests (set carousel/manual, invalid mode, auth required)
.\.venv\Scripts\python.exe tests/test_mode.py

# Interactive channel demo (requires API key)
.\.venv\Scripts\python.exe tests/test_channel_demo.py
```

### Test Files

| File                   | What it does                                                                                  |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| `test_pixel.py`        | Sends a single request that clears, draws one pixel, and pushes.                               |
| `client_test.py`       | Fires 3 clients x 5 frames at the server concurrently to verify load handling.                 |
| `test_endpoints.py`    | Tests `GET /status`, `POST /request`, validation (422 on empty functions), and carousel reflection. |
| `test_channel_switch.py` | Tests `POST /channel/switch` with valid key, missing key, wrong key, unknown app, and empty app_id. |
| `test_mode.py`         | Tests `POST /mode/set` for carousel, manual, invalid mode, and auth required.                  |
| `test_channel_demo.py` | Interactive demo: sends frames for two apps in a background thread; press Enter to switch, C for carousel. |

## Running the Demo

```powershell
# Start the server, then:
.\.venv\Scripts\python.exe examples/demo.py
```

The demo sends two frames ("1" and "2") with a red background in a loop.

## Project Structure

```
src/
  __init__.py              # Package marker
  main.py                  # FastAPI app factory + lifespan (worker loop)
  config.py                # Pydantic Settings (env vars)
  models.py                # PixooRequest, Function (Pydantic models)
  client.py                # PixooClient (HTTP client with convenience methods)
  commands.py              # Command registry (DRAWING_COMMANDS, DEVICE_CONTROL_COMMANDS)
  dependencies.py          # FastAPI dependencies (get_manager, verify_api_key)
  router.py                # API route definitions
  utils.py                 # WorkerQueue (priority queue)
  services/
    __init__.py            # Package marker
    channel_manager.py     # ChannelManager (owns all display state)

tests/
  test_pixel.py            # Single-pixel draw test
  client_test.py           # Multi-client load generator
  test_endpoints.py        # Endpoint integration tests
  test_channel_switch.py   # Channel switch auth/routing tests
  test_mode.py             # Mode set/auth tests
  test_channel_demo.py     # Interactive channel switching demo

examples/
  demo.py                  # Simple frame-loop demo

docs/
  architecture.md          # System design
  api.md                   # API reference
  development.md           # This file
```

## Adding a New Pixoo Command

1. Find the method name in the `pixoo` library (e.g., `draw_filled_rectangle`).
2. Add it to the appropriate list in `src/commands.py`:

```python
# For drawing commands (modify buffer, require push):
DRAWING_COMMANDS = [
    # ... existing commands ...
    "draw_filled_rectangle",
]

# For device control commands (immediate action, require API key):
DEVICE_CONTROL_COMMANDS = [
    # ... existing commands ...
    "set_brightness",
]
```

3. Use it in a request:

```json
{
  "name": "draw_filled_rectangle",
  "args": [0, 0, 10, 10, 255, 0, 0],
  "kwargs": {}
}
```

## Known Issues

- **Urgent queue**: No producer exists; `interrupt_event` is never set — preemption path is dead code.
- **Command typo**: `draw_character_at_location_rbg` has a typo (should be `rgb`) but matches the library method name.
