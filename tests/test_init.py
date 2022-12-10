"""Test Plum ecoMAX setup process."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util import dt as dt_util
from pyplumio.structures.alerts import Alert
import pytest

from custom_components.plum_ecomax import (
    DATE_STR_FORMAT,
    async_migrate_entry,
    async_setup_entry,
    async_setup_events,
    async_unload_entry,
    format_model_name,
)
from custom_components.plum_ecomax.connection import VALUE_TIMEOUT, EcomaxConnection
from custom_components.plum_ecomax.const import (
    ATTR_CODE,
    ATTR_DEVICE_ID,
    ATTR_FROM,
    ATTR_PRODUCT,
    ATTR_TO,
    CONF_CAPABILITIES,
    CONF_PRODUCT_TYPE,
    DOMAIN,
    EVENT_PLUM_ECOMAX_ALERT,
)


@patch(
    "custom_components.plum_ecomax.EcomaxConnection.async_setup",
    side_effect=(None, asyncio.TimeoutError),
)
@patch("custom_components.plum_ecomax.async_setup_services")
@patch.object(EcomaxConnection, "close", create=True, new_callable=AsyncMock)
async def test_setup_and_unload_entry(
    mock_close,
    async_setup_services,
    mock_async_setup,
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    mock_device,
) -> None:
    """Test setup and unload of config entry."""
    assert await async_setup_entry(hass, config_entry)
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(hass.data[DOMAIN][config_entry.entry_id], EcomaxConnection)

    # Test with exception.
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, config_entry)

    # Send HA stop event and check that connection was closed.
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    assert mock_close.call_count == 2
    mock_close.reset_mock()

    # Unload entry and verify that it is no longer present in hass data.
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.state is ConfigEntryState.NOT_LOADED
    mock_close.assert_awaited_once()
    mock_close.reset_mock()

    # Test when already unloaded.
    assert await async_unload_entry(hass, config_entry)
    mock_close.assert_not_awaited()


@patch(
    "custom_components.plum_ecomax.EcomaxConnection.async_setup",
    side_effect=(None, asyncio.TimeoutError),
)
@patch("custom_components.plum_ecomax.async_setup_services")
async def test_setup_mixers(
    async_setup_services,
    mock_async_setup,
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    mock_device,
    caplog,
) -> None:
    """Test setup mixers."""
    mock_device.get_value.side_effect = asyncio.TimeoutError
    assert await async_setup_entry(hass, config_entry)
    assert "Couldn't find any mixers" in caplog.text


@patch("pyplumio.helpers.filters._Delta")
@patch("homeassistant.core.EventBus.async_fire")
async def test_setup_events(
    mock_async_fire,
    mock_delta,
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    mock_device,
    caplog,
) -> None:
    """Test setup events."""
    connection = hass.data[DOMAIN][config_entry.entry_id]
    await async_setup_events(hass, connection)
    mock_device.subscribe.assert_called_once_with("alerts", mock_delta.return_value)
    args, _ = mock_delta.call_args

    # Test calling the callback with an alert.
    callback = args[0]
    utcnow = dt_util.utcnow()
    alert = Alert(code=0, from_dt=utcnow, to_dt=utcnow)
    mock_device_entry = Mock()
    with patch(
        "homeassistant.helpers.device_registry.DeviceRegistry.async_get_device",
        return_value=mock_device_entry,
    ):
        await callback([alert])
        mock_device.get_value.assert_called_once_with(
            ATTR_PRODUCT, timeout=VALUE_TIMEOUT
        )
        mock_async_fire.assert_called_once_with(
            EVENT_PLUM_ECOMAX_ALERT,
            {
                ATTR_DEVICE_ID: mock_device_entry.id,
                ATTR_CODE: 0,
                ATTR_FROM: utcnow.strftime(DATE_STR_FORMAT),
                ATTR_TO: utcnow.strftime(DATE_STR_FORMAT),
            },
        )

    # Test with timeout error while getting product info.
    mock_device.get_value = AsyncMock(side_effect=asyncio.TimeoutError)
    await callback([alert])
    await async_setup_events(hass, connection)
    assert "Event dispatch failed" in caplog.text


@patch.object(EcomaxConnection, "get_device", create=True, new_callable=AsyncMock)
@patch.object(
    EcomaxConnection,
    "connect",
    create=True,
    new_callable=AsyncMock,
    side_effect=(asyncio.TimeoutError, None),
)
@patch.object(EcomaxConnection, "close", create=True, new_callable=AsyncMock)
async def test_migrate_entry_from_v1v2_to_v3(
    mock_close,
    mock_connect,
    mock_get_device,
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Test migrating entry from version 1 or 2 to version 3."""
    config_entry.version = 2
    mock_product = Mock()
    mock_product.type = 0
    mock_get_device.return_value.get_value.return_value = mock_product

    with patch(
        "custom_components.plum_ecomax.async_get_device_capabilities",
        new_callable=AsyncMock,
        return_value="test",
    ) as mock_async_get_device_capabilities:
        assert not await async_migrate_entry(hass, config_entry)
        config_entry.version = 2
        assert await async_migrate_entry(hass, config_entry)

    assert mock_connect.call_count == 2
    mock_async_get_device_capabilities.assert_awaited_once_with(
        mock_get_device.return_value
    )
    mock_close.assert_awaited_once()
    data = {**config_entry.data}
    data[CONF_CAPABILITIES] = "test"
    data[CONF_PRODUCT_TYPE] = 0
    assert config_entry.version == 3


async def test_migrate_entry_from_v3_to_v4(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Test migrating entry from version 3 to version 4."""
    config_entry.version = 3
    data = {**config_entry.data}
    data["model"] = "EM123A"
    hass.config_entries.async_update_entry(config_entry, data=data)
    assert await async_migrate_entry(hass, config_entry)
    data = {**config_entry.data}
    assert data["model"] == "ecoMAX 123A"
    assert config_entry.version == 4


async def test_format_model_name() -> None:
    """Test model name formatter."""
    model_names = (
        ("EM350P2-ZF", "ecoMAX 350P2-ZF"),
        ("ecoMAXX800R3", "ecoMAXX 800R3"),
        ("ecoMAX 850i", "ecoMAX 850i"),
        ("ignore", "ignore"),
    )

    for raw, formatted in model_names:
        assert format_model_name(raw) == formatted
