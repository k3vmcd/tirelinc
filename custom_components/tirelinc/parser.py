"""Parser for TireLinc BLE devices."""
from __future__ import annotations

import logging
import asyncio

from bleak import BLEDevice
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)
from home_assistant_bluetooth import BluetoothServiceInfo
from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from sensor_state_data import SensorDeviceClass, SensorUpdate, Units
from sensor_state_data.enum import StrEnum

from .const import (
    SERVICE_UUID,
    READ_CHARACTERISTIC,
    WRITE_CHARACTERISTIC,
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
        self._name = None
        self._data = {}

    def supported(self, service_info: BluetoothServiceInfo) -> bool:
        """Check if this device is supported."""
        return service_info.name and service_info.name.startswith("TireLinc")

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Start a new update."""
        self._data = {}  # Initialize empty dict for sensor values
        self.set_device_manufacturer("TireLinc")
        self.set_device_type("TPMS")
        self._name = f"{service_info.name} {short_address(service_info.address)}"
        self.set_device_name(self._name)
        self.set_title(self._name)

    @property
    def title(self) -> str | None:
        """Return the title."""
        return self._name

    def get_device_name(self) -> str | None:
        """Return device name."""
        return self._name

    async def async_poll(self, ble_device: BLEDevice) -> dict:
        """Poll the device."""
        self._data = {}
        client = None
        
        try:
            # Connect with retry and timeout
            client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                ble_device.address,
                timeout=10.0
            )

            # Initialize event for notifications
            self._event = asyncio.Event()
            self._event.clear()

            # Get characteristics
            read_char = client.services.get_characteristic(READ_CHARACTERISTIC)
            write_char = client.services.get_characteristic(WRITE_CHARACTERISTIC)

            if not read_char or not write_char:
                _LOGGER.error(
                    "Missing required characteristics. Read: %s, Write: %s",
                    bool(read_char),
                    bool(write_char)
                )
                return self._data

            # Enable notifications
            await client.start_notify(read_char, self.notification_handler)
            
            # Write command to request data - no response needed
            command = bytearray([0x01])  # Simplified command
            await client.write_gatt_char(write_char, command, response=False)
            
            # Wait for notifications with timeout
            try:
                await asyncio.wait_for(self._event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for notifications")

            # Read any remaining data
            try:
                data = await client.read_gatt_char(read_char)
                if data and len(data) >= 10:
                    self._process_data(data)
            except Exception as err:
                _LOGGER.warning("Error reading final data: %s", err)

        except Exception as err:
            _LOGGER.error("Error polling device: %s", err)

        finally:
            if client:
                try:
                    await client.disconnect()
                except Exception as err:
                    _LOGGER.warning("Error disconnecting: %s", err)

        return self._data

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
    def notification_handler(self, _sender: int, data: bytearray) -> None:
        """Handle notification responses."""
        _LOGGER.debug("Received notification: %s", data.hex() if data else None)
        if data and len(data) >= 10:
            self._process_data(data)
            self._event.set()  # Signal that we got data

    def _process_data(self, data: bytearray) -> None:
        """Process the raw sensor data."""
        if not data or len(data) < 10:  # Ensure minimum data length
            _LOGGER.error("Received invalid data length: %s", len(data) if data else 0)
            return

        try:
            TIRE1_SENSOR_ID_bytes = bytes.fromhex(TIRE1_SENSOR_ID.replace("-", ""))
            TIRE2_SENSOR_ID_bytes = bytes.fromhex(TIRE2_SENSOR_ID.replace("-", ""))
            TIRE3_SENSOR_ID_bytes = bytes.fromhex(TIRE3_SENSOR_ID.replace("-", ""))
            TIRE4_SENSOR_ID_bytes = bytes.fromhex(TIRE4_SENSOR_ID.replace("-", ""))

            if data[0] not in [0x04, 0x01]:
                try:
                    sensor_id = bytes([data[1], data[2], data[3], data[4]])
                    self._handle_sensor_data(sensor_id, data)
                except IndexError as e:
                    _LOGGER.error("Invalid sensor data format: %s", e)
        except Exception as e:
            _LOGGER.error("Error processing data: %s", e)

    def _handle_sensor_data(self, sensor_id: bytes, data: bytearray) -> None:
        """Handle sensor data for a specific tire."""
        if len(data) < 10:  # Ensure we have enough data
            _LOGGER.error("Insufficient data length for sensor reading")
            return

        if data[0] == 0x00:  # Only process actual sensor readings
            try:
                temperature = data[7]
                pressure = data[9]

                sensor_mappings = {
                    bytes.fromhex(TIRE1_SENSOR_ID.replace("-", "")): (
                        TireLincSensor.TIRE1_PRESSURE,
                        TireLincSensor.TIRE1_TEMPERATURE,
                        "Tire 1"
                    ),
                    bytes.fromhex(TIRE2_SENSOR_ID.replace("-", "")): (
                        TireLincSensor.TIRE2_PRESSURE,
                        TireLincSensor.TIRE2_TEMPERATURE,
                        "Tire 2"
                    ),
                    bytes.fromhex(TIRE3_SENSOR_ID.replace("-", "")): (
                        TireLincSensor.TIRE3_PRESSURE,
                        TireLincSensor.TIRE3_TEMPERATURE,
                        "Tire 3"
                    ),
                    bytes.fromhex(TIRE4_SENSOR_ID.replace("-", "")): (
                        TireLincSensor.TIRE4_PRESSURE,
                        TireLincSensor.TIRE4_TEMPERATURE,
                        "Tire 4"
                    ),
                }

                if sensor_id in sensor_mappings:
                    pressure_key, temp_key, name = sensor_mappings[sensor_id]
                    # Store values directly in _data dict
                    self._data[str(pressure_key)] = pressure
                    self._data[str(temp_key)] = temperature
            except IndexError as e:
                _LOGGER.error("Invalid sensor data format: %s", e)