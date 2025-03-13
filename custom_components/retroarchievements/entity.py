"""RetroAchievements entity base class."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import RetroAchievementsDataUpdateCoordinator


class RetroAchievementsEntity(
    CoordinatorEntity[RetroAchievementsDataUpdateCoordinator]
):
    """Base class for RetroAchievements entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"RetroAchievements - {coordinator.config_entry.data['username']}",
            manufacturer="RetroAchievements",
        )


class RetroAchievementsGameEntity(
    CoordinatorEntity[RetroAchievementsDataUpdateCoordinator]
):
    """Base class for RetroAchievements game entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        description: EntityDescription,
        game_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self.game_id = game_id
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{game_id}_{description.key}"
        )

        # Get game name from the coordinator data
        game_name = "Unknown Game"
        if self.coordinator.data and "monitored_games" in self.coordinator.data:
            game_data = self.coordinator.data["monitored_games"].get(game_id, {})
            if game_data and "info" in game_data:
                game_name = game_data["info"].get("Title", "Unknown Game")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.config_entry.entry_id}_{game_id}")},
            name=f"{game_name}",
            manufacturer="RetroAchievements",
            model=f"Game ID: {game_id}",
            via_device=(DOMAIN, coordinator.config_entry.entry_id),
        )
