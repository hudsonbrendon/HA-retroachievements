"""RetroAchievements sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACHIEVEMENTS_EARNED,
    ATTR_ACHIEVEMENTS_TOTAL,
    ATTR_COMPLETION_PERCENTAGE,
    ATTR_CONSOLE_NAME,
    ATTR_GAME_ID,
    ATTR_GAME_TITLE,
    ATTR_POINTS_EARNED,
    ATTR_POINTS_TOTAL,
    CONF_USERNAME,
    DOMAIN,
)
from .coordinator import RetroAchievementsDataUpdateCoordinator

# Define sensor descriptions for user profile
USER_SENSORS = [
    SensorEntityDescription(
        key="username",
        translation_key="username",
        icon="mdi:account",
        # Removed entity_category=EntityCategory.DIAGNOSTIC to move from diagnostic section
    ),
    SensorEntityDescription(
        key="total_points",
        translation_key="total_points",
        icon="mdi:trophy",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="true_points",
        translation_key="true_points",
        icon="mdi:trophy-award",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rank",
        translation_key="rank",
        icon="mdi:podium",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Currently playing sensor removed
    SensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:account-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rich_presence",
        translation_key="rich_presence",
        icon="mdi:gamepad-variant",
    ),
    SensorEntityDescription(
        key="recently_played_count",
        translation_key="recently_played_count",
        icon="mdi:controller",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Add the recently_played sensor here as part of the user sensors
    SensorEntityDescription(
        key="recently_played",
        translation_key="recently_played",
        icon="mdi:history",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RetroAchievements sensors based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    # Create device for the user - this will group all user-related sensors
    if coordinator.data and "user_summary" in coordinator.data:
        user_data = coordinator.data["user_summary"]
        # Create user sensors
        for description in USER_SENSORS:
            entities.append(
                RetroAchievementsUserSensor(
                    coordinator=coordinator,
                    username=username,
                    description=description,
                )
            )
        # Create recent achievements sensor
        if "RecentAchievements" in user_data:
            entities.append(
                RetroAchievementsRecentAchievementsSensor(
                    coordinator=coordinator,
                    username=username,
                )
            )
        # Create recently played games sensors
        if "RecentlyPlayed" in user_data:
            for game in user_data["RecentlyPlayed"]:
                entities.append(
                    RetroAchievementsRecentlyPlayedSensor(
                        coordinator=coordinator,
                        username=username,
                        game_data=game,
                    )
                )

            # Remove RecentlyPlayedGameSensor since we're now handling recently_played in USER_SENSORS
            # The recently_played sensor will now be created with other user sensors

    # Create game sensors
    if coordinator.data and "recent_games" in coordinator.data:
        for game in coordinator.data["recent_games"]:
            entities.append(RetroAchievementsGameSensor(coordinator, username, game))

    # Add entities
    async_add_entities(entities, True)


class RetroAchievementsBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for RetroAchievements sensors."""

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
        description: SensorEntityDescription = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.username = username
        if description:
            self.entity_description = description
            self._attr_unique_id = f"{DOMAIN}_{self.username}_{description.key}"
            self._attr_has_entity_name = True
            self._attr_translation_key = description.translation_key
        # Create a device for the user profile
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{self.username}")},
            manufacturer="RetroAchievements",
            name=f"RetroAchievements {self.username}",
            configuration_url=f"https://retroachievements.org/user/{self.username}",
            model="User Profile",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )


class RetroAchievementsUserSensor(RetroAchievementsBaseSensor):
    """Representation of a RetroAchievements user sensor."""

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize user sensor."""
        super().__init__(coordinator, username, description)
        self._key = description.key
        # Special handling for username sensor - set entity_category for all other sensors
        # but not for the username sensor
        if self._key != "username" and hasattr(description, "entity_category"):
            self._attr_entity_category = description.entity_category
        # Keep translation_key for all sensors to ensure proper naming in the UI
        # For username sensor, we want it to be shown as "Username"/"Usuario" instead of the actual username
        # This ensures that the entity will be named according to the translation files
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data or "user_summary" not in self.coordinator.data:
            return None
        data = self.coordinator.data["user_summary"]
        # Get value based on sensor key
        if self._key == "username":
            return self.username
        if self._key == "total_points":
            return data.get("TotalPoints", 0)
        if self._key == "true_points":
            return data.get("TotalTruePoints", 0)
        if self._key == "rank":
            return data.get("Rank", 0)
        if self._key == "status":
            return data.get("Status", "Unknown")
        if self._key == "rich_presence":
            return data.get("RichPresenceMsg", "")
        if self._key == "recently_played_count":
            return len(self.coordinator.data.get("recent_games", []))
        if self._key == "recently_played":
            # Return the title of the most recently played game if available
            if data.get("RecentlyPlayed") and len(data.get("RecentlyPlayed", [])) > 0:
                recent_game = data["RecentlyPlayed"][0]
                return f"{recent_game.get('Title')} - {recent_game.get('ConsoleName')}"
            return "None"
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data or "user_summary" not in self.coordinator.data:
            return {}
        data = self.coordinator.data["user_summary"]

        # Default user attributes
        if self._key == "username":
            return {
                "id": data.get("ID"),
                "member_since": data.get("MemberSince"),
                "profile_url": f"https://retroachievements.org/user/{self.username}",
                "profile_pic": f"https://retroachievements.org{data.get('UserPic', '')}",
            }

        # Add special attributes for the recently_played sensor
        if (
            self._key == "recently_played"
            and data.get("RecentlyPlayed")
            and len(data.get("RecentlyPlayed", [])) > 0
        ):
            recent_game = data["RecentlyPlayed"][0]
            return {
                "game_id": recent_game.get("GameID"),
                "console_id": recent_game.get("ConsoleID"),
                "console_name": recent_game.get("ConsoleName"),
                "title": recent_game.get("Title"),
                "image_icon": f"https://retroachievements.org{recent_game.get('ImageIcon', '')}",
                "image_title": f"https://retroachievements.org{recent_game.get('ImageTitle', '')}",
                "image_ingame": f"https://retroachievements.org{recent_game.get('ImageIngame', '')}",
                "image_boxart": f"https://retroachievements.org{recent_game.get('ImageBoxArt', '')}",
                "last_played": recent_game.get("LastPlayed"),
                "achievements_total": recent_game.get("AchievementsTotal", 0),
                "game_url": f"https://retroachievements.org/game/{recent_game.get('GameID')}",
            }

        return {}


class RetroAchievementsRecentAchievementsSensor(RetroAchievementsBaseSensor):
    """Representation of a RetroAchievements recent achievements sensor."""

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_unique_id = f"{DOMAIN}_{self.username}_recent_achievements"
        self._attr_translation_key = "recent_achievements"
        self._attr_has_entity_name = True
        self._attr_icon = "mdi:trophy-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the number of recent achievements."""
        if (
            not self.coordinator.data
            or "RecentAchievements" not in self.coordinator.data
        ):
            return 0
        # Count all achievements in all games
        count = 0
        for game_id, achievements in self.coordinator.data[
            "RecentAchievements"
        ].items():
            count += len(achievements)
        return count

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if (
            not self.coordinator.data
            or "RecentAchievements" not in self.coordinator.data
        ):
            return {}
        # Extract recent achievements
        recent_achievements = []
        for game_id, achievements in self.coordinator.data[
            "RecentAchievements"
        ].items():
            for ach_id, achievement in achievements.items():
                achievement_data = {
                    "id": achievement.get("ID"),
                    "title": achievement.get("Title"),
                    "description": achievement.get("Description"),
                    "points": achievement.get("Points"),
                    "game": achievement.get("GameTitle"),
                    "date_awarded": achievement.get("DateAwarded"),
                    "image": f"https://retroachievements.org/Badge/{achievement.get('BadgeName')}.png",
                    "url": f"https://retroachievements.org/achievement/{achievement.get('ID')}",
                }
                recent_achievements.append(achievement_data)
        return {"achievements": recent_achievements}


class RetroAchievementsGameSensor(RetroAchievementsBaseSensor):
    """Representation of a RetroAchievements game sensor."""

    def __init__(self, coordinator, username, game_data):
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._game_data = game_data
        self._game_id = game_data.get("GameID")
        self._game_title = game_data.get("Title")
        self._console_name = game_data.get("ConsoleName")

        self._attr_unique_id = f"{DOMAIN}_{self.username}_game_{self._game_id}"
        self._attr_name = self._game_title
        self._attr_icon = "mdi:gamepad-variant"
        self._attr_has_entity_name = False
        self._attr_translation_key = "game"

        # Create a device for each game
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self.username}_game_{self._game_id}")},
            via_device=(DOMAIN, f"{self.username}"),  # Link to user device
            manufacturer="RetroAchievements",
            name=self._game_title,
            model=self._console_name,
            configuration_url=f"https://retroachievements.org/game/{self._game_id}",
        )

    def _get_achievement_data(self):
        """Get achievement data for this game from coordinator data."""
        if not self.coordinator.data or "Awarded" not in self.coordinator.data:
            return {}
        # Convert game ID to string as the API returns it as a string key in Awarded dict
        game_id_str = str(self._game_id)
        return self.coordinator.data.get("Awarded", {}).get(game_id_str, {})

    @property
    def native_value(self):
        """Return the state of the sensor - completion percentage."""
        achievement_data = self._get_achievement_data()
        if achievement_data:
            total = achievement_data.get("NumPossibleAchievements", 0)
            earned = achievement_data.get("NumAchieved", 0)
            if total > 0:
                return f"{round((earned / total) * 100)}%"
        return "0%"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self._game_data:
            return {}
        achievement_data = self._get_achievement_data()
        # Find game-specific achievements in the coordinator data
        game_achievements = []
        if (
            self.coordinator.data
            and "RecentAchievements" in self.coordinator.data
            and str(self._game_id) in self.coordinator.data["RecentAchievements"]
        ):
            achievements = self.coordinator.data["RecentAchievements"][
                str(self._game_id)
            ]
            for ach_id, achievement in achievements.items():
                game_achievements.append(
                    {
                        "id": achievement.get("ID"),
                        "title": achievement.get("Title"),
                        "description": achievement.get("Description"),
                        "points": achievement.get("Points"),
                        "date_awarded": achievement.get("DateAwarded"),
                        "image": f"https://retroachievements.org/Badge/{achievement.get('BadgeName')}.png",
                    }
                )
        # Build the attributes dictionary
        attrs = {
            ATTR_GAME_ID: self._game_id,
            ATTR_GAME_TITLE: self._game_title,
            ATTR_CONSOLE_NAME: self._game_data.get("ConsoleName"),
            "console_id": self._game_data.get("ConsoleID"),
            "last_played": self._game_data.get("LastPlayed"),
            "image_icon": f"https://retroachievements.org{self._game_data.get('ImageIcon', '')}",
            "image_boxart": f"https://retroachievements.org{self._game_data.get('ImageBoxArt', '')}",
            "game_url": f"https://retroachievements.org/game/{self._game_id}",
        }
        # Add achievement data if available
        if achievement_data:
            attrs.update(
                {
                    ATTR_ACHIEVEMENTS_TOTAL: achievement_data.get(
                        "NumPossibleAchievements", 0
                    ),
                    ATTR_ACHIEVEMENTS_EARNED: achievement_data.get("NumAchieved", 0),
                    ATTR_POINTS_TOTAL: achievement_data.get("PossibleScore", 0),
                    ATTR_POINTS_EARNED: achievement_data.get("ScoreAchieved", 0),
                    "hardcore_achievements_earned": achievement_data.get(
                        "NumAchievedHardcore", 0
                    ),
                    "hardcore_points_earned": achievement_data.get(
                        "ScoreAchievedHardcore", 0
                    ),
                    ATTR_COMPLETION_PERCENTAGE: round(
                        (
                            achievement_data.get("NumAchieved", 0)
                            / max(achievement_data.get("NumPossibleAchievements", 1), 1)
                        )
                        * 100
                    ),
                }
            )
        # Add recent achievements for this game
        if game_achievements:
            attrs["achievements"] = game_achievements
        return attrs


class RetroAchievementsRecentlyPlayedSensor(RetroAchievementsBaseSensor):
    """Representation of a RetroAchievements recently played game sensor."""

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
        game_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._game_data = game_data
        self._game_id = game_data.get("GameID")
        self._game_title = game_data.get("Title")
        self._console_name = game_data.get("ConsoleName")

        # Add debug logging to help troubleshoot
        from .const import LOGGER

        LOGGER.debug(
            "Creating recently played sensor for game: %s (ID: %s, Console: %s)",
            self._game_title,
            self._game_id,
            self._console_name,
        )

        # Create unique_id based on username and game_id
        self._attr_unique_id = f"{DOMAIN}_{username}_recently_played_{self._game_id}"

        # Name format: Title - ConsoleName
        self._attr_name = f"{self._game_title} - {self._console_name}"
        self._attr_icon = "mdi:gamepad-variant"

        # Make sure we don't use translation_key if we're setting a specific name
        self._attr_has_entity_name = False
        # self._attr_translation_key = "recently_played"  # Comment out as we're using a specific name

        # Create a device for this recently played game linked to the user profile
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{username}_recently_played_{self._game_id}")},
            via_device=(DOMAIN, f"{username}"),  # Link to user device
            manufacturer="RetroAchievements",
            name=f"{self._game_title} ({self._console_name})",
            model="Recently Played Game",
            configuration_url=f"https://retroachievements.org/game/{self._game_id}",
        )

    @property
    def native_value(self):
        """Return the name of the recently played game."""
        return f"{self._game_title} - {self._console_name}"

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the recently played game."""
        return {
            "game_id": self._game_id,
            "console_id": self._game_data.get("ConsoleID"),
            "console_name": self._console_name,
            "title": self._game_title,
            "image_icon": f"https://retroachievements.org{self._game_data.get('ImageIcon', '')}",
            "image_title": f"https://retroachievements.org{self._game_data.get('ImageTitle', '')}",
            "image_ingame": f"https://retroachievements.org{self._game_data.get('ImageIngame', '')}",
            "image_boxart": f"https://retroachievements.org{self._game_data.get('ImageBoxArt', '')}",
            "last_played": self._game_data.get("LastPlayed"),
            "achievements_total": self._game_data.get("AchievementsTotal", 0),
            "game_url": f"https://retroachievements.org/game/{self._game_id}",
        }
