"""Switch platform for TireLinc."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TireLinc switch."""
    async_add_entities([TireLincMotionSwitch(hass, entry)])

class TireLincMotionSwitch(SwitchEntity):
    """Representation of TireLinc motion switch."""

    _attr_has_entity_name = True
    _attr_name = "In Motion"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the motion switch."""
        self.hass = hass
        self.entry = entry
        device_name = entry.title.lower().replace(" ", "_")
        self._attr_unique_id = f"{entry.entry_id}_motion"
        self.entity_id = f"switch.{device_name}_motion"
        self._attr_is_on = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "TireLinc",
            "model": "TPMS",
        }
        
    @property
    def icon(self):
        """Return the icon."""
        return "mdi:car" if self.is_on else "mdi:car-brake-parking"

    async def async_turn_on(self, **kwargs):
        """Turn the motion switch on."""
        self._attr_is_on = True
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]
        coordinator.set_update_interval(True)
        await coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the motion switch off."""
        self._attr_is_on = False
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]
        coordinator.set_update_interval(False)
        await coordinator.async_refresh()
