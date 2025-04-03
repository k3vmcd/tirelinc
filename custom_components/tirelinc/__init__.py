"""The TireLinc integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.bluetooth import async_ble_device_from_address, async_discovered_service_info
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, POLL_INTERVAL_STATIONARY, POLL_INTERVAL_MOVING, CONF_SENSORS
from .parser import TireLincBluetoothDeviceData

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.SELECT]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TireLinc from a config entry."""
    address = entry.unique_id
    if address is None:
        raise ConfigEntryNotReady("Device address not found")

    device_data = TireLincBluetoothDeviceData()
    
    # Set sensor mappings from config entry
    if CONF_SENSORS in entry.data:
        _LOGGER.debug("Setting up sensor mappings: %s", entry.data[CONF_SENSORS])
        device_data.set_sensor_mappings(entry.data[CONF_SENSORS])

    async def _async_update():
        """Poll the device."""
        try:
            service_info = None
            for info in async_discovered_service_info(hass):
                if info.address == address:
                    service_info = info
                    break

            device = async_ble_device_from_address(hass, address, connectable=True)
            if not device:
                _LOGGER.error("Device %s not found", address)
                return {}
                
            _LOGGER.debug("Polling device %s", address)
            data = await device_data.async_poll(device, service_info)
            
            if not data:
                _LOGGER.warning("No data received from device %s", address)
                return {}
                
            _LOGGER.debug("Updated data: %s", data)
            return data
            
        except Exception as err:
            _LOGGER.error("Error polling device %s: %s", address, err)
            return {}

    coordinator = TireLincDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update,
        update_interval=timedelta(seconds=POLL_INTERVAL_STATIONARY),
    )

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class TireLincDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TireLinc data."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        *,
        name: str,
        update_interval: timedelta,
        update_method: callable,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self._update_method = update_method

    def set_update_interval(self, is_moving: bool) -> None:
        """Update the polling interval based on motion state."""
        self.update_interval = timedelta(
            seconds=POLL_INTERVAL_MOVING if is_moving else POLL_INTERVAL_STATIONARY
        )
        _LOGGER.debug(
            "Setting update interval to %s seconds",
            POLL_INTERVAL_MOVING if is_moving else POLL_INTERVAL_STATIONARY,
        )
        self.async_set_updated_data(self.data)

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            data = await self._update_method()
            _LOGGER.debug("Updated data: %s", data)
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}")