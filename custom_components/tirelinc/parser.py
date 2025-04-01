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
    CONFIG_NOTIFICATION_COUNT,
    SENSOR_NOTIFICATION_COUNT,
)

_LOGGER = logging.getLogger(__name__)


class TireLincSensor(StrEnum):
    """Available sensors."""
    SIGNAL_STRENGTH = "signal_strength"
    
    @classmethod
    def tire_pressure(cls, num: str) -> str:
        """Get tire pressure sensor key."""
        return f"tire{num}_pressure"
        
    @classmethod
    def tire_temperature(cls, num: str) -> str:
        """Get tire temperature sensor key."""
        return f"tire{num}_temperature"

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
        self._discovered_sensors = set()  # Track discovered sensors
        self._sensor_mappings = {}  # Will be populated from config entry
        self._learning_mode = False

    @property
    def discovered_sensors(self) -> set[str]:
        """Return set of discovered sensor IDs."""
        return self._discovered_sensors

    def set_learning_mode(self, enabled: bool) -> None:
        """Set learning mode."""
        self._learning_mode = enabled

    def set_sensor_mappings(self, mappings: dict[str, str]) -> None:
        """Set the sensor ID to position mappings."""
        _LOGGER.debug("Setting sensor mappings: %s", mappings)
        self._sensor_mappings = {}
        for position, sensor_id in mappings.items():
            # Convert position (e.g., "tire_1") to number (1)
            try:
                number = position.split("_")[1]
                sensor_bytes = bytes.fromhex(sensor_id.replace("-", ""))
                self._sensor_mappings[sensor_bytes] = number
                _LOGGER.debug("Mapped sensor %s to position %s", sensor_id, number)
            except (IndexError, ValueError) as err:
                _LOGGER.error("Invalid position format: %s (%s)", position, err)

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

            # Add signal strength from advertisement data
            if hasattr(ble_device, "advertisement"):
                self._data["signal_strength"] = ble_device.advertisement.rssi
            else:
                # Fallback for older versions
                self._data["signal_strength"] = getattr(ble_device, "rssi", 0)

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

        if data[0] not in [0x04, 0x01]:
            try:
                sensor_id = bytes([data[1], data[2], data[3], data[4]])
                self._handle_sensor_data(sensor_id, data)
            except IndexError as e:
                _LOGGER.error("Invalid sensor data format: %s", e)

    def _handle_sensor_data(self, sensor_id: bytes, data: bytearray) -> None:
        """Handle sensor data for a specific tire."""
        if len(data) < 10:
            return

        if data[0] == 0x00:
            try:
                temperature = data[7]
                pressure = data[9]
                sensor_id_str = "-".join(f"{b:02X}" for b in sensor_id)

                # Always store discovered sensors during learning mode
                if self._learning_mode:
                    self._discovered_sensors.add(sensor_id_str)
                    return

                # Normal operation - use configured mappings
                if sensor_id in self._sensor_mappings:
                    position = self._sensor_mappings[sensor_id]
                    pressure_key = f"tire{position}_pressure"
                    temp_key = f"tire{position}_temperature"
                    self._data[pressure_key] = pressure
                    self._data[temp_key] = temperature
                    _LOGGER.debug(
                        "Updated sensor data for position %s: pressure=%d, temp=%d", 
                        position, pressure, temperature
                    )
                else:
                    _LOGGER.debug(
                        "Received data for unconfigured sensor %s: pressure=%d, temp=%d",
                        sensor_id_str, pressure, temperature
                    )

            except IndexError as e:
                _LOGGER.error("Invalid sensor data format: %s", e)