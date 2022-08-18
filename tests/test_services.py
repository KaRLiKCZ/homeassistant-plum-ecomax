"""Test Plum ecoMAX services."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from pyplumio.helpers.schedule import Schedule, ScheduleDay
import pytest

from custom_components.plum_ecomax.connection import EcomaxConnection
from custom_components.plum_ecomax.const import ATTR_VALUE
from custom_components.plum_ecomax.services import (
    ATTR_END,
    ATTR_NAME,
    ATTR_START,
    ATTR_STATE,
    ATTR_WEEKDAY,
    SERVICE_SET_PARAMETER,
    SERVICE_SET_PARAMETER_SCHEMA,
    SERVICE_SET_SCHEDULE,
    SERVICE_UPDATE_CAPABILITIES,
    STATE_ON,
    async_setup_services,
)


async def test_setup_services(hass: HomeAssistant, caplog) -> None:
    """Test services setup."""
    mock_connection = AsyncMock(spec=EcomaxConnection)
    mock_service_call = AsyncMock(spec=ServiceCall)

    with patch(
        "homeassistant.core.ServiceRegistry.async_register"
    ) as mock_async_register:
        await async_setup_services(hass, mock_connection)

    assert mock_async_register.call_count == 3
    (
        set_parameter_service,
        set_schedule_service,
        update_capabilities_service,
    ) = mock_async_register.call_args_list

    # Test set parameter service.
    args, _ = set_parameter_service
    _, service, func, schema = args
    assert service == SERVICE_SET_PARAMETER
    assert schema == SERVICE_SET_PARAMETER_SCHEMA

    mock_service_call.data = {ATTR_NAME: "test_name", ATTR_VALUE: 39}
    mock_connection.capabilities = ["test_name"]
    with patch("asyncio.wait_for"):
        await func(mock_service_call)

    mock_connection.device.set_value.assert_called_once_with("test_name", 39)

    # Check that error is raised if device timed-out.
    with pytest.raises(HomeAssistantError), patch(
        "asyncio.wait_for", side_effect=asyncio.TimeoutError
    ):
        await func(mock_service_call)

    assert "Service timed out while waiting" in caplog.text

    # Check that error is raised if parameter is not in capability list.
    mock_connection.capabilities = []
    with pytest.raises(HomeAssistantError), patch("asyncio.wait_for"):
        await func(mock_service_call)

    # Test set schedule service.
    args, _ = set_schedule_service
    _, service, func, schema = args
    assert service == SERVICE_SET_SCHEDULE
    mock_service_call.data = {
        ATTR_NAME: "test_name",
        ATTR_WEEKDAY: "Monday",
        ATTR_STATE: True,
        ATTR_START: "00:00:00",
        ATTR_END: "10:00:00",
    }

    mock_schedule = Mock(spec=Schedule)
    mock_schedule.monday = Mock(spec=ScheduleDay)
    mock_schedule.monday.set_state.side_effect = (True, ValueError)
    mock_connection.device.data = {"schedules": {"test_name": mock_schedule}}
    await func(mock_service_call)
    mock_schedule.monday.set_state.assert_called_once_with(STATE_ON, "00:00", "10:00")
    with pytest.raises(HomeAssistantError):
        await func(mock_service_call)

    mock_connection.device.data = {}
    with pytest.raises(HomeAssistantError):
        await func(mock_service_call)

    # Test update capability service.
    args, _ = update_capabilities_service
    _, service, func = args
    assert service == SERVICE_UPDATE_CAPABILITIES
    mock_service_call.data = {ATTR_NAME: "test_name", ATTR_VALUE: 39}
    await func(mock_service_call)
    mock_connection.async_update_device_capabilities.assert_awaited_once()
