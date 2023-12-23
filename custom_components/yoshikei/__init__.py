"""The yoshikei integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, Yoshikei

PLATFORMS: list[Platform] = [Platform.CALENDAR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up yoshikei from a config entry."""
    _LOGGER.debug("Setting up yoshikei platform %s", entry.data)

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = Yoshikei(
        entry.data["username"], entry.data["password"]
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
