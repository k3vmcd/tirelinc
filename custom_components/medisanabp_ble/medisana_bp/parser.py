from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timezone

from bleak import BLEDevice
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
    retry_bluetooth_connection_error,
)
from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import SensorDeviceClass, SensorUpdate, Units
from sensor_state_data.enum import StrEnum

from .const import (
    CHARACTERISTIC_BLOOD_PRESSURE,
    # CHARACTERISTIC_BATTERY,
    UPDATE_INTERVAL,
    TIRE1_SENSOR_ID,
    TIRE2_SENSOR_ID,
    TIRE3_SENSOR_ID,
    TIRE4_SENSOR_ID,
)

_LOGGER = logging.getLogger(__name__)


class MedisanaBPSensor(StrEnum):

    PRESSURE = "pressure"
    TIRE1_PRESSURE = "tire1_pressure"
    TIRE2_PRESSURE = "tire2_pressure"
    TIRE3_PRESSURE = "tire3_pressure"
    TIRE4_PRESSURE = "tire4_pressure"
    TIRE1_TEMPERATURE = "tire1_temperature"
    TIRE2_TEMPERATURE = "tire2_temperature"
    TIRE3_TEMPERATURE = "tire3_temperature"
    TIRE4_TEMPERATURE = "tire4_temperature"
    SIGNAL_STRENGTH = "signal_strength"
    # BATTERY_PERCENT = "battery_percent"
    # TIMESTAMP = "timestamp"

class MedisanaBPBluetoothDeviceData(BluetoothData):
    """Data for TireLinc sensors."""

    def __init__(self) -> None:
        super().__init__()
        self._event = asyncio.Event()

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug("Parsing MedisanaBP BLE advertisement data: %s", service_info)
        self.set_device_manufacturer("TireLinc")
        self.set_device_type("TPMS")
        name = f"{service_info.name} {short_address(service_info.address)}"
        self.set_device_name(name)
        self.set_title(name)

    def poll_needed(
        self, service_info: BluetoothServiceInfo, last_poll: float | None
    ) -> bool:
        """
        This is called every time we get a service_info for a device. It means the
        device is working and online.
        """
        _LOGGER.warning("Poll Needed")
        _LOGGER.warning(last_poll)
        return not last_poll or last_poll > UPDATE_INTERVAL

    @retry_bluetooth_connection_error()
    def notification_handler(self, _, data) -> None:
        """Helper for command events"""
#        sensor_id = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4]
#        if sensor_id == 0x0E_B3_0B_02
        sensor_id = bytes([data[1], data[2], data[3], data[4]])
        TIRE1_SENSOR_ID_bytes = bytes.fromhex(TIRE1_SENSOR_ID.replace("-", ""))
        TIRE2_SENSOR_ID_bytes = bytes.fromhex(TIRE2_SENSOR_ID.replace("-", ""))
        TIRE3_SENSOR_ID_bytes = bytes.fromhex(TIRE3_SENSOR_ID.replace("-", ""))
        TIRE4_SENSOR_ID_bytes = bytes.fromhex(TIRE4_SENSOR_ID.replace("-", ""))
        if sensor_id == TIRE1_SENSOR_ID_bytes:
            if data[0] == 0x02:
                tire1_alert_min_pressure = data[7]
                tire1_alert_max_pressure = data[9]
                tire1_alert_max_temperature = data[11]
                tire1_alert_max_temp_change = data[13]
            elif data[0] == 0x00:
                tire1_temperature = data[7]
                tire1_pressure = data[9]
            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE1_PRESSURE),
            native_unit_of_measurement=Units.PRESSURE_PSI,
            native_value=tire1_pressure,
            device_class=SensorDeviceClass.PRESSURE,
            name="Tire 1 Pressure",
            )

            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE1_TEMPERATURE),
            native_unit_of_measurement=Units.TEMPERATURE_FAHRENHEIT,
            native_value=tire1_temperature,
            device_class=SensorDeviceClass.TEMPERATURE,
            name="Tire 1 Temperature",
            )

            _LOGGER.info("Got Tire 1 data from TPMS device (temperature: %s, pressure: %s)", tire1_temperature, tire1_pressure)

        elif sensor_id == TIRE2_SENSOR_ID_bytes:
            if data[0] == 0x02:
                tire2_alert_min_pressure = data[7]
                tire2_alert_max_pressure = data[9]
                tire2_alert_max_temperature = data[11]
                tire2_alert_max_temp_change = data[13]
            elif data[0] == 0x00:
                tire2_temperature = data[7]
                tire2_pressure = data[9]

            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE2_PRESSURE),
            native_unit_of_measurement=Units.PRESSURE_PSI,
            native_value=tire2_pressure,
            device_class=SensorDeviceClass.PRESSURE,
            name="Tire 2 Pressure",
            )

            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE2_TEMPERATURE),
            native_unit_of_measurement=Units.TEMPERATURE_FAHRENHEIT,
            native_value=tire2_temperature,
            device_class=SensorDeviceClass.TEMPERATURE,
            name="Tire 2 Temperature",
            )

            _LOGGER.info("Got Tire 2 data from TPMS device (temperature: %s, pressure: %s)", tire2_temperature, tire3_pressure)

        elif sensor_id == TIRE3_SENSOR_ID_bytes:
            if data[0] == 0x02:
                tire3_alert_min_pressure = data[7]
                tire3_alert_max_pressure = data[9]
                tire3_alert_max_temperature = data[11]
                tire3_alert_max_temp_change = data[13]
            elif data[0] == 0x00:
                tire3_temperature = data[7]
                tire3_pressure = data[9]

            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE3_PRESSURE),
            native_unit_of_measurement=Units.PRESSURE_PSI,
            native_value=tire3_pressure,
            device_class=SensorDeviceClass.PRESSURE,
            name="Tire 3 Pressure",
            )

            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE3_TEMPERATURE),
            native_unit_of_measurement=Units.TEMPERATURE_FAHRENHEIT,
            native_value=tire3_temperature,
            device_class=SensorDeviceClass.TEMPERATURE,
            name="Tire 3 Temperature",
            )

            _LOGGER.info("Got Tire 3 data from TPMS device (temperature: %s, pressure: %s)", tire3_temperature, tire3_pressure)

        elif sensor_id == TIRE4_SENSOR_ID_bytes:
            if data[0] == 0x02:
                tire4_alert_min_pressure = data[7]
                tire4_alert_max_pressure = data[9]
                tire4_alert_max_temperature = data[11]
                tire4_alert_max_temp_change = data[13]
            elif data[0] == 0x00:
                tire4_temperature = data[7]
                tire4_pressure = data[9]

            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE4_PRESSURE),
            native_unit_of_measurement=Units.PRESSURE_PSI,
            native_value=tire4_pressure,
            device_class=SensorDeviceClass.PRESSURE,
            name="Tire 4 Pressure",
            )

            self.update_sensor(
            key=str(MedisanaBPSensor.TIRE4_TEMPERATURE),
            native_unit_of_measurement=Units.TEMPERATURE_FAHRENHEIT,
            native_value=tire4_temperature,
            device_class=SensorDeviceClass.TEMPERATURE,
            name="Tire 4 Temperature",
            )

            _LOGGER.info("Got Tire 4 data from TPMS device (temperature: %s, pressure: %s)", tire4_temperature, tire4_pressure)


        # _LOGGER.warn(
        #     "Got data from BPM device (temperature: %s, pressure: %s)",
        #     tire2_temperature, tire2_pressure)

        # self.update_sensor(
        #     key=str(MedisanaBPSensor.PRESSURE),
        #     native_unit_of_measurement=Units.PRESSURE_PSI,
        #     native_value=tire2_pressure,
        #     device_class=SensorDeviceClass.PRESSURE,
        #     name="Pressure",
        # )
        # self.update_sensor(
        #     key=str(MedisanaBPSensor.DIASTOLIC),
        #     native_unit_of_measurement=Units.PRESSURE_MMHG,
        #     native_value=diast,
        #     device_class=SensorDeviceClass.PRESSURE,
        #     name="Diastolic",
        # )
        # self.update_sensor(
        #     key=str(MedisanaBPSensor.PULSE),
        #     native_unit_of_measurement="bpm",
        #     native_value=puls,
        #     name="Pulse",
        # )
        self._event.set()
        return

    async def async_poll(self, ble_device: BLEDevice) -> SensorUpdate:
        """
        Poll the device to retrieve any values we can't get from passive listening.
        """
        _LOGGER.debug("Connecting to BLE device: %s", ble_device.address)
        client = await establish_connection(
            BleakClientWithServiceCache, ble_device, ble_device.address
        )
        try:
            await client.start_notify(
                CHARACTERISTIC_BLOOD_PRESSURE, self.notification_handler
            )
        except:
            _LOGGER.warn("Notify Bleak error")

        # battery_char = client.services.get_characteristic(CHARACTERISTIC_BATTERY)
        # battery_payload = await client.read_gatt_char(battery_char)
        # self.update_sensor(
        #     key=str(MedisanaBPSensor.BATTERY_PERCENT),
        #     native_unit_of_measurement=Units.PERCENTAGE,
        #     native_value=battery_payload[0],
        #     device_class=SensorDeviceClass.BATTERY,
        #     name="Battery",
        # )

        # Wait to see if a callback comes in.
        try:
            await asyncio.wait_for(self._event.wait(), 15)
        except asyncio.TimeoutError:
            _LOGGER.warn("Timeout getting command data.")
        except:
            _LOGGER.warn("Wait For Bleak error")
        finally:
            await client.stop_notify(CHARACTERISTIC_BLOOD_PRESSURE)
            await client.disconnect()
            _LOGGER.debug("Disconnected from active bluetooth client")
        return self._finish_update()
