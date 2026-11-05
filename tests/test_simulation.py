import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from unittest.mock import patch
from src.services.channel_manager import ChannelManager


def test_simulation_bypasses_network_discovery():
	with patch("src.services.channel_manager.Pixoo") as mock_pixoo:
		manager = ChannelManager(pixoo_ip=None, simulated=True)
		mock_pixoo.assert_called_once_with("127.0.0.1", simulated=True)
		assert manager.pixoo is not None
