"""Test the select platform."""

from unittest.mock import patch

from homeassistant.components.select.const import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pyplumio.structures.ecomax_parameters import (
    EcomaxParameter,
    EcomaxParameterDescription,
)
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plum_ecomax.connection import EcomaxConnection
from custom_components.plum_ecomax.select import STATE_AUTO


@pytest.fixture(autouse=True)
def bypass_connection_setup():
    """Mock async get current platform."""
    with patch("custom_components.plum_ecomax.connection.EcomaxConnection.async_setup"):
        yield


@pytest.fixture(autouse=True)
def bypass_async_migrate_entry():
    """Bypass async migrate entry."""
    with patch("custom_components.plum_ecomax.async_migrate_entry", return_value=True):
        yield


@pytest.fixture(autouse=True)
def set_connected(connected):
    """Assume connected."""


@pytest.fixture(name="async_select_option")
async def fixture_async_select_option():
    """Selects the option."""

    async def async_select_option(hass: HomeAssistant, entity_id: str, option: str):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
            blocking=True,
        )
        return hass.states.get(entity_id)

    return async_select_option


@pytest.mark.usefixtures("ecomax_p")
async def test_summer_mode_select(
    hass: HomeAssistant,
    connection: EcomaxConnection,
    config_entry: MockConfigEntry,
    setup_integration,
    async_select_option,
) -> None:
    """Test summer mode select."""
    await setup_integration(hass, config_entry)
    summer_mode_entity_id = "select.ecomax_summer_mode"
    summer_mode_select_key = "summer_mode"

    # Test entry.
    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get(summer_mode_entity_id)
    assert entry
    assert entry.translation_key == "summer_mode"

    # Get initial value.
    state = hass.states.get(summer_mode_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_FRIENDLY_NAME] == "ecoMAX Summer mode"
    assert state.attributes[ATTR_ICON] == "mdi:weather-sunny"
    assert state.attributes[ATTR_OPTIONS] == [STATE_OFF, STATE_AUTO, STATE_ON]
    options = state.attributes[ATTR_OPTIONS]

    # Dispatch new value.
    await connection.device.dispatch(
        summer_mode_select_key,
        EcomaxParameter(
            device=connection.device,
            value=1,
            min_value=0,
            max_value=2,
            description=EcomaxParameterDescription(summer_mode_select_key),
        ),
    )
    state = hass.states.get(summer_mode_entity_id)
    assert state.state == STATE_AUTO

    # Select an option.
    with patch("pyplumio.devices.Device.set_nowait") as mock_set_nowait:
        state = await async_select_option(hass, summer_mode_entity_id, STATE_ON)

    mock_set_nowait.assert_called_once_with(
        summer_mode_select_key, options.index(STATE_ON)
    )
    assert state.state == STATE_ON
