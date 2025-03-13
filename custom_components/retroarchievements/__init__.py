"""The RetroAchievements integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RetroAchievementsApiClient
from .const import CONF_API_KEY, CONF_USERNAME, DOMAIN, LOGGER

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RetroAchievements from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client instance
    session = async_get_clientsession(hass)
    client = RetroAchievementsApiClient(
        username=entry.data[CONF_USERNAME],
        api_key=entry.data[CONF_API_KEY],
        session=session,
    )

    # Store API client and config entry in hass data
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "config": entry.data,
    }

    # Load platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for config entry changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
