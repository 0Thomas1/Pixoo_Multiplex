# API Reference

## Base URL

```
http://localhost:8000
```

All endpoints are prefixed with `/api/v1`.

## Authentication

Most endpoints accept an optional `X-API-Key` header. When the server is configured with an API key, admin-only endpoints (`/channel/switch`, `/mode/set`) require it. Providing a valid key on `/request` also marks the request as admin, unlocking device control commands.

```
X-API-Key: your-api-key-here
```

---

## Endpoints

### GET /api/v1/status

Get current server status. No authentication required.

**Response:**

```json
{
  "status": "running",
  "channels": ["app_0", "app_1"],
  "carousel": ["app_0", "app_1"],
  "urgent_queue_size": 0
}
```

| Field | Type | Description |
|---|---|---|
| `status` | string | Always `"running"` |
| `channels` | list[string] | Active app IDs with queued requests |
| `carousel` | list[string] | Round-robin display order |
| `urgent_queue_size` | integer | Number of pending urgent requests |

---

### POST /api/v1/request

Submit a PixooRequest for display. If a valid `X-API-Key` header is provided, `is_admin` is set to `true` on the request, allowing device control commands.

**Request Body:**

```json
{
  "app_id": "my_app",
  "functions": [
    {
      "name": "clear",
      "args": [],
      "kwargs": {}
    },
    {
      "name": "draw_pixel_at_location_rgb",
      "args": [1, 1, 255, 255, 255],
      "kwargs": {}
    },
    {
      "name": "push",
      "args": [],
      "kwargs": {}
    }
  ],
  "duration": 5,
  "is_admin": false
}
```

**Response:**

```json
{
  "status": "request added to queue",
  "app_id": "my_app",
  "functions_len": 3
}
```

---

### POST /api/v1/channel/switch

Switch to a specific app (manual mode). Requires a valid `X-API-Key` header.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `app_id` | string | Yes | The app ID to switch to |

**Response:**

```json
{
  "status": "channel switched",
  "app_id": "my_app",
  "mode": "manual"
}
```

**Errors:**

- `404` — `app_id` not found in the carousel.

---

### POST /api/v1/mode/set

Set the display mode. Requires a valid `X-API-Key` header.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `mode` | string | Yes | `"carousel"` or `"manual"` |

**Response:**

```json
{
  "status": "mode set",
  "mode": "carousel"
}
```

**Errors:**

- `400` — Invalid mode value.

---

## Data Models

### PixooRequest

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `app_id` | string | Yes | — | App identifier |
| `functions` | list[Function] | Yes | — | Commands to execute (min 1) |
| `duration` | integer | No | 5 | Seconds to display before advancing |
| `is_admin` | boolean | No | false | Whether request can use device control commands |

### Function

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | Yes | — | Command name from the allowlist |
| `args` | list | No | [] | Positional arguments |
| `kwargs` | dict | No | {} | Keyword arguments |

---

## Command Allowlist

Commands are split into two categories. Drawing commands modify a buffer that requires `push()` to display. Device control commands take immediate action and require a valid API key (`is_admin: true`).

### Drawing Commands

| Command | Description |
|---|---|
| `clear` | Clear the display buffer |
| `clear_rgb` | Clear the display buffer with a color |
| `draw_character` | Draw a character |
| `draw_character_at_location_rgb` | Draw a character at (x, y) with RGB color |
| `draw_filled_rectangle` | Draw a filled rectangle |
| `draw_filled_rectangle_from_top_left_to_bottom_right_rgb` | Draw a filled rectangle with RGB color |
| `draw_image` | Draw an image |
| `draw_image_at_location` | Draw a base64 image at (x, y) |
| `draw_line` | Draw a line |
| `draw_line_from_start_to_stop_rgb` | Draw a line with RGB color |
| `draw_pixel` | Draw a single pixel |
| `draw_pixel_at_index` | Draw a pixel by index |
| `draw_pixel_at_index_rgb` | Draw a pixel by index with RGB color |
| `draw_pixel_at_location_rgb` | Draw a pixel at (x, y) with RGB color |
| `draw_text` | Draw text |
| `draw_text_at_location_rgb` | Draw text at (x, y) with RGB color |
| `fill` | Fill the display |
| `fill_rgb` | Fill the display with an RGB color |
| `push` | Push the buffer to the display |

### Device Control Commands (Admin Only)

| Command | Description |
|---|---|
| `find_local_device_ip` | Discover the device IP on the LAN |
| `get_all_device_configurations` | Get all device configuration |
| `get_device_time` | Get the device clock time |
| `play_local_gif` | Play a local GIF file |
| `play_local_gif_directory` | Play all GIFs in a directory |
| `play_net_gif` | Play a GIF from a URL |
| `sound_buzzer` | Sound the device buzzer |
| `reboot` | Reboot the device |
| `send_text` | Send text to the device |
| `send_text_at_location_rgb` | Send text at a location with RGB color |
| `set_brightness` | Set display brightness |
| `set_channel` | Set the device channel |
| `set_clock` | Enable/disable the clock display |
| `set_face` | Set the clock face |
| `set_high_light_mode` | Set highlight mode |
| `set_mirror_mode` | Set mirror mode |
| `set_noise_status` | Set noise status |
| `set_score_board` | Set score board |
| `set_screen` | Set the screen |
| `set_screen_off` | Turn the screen off |
| `set_screen_on` | Turn the screen on |
| `set_visualizer` | Set the visualizer |
| `set_white_balance` | Set white balance |
| `set_white_balance_rgb` | Set white balance with RGB |
| `validate_connection` | Validate the device connection |

---

## Python Client

The `PixooClient` class in `src/client.py` provides a convenient wrapper around the API.

### ClientResult

Every client method returns a `ClientResult` dataclass:

| Field | Type | Description |
|---|---|---|
| `success` | bool | True if the HTTP response was 2xx |
| `status_code` | int | HTTP status code |
| `data` | any | Parsed JSON dict, or raw text if not JSON |

### PixooClient

```python
from src.client import PixooClient

client = PixooClient(appid="my_app", host="localhost", port=8000, api_key="secret")
```

**Constructor Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `appid` | string | Yes | — | Identifier for this client's app |
| `host` | string | Yes | — | Server hostname or IP |
| `port` | integer | Yes | — | Server port |
| `api_key` | string | No | None | API key sent as `X-API-Key` header |

**Methods:**

| Method | Description |
|---|---|
| `send(request)` | Send a `PixooRequest` to the server |
| `get_status()` | Get current server status |
| `switch_channel(app_id)` | Switch to a specific app (requires API key) |
| `set_mode(mode)` | Set display mode: `"carousel"` or `"manual"` (requires API key) |
| `clear()` | Clear the display |
| `push()` | Push the current buffer to the display |
| `fill_rgb(r, g, b)` | Fill the entire display with a color |
| `draw_text(text, x, y, r, g, b)` | Draw text at a location |
| `draw_pixel(x, y, r, g, b)` | Draw a single pixel |
| `draw_line(x1, y1, x2, y2, r, g, b)` | Draw a line between two points |
| `draw_filled_rectangle(x1, y1, x2, y2, r, g, b)` | Draw a filled rectangle |
| `draw_character(char, x, y, r, g, b)` | Draw a single character |
| `draw_image(image_data, x=0, y=0)` | Draw a base64-encoded image |

---

## Example: Draw a White Pixel at (1,1)

### Using the Python client

```python
from src.client import PixooClient

client = PixooClient(appid="test", host="localhost", port=8000)

client.clear()
client.draw_pixel(1, 1, 255, 255, 255)
client.push()
```

### Using raw HTTP

```python
import requests

request = {
    "app_id": "test",
    "functions": [
        {"name": "clear", "args": [], "kwargs": {}},
        {"name": "draw_pixel_at_location_rgb", "args": [1, 1, 255, 255, 255], "kwargs": {}},
        {"name": "push", "args": [], "kwargs": {}},
    ],
    "duration": 5,
}

response = requests.post("http://localhost:8000/api/v1/request", json=request)
print(response.json())
```

### Using the Python client with a PixooRequest

```python
from src.client import PixooClient
from src.models import PixooRequest, Function

client = PixooClient(appid="test", host="localhost", port=8000)

request = PixooRequest(
    app_id="test",
    functions=[
        Function(name="clear"),
        Function(name="draw_pixel_at_location_rgb", args=[1, 1, 255, 255, 255]),
        Function(name="push"),
    ],
    duration=5,
)

result = client.send(request)
print(result.success, result.status_code, result.data)
```
