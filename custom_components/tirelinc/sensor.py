"""Support for TireLinc sensors."""
from __future__ import annotations

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

from .const import DOMAIN
from .parser import TireLincSensor

@dataclass
class TireLincSensorEntityDescription(SensorEntityDescription):
    """Describes TireLinc sensor entity."""

SENSOR_DESCRIPTIONS: dict[str, TireLincSensorEntityDescription] = {
    TireLincSensor.TIRE1_PRESSURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE1_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
    ),
    TireLincSensor.TIRE1_TEMPERATURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE1_TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer-lines",
    ),
    TireLincSensor.TIRE2_PRESSURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE2_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
    ),
    TireLincSensor.TIRE2_TEMPERATURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE2_TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer-lines",
    ),
    TireLincSensor.TIRE3_PRESSURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE3_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
    ),
    TireLincSensor.TIRE3_TEMPERATURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE3_TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer-lines",
    ),
    TireLincSensor.TIRE4_PRESSURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE4_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
    ),
    TireLincSensor.TIRE4_TEMPERATURE: TireLincSensorEntityDescription(
        key=TireLincSensor.TIRE4_TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer-lines",
    ),
    TireLincSensor.SIGNAL_STRENGTH: TireLincSensorEntityDescription(
        key=TireLincSensor.SIGNAL_STRENGTH,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the TireLinc BLE sensors."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for description in SENSOR_DESCRIPTIONS.values():
        entities.append(TireLincSensorEntity(coordinator, description, entry))
    
    async_add_entities(entities)


class TireLincSensorEntity(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """Representation of a TireLinc sensor."""

    _attr_has_entity_name = True

    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        description: TireLincSensorEntityDescription,
        entry: config_entries.ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "TireLinc TPMS",
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
