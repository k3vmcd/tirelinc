[![GitHub Release](https://img.shields.io/github/release/k3vmcd/ha-tirelinc.svg?style=flat-square)](https://github.com/k3vmcd/ha-tirelinc/releases)
[![License](https://img.shields.io/github/license/k3vmcd/ha-tirelinc.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-default-orange.svg?style=flat-square)](https://hacs.xyz)


# Home Assistant TireLinc Integration
Integrates TireLinc TPMS (https://www.lippert.com/rv-camping/collections/tire-linc) to Home Assistant using active connection to get information from the sensors.

Current Limitations:
 - You MUST successfully pair the tires to the central TireLinc repeater using the manufacturer device before data will be received by this integration. The tires report their sensor data on the 433MHz band and the central repeater unit translates that into the Bluetooth signal required by this integration. This integration will NOT read the 433MHz data directly.
 - Scans 4 tires only. May throw errors with 2 tires and currently will not scan 6 tires. (The user may manually adjust the code to edit the number of tires scanned by editing `./sensor.py`, `./tirelinc/const.py`, and `./tirelinc/parser.py`).
 - Code that could possibly expose the configured alert thresholds is currently unused and will not expose these sensors (unless user manually adds the sensors with additional edits to sensor.py). It is left in there to decode what was discovered in reverse engineering the hex data bytes. These thresholds - min/max pressure, max temperature, and max temperature change alerts - are configured in the manufactuerer device. The expectation of this integration is the user would configure native Home Assistant automations and set their own, separate thresholds within Home Assistant and therefore these manufacturer data would be irrelevant/confusing.
 - There is a known issue with polling frequency. During testing, the polling interval is shown to be quite random and range from 3 minutes up to more than 1 hour in between updates.
 - The TireLinc system regularly "loses" sensors and it is not possible for this integration to correct this shortcoming. Usually the TireLinc system should update every 15 minutes when stationary and every 5 minutes when moving. However, sometimes specific sensors do not report in until they move, and even then their update frequency is not always a consistent 5 minute interval. Potentially this is related to signal/noise ratio between the tire sensors and the central repeater. Yet, for the developer, this integration is shown to be more reliable than the manufacturer unit to report the most current data the central repeater has on each tire.
 

Exposes the following sensors:
 - Tire 1 Pressure
 - Tire 1 Temperature
 - Tire 2 Pressure
 - Tire 2 Temperature
 - Tire 3 Pressure
 - Tire 3 Temperature
 - Tire 4 Pressure
 - Tire 4 Temperature

In a 4 tire setup, the tire locations will be:
 - Tire 1: Front Left
 - Tire 2: Rear Left
 - Tire 3: Front Right
 - Tire 4: Rear Right

## Installation

Easiest install is via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=k3vmcd&repository=ha-tirelinc&category=integration)

`HACS -> Explore & Add Repositories -> TireLinc`

The device will be autodiscovered once the data are received by any bluetooth proxy.

If you are using an ESPHome device to connect to TireLinc, ensure you have it configured with:

```
bluetooth_proxy:
  active: True
```
and, as the ESPHome docs suggest to improve RAM management:
```
  framework:
    type: esp-idf
```
