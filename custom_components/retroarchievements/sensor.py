"""RetroAchievements sensor platform."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import RetroAchievementsApiClient
from .const import (
    ATTR_ACHIEVEMENTS_EARNED,
    ATTR_ACHIEVEMENTS_TOTAL,
    ATTR_COMPLETION_PERCENTAGE,
    ATTR_CONSOLE_NAME,
    ATTR_GAME_ID,
    ATTR_GAME_TITLE,
    ATTR_POINTS_EARNED,
    ATTR_POINTS_TOTAL,
    CONF_API_KEY,
    CONF_USERNAME,
    DOMAIN,
    LOGGER,
)

# Define sensor descriptions for user profile
USER_SENSORS = [
    SensorEntityDescription(
        key="total_points",
        name="Total Points",
        icon="mdi:trophy",
    ),
    SensorEntityDescription(
        key="true_points",
        name="True Points",
        icon="mdi:trophy-award",
    ),
    SensorEntityDescription(
        key="rank",
        name="Rank",
        icon="mdi:podium",
    ),
    SensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:account-check",
    ),
    SensorEntityDescription(
        key="rich_presence",
        name="Rich Presence",
        icon="mdi:gamepad-variant",
    ),
    SensorEntityDescription(
        key="recently_played_count",
        name="Recently Played Games Count",
        icon="mdi:controller",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RetroAchievements sensors based on a config entry."""
    username = entry.data[CONF_USERNAME]
    api_key = entry.data[CONF_API_KEY]

    session = async_create_clientsession(hass)
    client = RetroAchievementsApiClient(
        username=username,
        api_key=api_key,
        session=session,
    )

    # Create coordinator to manage API calls
    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
        update_method=client.async_get_user_summary,
        update_interval=timedelta(minutes=30),  # Update every 30 minutes
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Create device for the user - this will group all user-related sensors
    if coordinator.data:
        # Create user sensors
        for description in USER_SENSORS:
            entities.append(
                RetroAchievementsUserSensor(
                    coordinator=coordinator,
                    entry=entry,
                    description=description,
                )
            )

        # Create recent achievements sensor
        if "RecentAchievements" in coordinator.data:
            entities.append(
                RetroAchievementsRecentAchievementsSensor(
                    coordinator=coordinator,
                    entry=entry,
                )
            )

    # Create game sensors
    if coordinator.data and "RecentlyPlayed" in coordinator.data:
        for game in coordinator.data["RecentlyPlayed"]:
            entities.append(RetroAchievementsGameSensor(coordinator, entry, game))

    # Add entities
    async_add_entities(entities, True)


class RetroAchievementsBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for RetroAchievements sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.username = entry.data[CONF_USERNAME]

        if description:
            self.entity_description = description
            self._attr_unique_id = f"{DOMAIN}_{self.username}_{description.key}"
            self._attr_name = f"{description.name}"

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
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize user sensor."""
        super().__init__(coordinator, entry, description)
        self._key = description.key

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        data = self.coordinator.data

        # Get value based on sensor key
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
            return len(data.get("RecentlyPlayed", []))

        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = self.coordinator.data

        if not data:
            return {}

        # Add common attributes to all user sensors
        attrs = {
            "id": data.get("ID"),
            "member_since": data.get("MemberSince"),
            "profile_url": f"https://retroachievements.org/user/{self.username}",
            "profile_pic": f"https://retroachievements.org{data.get('UserPic', '')}",
        }

        return attrs


class RetroAchievementsRecentAchievementsSensor(RetroAchievementsBaseSensor):
    """Representation of a RetroAchievements recent achievements sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self.username}_recent_achievements"
        self._attr_name = "Recent Achievements"
        self._attr_icon = "mdi:trophy-outline"

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
                recent_achievements.append(
                    {
                        "id": achievement.get("ID"),
                        "title": achievement.get("Title"),
                        "description": achievement.get("Description"),
                        "points": achievement.get("Points"),
                        "game": achievement.get("GameTitle"),
                        "date_awarded": achievement.get("DateAwarded"),
                        "image": f"https://retroachievements.org/Badge/{achievement.get('BadgeName')}.png",
                        "url": f"https://retroachievements.org/achievement/{achievement.get('ID')}",
                    }
                )

        return {"achievements": recent_achievements}


class RetroAchievementsGameSensor(RetroAchievementsBaseSensor):
    """Representation of a RetroAchievements game sensor."""

    def __init__(self, coordinator, entry, game_data):
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._game_data = game_data
        self._game_id = game_data.get("GameID")
        self._game_title = game_data.get("Title")
        self._console_name = game_data.get("ConsoleName")

        self._attr_unique_id = f"{DOMAIN}_{self.username}_game_{self._game_id}"
        self._attr_name = self._game_title
        self._attr_icon = "mdi:gamepad-variant"

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
