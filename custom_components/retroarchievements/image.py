"""Image platform: current game box art and last achievement badge."""

from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_USERNAME, DOMAIN
from .coordinator import RetroAchievementsDataUpdateCoordinator
from .entity import user_device_info

BASE_SITE_URL = "https://retroachievements.org"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the image entities based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator: RetroAchievementsDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]["coordinator"]
    async_add_entities(
        [
            RetroAchievementsBoxArtImage(hass, coordinator, username),
            RetroAchievementsLastBadgeImage(hass, coordinator, username),
        ]
    )


class _RetroAchievementsBaseImage(CoordinatorEntity, ImageEntity):
    """Base image entity that serves a coordinator-derived remote URL."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
        key: str,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_{key}"
        self._attr_device_info = user_device_info(username)
        self._last_url = self._compute_url()
        self._attr_image_last_updated = dt_util.utcnow()

    def _compute_url(self) -> str | None:
        """Return the current image URL. Overridden by subclasses."""
        raise NotImplementedError

    @property
    def image_url(self) -> str | None:
        return self._compute_url()

    @callback
    def _handle_coordinator_update(self) -> None:
        url = self._compute_url()
        if url != self._last_url:
            self._last_url = url
            self._attr_image_last_updated = dt_util.utcnow()
            self._cached_image = None
        super()._handle_coordinator_update()


class RetroAchievementsBoxArtImage(_RetroAchievementsBaseImage):
    """Box art of the most recently played game."""

    _attr_translation_key = "box_art"

    def __init__(self, hass, coordinator, username) -> None:
        super().__init__(hass, coordinator, username, "box_art")

    def _compute_url(self) -> str | None:
        data = (self.coordinator.data or {}).get("user_summary") or {}
        recently_played = data.get("RecentlyPlayed") or []
        if not recently_played:
            return None
        box_art = recently_played[0].get("ImageBoxArt")
        return f"{BASE_SITE_URL}{box_art}" if box_art else None


class RetroAchievementsLastBadgeImage(_RetroAchievementsBaseImage):
    """Badge of the most recently earned achievement."""

    _attr_translation_key = "last_badge"

    def __init__(self, hass, coordinator, username) -> None:
        super().__init__(hass, coordinator, username, "last_badge")

    def _compute_url(self) -> str | None:
        recent = (self.coordinator.data or {}).get("RecentAchievements") or {}
        latest: dict | None = None
        latest_date = ""
        for achievements in recent.values():
            if not isinstance(achievements, dict):
                continue
            for achievement in achievements.values():
                date = achievement.get("DateAwarded") or ""
                if latest is None or date >= latest_date:
                    latest = achievement
                    latest_date = date
        if not latest:
            return None
        badge = latest.get("BadgeName")
        return f"{BASE_SITE_URL}/Badge/{badge}.png" if badge else None
