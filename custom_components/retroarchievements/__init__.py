"""The RetroAchievements integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RetroAchievementsApiClient
from .const import CONF_USERNAME, DOMAIN, LOGGER, PLATFORMS
from .coordinator import RetroAchievementsDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RetroAchievements from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_client = RetroAchievementsApiClient(
        username=entry.data[CONF_USERNAME],
        api_key=entry.data[CONF_API_KEY],
        session=async_get_clientsession(hass),
    )

    coordinator = RetroAchievementsDataUpdateCoordinator(
        hass=hass, api_client=api_client, entry=entry
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api_client": api_client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)
