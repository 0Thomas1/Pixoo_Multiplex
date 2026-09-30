# Pixoo Worker

FastAPI service that multiplexes multiple "apps" onto a single 64x64 Pixoo64 LED display.

## Features

- **Multi-app carousel**: Multiple apps share one display via round-robin scheduling
- **Function-based API**: Send ordered lists of device commands (clear, draw, push)
- **Priority queue**: Urgent requests can preempt the carousel
- **Python client**: `PixooClient` with low-level and high-level methods
- **Pydantic validation**: Request/response models with automatic validation
- **Simulated mode**: Run without hardware using the pixoo library's simulator

## Requirements

- Python 3.10+
- A Pixoo64 device on your LAN (or use simulated mode)

## Installation

```powershell
# Create virtual environment
python -m venv .venv

# Install dependencies
.\.venv\Scripts\pip.exe install fastapi uvicorn pydantic pixoo requests python-dotenv

# Copy config template
copy .env.example .env
```

## Configuration

Edit `.env` to set your device IP and optional API key:

```env
PIXOO_IP=192.168.1.100
API_KEY=your-secret-key
```

If `PIXOO_IP` is unset, the server auto-discovers the device on your LAN.

## Running the Server

```powershell
# Start the server
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000

# Smoke check (import only)
.\.venv\Scripts\python.exe -c "from src.main import app"
```

## Using the Python Client

```python
from src.client import PixooClient
from src.models import PixooRequest, Function

client = PixooClient("my_app", "localhost", 8000)

# Send a single request
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

### Admin Commands (require API key)

```python
client = PixooClient("my_app", "localhost", 8000, api_key="your-secret-key")
client.set_brightness(50)
client.set_channel(2)
```

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/status` | Server status and active channels |
| POST | `/api/v1/request` | Submit a PixooRequest for display |
| POST | `/api/v1/channel/switch` | Switch to a specific app (requires API key) |
| POST | `/api/v1/mode/set` | Set display mode: `carousel` or `manual` (requires API key) |

## Demo

```powershell
# Run the demo (server must be running)
.\.venv\Scripts\python.exe examples\demo.py
```

## Project Structure

```
src/
  __init__.py
  main.py              # FastAPI app factory
  router.py            # API endpoints
  models.py            # PixooRequest, Function (Pydantic models)
  client.py            # PixooClient (low-level + high-level)
  commands.py          # Command allowlist registry
  config.py            # Settings (env-based)
  dependencies.py      # FastAPI dependencies
  services/
    channel_manager.py # Queue management + worker loop
tests/
  client_test.py       # Multi-client load generator
  test_pixel.py        # Single-pixel draw test
  ...
examples/
  demo.py              # fill_rgb + draw_text demo
docs/
  architecture.md      # System design
  api.md               # API reference
  development.md       # Dev guide
```

## Known Issues

- **Hot loop**: `carousel_index` is never advanced in `worker_loop()`, so the first app is re-sent forever
- **Urgent queue**: No producer exists; `interrupt_event` is never set — preemption path is dead code
- **Command typo**: `draw_character_at_location_rbg` has a typo (should be `rgb`) but matches the library method name

See [docs/development.md](docs/development.md) for details.

## License

MIT
