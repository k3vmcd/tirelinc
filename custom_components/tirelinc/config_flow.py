"""Config flow for TireLinc integration."""
from __future__ import annotations
import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
    async_ble_device_from_address,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_SENSORS, CONF_LEARNING_MODE, DISCOVERY_TIMEOUT, MAX_TIRES
from .parser import TireLincBluetoothDeviceData

_LOGGER = logging.getLogger(__name__)

class TireLincConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TireLinc."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._device_data = TireLincBluetoothDeviceData()
        self._discovered_sensors: dict[str, str] = {}
        self._learning_mode = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self._learning_mode = user_input[CONF_LEARNING_MODE]
            if self._discovery_info:
                return await self._process_discovery()
            return await self.async_step_bluetooth_discovery()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_LEARNING_MODE, default=True): bool,
            }),
        )

    async def async_step_bluetooth_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle bluetooth discovery step."""
        _LOGGER.debug("Starting Bluetooth discovery")
        
        discovered_devices = async_discovered_service_info(self.hass)
        _LOGGER.debug("Found %d Bluetooth devices", len(discovered_devices))
        
        for info in discovered_devices:
            _LOGGER.debug("Checking device: %s (%s)", info.name, info.address)
            if info.name and info.name.startswith("TireLinc"):
                _LOGGER.debug("Found TireLinc device: %s", info.name)
                discovery_info = info
                return await self.async_step_bluetooth(discovery_info)

        _LOGGER.debug("No TireLinc devices found")
        return self.async_abort(reason="no_devices_found")

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug("Bluetooth discovery step: %s", discovery_info.address)
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        
        self._discovery_info = discovery_info
        name = discovery_info.name or "TireLinc"
        address_suffix = discovery_info.address.replace(":", "")[-4:].upper()
        self.context["title_placeholders"] = {"name": f"{name} {address_suffix}"}
        
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm bluetooth discovery."""
        _LOGGER.debug("Bluetooth confirm step")
        if user_input is not None:
            return await self.async_step_user()

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def _process_discovery(self) -> FlowResult:
        """Process the discovery."""
        _LOGGER.debug("Processing discovery for: %s", self._discovery_info.address)
        if self._learning_mode:
            discovered = await self._discover_sensors()
            if discovered:
                return await self.async_step_configure_sensors()
            return self.async_abort(reason="no_sensors_found")
        return await self.async_step_configure_sensors()

    async def _discover_sensors(self) -> bool:
        """Discover tire sensors."""
        if not self._discovery_info:
            return False

        device = async_ble_device_from_address(
            self.hass, 
            self._discovery_info.address, 
            connectable=True
        )
        if not device:
            return False

        # Enable learning mode and poll device
        self._device_data.set_learning_mode(True)
        await self._device_data.async_poll(device)
        discovered = self._device_data.discovered_sensors
        
        if not discovered:
            return False

        # Store discovered sensors
        self._discovered_sensors = {
            sensor_id: f"Sensor {i+1} ({sensor_id})"
            for i, sensor_id in enumerate(discovered)
        }
        return True

    async def async_step_configure_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let user configure discovered sensors."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=self.context["title_placeholders"]["name"],
                data={
                    CONF_ADDRESS: self._discovery_info.address,
                    CONF_SENSORS: user_input,
                }
            )

        if not self._discovered_sensors:
            errors["base"] = "no_sensors"
            return self.async_abort(reason="no_sensors_found")

        options = {k: v for k, v in self._discovered_sensors.items()}
        schema = {}
        
        # Create dropdown for each tire position
        for i in range(1, len(self._discovered_sensors) + 1):
            schema[vol.Required(f"tire_{i}", default=list(options.keys())[i-1])] = vol.In(options)

        return self.async_show_form(
            step_id="configure_sensors",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "sensors": ", ".join(self._discovered_sensors.values())
            },
        )