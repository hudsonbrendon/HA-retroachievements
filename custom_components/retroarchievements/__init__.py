"""The RetroAchievements integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RetroAchievementsApiClient
from .const import CONF_USERNAME, DOMAIN, PLATFORMS, SERVICE_REFRESH
from .coordinator import RetroAchievementsDataUpdateCoordinator

type RetroAchievementsConfigEntry = ConfigEntry[RetroAchievementsDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: RetroAchievementsConfigEntry
) -> bool:
    """Set up RetroAchievements from a config entry."""
    api_client = RetroAchievementsApiClient(
        username=entry.data[CONF_USERNAME],
        api_key=entry.data[CONF_API_KEY],
        session=async_get_clientsession(hass),
    )

    coordinator = RetroAchievementsDataUpdateCoordinator(
        hass=hass, api_client=api_client, entry=entry
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_refresh_service(hass)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


def _async_register_refresh_service(hass: HomeAssistant) -> None:
    """Register the refresh service (once for the whole integration)."""
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        return

    async def _handle_refresh(_call: ServiceCall) -> None:
        entries: list[RetroAchievementsConfigEntry] = hass.config_entries.async_entries(
            DOMAIN
        )
        loaded = [e for e in entries if getattr(e, "runtime_data", None)]
        if not loaded:
            msg = "No loaded RetroAchievements entries to refresh"
            raise HomeAssistantError(msg)
        for entry in loaded:
            await entry.runtime_data.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_REFRESH, _handle_refresh)


async def async_unload_entry(
    hass: HomeAssistant, entry: RetroAchievementsConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        remaining = [
            e
            for e in hass.config_entries.async_entries(DOMAIN)
            if e.entry_id != entry.entry_id and getattr(e, "runtime_data", None)
        ]
        if not remaining and hass.services.has_service(DOMAIN, SERVICE_REFRESH):
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
    return unload_ok


async def update_listener(
    hass: HomeAssistant, entry: RetroAchievementsConfigEntry
) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)
