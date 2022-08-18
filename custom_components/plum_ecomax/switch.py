"""Platform for switch integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from pyplumio.helpers.filters import on_change
from pyplumio.helpers.parameter import Parameter

from .connection import EcomaxConnection
from .const import DOMAIN
from .entity import EcomaxEntity


@dataclass
class EcomaxSwitchEntityDescription(SwitchEntityDescription):
    """Describes ecoMAX switch entity."""

    state_off: int = 0
    state_on: int = 1
    filter_fn: Callable[[Any], Any] = on_change


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
    EcomaxSwitchEntityDescription(
        key="schedule_heating_switch",
        name="Heating Schedule Switch",
    ),
    EcomaxSwitchEntityDescription(
        key="schedule_water_heater_switch",
        name="Water Heater Schedule Switch",
    ),
)


class EcomaxSwitch(EcomaxEntity, SwitchEntity):
    """Represents ecoMAX switch platform."""

    _connection: EcomaxConnection
    entity_description: EntityDescription
    _attr_is_on: bool | None

    def __init__(
        self, connection: EcomaxConnection, description: EcomaxSwitchEntityDescription
    ):
        """Initialize ecoMAX switch object."""
        self._connection = connection
        self.entity_description = description
        self._attr_is_on = None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self.device.set_value(
            self.entity_description.key, self.entity_description.state_on
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self.device.set_value(
            self.entity_description.key, self.entity_description.state_off
        )
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self, value: Parameter) -> None:
        """Update entity state."""
        states = {
            self.entity_description.state_on: True,
            self.entity_description.state_off: False,
        }
        self._attr_is_on = states[value.value] if value.value in states else None
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up the sensor platform."""
    connection = hass.data[DOMAIN][config_entry.entry_id]
    return async_add_entities(
        [EcomaxSwitch(connection, description) for description in SWITCH_TYPES], False
    )
