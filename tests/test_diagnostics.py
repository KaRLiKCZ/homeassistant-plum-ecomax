"""Test Plum ecoMAX diagnostics."""

from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.plum_ecomax.connection import EcomaxConnection
from custom_components.plum_ecomax.const import DOMAIN
from custom_components.plum_ecomax.diagnostics import (
    REDACTED,
    async_get_config_entry_diagnostics,
)


async def test_diagnostics(hass: HomeAssistant, config_entry: ConfigEntry, mock_device):
    """Test config entry diagnostics."""
    mock_connection = AsyncMock(spec=EcomaxConnection)
    mock_connection.device = mock_device

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = mock_connection
    result = await async_get_config_entry_diagnostics(hass, config_entry)
    assert "pyplumio" in result
    assert result["entry"] == {
        "title": "Mock Title",
        "data": {
            "connection_type": "TCP",
            "device": "/dev/ttyUSB0",
            "host": REDACTED,
            "port": 8899,
            "uid": REDACTED,
            "product_type": 0,
            "model": "EMTEST",
            "software": "1.13.5.A1",
            "capabilities": ["fuel_burned", "heating_temp", "mixers"],
        },
    }
    assert result["data"] == {
        "test_data": "test_value",
        "product": mock_connection.device.data["product"],
        "password": REDACTED,
        "mixers": [{"test_mixer_data": "test_mixer_value"}],
    }
    assert mock_connection.device.data["product"].uid == REDACTED
