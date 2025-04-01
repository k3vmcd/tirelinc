"""Constants for TireLinc."""
from __future__ import annotations

DOMAIN = "tirelinc"

# Update intervals (in seconds)
POLL_INTERVAL_STATIONARY = 900  # 15 minutes
POLL_INTERVAL_MOVING = 30  # 30 seconds - increased from 15 to reduce device stress
UPDATE_INTERVAL = POLL_INTERVAL_STATIONARY  # Default to stationary interval

# Bluetooth characteristics - TireLinc device
SERVICE_UUID = "00000000-00b7-4807-beee-e0b0879cf3dd"  # Main service
READ_CHARACTERISTIC = "00000002-00b7-4807-beee-e0b0879cf3dd"  # Read/notify characteristic
WRITE_CHARACTERISTIC = "00000001-00b7-4807-beee-e0b0879cf3dd"  # Write characteristic

# Configuration constants
CONF_SENSORS = "sensors"
CONF_LEARNING_MODE = "learning_mode"
DISCOVERY_TIMEOUT = 300  # 5 minutes to discover sensors
MAX_TIRES = 6  # Maximum number of tires supported

# Default notification counts
DEFAULT_NOTIFICATION_COUNT = 4  # Default to 4 tires worth of notifications
CONFIG_NOTIFICATION_COUNT = DEFAULT_NOTIFICATION_COUNT
SENSOR_NOTIFICATION_COUNT = DEFAULT_NOTIFICATION_COUNT
