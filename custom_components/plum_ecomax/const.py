"""Constants for the Plum ecoMAX integration."""

from typing import Final

DOMAIN = "plum_ecomax"
MANUFACTURER: Final = "Plum Sp. z o.o."

# Generic attributes.
ATTR_ALERTS: Final = "alerts"
ATTR_ECOMAX_CONTROL: Final = "ecomax_control"
ATTR_ECOMAX_PARAMETERS: Final = "ecomax_parameters"
ATTR_END: Final = "end"
ATTR_FROM: Final = "from"
ATTR_LOADED: Final = "loaded"
ATTR_MIXERS: Final = "mixers"
ATTR_MIXER_PARAMETERS: Final = "mixer_parameters"
ATTR_MODULES: Final = "modules"
ATTR_PASSWORD: Final = "password"
ATTR_PRODUCT: Final = "product"
ATTR_SCHEDULES: Final = "schedules"
ATTR_SENSORS: Final = "sensors"
ATTR_START: Final = "start"
ATTR_THERMOSTATS: Final = "thermostats"
ATTR_THERMOSTAT_PARAMETERS: Final = "thermostat_parameters"
ATTR_TO: Final = "to"
ATTR_VALUE: Final = "value"
ATTR_WATER_HEATER: Final = "water_heater"
ATTR_WATER_HEATER_TEMP: Final = "water_heater_temp"
ATTR_WEEKDAY: Final = "weekday"
ATTR_FIRMWARE: Final = "firmware"

# Devices.
ECOMAX: Final = "ecomax"
ECOLAMBDA: Final = "ecolambda"
ECOSTER: Final = "ecoster"

# Modules.
MODULE_A: Final = "module_a"
MODULE_B: Final = "module_b"
MODULE_C: Final = "module_c"

# Weekdays.
WEEKDAYS: Final[tuple[str, ...]] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

# Configuration flow.
CONF_CAPABILITIES: Final = "capabilities"
CONF_CONNECTION_TYPE: Final = "connection_type"
CONF_DEVICE: Final = "device"
CONF_HOST: Final = "host"
CONF_MODEL: Final = "model"
CONF_PORT: Final = "port"
CONF_PRODUCT_TYPE: Final = "product_type"
CONF_PRODUCT_ID: Final = "product_id"
CONF_SOFTWARE: Final = "software"
CONF_SUB_DEVICES: Final = "sub_devices"
CONF_TITLE: Final = "title"
CONF_UID: Final = "uid"

# Connection types.
CONNECTION_TYPE_TCP: Final = "TCP"
CONNECTION_TYPE_SERIAL: Final = "Serial"
CONNECTION_TYPES: Final = (CONNECTION_TYPE_TCP, CONNECTION_TYPE_SERIAL)

# Defaults.
DEFAULT_CONNECTION_TYPE: Final = CONNECTION_TYPE_TCP
DEFAULT_DEVICE: Final = "/dev/ttyUSB0"
DEFAULT_PORT: Final = 8899

# Units of measurement.
CALORIFIC_KWH_KG: Final = "kWh/kg"
FLOW_KGH: Final = "kg/h"

# Events.
EVENT_PLUM_ECOMAX_ALERT: Final = "plum_ecomax_alert"
