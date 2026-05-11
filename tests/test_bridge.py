"""Tests for aiolocknalert."""

from aiolocknalert import LocknAlertBridgeApi


def test_base_url() -> None:
    """Test base URL generation."""
    api = LocknAlertBridgeApi("192.168.40.28", port=443)
    assert api.base_url == "https://192.168.40.28:443"