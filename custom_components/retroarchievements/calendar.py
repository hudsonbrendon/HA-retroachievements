"""RetroAchievements calendar platform: recent unlocks as calendar events."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_USERNAME, DOMAIN
from .coordinator import RetroAchievementsDataUpdateCoordinator

# Coordinator already fetches everything; entity reads are local. No throttling.
PARALLEL_UPDATES = 0

# Each unlock is rendered as a short event of this duration.
_EVENT_DURATION = timedelta(minutes=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RetroAchievements calendar based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator = entry.runtime_data
    async_add_entities([RetroAchievementsAchievementsCalendar(coordinator, username)])


def _parse_award_dt(value: str | None) -> datetime | None:
    """Parse a RetroAchievements unlock timestamp into an aware datetime."""
    if not value:
        return None
    parsed = dt_util.parse_datetime(str(value))
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return parsed


class RetroAchievementsAchievementsCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar of recently unlocked achievements."""

    _attr_has_entity_name = True
    _attr_translation_key = "achievements"
    _attr_icon = "mdi:calendar-check"

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_achievements_calendar"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{username}")},
            manufacturer="RetroAchievements",
            name=f"RetroAchievements {username}",
            configuration_url=f"https://retroachievements.org/user/{username}",
            model="User Profile",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    def _build_events(self) -> list[CalendarEvent]:
        """Build calendar events from the coordinator's unlock history."""
        unlocks = (self.coordinator.data or {}).get("earned_between") or []
        events: list[CalendarEvent] = []
        for unlock in unlocks:
            if not isinstance(unlock, dict):
                continue
            start = _parse_award_dt(unlock.get("Date") or unlock.get("DateAwarded"))
            if start is None:
                continue
            game = unlock.get("GameTitle")
            title = unlock.get("Title") or "Achievement"
            summary = f"{title} ({game})" if game else title
            description = unlock.get("Description")
            points = unlock.get("Points")
            if points is not None:
                description = f"{description or ''} [{points} pts]".strip()
            events.append(
                CalendarEvent(
                    start=start,
                    end=start + _EVENT_DURATION,
                    summary=summary,
                    description=description or None,
                    uid=str(unlock.get("ID")) if unlock.get("ID") else None,
                )
            )
        events.sort(key=lambda event: event.start)
        return events

    @property
    def event(self) -> CalendarEvent | None:
        """Return the most recent unlock event for state display."""
        events = self._build_events()
        return events[-1] if events else None

    async def async_get_events(
        self,
        hass: HomeAssistant,  # noqa: ARG002
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events within the requested time range."""
        return [
            event
            for event in self._build_events()
            if event.start < end_date and event.end > start_date
        ]
