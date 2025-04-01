"""Constants for TireLinc."""
from __future__ import annotations

DOMAIN = "tirelinc"

# Update intervals (in seconds)
POLL_INTERVAL_STATIONARY = 900  # 15 minutes
POLL_INTERVAL_MOVING = 30  # 30 seconds - increased from 15 to reduce device stress

# Bluetooth characteristics - TireLinc device
SERVICE_UUID = "00000000-00b7-4807-beee-e0b0879cf3dd"  # Main service
READ_CHARACTERISTIC = "00000002-00b7-4807-beee-e0b0879cf3dd"  # Read/notify characteristic
WRITE_CHARACTERISTIC = "00000001-00b7-4807-beee-e0b0879cf3dd"  # Write characteristic

# Tire sensor IDs - these need to be customized by the user
TIRE1_SENSOR_ID = "0E-B3-0B-02"
TIRE2_SENSOR_ID = "0E-88-46-02"
TIRE3_SENSOR_ID = "0E-FF-47-02"
TIRE4_SENSOR_ID = "0E-61-3A-02"

# Expected notification counts
CONFIG_NOTIFICATION_COUNT = 6  # Number of 0x02 packets expected
SENSOR_NOTIFICATION_COUNT = 4  # Number of 0x00 packets expected
