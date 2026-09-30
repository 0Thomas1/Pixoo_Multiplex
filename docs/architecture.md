# Architecture

## Overview

Pixoo Worker is a FastAPI service that multiplexes multiple "apps" onto a single 64x64 Pixoo64 LED display. It uses a carousel model: each app gets a turn on screen, round-robin style. A manual mode allows pinning the display to a single app.

## Components

```
┌─────────────┐     POST /api/v1/request     ┌──────────────────┐
│   Client    │ ─────────────────────────────▶│   FastAPI App    │
│ (PixooClient)│                              │   (main.py)      │
└─────────────┘                              └────────┬─────────┘
                                                       │
                                                       ▼
                                             ┌──────────────────┐
                                             │ ChannelManager   │
                                             │                  │
                                             │ ┌──────────────┐ │
                                             │ │ urgent_queue │ │  ← no producer (dead code)
                                             │ └──────────────┘ │
                                             │ ┌──────────────┐ │
                                             │ │ channel_0    │ │  ← carousel order
                                             │ │ [app_id...]  │ │
                                             │ └──────────────┘ │
                                             │ ┌──────────────┐ │
                                             │ │ channels     │ │  ← per-app queues
                                             │ │ {app_id: Q}  │ │
                                             │ └──────────────┘ │
                                             │ ┌──────────────┐ │
                                             │ │ commands     │ │  ← allowlist
                                             │ │ {name: fn}   │ │
                                             │ └──────────────┘ │
                                             └────────┬─────────┘
                                                       │
                                                       ▼
                                             ┌──────────────────┐
                                             │  Pixoo Device    │
                                             │  (64x64 LED)     │
                                             └──────────────────┘
```

## Data Flow

1. Client sends `POST /api/v1/request` with a `PixooRequest` JSON body
2. `ChannelManager.enqueue_request()` validates admin permissions, creates the app's queue on first use, and enqueues the request
3. `worker_loop()` picks the next request based on mode (urgent → manual → carousel)
4. `send_to_pixoo()` iterates over `request.functions` and dispatches each to the device via the command allowlist
5. The worker sleeps for `request.duration` seconds before processing the next request

## State Model

| State | Type | Description |
|---|---|---|
| `channels` | `dict[str, asyncio.Queue]` | Per-app FIFO of `PixooRequest` objects (max 100 per queue) |
| `channel_0` | `list[str]` | Carousel: ordered list of active app_ids |
| `urgent_queue` | `asyncio.Queue` | High-priority requests drained before all else |
| `interrupt_event` | `asyncio.Event` | Signals the worker to wake early from a sleep |
| `mode` | `str` | `"carousel"` or `"manual"` (default: `"manual"`) |
| `manual_app` | `str \| None` | The selected app_id when in manual mode |
| `commands` | `dict[str, Callable]` | Allowlist of device functions from `DRAWING_COMMANDS + DEVICE_CONTROL_COMMANDS` |
| `admin_commands` | `set[str]` | Subset of commands requiring API key (`DEVICE_CONTROL_COMMANDS`) |

## Worker Loop

```
while True:
    # 1. Urgent queue (highest priority)
    if urgent_queue not empty:
        request = urgent_queue.get()
        send_to_pixoo(request)
        sleep_interruptible(duration, interruptable=False)
        continue

    # 2. Manual mode: only process the selected app
    if mode == "manual" and manual_app:
        queue = channels[manual_app]
        if queue not empty:
            request = queue.get()
            send_to_pixoo(request)
            sleep_interruptible(duration, interruptable=True)
        else:
            sleep(1)
        continue

    # 3. Carousel mode: round-robin through all apps
    if channel_0 not empty:
        current_app = channel_0[carousel_index]
        queue = channels[current_app]
        if queue not empty:
            request = queue.get()
            send_to_pixoo(request)
            sleep_interruptible(duration, interruptable=True)
            carousel_index = (carousel_index + 1) % len(channel_0)
        else:
            sleep(1)
    else:
        sleep(1)
```

### Carousel Index

The `carousel_index` is advanced after each successful dequeue in carousel mode (line 70 of `channel_manager.py`). It wraps around using modulo arithmetic. This means the carousel does rotate through apps as designed.

### Urgent Queue — Dead Code

The `urgent_queue` is checked at the top of every worker loop iteration, but **no code path ever enqueues to it**. There is no API endpoint, no internal mechanism, and no producer of any kind. The queue is always empty, making this branch dead code. To activate it, you would need to add a producer (e.g., a `POST /api/v1/urgent` endpoint or an internal trigger).

### Interrupt Event — Dead Code

The `interrupt_event` is never `.set()` anywhere in the codebase. The `sleep_interruptible()` method checks it, but since it is never set, the worker always sleeps for the full duration. This is closely related to the urgent queue: the intended design was likely for urgent requests to set the event and preempt the current frame.

## Command Allowlist

Only commands in `DRAWING_COMMANDS` and `DEVICE_CONTROL_COMMANDS` (defined in `commands.py`) are exposed via `ChannelManager.commands`. Any function name not in this dict is rejected with `"Unknown function"`.

### Drawing Commands

These modify a buffer that requires `push()` to display:

| Command | Description |
|---|---|
| `clear` | Clear the display |
| `clear_rgb` | Clear with a specific color |
| `draw_character` | Draw a character |
| `draw_character_at_location_rgb` | Draw character at position |
| `draw_filled_rectangle` | Draw a filled rectangle |
| `draw_filled_rectangle_from_top_left_to_bottom_right_rgb` | Filled rectangle with color |
| `draw_image` | Draw an image |
| `draw_image_at_location` | Draw image at position |
| `draw_line` | Draw a line |
| `draw_line_from_start_to_stop_rgb` | Line with color |
| `draw_pixel` | Draw a single pixel |
| `draw_pixel_at_index` | Draw pixel at index |
| `draw_pixel_at_index_rgb` | Draw pixel at index with color |
| `draw_pixel_at_location_rgb` | Draw pixel at position with color |
| `draw_text` | Draw text |
| `draw_text_at_location_rgb` | Draw text at position with color |
| `fill` | Fill the display |
| `fill_rgb` | Fill with a specific color |
| `push` | Push the buffer to the display |

### Device Control Commands (Admin Only)

These take immediate action on the device and require API key verification:

| Command | Description |
|---|---|
| `find_local_device_ip` | Discover device IP |
| `get_all_device_configurations` | Get all config |
| `get_device_time` | Get device time |
| `play_local_gif` | Play a local GIF |
| `play_local_gif_directory` | Play GIFs from directory |
| `play_net_gif` | Play a network GIF |
| `sound_buzzer` | Sound the buzzer |
| `reboot` | Reboot the device |
| `send_text` | Send text to display |
| `send_text_at_location_rgb` | Send text at position |
| `set_brightness` | Set brightness |
| `set_channel` | Set channel |
| `set_clock` | Set clock |
| `set_face` | Set face |
| `set_high_light_mode` | Set highlight mode |
| `set_mirror_mode` | Set mirror mode |
| `set_noise_status` | Set noise status |
| `set_score_board` | Set scoreboard |
| `set_screen` | Set screen |
| `set_screen_off` | Turn screen off |
| `set_screen_on` | Turn screen on |
| `set_visualizer` | Set visualizer |
| `set_white_balance` | Set white balance |
| `set_white_balance_rgb` | Set white balance with color |
| `validate_connection` | Validate connection |

To add a new command, add it to the appropriate list in `commands.py`.

## API Key Verification

The API key flow uses a FastAPI dependency:

1. `verify_api_key()` reads the `X-API-Key` header
2. If the header is missing or doesn't match `settings.api_key`, it returns `None`
3. If it matches, it returns the key string
4. In `POST /api/v1/request`, if `api_key` is truthy, `request.is_admin` is set to `True`
5. In `enqueue_request()`, if any function is in `admin_commands` but `request.is_admin` is `False`, the request is rejected with `{"status": "forbidden"}`
6. `POST /api/v1/channel/switch` and `POST /api/v1/mode/set` require a valid API key (the `_api_key` dependency parameter is prefixed with `_` to indicate it's required but unused in the body)

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/status` | No | Get server status (channels, carousel, urgent queue size) |
| `POST` | `/api/v1/request` | Optional | Enqueue a PixooRequest (admin key required for device control commands) |
| `POST` | `/api/v1/channel/switch` | Yes | Switch to a specific app (manual mode) |
| `POST` | `/api/v1/mode/set` | Yes | Set display mode (`"carousel"` or `"manual"`) |
