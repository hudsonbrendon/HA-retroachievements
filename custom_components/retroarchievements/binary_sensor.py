"""Binary sensors for the RetroAchievements integration."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_USERNAME, DOMAIN
from .coordinator import RetroAchievementsDataUpdateCoordinator


def _user_device_info(username: str) -> DeviceInfo:
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, f"{username}")},
        manufacturer="RetroAchievements",
        name=f"RetroAchievements {username}",
        configuration_url=f"https://retroachievements.org/user/{username}",
        model="User Profile",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator: RetroAchievementsDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]["coordinator"]
    async_add_entities(
        [
            RetroAchievementsIsGamingBinarySensor(coordinator, username),
            RetroAchievementsAOTWUnlockedBinarySensor(coordinator, username),
        ],
        True,
    )


class RetroAchievementsIsGamingBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that is ON while the user is actively gaming."""

    _attr_has_entity_name = True
    _attr_translation_key = "is_gaming"
    _attr_icon = "mdi:gamepad-circle"

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        super().__init__(coordinator)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_is_gaming"
        self._attr_device_info = _user_device_info(username)

    @property
    def is_on(self) -> bool:
        data = (self.coordinator.data or {}).get("user_summary") or {}
        rich = (data.get("RichPresenceMsg") or "").strip()
        status = data.get("Status", "")
        if not rich or status != "Online":
            return False
        last_activity = data.get("LastActivity") or {}
        ts = last_activity.get("timestamp") or last_activity.get("lastupdate")
        if not ts:
            return False
        try:
            normalized = ts.replace("Z", "+00:00").replace(" ", "T")
            last = datetime.fromisoformat(normalized)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            return False
        threshold_seconds = self.coordinator._idle_threshold_minutes * 60
        now = datetime.now(timezone.utc)
        return (now - last).total_seconds() <= threshold_seconds


class RetroAchievementsAOTWUnlockedBinarySensor(
    CoordinatorEntity, BinarySensorEntity
):
    """Binary sensor that is ON when the user has unlocked the current AOTW."""

    _attr_has_entity_name = True
    _attr_translation_key = "aotw_unlocked"

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        super().__init__(coordinator)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_aotw_unlocked"
        self._attr_device_info = _user_device_info(username)

    @property
    def icon(self) -> str:
        return "mdi:trophy" if self.is_on else "mdi:trophy-broken"

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_aotw_unlocked()
