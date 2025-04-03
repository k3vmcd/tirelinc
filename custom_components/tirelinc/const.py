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

# Default tire names by configuration
DEFAULT_TIRE_NAMES = {
    2: {
        "tire_1": "Left Tire",
        "tire_2": "Right Tire"
    },
    4: {
        "tire_1": "Front Left Tire",
        "tire_2": "Rear Left Tire", 
        "tire_3": "Front Right Tire",
        "tire_4": "Rear Right Tire"
    },
    6: {
        "tire_1": "Front Left Tire",
        "tire_2": "Middle Left Tire",
        "tire_3": "Rear Left Tire",
        "tire_4": "Front Right Tire",
        "tire_5": "Middle Right Tire",
        "tire_6": "Rear Right Tire"
    }
}

# Tire configurations
TIRE_CONFIGS = {
    2: ["tire_1", "tire_2"],  # Front only
    4: ["tire_1", "tire_2", "tire_3", "tire_4"],  # Standard 4-tire
    6: ["tire_1", "tire_2", "tire_3", "tire_4", "tire_5", "tire_6"]  # 6-tire
}

# Rotation patterns by tire count
ROTATION_PATTERNS = {
    2: {
        "x_pattern": {
            "name": "X Pattern (2 Tire)",
            "mapping": {
                "tire_1": "tire_2",  # Left -> Right
                "tire_2": "tire_1"   # Right -> Left
            }
        }
    },
    4: {
        "forward_cross": {
            "name": "Forward Cross",
            "mapping": {
                "tire_1": "tire_2",  # Front Left -> Rear Left
                "tire_2": "tire_3",  # Rear Left -> Front Right
                "tire_3": "tire_4",  # Front Right -> Rear Right
                "tire_4": "tire_1"   # Rear Right -> Front Left
            }
        },
        "rearward_cross": {
            "name": "Rearward Cross",
            "mapping": {
                "tire_1": "tire_4",  # Front Left -> Rear Right
                "tire_2": "tire_1",  # Rear Left -> Front Left
                "tire_3": "tire_2",  # Front Right -> Rear Left
                "tire_4": "tire_3"   # Rear Right -> Front Right
            }
        },
        "x_pattern": {
            "name": "X Pattern",
            "mapping": {
                "tire_1": "tire_4",  # Front Left -> Rear Right
                "tire_2": "tire_3",  # Rear Left -> Front Right
                "tire_3": "tire_2",  # Front Right -> Rear Left
                "tire_4": "tire_1"   # Rear Right -> Front Left
            }
        }
    },
    6: {
        "forward_cross": {
            "name": "Forward Cross (6-Tire)",
            "mapping": {
                "tire_1": "tire_2",  # Front Left -> Middle Left
                "tire_2": "tire_3",  # Middle Left -> Rear Left
                "tire_3": "tire_4",  # Rear Left -> Front Right
                "tire_4": "tire_5",  # Front Right -> Middle Right
                "tire_5": "tire_6",  # Middle Right -> Rear Right
                "tire_6": "tire_1"   # Rear Right -> Front Left
            }
        },
        "rearward_cross": {
            "name": "Rearward Cross (6-Tire)",
            "mapping": {
                "tire_1": "tire_6",  # Front Left -> Rear Right
                "tire_2": "tire_1",  # Middle Left -> Front Left
                "tire_3": "tire_2",  # Rear Left -> Middle Left
                "tire_4": "tire_3",  # Front Right -> Rear Left
                "tire_5": "tire_4",  # Middle Right -> Front Right
                "tire_6": "tire_5"   # Rear Right -> Middle Right
            }
        },
        "x_pattern": {
            "name": "X Pattern (6-Tire)",
            "mapping": {
                "tire_1": "tire_6",  # Front Left -> Rear Right
                "tire_2": "tire_5",  # Middle Left -> Middle Right
                "tire_3": "tire_4",  # Rear Left -> Front Right
                "tire_4": "tire_3",  # Front Right -> Rear Left
                "tire_5": "tire_2",  # Middle Right -> Middle Left
                "tire_6": "tire_1"   # Rear Right -> Front Left
            }
        }
    }
}

CONF_TIRE_NAMES = "tire_names"
CONF_ROTATION_PATTERN = "rotation_pattern"
