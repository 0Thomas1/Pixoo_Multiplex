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
| `channels` | `dict[str, asyncio.Queue]` | Per-app FIFO of `PixooRequest` objects |
| `channel_0` | `list[str]` | Carousel: ordered list of active app_ids |
| `urgent_queue` | `asyncio.Queue` | High-priority requests drained before carousel |
| `interrupt_event` | `asyncio.Event` | Signals the worker to wake early |

## Worker Loop

```
while True:
    if urgent_queue not empty:
        request = urgent_queue.get()
        send_to_pixoo(request)
        sleep(request.duration)
        continue

    if channel_0 not empty:
        current_app = channel_0[carousel_index]
        request = channels[current_app].get()
        send_to_pixoo(request)
        # TODO: advance carousel_index
    else:
        sleep(1)
```

## Command Allowlist

Only these device commands are exposed (in `ChannelManager.commands`):

| Command | Description |
|---|---|
| `clear` | Clear the display |
| `clear_rgb` | Clear with a specific color |
| `draw_character` | Draw a character |
| `draw_character_at_location_rbg` | Draw character at position (note: typo in name) |
| `draw_pixel_at_location_rgb` | Draw a single pixel |
| `push` | Push the buffer to the display |

To add a new command, add it to the `commands` dict in `ChannelManager.__init__`.
