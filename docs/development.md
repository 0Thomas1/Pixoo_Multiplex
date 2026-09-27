# Development Guide

## Setup

```powershell
# Create virtual environment
python -m venv .venv

# Install dependencies
.\.venv\Scripts\pip.exe install fastapi uvicorn pydantic pixoo requests python-dotenv

# Configure
copy .env.example .env
# Edit .env with your Pixoo64 IP address
```

## Running

```powershell
# Dev server (auto-reload)
.\.venv\Scripts\python.exe -m fastapi dev src.main:app

# Production-style
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Smoke check (import only)
.\.venv\Scripts\python.exe -c "from src.main import app"
```

## Testing

```powershell
# Start the server first, then:

# Single pixel test
.\.venv\Scripts\python.exe tests/test_pixel.py

# Load test (3 clients x 5 requests)
.\.venv\Scripts\python.exe tests/client_test.py
```

## Project Structure

```
src/
  __init__.py      # Package marker
  main.py          # FastAPI app + ChannelManager
  models.py        # PixooRequest, Function (Pydantic models)
  client.py        # PixooClient
  utils.py         # WorkerQueue (priority queue)

tests/
  test_pixel.py    # Single-pixel draw test
  client_test.py   # Multi-client load generator

docs/
  architecture.md  # System design
  api.md           # API reference
  development.md   # This file
```

## Adding a New Pixoo Command

1. Find the method name in the `pixoo` library (e.g., `draw_filled_rectangle`)
2. Add it to `ChannelManager.commands` in `src/main.py`:

```python
self.commands = {
    # ... existing commands ...
    "draw_filled_rectangle": self.pixoo.draw_filled_rectangle,
}
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

- **Hot loop**: `carousel_index` is never advanced (commented out in `worker_loop`), so the first app is re-sent forever
- **Urgent queue**: No producer exists; `interrupt_event` is never set — preemption path is dead code
- **Command typo**: `draw_character_at_location_rbg` has a typo (should be `rgb`) but matches the library method name
