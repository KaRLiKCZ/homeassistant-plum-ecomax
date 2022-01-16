"""Platform for binary sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from pyplumio.devices import EcoMAX

from .const import DOMAIN
from .entity import EcomaxEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    sensors = [
        EcomaxBinarySensor("co_pump", "CO Pump State"),
        EcomaxBinarySensor("cwu_pump", "CWU Pump State"),
        EcomaxBinarySensor("fan", "Fan State"),
        EcomaxBinarySensor("lighter", "Lighter State"),
    ]
    connection = hass.data[DOMAIN][config_entry.entry_id]
    await connection.add_entities(sensors, async_add_entities)


class EcomaxBinarySensor(EcomaxEntity, BinarySensorEntity):
    """Binary sensor representation."""

    async def update_entity(self, ecomax: EcoMAX):
        """Update sensor state. Called by connection instance."""
        await super().update_entity(ecomax)
        state = self.get_attribute(self._id)
        if state is not None:
            state = STATE_ON if state else STATE_OFF
            if self._state != state:
                self._state = state
                self.async_write_ha_state()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
