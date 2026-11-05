import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from unittest.mock import patch
from src.client import PixooClient


def test_client_buffers_drawing_commands_until_push():
	client = PixooClient("test_app", "localhost", 8000)
	with patch.object(client, "send") as mock_send:
		# Fluent chaining / buffering
		client.clear()
		client.fill_rgb(255, 0, 0)
		client.draw_pixel_at_location_rgb(1, 1, 255, 255, 255)
		# No network calls yet
		mock_send.assert_not_called()

		# Now push
		client.push(duration=3, urgent=False)
		assert mock_send.call_count == 1
		req = mock_send.call_args[0][0]
		assert req.app_id == "test_app"
		assert req.duration == 3
		assert req.urgent is False
		assert len(req.functions) == 4
		assert req.functions[0].name == "clear"
		assert req.functions[1].name == "fill_rgb"
		assert req.functions[2].name == "draw_pixel_at_location_rgb"
		assert req.functions[3].name == "push"


def test_client_device_control_executes_immediately():
	client = PixooClient("test_app", "localhost", 8000, api_key="secret")
	with patch.object(client, "send") as mock_send:
		client.set_brightness(50)
		assert mock_send.call_count == 1
		req = mock_send.call_args[0][0]
		assert req.functions[0].name == "set_brightness"
		assert req.functions[0].args == [50]
