# API Reference

## Base URL

```
http://localhost:8000
```

## Endpoints

### GET /api/v1/status

Get current server status.

**Response:**

```json
{
  "status": "running",
  "channels": ["app_0", "app_1"],
  "carousel": ["app_0", "app_1"],
  "urgent_queue_size": 0
}
```

---

### POST /api/v1/request

Submit a PixooRequest for display.

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
  "duration": 5
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

## Data Models

### PixooRequest

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `app_id` | string | Yes | — | App identifier |
| `functions` | list[Function] | Yes | — | Commands to execute (min 1) |
| `duration` | integer | No | 5 | Seconds to display |

### Function

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | Yes | — | Command name from allowlist |
| `args` | list | No | [] | Positional arguments |
| `kwargs` | dict | No | {} | Keyword arguments |

## Example: Draw a White Pixel at (1,1)

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
