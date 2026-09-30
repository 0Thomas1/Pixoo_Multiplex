# AGENTS.md

FastAPI service that multiplexes several "apps" onto a single 64x64 Pixoo64 LED display.
Single package, flat layout, no build step. `Notes.md` holds the (truncated) design pseudo-code.

## Commands

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000   # dev server
.\.venv\Scripts\python.exe -c "from src.main import app"          # cheapest smoke check
.\.venv\Scripts\python.exe tests/client_test.py                  # manual load generator, needs the server up
.\.venv\Scripts\python.exe tests/test_endpoints.py               # endpoint tests, needs the server up
.\.venv\Scripts\python.exe tests/test_channel_switch.py          # channel switch tests, needs the server up
.\.venv\Scripts\python.exe tests/test_mode.py                    # mode tests, needs the server up
.\.venv\Scripts\python.exe tests/test_pixel.py                   # single-pixel draw test, needs the server up
.\.venv\Scripts\python.exe examples\demo.py                      # demo client, needs the server up
```

- Dependencies are listed in `requirements.txt` (fastapi, uvicorn, pydantic>=2,
  pydantic-settings, pixoo==0.9.2, requests, python-dotenv). Install with
  `pip install -r requirements.txt`. There is no `pyproject.toml` and no lockfile.
- There is **no test runner** (pytest is not installed). All `tests/` files are `__main__`
  scripts that use `assert` and print PASS/FAIL. Run them as scripts, never via a test runner.
- `tests/client_test.py` fires 3 clients x 5 frames at `localhost:8000` via a `ThreadPoolExecutor`.

## Configuration

- `PIXOO_IP` env var sets the device IP. If unset, `Pixoo(None)` auto-discovers via `find_local_device_ip()`.
- `API_KEY` env var enables device-control commands. If set, clients must send it via the
  `X-API-Key` header. Requests containing admin commands without a valid key are rejected.
- Additional settings in `src/config.py`: `cors_origins` (default `["*"]`), `log_level` (default `"INFO"`).
- Copy `.env.example` to `.env` and edit.

## Hardware / dev loop

- `pixoo.Pixoo.__init__` performs **network I/O in the constructor** (`fill()` +
  `validate_connection()`). Because `ChannelManager` is instantiated in the FastAPI `lifespan`,
  startup blocks on the device being reachable on the LAN.
- Run without hardware via the library's simulator: `Pixoo(ip, simulated=True)`. That makes
  `validate_connection()` return `True` unconditionally and turns every draw method into a no-op
  (`pixoo/objects/pixoo.py`). `Simulator` is not re-exported as `pixoo.Simulator`; it lives in
  `pixoo/objects/simulator.py` and is imported into `pixoo/objects/pixoo.py`.
- `Pixoo(ip_address=None)` auto-discovers the device via `find_local_device_ip()`.

## Architecture

`ChannelManager` (src/services/channel_manager.py) owns all state; FastAPI routes are thin wrappers over it.

- `channels: {app_id -> asyncio.Queue}` — per-app FIFO of `PixooRequest` objects (max 100).
- `channel_0: [app_id, ...]` — the carousel: round-robin order shown on the one screen.
- `urgent_queue` — drained first, intended to preempt a long frame.
- `interrupt_event` — asyncio.Event to wake the worker early.
- `mode` — `"carousel"` or `"manual"`.
- `manual_app` — the selected app in manual mode.
- `worker_loop()` is started as a task in the FastAPI `lifespan` and cancelled on shutdown.
- Single ingress route: `POST /api/v1/request` takes a `PixooRequest`
  (`app_id`/`functions: list[Function]`/`duration`/`is_admin`, each `Function` = `name`/`args`/`kwargs`).
- Admin commands (from `DEVICE_CONTROL_COMMANDS`) are rejected unless `request.is_admin` is True,
  which is set by the `/request` route when a valid `X-API-Key` header is present.

### Command allowlist

`src/commands.py` defines two lists:
- `DRAWING_COMMANDS` — buffer operations (clear, draw_*, fill_*, push)
- `DEVICE_CONTROL_COMMANDS` — immediate device actions (set_brightness, set_channel, reboot, etc.)

`ChannelManager.commands` is built from both lists via `getattr(self.pixoo, name)`.
To support a new Pixoo command you must add it to the appropriate list in `src/commands.py`;
otherwise the worker prints `Unknown function`.

### Unfinished plumbing — do not assume the pipeline works

- `urgent_queue` has no producer and `interrupt_event` is never `.set()`, so the preemption path
  is dead code.
- `/channel/switch` and `/mode/set` declare `verify_api_key` as a dependency but assign it to
  `_api_key` (unused), so the API key is not actually validated on those endpoints.
- `WorkerQueue` in `src/utils.py` is defined but not used.

## Conventions

- **Tabs** for indentation in `src/main.py`, `src/client.py`, `src/models.py`, `src/router.py`,
  `src/commands.py`, `src/config.py`, `src/dependencies.py`, `src/services/channel_manager.py`,
  `tests/`, and `examples/`. `src/utils.py` is the lone 4-space file; don't reformat it.
- No CI, no linter, no formatter config. Keep changes minimal and match surrounding style.
