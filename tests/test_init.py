"""Test Plum ecoMAX setup process."""

import asyncio
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.plum_ecomax import (
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.plum_ecomax.connection import EcomaxConnection
from custom_components.plum_ecomax.const import CONF_CAPABILITIES, DOMAIN


@patch("custom_components.plum_ecomax.EcomaxConnection.async_setup")
@patch("custom_components.plum_ecomax.async_setup_services")
@patch.object(EcomaxConnection, "close", create=True, new_callable=AsyncMock)
async def test_setup_and_unload_entry(
    mock_close,
    async_setup_services,
    mock_async_setup,
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Test setup and unload of config entry."""
    assert await async_setup_entry(hass, config_entry)

    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(hass.data[DOMAIN][config_entry.entry_id], EcomaxConnection)
    mock_async_setup.assert_awaited_once()
    async_setup_services.assert_awaited_once()

    # Unload entry and verify that it is no longer present in hass data.
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]
    mock_close.assert_awaited_once()
    mock_close.reset_mock()

    # Test when already unloaded.
    assert await async_unload_entry(hass, config_entry)
    mock_close.assert_not_awaited()


@patch.object(EcomaxConnection, "get_device", create=True, new_callable=AsyncMock)
@patch.object(
    EcomaxConnection,
    "connect",
    create=True,
    new_callable=AsyncMock,
    side_effect=(asyncio.TimeoutError, None),
)
@patch.object(EcomaxConnection, "close", create=True, new_callable=AsyncMock)
async def test_migrate_entry(
    mock_close,
    mock_connect,
    mock_get_device,
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Test migrating entry to a new version."""
    config_entry.version = 1
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_update_entry"
    ) as mock_async_update_entry, patch(
        "custom_components.plum_ecomax.async_get_device_capabilities",
        new_callable=AsyncMock,
        return_value="test",
    ) as mock_async_get_device_capabilities:
        assert not await async_migrate_entry(hass, config_entry)
        config_entry.version = 1
        assert await async_migrate_entry(hass, config_entry)

    assert mock_connect.call_count == 2
    mock_async_get_device_capabilities.assert_awaited_once_with(
        mock_get_device.return_value
    )
    mock_close.assert_awaited_once()
    data = {**config_entry.data}
    data[CONF_CAPABILITIES] = "test"
    mock_async_update_entry.assert_called_once_with(config_entry, data=data)
    assert config_entry.version == 2
