# Pixoo Worker

FastAPI service that multiplexes multiple "apps" onto a single 64x64 Pixoo64 LED display.

## Features

- **Multi-app carousel**: Multiple apps share one display via round-robin scheduling
- **Function-based API**: Send ordered lists of device commands (clear, draw, push)
- **Priority queue**: Urgent requests can preempt the carousel
- **Pydantic validation**: Request/response models with automatic validation
- **Simulated mode**: Run without hardware using the pixoo library's simulator

## Quickstart

```powershell
# Install dependencies
.\.venv\Scripts\pip.exe install fastapi uvicorn pydantic pixoo requests python-dotenv

# Configure your device IP
copy .env.example .env
# Edit .env and set PIXOO_IP=192.168.x.x

# Start the server
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000

# In another terminal, run a test
.\.venv\Scripts\python.exe tests/test_pixel.py
```

## Project Structure

```
src/           # Source code (FastAPI app, models, client)
tests/         # Test scripts
docs/          # Documentation
.env           # Local config (gitignored)
.env.example   # Config template
```

## Documentation

- [Architecture](docs/architecture.md) — System design and data flow
- [API Reference](docs/api.md) — Endpoint documentation with examples
- [Development](docs/development.md) — Setup, testing, and debugging

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/status` | Server status and active channels |
| POST | `/api/v1/request` | Submit a PixooRequest for display |

## License

MIT
