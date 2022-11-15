"""Test Plum ecoMAX binary sensor platform."""


from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plum_ecomax.binary_sensor import (
    EcomaxBinarySensor,
    async_setup_entry,
)


async def test_async_setup_and_update_entry(
    hass: HomeAssistant,
    async_add_entities: AddEntitiesCallback,
    config_entry: MockConfigEntry,
    bypass_hass_write_ha_state,
    bypass_model_check,
) -> None:
    """Test setup and update binary sensor entry."""
    assert await async_setup_entry(hass, config_entry, async_add_entities)
    await hass.async_block_till_done()
    async_add_entities.assert_called_once()
    args, _ = async_add_entities.call_args
    binary_sensors = args[0]
    binary_sensor = binary_sensors.pop(0)

    # Check that binary sensor state is unknown and update it.
    assert isinstance(binary_sensor, EcomaxBinarySensor)
    assert binary_sensor.is_on is None
    await binary_sensor.async_update(True)
    assert binary_sensor.is_on


@patch("custom_components.plum_ecomax.sensor.async_get_current_platform")
@patch("homeassistant.helpers.entity_platform.AddEntitiesCallback")
async def test_model_check(
    mock_async_add_entities,
    mock_async_get_current_platform,
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
):
    """Test sensor model check."""
    for model_sensor in (
        ("EM860p", "lighter"),
        ("EM350P-R2", "lighter"),
        ("ecoMAX 850i", "fireplace_pump"),
    ):
        with patch(
            "custom_components.plum_ecomax.connection.EcomaxConnection.model",
            model_sensor[0],
        ):
            await async_setup_entry(hass, config_entry, mock_async_add_entities)
            args, _ = mock_async_add_entities.call_args
            sensor = args[0].pop()
            assert sensor.entity_description.key == model_sensor[1]


@patch("homeassistant.helpers.entity_platform.AddEntitiesCallback")
async def test_model_check_with_unknown_model(
    mock_async_add_entities,
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog,
):
    """Test model check with the unknown model."""
    with patch(
        "custom_components.plum_ecomax.connection.EcomaxConnection.model",
        "unknown",
    ):
        assert not await async_setup_entry(hass, config_entry, mock_async_add_entities)
        assert "Couldn't setup platform" in caplog.text
