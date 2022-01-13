"""Implement async Plum ecoMAX connection."""
import logging

from pyplumio import econet_connection
from pyplumio.devices import EcoMAX
from pyplumio.econet import EcoNET

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONNECTION_CHECK_TRIES, DEFAULT_PORT, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EcomaxConnection:
    """Repsentation of ecoMAX connection."""

    _sensors: list = []
    _check_ok = False
    _check_tries = 0
    _product = None
    _uid = None

    def __init__(self, hass: HomeAssistant, host: str, port: int = DEFAULT_PORT):
        """Construct new connection."""
        self._host = host
        self._port = port
        self._name = host
        self._hass = hass
        self.econet = econet_connection(host, port)

    async def _check_callback(self, ecomax: EcoMAX, econet: EcoNET):
        """Called when connection check succeeds."""
        if self._check_tries > CONNECTION_CHECK_TRIES:
            _LOGGER.exception("Connection succeeded, but device failed to respond.")
            econet.close()

        if ecomax.uid is not None and ecomax.product is not None:
            self._uid = ecomax.uid
            self._product = ecomax.product
            self._check_ok = True
            econet.close()

        self._check_tries += 1

    async def check(self):
        """Perform connection check."""
        await self.econet.task(self._check_callback, 1)
        return self._check_ok

    async def async_setup(self):
        """Setup connection and add hass stop handler."""
        self._task = self._hass.loop.create_task(
            self.econet.task(self.update_sensors, UPDATE_INTERVAL)
        )
        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.close)

    async def async_unload(self):
        """Close connection on entry unload."""
        await self._hass.async_add_executor_job(self.close)

    async def add_entities(self, sensors, add_entities_callback: AddEntitiesCallback):
        """Add sensor entities to the processing queue."""
        for sensor in sensors:
            sensor.set_connection(self)
            self._sensors.append(sensor)

        add_entities_callback(sensors, True)

    async def update_sensors(self, ecomax: EcoMAX, econet: EcoNET):
        """Call update method for sensor instance."""
        self._product = ecomax.product
        self._uid = ecomax.uid
        if ecomax.has_data():
            for sensor in self._sensors:
                await sensor.update_sensor(ecomax)

    @property
    def product(self):
        """Return currently connected product type."""
        return self._product

    @property
    def uid(self):
        """Return currently connected product uid."""
        return self._uid

    @property
    def name(self):
        """Return connection name."""
        return self._name

    @property
    def host(self):
        """Return connection host."""
        return self._host

    @property
    def port(self):
        """Return connection port."""
        return self._port

    def close(self, event):
        """Close connection and cancel connection coroutine."""
        self.econet.close()
        if self._task:
            self._task.cancel()
