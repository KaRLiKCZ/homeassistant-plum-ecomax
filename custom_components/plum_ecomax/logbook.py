"""Describe Plum ecoMAX logbook events."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.logbook.const import (
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
from homeassistant.core import Event, HomeAssistant, callback

from custom_components.plum_ecomax.const import (
    ATTR_CODE,
    ATTR_FROM,
    ATTR_TO,
    DOMAIN,
    ECOMAX_ALERT_EVENT,
)


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[[str, str, Callable[[Event], dict[str, str]]], None],
) -> None:
    """Describe logbook events."""

    @callback
    def async_describe_alert_event(event: Event) -> dict[str, str]:
        """Describe ecomax logbook event."""
        alert_code = event.data[ATTR_CODE]
        start_time = event.data[ATTR_FROM]
        end_time = event.data[ATTR_TO]
        time_string = f"was generated at {start_time}"
        if end_time is not None:
            time_string += f" and resolved at {end_time}"

        return {
            LOGBOOK_ENTRY_NAME: "ecoMAX",
            LOGBOOK_ENTRY_MESSAGE: f"The alert with code '{alert_code}' {time_string}",
        }

    async_describe_event(DOMAIN, ECOMAX_ALERT_EVENT, async_describe_alert_event)
