# Architecture

## Overview

Pixoo Worker is a FastAPI service that multiplexes multiple "apps" onto a single 64x64 Pixoo64 LED display. It uses a carousel model: each app gets a turn on screen, round-robin style.

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
                                            │ │ urgent_queue │ │
                                            │ └──────────────┘ │
                                            │ ┌──────────────┐ │
                                            │ │ channel_0    │ │  ← carousel order
                                            │ │ [app_id...]  │ │
                                            │ └──────────────┘ │
                                            │ ┌──────────────┐ │
                                            │ │ channels     │ │  ← per-app queues
                                            │ │ {app_id: Q}  │ │
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
2. `ChannelManager.enqueue_request()` adds the request to the app's queue
3. `worker_loop()` picks the next app from the carousel and dequeues a request
4. `send_to_pixoo()` iterates over `request.functions` and dispatches each to the device

## State Model

| State | Type | Description |
|---|---|---|
| `app_queues` | `dict[str, asyncio.Queue]` | Per-app FIFO of `PixooRequest` objects (maxsize=100) |
| `carousel_apps` | `list[str]` | Carousel: ordered list of active app_ids |
| `urgent_queue` | `asyncio.Queue` | High-priority requests drained before carousel |
| `interrupt_event` | `asyncio.Event` | Signals the worker to wake early on urgent request |
| `mode` | `str` | Display mode: `"carousel"` or `"manual"` |
| `manual_app` | `str | None` | Target app displayed in manual mode |

## Worker Loop

```
while True:
    if urgent_queue not empty:
        request = urgent_queue.get()
        send_to_pixoo(request)
        sleep(request.duration)
        advance carousel_index
        continue

    if mode == "manual" and manual_app:
        process manual_app request
        sleep(request.duration, interruptable=True)
        continue

    if carousel_apps not empty:
        current_app = carousel_apps[carousel_index]
        process current_app request
        sleep(request.duration, interruptable=True)
        advance carousel_index
    else:
        sleep(1)
```

## Command Allowlist

Device commands are strictly categorized in `src/commands.py`:
- `DRAWING_COMMANDS`: Frame buffer modifications (`clear`, `fill_rgb`, `draw_text_at_location_rgb`, `draw_pixel_at_location_rgb`, `push`, etc.).
- `DEVICE_CONTROL_COMMANDS`: Administrative actions (`set_brightness`, `set_screen`, `reboot`, etc.) gated behind `X-API-Key` authentication.
