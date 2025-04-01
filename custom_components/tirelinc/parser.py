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
    CONFIG_NOTIFICATION_COUNT,
    SENSOR_NOTIFICATION_COUNT,
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
        """Initialize the parser."""
        super().__init__()
        self._name = None
        self._data = {}
        self._config_received = False
        self._sensor_data_received = False
        self._config_count = 0
        self._sensor_count = 0
        self._event = asyncio.Event()

    def supported(self, service_info: BluetoothServiceInfo) -> bool:
        """Check if this device is supported."""
        return service_info.name and service_info.name.startswith("TireLinc")

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Start a new update."""
        self._data = {}  # Initialize empty dict for sensor values
        self.set_device_manufacturer("TireLinc")
        self.set_device_type("TPMS")
        address_suffix = service_info.address.replace(":", "")[-4:].upper()
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
        self._config_received = False
        self._sensor_data_received = False
        self._config_count = 0
        self._sensor_count = 0
        self._event.clear()
        client = None
        
        try:
            # Connect with retry and timeout
            client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                ble_device.address,
                timeout=10.0
            )

            # Get characteristics
            read_char = client.services.get_characteristic(READ_CHARACTERISTIC)
            write_char = client.services.get_characteristic(WRITE_CHARACTERISTIC)

            if not read_char or not write_char:
                _LOGGER.error("Missing required characteristics")
                return self._data

            # Enable notifications first
            await client.start_notify(read_char, self.notification_handler)
            await asyncio.sleep(0.5)  # Short delay before writing
            
            # Write command to request data
            command = bytearray([0x01])
            await client.write_gatt_char(write_char, command, response=False)
            
            # Wait for data with timeout
            try:
                await asyncio.wait_for(self._event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for complete data")
                # Return partial data if we have any
                return self._data

        except Exception as err:
            _LOGGER.error("Error polling device: %s", err)

        finally:
            if client and client.is_connected:
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

    def notification_handler(self, _sender: int, data: bytearray) -> None:
        """Handle notification responses."""
        if not data:
            return

        _LOGGER.debug("Received notification: %s", data.hex())
        
        try:
            # Config packets (0x02) and sensor data packets (0x00)
            packet_type = data[0]
            
            if packet_type == 0x02:
                self._config_count += 1
                _LOGGER.debug("Config packet received (%d/%d)", 
                            self._config_count, CONFIG_NOTIFICATION_COUNT)
                if self._config_count >= CONFIG_NOTIFICATION_COUNT:
                    self._config_received = True
                    _LOGGER.debug("Config data complete")
            
            elif packet_type == 0x00:
                self._process_data(data)
                self._sensor_count += 1
                _LOGGER.debug("Sensor packet received (%d/%d)", 
                            self._sensor_count, SENSOR_NOTIFICATION_COUNT)
                if self._sensor_count >= SENSOR_NOTIFICATION_COUNT:
                    self._sensor_data_received = True
                    _LOGGER.debug("Sensor data complete")
            
            # Set event when either condition is met:
            # 1. Both config and sensor data are complete
            # 2. Just sensor data is complete (config data might not always arrive)
            if (self._config_received and self._sensor_data_received) or self._sensor_data_received:
                self._event.set()
                _LOGGER.debug("Setting completion event")

        except Exception as err:
            _LOGGER.error("Error handling notification: %s", err)

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
                    bytes.fromhex(TIRE1_SENSOR_ID.replace("-", "")): ("tire_1", 1),
                    bytes.fromhex(TIRE2_SENSOR_ID.replace("-", "")): ("tire_2", 2),
                    bytes.fromhex(TIRE3_SENSOR_ID.replace("-", "")): ("tire_3", 3),
                    bytes.fromhex(TIRE4_SENSOR_ID.replace("-", "")): ("tire_4", 4),
                }

                if sensor_id in sensor_mappings:
                    name_prefix, tire_num = sensor_mappings[sensor_id]
                    pressure_key = f"tire{tire_num}_pressure"
                    temp_key = f"tire{tire_num}_temperature"
                    # Store values directly in _data dict
                    self._data[pressure_key] = pressure
                    self._data[temp_key] = temperature

            except IndexError as e:
                _LOGGER.error("Invalid sensor data format: %s", e)