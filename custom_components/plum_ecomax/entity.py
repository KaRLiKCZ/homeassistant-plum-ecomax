"""Base ecoMAX entity class."""

from abc import ABC, abstractmethod

from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from pyplumio.helpers.filters import on_change

from .connection import EcomaxConnection


class EcomaxEntity(ABC):
    """Represents base ecoMAX entity."""

    _connection: EcomaxConnection
    entity_description: EntityDescription

    async def async_added_to_hass(self):
        """Called when an entity has their entity_id assigned."""
        self.device.register_callback(
            [self.entity_description.key], on_change(self.async_update)
        )

    async def async_removed_from_hass(self):
        """Called when an entity is about to be removed."""
        self.device.remove_callback([self.entity_description.key], self.async_update)

    @property
    def device(self):
        """Return device object."""
        return self._connection.device

    @property
    def available(self) -> bool:
        """Indicates whether the entity is available."""
        return self._connection.device is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self._connection.device_info

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Indicate if the entity should be enabled when first added."""
        return self.entity_description.key in self._connection.capabilities

    @property
    def unique_id(self) -> str:
        """A unique identifier for this entity."""
        return f"{self._connection.uid}-{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Name of the entity."""
        return f"{self._connection.name} {self.entity_description.name}"

    @property
    def should_poll(self) -> bool:
        """Should hass check with the entity for an updated state."""
        return False

    @abstractmethod
    async def async_update(self, value) -> None:
        """Retrieve latest state."""
