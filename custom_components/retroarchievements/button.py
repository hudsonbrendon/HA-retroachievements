"""Button platform for the RetroAchievements integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_USERNAME, DOMAIN
from .coordinator import RetroAchievementsDataUpdateCoordinator
from .entity import user_device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the refresh button based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator: RetroAchievementsDataUpdateCoordinator = entry.runtime_data
    async_add_entities([RetroAchievementsRefreshButton(coordinator, username)])


class RetroAchievementsRefreshButton(CoordinatorEntity, ButtonEntity):
    """Button that triggers an immediate data refresh."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        super().__init__(coordinator)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_refresh"
        self._attr_device_info = user_device_info(username)

    async def async_press(self) -> None:
        """Refresh the coordinator data."""
        await self.coordinator.async_request_refresh()
