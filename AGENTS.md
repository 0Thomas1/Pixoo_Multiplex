# AGENTS.md

FastAPI service that multiplexes several "apps" onto a single 64x64 Pixoo64 LED display.
Single package, flat layout, no build step. `Notes.md` holds the (truncated) design pseudo-code.

## Commands

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000   # dev server
.\.venv\Scripts\python.exe tests/client_test.py                  # manual load generator, needs the server up
.\.venv\Scripts\python.exe -c "from src.main import app"          # cheapest smoke check
```

- There is **no dependency manifest** (no `pyproject.toml`/`requirements.txt`) and **no test runner**
  (pytest is not installed). The gitignored `.venv` (Python 3.10.6) is the only record of deps:
  fastapi, uvicorn, pydantic 2, `pixoo` 0.9.2, requests, python-dotenv. Install into `.venv`; don't assume a lockfile.
- `tests/client_test.py` is a `__main__` script, **not** a pytest test. It fires 3 clients x 5 frames at
  `localhost:8000` via a `ThreadPoolExecutor`. Run it as a script, never via a test runner.

## Configuration

- `PIXOO_IP` env var sets the device IP. If unset, `Pixoo(None)` auto-discovers via `find_local_device_ip()`.

## Hardware / dev loop

- `pixoo.Pixoo.__init__` performs **network I/O in the constructor** (`fill()` +
  `validate_connection()`). Because `ChannelManager` is instantiated at module import, startup
  blocks on the device being reachable on the LAN.
- Run without hardware via the library's simulator: `Pixoo(ip, simulated=True)`. That makes
  `validate_connection()` return `True` unconditionally and turns every draw method into a no-op
  (`pixoo/objects/pixoo.py`). `Simulator` is not re-exported as `pixoo.Simulator`; it lives in
  `pixoo/objects/simulator.py` and is imported into `pixoo/objects/pixoo.py`.
- `Pixoo(ip_address=None)` auto-discovers the device via `find_local_device_ip()`.

## Architecture

`ChannelManager` (src/main.py) owns all state; FastAPI routes are thin wrappers over it.

- `channels: {app_id -> asyncio.Queue}` — per-app FIFO of `PixooRequest` objects.
- `channel_0: [app_id, ...]` — the carousel: round-robin order shown on the one screen.
- `urgent_queue` — drained first, intended to preempt a long frame.
- `worker_loop()` is started as a task in the FastAPI `lifespan` and cancelled on shutdown.
- Single ingress route: `POST /api/v1/request` takes a `PixooRequest`
  (`app_id`/`functions: list[Function]`/`duration`, each `Function` = `name`/`args`/`kwargs`).

### Unfinished plumbing — do not assume the pipeline works

- `carousel_index` is never advanced (the increment at src/main.py:43-46 is commented out), so the
  worker re-sends the first app forever in a hot loop.
- `urgent_queue` has no producer and `interrupt_event` is never `.set()`, so the preemption path
  is dead code.

## Conventions

- **Tabs** for indentation in `src/main.py`, `src/client.py`, `src/models.py`, `tests/client_test.py`.
  `src/utils.py` is the lone 4-space file; don't reformat it.
- `ChannelManager.commands` is an allowlist of only device calls, exposed under custom names
  (`draw_character_at_location_rbg` -> `draw_character_at_location_rgb`). To support a new Pixoo
  command you must add it there; otherwise the worker prints `Unknown function`.
- No CI, no linter, no formatter config. Keep changes minimal and match surrounding style.
