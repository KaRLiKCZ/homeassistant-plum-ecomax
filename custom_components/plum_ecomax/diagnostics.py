"""Diagnostics support for Plum ecoMAX."""
from __future__ import annotations

from typing import Any, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pyplumio import __version__ as pyplumio_version
from pyplumio.devices import Device
from pyplumio.helpers.event_manager import EventManager

from .const import ATTR_PASSWORD, ATTR_PRODUCT, CONF_HOST, CONF_UID, DOMAIN

REDACTED: Final = "**REDACTED**"


def _value_as_dict(value):
    """Return value as a dictionary."""
    if isinstance(value, EventManager):
        return dict(value.data)

    return value


def _data_as_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Return data as dictionary."""
    for key, value in data.items():
        data[key] = (
            _data_as_dict(dict(value))
            if isinstance(value, dict)
            else _value_as_dict(value)
        )

    return data


def _redact_device_data(data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive information in device data."""
    if ATTR_PRODUCT in data:
        data[ATTR_PRODUCT].uid = REDACTED

    if ATTR_PASSWORD in data:
        data[ATTR_PASSWORD] = REDACTED

    return data


def _redact_entry_data(entry_data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive information in config entry data."""
    for field in (CONF_UID, CONF_HOST):
        if field in entry_data:
            entry_data[field] = REDACTED

    return entry_data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    device: Device = hass.data[DOMAIN][entry.entry_id].device
    return {
        "entry": {
            "title": entry.title,
            "data": _redact_entry_data(dict(entry.data)),
        },
        "pyplumio": {
            "version": pyplumio_version,
        },
        "data": _redact_device_data(_data_as_dict(dict(device.data))),
    }
