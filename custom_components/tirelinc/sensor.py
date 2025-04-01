"""Support for TireLinc sensors."""
from __future__ import annotations

import logging

from dataclasses import dataclass

from homeassistant import config_entries
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, CONF_SENSORS, MAX_TIRES
from .parser import TireLincSensor

_LOGGER = logging.getLogger(__name__)

@dataclass
class TireLincSensorEntityDescription(SensorEntityDescription):
    """Describes TireLinc sensor entity."""

def create_sensor_descriptions() -> dict[str, TireLincSensorEntityDescription]:
    """Create sensor descriptions."""
    descriptions = {}
    
    # Add signal strength sensor
    descriptions[TireLincSensor.SIGNAL_STRENGTH] = TireLincSensorEntityDescription(
        key=TireLincSensor.SIGNAL_STRENGTH,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_visible_default=False,
        name="Signal Strength",
    )
    
    # Create template descriptions for tire sensors
    for i in range(1, MAX_TIRES + 1):
        descriptions[f"tire{i}_pressure"] = TireLincSensorEntityDescription(
            key=f"tire{i}_pressure",
            native_unit_of_measurement=UnitOfPressure.PSI,
            device_class=SensorDeviceClass.PRESSURE,
            icon="mdi:car-tire-alert",
        )
        descriptions[f"tire{i}_temperature"] = TireLincSensorEntityDescription(
            key=f"tire{i}_temperature",
            native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
            device_class=SensorDeviceClass.TEMPERATURE,
            icon="mdi:thermometer-lines",
        )
    
    return descriptions

SENSOR_DESCRIPTIONS = create_sensor_descriptions()

async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the TireLinc BLE sensors."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Get configured sensors from entry
    configured_sensors = entry.data.get(CONF_SENSORS, {})
    _LOGGER.debug("Setting up sensors for config: %s", configured_sensors)
    
    entities = []
    
    # Create signal strength sensor
    signal_desc = SENSOR_DESCRIPTIONS.get("signal_strength")
    if signal_desc:
        entities.append(TireLincSensorEntity(coordinator, signal_desc, entry))
        _LOGGER.debug("Added signal strength sensor")
    
    # Create tire sensors based on configuration
    for tire_key, sensor_id in configured_sensors.items():
        # Extract tire number from key (e.g., "tire_1" -> "1")
        try:
            tire_num = tire_key.split("_")[1]
            _LOGGER.debug("Setting up sensors for tire %s (ID: %s)", tire_num, sensor_id)
            
            # Add pressure sensor
            pressure_key = f"tire{tire_num}_pressure"
            if pressure_key in SENSOR_DESCRIPTIONS:
                entities.append(TireLincSensorEntity(coordinator, SENSOR_DESCRIPTIONS[pressure_key], entry))
                _LOGGER.debug("Added pressure sensor for tire %s", tire_num)
            
            # Add temperature sensor
            temp_key = f"tire{tire_num}_temperature"
            if temp_key in SENSOR_DESCRIPTIONS:
                entities.append(TireLincSensorEntity(coordinator, SENSOR_DESCRIPTIONS[temp_key], entry))
                _LOGGER.debug("Added temperature sensor for tire %s", tire_num)
                
        except (IndexError, ValueError) as err:
            _LOGGER.error("Error setting up tire sensors for %s: %s", tire_key, err)
    
    _LOGGER.debug("Created %d sensor entities", len(entities))
    async_add_entities(entities)


class TireLincSensorEntity(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """Representation of a TireLinc sensor."""

    _attr_has_entity_name = False

    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        description: TireLincSensorEntityDescription,
        entry: config_entries.ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        # Get device name part (e.g., "tirelinc_f45a")
        device_name = entry.title.lower().replace(" ", "_")
        
        if description.key == TireLincSensor.SIGNAL_STRENGTH:
            # Special handling for signal strength sensor
            entity_id = f"{device_name}_signal_strength"
            display_name = "Signal Strength"
        else:
            # Extract tire number and type from the key
            key_parts = description.key.split("_", 1)  # Split only on first underscore
            if len(key_parts) > 1:
                tire_num = key_parts[0][4]  # Get number from "tire1"
                measure_type = key_parts[1]  # Get "pressure" or "temperature"
                
                # Build entity_id (e.g., "tirelinc_f45a_tire_1_pressure")
                entity_id = f"{device_name}_tire_{tire_num}_{measure_type}"
                # Set display name (e.g., "Tire 1 Pressure")
                display_name = f"Tire {tire_num} {measure_type.title()}"
            else:
                entity_id = f"{device_name}_{description.key}"
                display_name = description.key.replace("_", " ").title()

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self.entity_id = f"sensor.{entity_id}"
        self._attr_name = display_name
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "TireLinc",
            "model": "TPMS",
        }

    @property
    def native_value(self) -> str | int | None:
        """Return the native value."""
        if not self.coordinator.data:
            return None
        try:
            return self.coordinator.data[self.entity_description.key]
        except (KeyError, TypeError):
            return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
