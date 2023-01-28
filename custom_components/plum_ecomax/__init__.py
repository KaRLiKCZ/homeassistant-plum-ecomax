"""The Plum ecoMAX integration."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry
from pyplumio.helpers.filters import delta
from pyplumio.structures.alerts import Alert

from .connection import (
    DEVICE_TIMEOUT,
    VALUE_TIMEOUT,
    EcomaxConnection,
    async_get_connection_handler,
    async_get_sub_devices,
)
from .const import (
    ATTR_CODE,
    ATTR_DEVICE_ID,
    ATTR_FROM,
    ATTR_PRODUCT,
    ATTR_TO,
    CONF_CAPABILITIES,
    CONF_MODEL,
    CONF_PRODUCT_TYPE,
    CONF_SUB_DEVICES,
    DOMAIN,
    ECOMAX,
    EVENT_PLUM_ECOMAX_ALERT,
)
from .services import async_setup_services

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.WATER_HEATER,
]

DATE_STR_FORMAT: Final = "%Y-%m-%d %H:%M:%S"

ATTR_ALERTS: Final = "alerts"

_LOGGER = logging.getLogger(__name__)


def format_model_name(model_name: str) -> str:
    """Format the device model."""
    if m := re.match(r"^([A-Z]+)\s{0,}([0-9]{3,})(.+)$", model_name, re.IGNORECASE):
        model_device, model_number, model_suffix = m.groups()
        model_device = "ecoMAX" if model_device == "EM" else model_device
        return f"{model_device} {model_number}{model_suffix}"

    return model_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Plum ecoMAX from a config entry."""
    connection = EcomaxConnection(
        hass, entry, await async_get_connection_handler(hass, entry.data)
    )

    async def async_close_connection(event=None):
        """Close ecoMAX connection on HA Stop."""
        await connection.close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_close_connection)
    )

    try:
        await connection.async_setup()
    except asyncio.TimeoutError as e:
        raise ConfigEntryNotReady("Device not found") from e

    await async_setup_services(hass, connection)
    await async_setup_events(hass, connection)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = connection
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_setup_events(hass: HomeAssistant, connection: EcomaxConnection) -> None:
    """Setup ecoMAX events."""

    dr = device_registry.async_get(hass)

    async def _displatch_alert_events(alerts: list[Alert]) -> None:
        """Handle ecoMAX alert events."""
        try:
            product_info = await connection.device.get_value(
                ATTR_PRODUCT, timeout=VALUE_TIMEOUT
            )
        except asyncio.TimeoutError:
            _LOGGER.error("Event dispatch failed. Couldn't get the device UID in time")
            return

        device = dr.async_get_device({(DOMAIN, product_info.uid)})
        for alert in alerts:
            event_data = {
                ATTR_DEVICE_ID: device.id,
                ATTR_CODE: alert.code,
                ATTR_FROM: alert.from_dt.strftime(DATE_STR_FORMAT),
            }
            if alert.to_dt is not None:
                event_data[ATTR_TO] = alert.to_dt.strftime(DATE_STR_FORMAT)

            hass.bus.async_fire(EVENT_PLUM_ECOMAX_ALERT, event_data)

    connection.device.subscribe(ATTR_ALERTS, delta(_displatch_alert_events))


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        try:
            connection: EcomaxConnection = hass.data[DOMAIN][entry.entry_id]
            await connection.close()
            hass.data[DOMAIN].pop(entry.entry_id)
        except KeyError:
            pass

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    try:
        if config_entry.version in (1, 2):
            data = {**config_entry.data}
            connection = EcomaxConnection(
                hass,
                config_entry,
                await async_get_connection_handler(hass, config_entry.data),
            )
            await connection.connect()
            device = await connection.get_device(ECOMAX, timeout=DEVICE_TIMEOUT)
            product = await device.get_value(ATTR_PRODUCT, timeout=VALUE_TIMEOUT)
            data[CONF_PRODUCT_TYPE] = product.type
            await connection.close()
            config_entry.version = 3
            hass.config_entries.async_update_entry(config_entry, data=data)

        if config_entry.version == 3:
            data = {**config_entry.data}
            data[CONF_MODEL] = format_model_name(data[CONF_MODEL])
            config_entry.version = 4
            hass.config_entries.async_update_entry(config_entry, data=data)

        if config_entry.version == 4:
            data = {**config_entry.data}
            try:
                del data[CONF_CAPABILITIES]
            except KeyError:
                pass

            connection = EcomaxConnection(
                hass,
                config_entry,
                await async_get_connection_handler(hass, config_entry.data),
            )
            await connection.connect()
            device = await connection.get_device(ECOMAX, timeout=DEVICE_TIMEOUT)
            data[CONF_SUB_DEVICES] = await async_get_sub_devices(device)
            await connection.close()
            config_entry.version = 5
            hass.config_entries.async_update_entry(config_entry, data=data)

        _LOGGER.info("Migration to version %s successful", config_entry.version)
    except asyncio.TimeoutError:
        _LOGGER.error("Migration failed, device has failed to respond in time")
        return False

    return True
