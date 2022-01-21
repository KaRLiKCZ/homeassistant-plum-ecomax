# hassio-plum-ecomax - ecoMAX pellet boiler regulator integration for Home Assistant.
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview
This Home Assistant integration provides support for ecoMAX automatic pellet boilers controllers manufactured by [Plum Sp. z o.o.](https://www.plum.pl/)

It is based on [PyPlumIO](https://github.com/denpamusic/PyPlumIO) package and currently only supports connection to ecoMAX controller via serial network server, for example [Elfin EW11](https://aliexpress.ru/item/4001104348624.html).

Support for USB to RS485 converters is also planned and will be implemented in future.

This project is currently in __Pre-Alpha__ stage, so use it with caution.

## Entities
This integration provides following entities.
### 🌡 Sensors
- CO Temperature
- CWU Temperature
- Exhaust Temperature
- Outside Temperature
- CO Target Temperature
- CWU Target Temperature
- Feeder Temperature
- Boiler Load
- Fan Power
- Fuel Level
- Fuel Consumption
- Boiler Mode
- Boiler Power

### 💡 Binary Sensors
- CO Pump State
- CWU Pump State
- Fan State
- Lighter State

### 🔲 Switches
- Regulator Master Switch
- Weather Control Switch
- Water Heater Disinfection Switch
- Water Heater Pump Switch
- Summer Mode Switch
- Fuzzy Logic Switch

### 🎚 Numbers (Changeable sliders)
- Boiler Temperature
- Grate Mode Temperature

### 🚿 Water Heater
Integration provides full control for connected passive water heater. This includes ability to set target temperature, switch into priority, non-priority mode or turn off.

## Installation
Currently only manual installation method is available:

1. Clone this repository with:
```sh
git clone https://github.com/denpamusic/hassio-plum-ecomax
```

2. Move `custom_components` directory from `hassio-plum-ecomax` to your Home Assistant configuration directory. ([next to configuration.yaml](https://www.home-assistant.io/docs/configuration/))

```sh
cp -r ./hassio-plum-ecomax/custom_components ~/.homeassistant
```

3. Restart Home Assistant
4. Click `Add Integration` button and search for `Plum ecoMAX` in integration menu.
5. Enter your connection details and click `Submit`.  
![Configuration dialog](https://raw.githubusercontent.com/denpamusic/hassio-plum-ecomax/dce2aa3de3dc4fd85f5a5464aa7ae9ced143094f/images/config.png)

6. Your device should now be available in your Home Assistant installation.
![Success](https://raw.githubusercontent.com/denpamusic/hassio-plum-ecomax/main/images/success.png)

## License
This product is distributed under MIT license.
