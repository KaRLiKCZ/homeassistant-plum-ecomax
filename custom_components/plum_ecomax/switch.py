"""Platform for switch integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN


@dataclass
class EcomaxSwitchEntityDescription(SwitchEntityDescription):
    """Describes ecoMAX switch entity."""

    state_off: int = 0
    state_on: int = 1


SWITCH_TYPES: tuple[EcomaxSwitchEntityDescription, ...] = (
    EcomaxSwitchEntityDescription(
        key="boiler_control",
        name="Regulator Switch",
    ),
    EcomaxSwitchEntityDescription(
        key="heating_weather_control",
        name="Weather Control Switch",
    ),
    EcomaxSwitchEntityDescription(
        key="water_heater_disinfection",
        name="Water Heater Disinfection Switch",
    ),
    EcomaxSwitchEntityDescription(
        key="water_heater_work_mode",
        name="Water Heater Pump Switch",
        state_on=2,
    ),
    EcomaxSwitchEntityDescription(
        key="summer_mode",
        name="Summer Mode Switch",
    ),
    EcomaxSwitchEntityDescription(
        key="fuzzy_logic",
        name="Fuzzy Logic Switch",
    ),
)


class EcomaxSwitch(SwitchEntity):
    """Representation of ecoMAX switch."""

    def __init__(self, connection, description: EcomaxSwitchEntityDescription):
        self._connection = connection
        self.entity_description = description
        self._attr_name = f"{connection.name} {description.name}"
        self._attr_unique_id = f"{connection.uid}-{description.key}"
        self._attr_should_poll = False
        self._attr_is_on = None

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        setattr(
            self._connection.ecomax,
            self.entity_description.key,
            self.entity_description.state_on,
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        setattr(
            self._connection.ecomax,
            self.entity_description.key,
            self.entity_description.state_off,
        )
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Retrieve latest state."""
        states = {
            self.entity_description.state_on: True,
            self.entity_description.state_off: False,
        }

        state = getattr(self._connection.ecomax, self.entity_description.key, None)
        self._attr_is_on = (
            states[state.value] if state is not None and state.value in states else None
        )
        self.async_write_ha_state()

    @property
    def device_info(self) -> Optional[dict]:
        """Return device info."""
        return self._connection.device_info

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Indicate if the entity should be enabled when first added."""
        return self.entity_description.key in self._connection.capabilities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform.

    Keyword arguments:
        hass -- instance of Home Assistant core
        config_entry -- instance of config entry
        async_add_entities -- callback to add entities to hass
    """
    connection = hass.data[DOMAIN][config_entry.entry_id]
    connection.add_entities(
        [EcomaxSwitch(connection, description) for description in SWITCH_TYPES],
        async_add_entities,
    )
