# AGENTS.md

FastAPI service that multiplexes several "apps" onto a single 64x64 Pixoo64 LED display.
Single package, flat layout, no build step. `Notes.md` holds the (truncated) design pseudo-code.
`README.md` and `docs/` cover setup/API but drift from the code (e.g. `docs/api.md` returns
`"channel switched"` while the code returns `"switched"`); treat `src/` as the source of truth.

## Commands

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000   # dev server
.\.venv\Scripts\python.exe -c "from src.main import app"          # cheapest smoke check
.\.venv\Scripts\python.exe tests/client_test.py                  # manual load generator, needs the server up
.\.venv\Scripts\python.exe tests/test_endpoints.py               # endpoint tests, needs the server up
.\.venv\Scripts\python.exe tests/test_channel_switch.py          # channel switch tests, needs the server up
.\.venv\Scripts\python.exe tests/test_mode.py                    # mode tests, needs the server up
.\.venv\Scripts\python.exe tests/test_pixel.py                   # single-pixel draw test, needs the server up
.\.venv\Scripts\python.exe tests/test_channel_demo.py            # interactive switch demo, needs server + API_KEY
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
- Simulated mode is **not wired into the app**: `ChannelManager.__init__` always calls
  `Pixoo(pixoo_ip)` and no setting exposes `simulated`. Running without hardware requires editing
  that call.
- The library's network calls set no timeouts, so an unreachable/half-routed IP can hang startup
  indefinitely instead of failing fast.

## Architecture

`ChannelManager` (src/services/channel_manager.py) owns all state; FastAPI routes are thin wrappers over it.

- `channels: {app_id -> asyncio.Queue}` — per-app FIFO of `PixooRequest` objects (max 100).
  When full, `enqueue_request` drops the oldest queued request to make room for the new one.
- `channel_0: [app_id, ...]` — the carousel: round-robin order shown on the one screen.
- `urgent_queue` — drained first, intended to preempt a long frame.
- `interrupt_event` — asyncio.Event to wake the worker early.
- `mode` — `"carousel"` or `"manual"` (defaults to `"manual"`).
- `manual_app` — the selected app in manual mode; `None` until `/channel/switch` is called.
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
  `_api_key` (unused). `verify_api_key` returns `None` for a missing/wrong key and never raises,
  so those endpoints return 200 without a key. `tests/test_channel_switch.py` and
  `tests/test_mode.py` assert 401s and therefore fail as written — not a regression to chase.
- Admin commands without a key are rejected as HTTP **200** with `{"status": "forbidden"}`,
  not 403 (`enqueue_request`).
- Default `mode == "manual"` while `manual_app is None`; the manual branch needs a non-None
  `manual_app`, so out of the box the worker round-robins the carousel until a switch happens.
- `WorkerQueue` in `src/utils.py` is defined but not used.

## Conventions

- **Tabs** for indentation in `src/main.py`, `src/client.py`, `src/models.py`, `src/router.py`,
  `src/commands.py`, `src/config.py`, `src/dependencies.py`, `src/services/channel_manager.py`,
  `tests/`, and `examples/`. `src/utils.py` is the lone 4-space file; don't reformat it.
- No CI, no linter, no formatter config. Keep changes minimal and match surrounding style.
