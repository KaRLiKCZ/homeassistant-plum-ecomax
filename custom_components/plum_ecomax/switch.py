"""Platform for switch integration."""
from __future__ import annotations

from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
import logging
from typing import Any, Literal

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from pyplumio.const import ProductType
from pyplumio.filters import on_change
from pyplumio.helpers.parameter import Parameter
from pyplumio.helpers.typing import ParameterValueType

from .connection import EcomaxConnection
from .const import ALL, DOMAIN, MODULE_A
from .entity import EcomaxEntity, MixerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, slots=True)
class EcomaxSwitchEntityDescription(SwitchEntityDescription):
    """Describes ecoMAX switch entity."""

    product_types: set[ProductType]
    filter_fn: Callable[[Any], Any] = on_change
    module: str = MODULE_A
    state_off: ParameterValueType = STATE_OFF
    state_on: ParameterValueType = STATE_ON


SWITCH_TYPES: tuple[EcomaxSwitchEntityDescription, ...] = (
    EcomaxSwitchEntityDescription(
        key="ecomax_control",
        translation_key="controller_switch",
        product_types={ProductType.ECOMAX_P, ProductType.ECOMAX_I},
    ),
    EcomaxSwitchEntityDescription(
        key="water_heater_disinfection",
        translation_key="water_heater_disinfection_switch",
        product_types={ProductType.ECOMAX_P, ProductType.ECOMAX_I},
    ),
    EcomaxSwitchEntityDescription(
        key="water_heater_work_mode",
        translation_key="water_heater_pump_switch",
        product_types={ProductType.ECOMAX_P, ProductType.ECOMAX_I},
        state_off=0,
        state_on=2,
    ),
    EcomaxSwitchEntityDescription(
        key="heating_weather_control",
        translation_key="weather_control_switch",
        product_types={ProductType.ECOMAX_P},
    ),
    EcomaxSwitchEntityDescription(
        key="fuzzy_logic",
        translation_key="fuzzy_logic_switch",
        product_types={ProductType.ECOMAX_P},
    ),
    EcomaxSwitchEntityDescription(
        key="heating_schedule_switch",
        translation_key="heating_schedule_switch",
        product_types={ProductType.ECOMAX_P},
    ),
    EcomaxSwitchEntityDescription(
        key="water_heater_schedule_switch",
        translation_key="water_heater_schedule_switch",
        product_types={ProductType.ECOMAX_P},
    ),
)


class EcomaxSwitch(EcomaxEntity, SwitchEntity):
    """Represents ecoMAX switch platform."""

    _attr_is_on: bool | None
    _connection: EcomaxConnection
    entity_description: EntityDescription

    def __init__(
        self, connection: EcomaxConnection, description: EcomaxSwitchEntityDescription
    ):
        """Initialize ecoMAX switch object."""
        self._attr_available = False
        self._attr_is_on = None
        self._connection = connection
        self.entity_description = description

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self.device.set_nowait(
            self.entity_description.key, self.entity_description.state_on
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        self.device.set_nowait(
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


@dataclass(slots=True)
class MixerSwitchEntityDescription(EcomaxSwitchEntityDescription):
    """Describes ecoMAX mixer switch entity."""

    indexes: set[int] | Literal["all"] = ALL


MIXER_SWITCH_TYPES: tuple[MixerSwitchEntityDescription, ...] = (
    MixerSwitchEntityDescription(
        key="summer_work",
        translation_key="enable_in_summer_mode",
        product_types={ProductType.ECOMAX_P, ProductType.ECOMAX_I},
    ),
    MixerSwitchEntityDescription(
        key="weather_control",
        translation_key="weather_control_switch",
        product_types={ProductType.ECOMAX_P},
    ),
    MixerSwitchEntityDescription(
        key="off_therm_pump",
        translation_key="disable_pump_on_thermostat",
        product_types={ProductType.ECOMAX_P},
    ),
    MixerSwitchEntityDescription(
        key="support",
        translation_key="enable_circuit",
        product_types={ProductType.ECOMAX_I},
        state_off=0,
        state_on=1,
        indexes={1},
    ),
)


class MixerSwitch(MixerEntity, EcomaxSwitch):
    """Represents mixer switch platform."""

    def __init__(
        self,
        connection: EcomaxConnection,
        description: EcomaxSwitchEntityDescription,
        index: int,
    ):
        """Initialize mixer switch object."""
        self.index = index
        super().__init__(connection, description)


def get_by_product_type(
    product_type: ProductType,
    descriptions: Iterable[EcomaxSwitchEntityDescription],
) -> Generator[EcomaxSwitchEntityDescription, None, None]:
    """Filter descriptions by product type."""
    for description in descriptions:
        if product_type in description.product_types:
            yield description


def get_by_modules(
    connected_modules, descriptions: Iterable[EcomaxSwitchEntityDescription]
) -> Generator[EcomaxSwitchEntityDescription, None, None]:
    """Filter descriptions by modules."""
    for description in descriptions:
        if getattr(connected_modules, description.module, None) is not None:
            yield description


def get_by_index(
    index, descriptions: Iterable[MixerSwitchEntityDescription]
) -> Generator[EcomaxSwitchEntityDescription, None, None]:
    """Filter mixer/circuit descriptions by indexes."""
    index += 1
    for description in descriptions:
        if description.indexes == ALL or index in description.indexes:
            yield description


def async_setup_ecomax_switch(connection: EcomaxConnection) -> list[EcomaxSwitch]:
    """Setup ecoMAX switches."""
    return [
        EcomaxSwitch(connection, description)
        for description in get_by_modules(
            connection.device.modules,
            get_by_product_type(connection.product_type, SWITCH_TYPES),
        )
    ]


def async_setup_mixer_switch(connection: EcomaxConnection) -> list[MixerSwitch]:
    """Setup mixers switches."""
    entities: list[MixerSwitch] = []

    for index in connection.device.mixers.keys():
        entities.extend(
            MixerSwitch(connection, description, index)
            for description in get_by_index(
                index,
                get_by_modules(
                    connection.device.modules,
                    get_by_product_type(connection.product_type, MIXER_SWITCH_TYPES),
                ),
            )
        )

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up the sensor platform."""
    connection: EcomaxConnection = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug("Starting setup of switch platform...")

    entities: list[EcomaxSwitch] = []

    # Add ecoMAX switches.
    entities.extend(async_setup_ecomax_switch(connection))

    # Add mixer/circuit switches.
    if connection.has_mixers and await connection.async_setup_mixers():
        entities.extend(async_setup_mixer_switch(connection))

    return async_add_entities(entities)
