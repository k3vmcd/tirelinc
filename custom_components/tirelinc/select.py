"""Support for TireLinc rotation pattern selection."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN, ROTATION_PATTERNS, CONF_SENSORS, 
    CONF_TIRE_NAMES, TIRE_CONFIGS, DEFAULT_TIRE_NAMES
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the rotation pattern select entity."""
    async_add_entities([TireRotationPatternSelect(hass, entry)])

class TireRotationPatternSelect(SelectEntity):
    """Representation of a tire rotation pattern selector."""

    _attr_has_entity_name = True
    _attr_name = "Rotation Pattern"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the rotation pattern selector."""
        self.hass = hass
        self.entry = entry
        device_name = entry.title.lower().replace(" ", "_")
        self._attr_unique_id = f"{entry.entry_id}_rotation"
        self.entity_id = f"select.{device_name}_rotation"
        
        # Determine number of tires configured
        configured_sensors = entry.data.get(CONF_SENSORS, {})
        num_tires = len(configured_sensors)
        
        # Get valid patterns for this tire configuration
        valid_patterns = ROTATION_PATTERNS.get(num_tires, {})
        self._attr_options = ["Select Pattern"] + list(valid_patterns.keys())
        self._attr_current_option = "Select Pattern"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "TireLinc",
            "model": "TPMS",
        }

    async def async_select_option(self, option: str) -> None:
        """Handle rotation pattern selection."""
        if option == "Select Pattern":
            return

        # Get current configuration
        configured_sensors = self.entry.data.get(CONF_SENSORS, {})
        num_tires = len(configured_sensors)
        
        # Get patterns for this tire configuration
        valid_patterns = ROTATION_PATTERNS.get(num_tires, {})
        if option not in valid_patterns:
            return

        # Get current names - fallback to defaults if not set
        current_names = self.entry.data.get(
            CONF_TIRE_NAMES, 
            DEFAULT_TIRE_NAMES.get(num_tires, {})
        )
        pattern = valid_patterns[option]["mapping"]
        
        # Create new mappings based on rotation pattern
        new_names = {}
        new_sensors = {}
        
        # Map both names and sensors according to rotation pattern
        for new_pos, old_pos in pattern.items():
            # Get the name from current names or default tire names
            if old_pos in current_names:
                new_names[new_pos] = current_names[old_pos]
            else:
                # Fallback to default name if not found
                default_names = DEFAULT_TIRE_NAMES.get(num_tires, {})
                new_names[new_pos] = default_names.get(new_pos, f"Tire {new_pos.split('_')[1]}")
            
            # Map sensor IDs
            if old_pos in configured_sensors:
                new_sensors[new_pos] = configured_sensors[old_pos]
        
        _LOGGER.debug("Applying rotation pattern %s", option)
        _LOGGER.debug("New sensor mappings: %s", new_sensors)
        _LOGGER.debug("New name mappings: %s", new_names)
        
        # Update config entry with new mappings
        new_data = {
            **self.entry.data,
            CONF_TIRE_NAMES: new_names,
            CONF_SENSORS: new_sensors
        }
        
        # Update entry and trigger reload
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        await self.hass.config_entries.async_reload(self.entry.entry_id)
        
        self._attr_current_option = option
        self.async_write_ha_state()
        
        # Reset selection after applying
        await self.async_select_option("Select Pattern")
