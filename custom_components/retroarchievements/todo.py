"""Todo platform exposing the user's 'Want to Play' backlog (read-only)."""

from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    """Set up the Want to Play todo list based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator: RetroAchievementsDataUpdateCoordinator = entry.runtime_data
    async_add_entities([RetroAchievementsWantToPlayTodoList(coordinator, username)])


class RetroAchievementsWantToPlayTodoList(CoordinatorEntity, TodoListEntity):
    """Read-only todo list mirroring the RetroAchievements backlog."""

    _attr_has_entity_name = True
    _attr_translation_key = "want_to_play"
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        super().__init__(coordinator)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_want_to_play"
        self._attr_device_info = user_device_info(username)

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return the backlog games as todo items."""
        want_to_play = (self.coordinator.data or {}).get("want_to_play") or {}
        items: list[TodoItem] = []
        for game in want_to_play.get("Results") or []:
            game_id = game.get("GameID")
            if game_id is None:
                continue
            title = game.get("Title") or "Unknown game"
            console = game.get("ConsoleName")
            summary = f"{title} ({console})" if console else title
            items.append(
                TodoItem(
                    uid=str(game_id),
                    summary=summary,
                    status=TodoItemStatus.NEEDS_ACTION,
                )
            )
        return items
