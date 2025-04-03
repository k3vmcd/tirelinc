[![GitHub Release](https://img.shields.io/github/release/k3vmcd/ha-tirelinc.svg?style=flat-square)](https://github.com/k3vmcd/ha-tirelinc/releases)
[![License](https://img.shields.io/github/license/k3vmcd/ha-tirelinc.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-default-orange.svg?style=flat-square)](https://hacs.xyz)

# Home Assistant TireLinc Integration

This integration connects TireLinc TPMS (Tire Pressure Monitoring System) devices to Home Assistant. It supports monitoring pressure and temperature for up to 6 tires using Bluetooth.

## ⚠️ Important Upgrade Notice

If upgrading from a version prior to 0.2.0, you MUST completely remove and reinstall the integration due to breaking changes in the sensor configuration system:

1. **Backup your configuration:**
   - Note your tire sensor positions and mappings
   - Screenshot or record any automations using TireLinc entities

2. **Remove the old integration:**
   - Go to Settings → Devices & Services
   - Find the TireLinc integration
   - Click the 3 dots menu → Delete
   - Click Delete
   - Restart Home Assistant

4. **Fresh Install:**
   - Install the latest version via HACS
   - Restart Home Assistant
   - Add the integration through the UI, it should automatically detect your device
   - Complete the new setup process
   - Verify sensor mappings match your previous configuration

5. **Post-Install:**
   - Update any automations with new entity IDs
   - Test all tire positions are reporting correctly

## ⚠️ Important Setup Requirements

1. **Pre-pairing Required**: You MUST pair the tires to the TireLinc repeater using the manufacturer's app BEFORE using this integration. The integration cannot directly read the 433MHz tire sensor signals - it only communicates with the Bluetooth repeater.

2. **Sensor Discovery & Mapping**: During setup, the integration will discover your tire sensors. For correct position mapping:
   - Download [nRF Connect](https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-mobile)
   - Connect to your TireLinc device
   - Expand "Unknown Service"
   - Subscribe to notifications on characteristic `00000002-00b7-4807-beee-e0b0879cf3dd`
   - Check the logs (swipe right)
   - Look for lines starting with `00` or `02`
   - The sensor IDs are the 4 bytes after these prefixes (e.g., in `00-0E-FF-47-02`, the ID is `0E-FF-47-02`)
   - Sensors report in order from positions 1-4 - note this order to verify correct mapping

3. **Vehicle Movement**: Initial sensor discovery works best when:
   - The vehicle has been driven recently (within 15 minutes)
   - All tires are at normal operating temperature
   - The vehicle is within good Bluetooth range

## Features

- Auto-discovery of tire sensors during setup
- Support for 2, 4, or 6 tire configurations
- Pressure and temperature monitoring for each tire
- Automatic tire position mapping
- Motion-based update frequency (faster updates while moving)
- Tire rotation pattern selection and automatic sensor remapping

## Installation

1. Install via HACS (recommended):
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=k3vmcd&repository=ha-tirelinc&category=integration)

   Navigate to: `HACS -> Explore & Add Repositories -> TireLinc`

2. Initial Setup:
   - The device will be auto-discovered once Bluetooth data is received
   - Follow the configuration flow to discover and map your tire sensors
   - Each sensor will be automatically assigned to a tire position

## Requirements

1. TireLinc TPMS central repeater and tire sensors must be pre-paired using the manufacturer's app
2. Home Assistant with Bluetooth support (built-in or ESPHome proxy)

### ESPHome Bluetooth Proxy Configuration

If using an ESPHome device as a Bluetooth proxy, add:

```yaml
bluetooth_proxy:
  active: True

# Recommended for better RAM management
framework:
  type: esp-idf
```

## Technical Details

- Initial Setup: The tires must first be paired with the TireLinc repeater using the manufacturer's device. The repeater translates 433MHz tire sensor signals to Bluetooth.

### In Motion Switch
The integration provides an "In Motion" switch that controls the update frequency:
- When **OFF** (default):
  - Uses stationary mode polling (15 minute intervals)
  - Suitable for parked vehicles
  - Conserves battery and network resources
  
- When **ON**:
  - Activates moving mode polling (30 second intervals)
  - Use before and during travel
  - Provides more frequent pressure/temperature updates
  - Note: This only increases how often we check for new data - it does not affect how frequently the sensors themselves report to the repeater
  
You can automate this switch based on:
- RV Power status
- Vehicle ignition status
- GPS/location changes
- Other motion sensors
- Time of day (e.g., typical travel times)

### Tire Rotation
The integration provides a "Rotation Pattern" select entity to help manage tire rotations:

**2-Tire Configuration:**
```
X Pattern:
[1/L] ↔ [2/R]    # Left and Right swap
```

**4-Tire Configuration:**
```
Forward Cross:
[1/FL] → [2/RL]    # Front Left to Rear Left
[2/RL] → [3/FR]    # Rear Left to Front Right
[3/FR] → [4/RR]    # Front Right to Rear Right
[4/RR] → [1/FL]    # Rear Right to Front Left

Rearward Cross:
[1/FL] → [4/RR]    # Front Left to Rear Right
[2/RL] → [1/FL]    # Rear Left to Front Left
[3/FR] → [2/RL]    # Front Right to Rear Left
[4/RR] → [3/FR]    # Rear Right to Front Right

X Pattern:
[1/FL] ↔ [4/RR]    # Front Left and Rear Right swap
[2/RL] ↔ [3/FR]    # Rear Left and Front Right swap
```

**6-Tire Configuration:**
```
Forward Cross:
[1/FL] → [2/ML]    # Front Left to Middle Left
[2/ML] → [3/RL]    # Middle Left to Rear Left
[3/RL] → [4/FR]    # Rear Left to Front Right
[4/FR] → [5/MR]    # Front Right to Middle Right
[5/MR] → [6/RR]    # Middle Right to Rear Right
[6/RR] → [1/FL]    # Rear Right to Front Left

Rearward Cross:
[1/FL] → [6/RR]    # Front Left to Rear Right
[2/ML] → [1/FL]    # Middle Left to Front Left
[3/RL] → [2/ML]    # Rear Left to Middle Left
[4/FR] → [3/RL]    # Front Right to Rear Left
[5/MR] → [4/FR]    # Middle Right to Front Right
[6/RR] → [5/MR]    # Rear Right to Middle Right

X Pattern:
[1/FL] → [6/RR]    # Front Left to Rear Right
[2/ML] → [5/MR]    # Middle Left to Middle Right
[3/RL] → [4/FR]    # Rear Left to Front Right
[4/FR] → [3/RL]    # Front Right to Rear Left
[5/MR] → [2/ML]    # Middle Right to Middle Left
[6/RR] → [1/FL]    # Rear Right to Front Left
```

After selecting a pattern:
1. The integration automatically updates sensor mappings
2. Names and positions are updated to match the new configuration
3. The selection resets to "Select Pattern" when complete

**Legend:**
- FL = Front Left    - FR = Front Right
- ML = Middle Left   - MR = Middle Right
- RL = Rear Left     - RR = Rear Right
- → = Moves to       - ↔ = Swaps with

### Update Frequency
- **Stationary Mode**:
  - Expected: Every 15 minutes
  - Reality: May vary significantly (3-60+ minutes)
  - Some sensors may become temporarily unavailable
  
- **Moving Mode**:
  - Expected: Every 30 seconds
  - Reality: More consistent but may still vary
  - Movement typically "wakes up" unresponsive sensors

### Tire Positions
Standard 4-tire configuration mapping:
- Tire 1: Front Left
- Tire 2: Rear Left
- Tire 3: Front Right
- Tire 4: Rear Right

For 2-tire setups:
- Tire 1: Left
- Tire 2: Right

For 6-tire setups:
- Tire 1: Front Left
- Tire 2: Middle Left
- Tire 3: Rear Left
- Tire 4: Front Right
- Tire 5: Middle Right
- Tire 6: Rear Right

## ⚠️ Known Limitations

1. **Signal Reliability Issues**:
   - Sensors may temporarily stop reporting without warning
   - Some sensors require vehicle movement to resume reporting
   - Signal quality varies with distance from repeater
   - Metal objects (including the vehicle itself) can interfere with signals

2. **Update Frequency Inconsistency**:
   - Updates are not guaranteed at fixed intervals
   - Stationary mode can be especially unpredictable
   - Moving mode is more reliable but still variable

3. **System Limitations**:
   - The integration cannot fix underlying TireLinc communication issues
   - Alert thresholds set in manufacturer's app are not exposed
   - Use Home Assistant automations for pressure/temperature alerts

## Troubleshooting

1. If sensors aren't discovered:
   - Ensure vehicle has been driven recently
   - Verify TireLinc repeater has power
   - Check Bluetooth connection strength
   - Try moving closer to the vehicle

2. If sensor positions are wrong:
   - Use nRF Connect to verify sensor reporting order
   - Delete and re-add the integration
   - Record sensors in order during discovery

3. If updates are inconsistent:
   - This is normal behavior
   - Consider adding automations with longer timeout periods
   - Use state age tracking for alerts

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/k3vmcd/ha-tirelinc/issues).

When reporting issues, please include:
- Your tire configuration (2/4/6 tires)
- Bluetooth proxy type (built-in/ESPHome)
- Any recent changes or updates
