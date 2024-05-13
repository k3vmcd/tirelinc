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
    CHARACTERISTIC_TIRELINC_SENSORS,
    # CHARACTERISTIC_BATTERY,
    UPDATE_INTERVAL,
    TIRE1_SENSOR_ID,
    TIRE2_SENSOR_ID,
    TIRE3_SENSOR_ID,
    TIRE4_SENSOR_ID,
    EXPECTED_NOTIFICATION_COUNT,
)

_LOGGER = logging.getLogger(__name__)


class TireLincSensor(StrEnum):

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

class TireLincBluetoothDeviceData(BluetoothData):
    """Data for TireLinc sensors."""

    def __init__(self) -> None:
        super().__init__()
        self._event = asyncio.Event()
        self._notification_count = 0

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug("Parsing TireLinc BLE advertisement data: %s", service_info)
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
        _LOGGER.warn("Last poll: %s", last_poll)
        _LOGGER.warn("Update interval: %s", UPDATE_INTERVAL)
        return not last_poll or last_poll > UPDATE_INTERVAL

    # @retry_bluetooth_connection_error()
    def notification_handler(self, _, data) -> None:
        """Helper for command events"""
        try:
            TIRE1_SENSOR_ID_bytes = bytes.fromhex(TIRE1_SENSOR_ID.replace("-", ""))
            TIRE2_SENSOR_ID_bytes = bytes.fromhex(TIRE2_SENSOR_ID.replace("-", ""))
            TIRE3_SENSOR_ID_bytes = bytes.fromhex(TIRE3_SENSOR_ID.replace("-", ""))
            TIRE4_SENSOR_ID_bytes = bytes.fromhex(TIRE4_SENSOR_ID.replace("-", ""))

            if data[0] not in [0x04, 0x01]:
                sensor_id = bytes([data[1], data[2], data[3], data[4]])
            else:
                sensor_id = 0

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
                key=str(TireLincSensor.TIRE1_PRESSURE),
                native_unit_of_measurement=Units.PRESSURE_PSI,
                native_value=tire1_pressure,
                device_class=SensorDeviceClass.PRESSURE,
                name="Tire 1 Pressure",
                )

                self.update_sensor(
                key=str(TireLincSensor.TIRE1_TEMPERATURE),
                native_unit_of_measurement=Units.TEMP_FAHRENHEIT,
                native_value=tire1_temperature,
                device_class=SensorDeviceClass.TEMPERATURE,
                name="Tire 1 Temperature",
                )

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
                key=str(TireLincSensor.TIRE2_PRESSURE),
                native_unit_of_measurement=Units.PRESSURE_PSI,
                native_value=tire2_pressure,
                device_class=SensorDeviceClass.PRESSURE,
                name="Tire 2 Pressure",
                )

                self.update_sensor(
                key=str(TireLincSensor.TIRE2_TEMPERATURE),
                native_unit_of_measurement=Units.TEMP_FAHRENHEIT,
                native_value=tire2_temperature,
                device_class=SensorDeviceClass.TEMPERATURE,
                name="Tire 2 Temperature",
                )

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
                key=str(TireLincSensor.TIRE3_PRESSURE),
                native_unit_of_measurement=Units.PRESSURE_PSI,
                native_value=tire3_pressure,
                device_class=SensorDeviceClass.PRESSURE,
                name="Tire 3 Pressure",
                )

                self.update_sensor(
                key=str(TireLincSensor.TIRE3_TEMPERATURE),
                native_unit_of_measurement=Units.TEMP_FAHRENHEIT,
                native_value=tire3_temperature,
                device_class=SensorDeviceClass.TEMPERATURE,
                name="Tire 3 Temperature",
                )

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
                key=str(TireLincSensor.TIRE4_PRESSURE),
                native_unit_of_measurement=Units.PRESSURE_PSI,
                native_value=tire4_pressure,
                device_class=SensorDeviceClass.PRESSURE,
                name="Tire 4 Pressure",
                )

                self.update_sensor(
                key=str(TireLincSensor.TIRE4_TEMPERATURE),
                native_unit_of_measurement=Units.TEMP_FAHRENHEIT,
                native_value=tire4_temperature,
                device_class=SensorDeviceClass.TEMPERATURE,
                name="Tire 4 Temperature",
                )

        except NameError:
            # Handle when variables are not defined
            pass

        # Increment the notification count
        self._notification_count += 1
        _LOGGER.warn("Notification count %s", self._notification_count)
        # Check if all expected notifications are processed
        if self._notification_count >= EXPECTED_NOTIFICATION_COUNT:
            # Reset the counter and set the event to indicate that all notifications are processed
            self._notification_count = 0
            _LOGGER.warn("Notification count %s", self._notification_count)
            self._event.set()
            _LOGGER.warn("Event %s", self._event.is_set())
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
                CHARACTERISTIC_TIRELINC_SENSORS, self.notification_handler
            )
            # Wait until all notifications are processed
            try:
                await asyncio.wait_for(self._event.wait(), 15)
            except asyncio.TimeoutError:
                _LOGGER.warn("Timeout waiting for notifications to be processed")
        except:
            _LOGGER.warn("Notify Bleak error")
        finally:
            # await client.stop_notify(CHARACTERISTIC_TIRELINC_SENSORS)
            await client.disconnect()
            _LOGGER.debug("Disconnected from active bluetooth client")
        return self._finish_update()