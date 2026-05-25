"""RetroAchievements sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
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
    LOGGER,
)
from .coordinator import RetroAchievementsDataUpdateCoordinator

# Coordinator already fetches everything; entity reads are local. No throttling.
PARALLEL_UPDATES = 0

_STAT_KEYS = frozenset(
    {
        "hardcore_points",
        "softcore_points",
        "games_mastered",
        "games_beaten",
        "games_played",
        "awards_total",
    }
)

_SOCIAL_KEYS = frozenset(
    {
        "following_count",
        "followers_count",
        "set_requests",
        "achievements_earned_today",
        "recent_game_awards",
        "top_ten",
    }
)

USER_SENSORS = [
    SensorEntityDescription(
        key="username",
        translation_key="username",
        icon="mdi:account",
    ),
    SensorEntityDescription(
        key="total_points",
        translation_key="total_points",
        icon="mdi:trophy",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="true_points",
        translation_key="true_points",
        icon="mdi:trophy-award",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rank",
        translation_key="rank",
        icon="mdi:podium",
        state_class=SensorStateClass.MEASUREMENT,
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
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="recently_played",
        translation_key="recently_played",
        icon="mdi:history",
    ),
    SensorEntityDescription(
        key="hardcore_points",
        translation_key="hardcore_points",
        icon="mdi:trophy",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="softcore_points",
        translation_key="softcore_points",
        icon="mdi:trophy-outline",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="games_mastered",
        translation_key="games_mastered",
        icon="mdi:medal",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="games_beaten",
        translation_key="games_beaten",
        icon="mdi:flag-checkered",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="games_played",
        translation_key="games_played",
        icon="mdi:gamepad-square",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="awards_total",
        translation_key="awards_total",
        icon="mdi:medal-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="following_count",
        translation_key="following_count",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="followers_count",
        translation_key="followers_count",
        icon="mdi:account-multiple-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="set_requests",
        translation_key="set_requests",
        icon="mdi:playlist-plus",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="achievements_earned_today",
        translation_key="achievements_earned_today",
        icon="mdi:calendar-today",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="recent_game_awards",
        translation_key="recent_game_awards",
        icon="mdi:medal",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="top_ten",
        translation_key="top_ten",
        icon="mdi:trophy-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RetroAchievements sensors based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator = entry.runtime_data

    entities = []
    if coordinator.data and "user_summary" in coordinator.data:
        user_data = coordinator.data["user_summary"]
        for description in USER_SENSORS:
            entities.append(
                RetroAchievementsUserSensor(
                    coordinator=coordinator,
                    username=username,
                    description=description,
                )
            )
        if "RecentAchievements" in user_data:
            entities.append(
                RetroAchievementsRecentAchievementsSensor(
                    coordinator=coordinator,
                    username=username,
                )
            )
        entities.append(
            RetroAchievementsAOTWSensor(
                coordinator=coordinator,
                username=username,
            )
        )
        if "RecentlyPlayed" in user_data:
            for game in user_data["RecentlyPlayed"]:
                entities.append(
                    RetroAchievementsRecentlyPlayedSensor(
                        coordinator=coordinator,
                        username=username,
                        game_data=game,
                    )
                )

    if coordinator.data and "recent_games" in coordinator.data:
        for game in coordinator.data["recent_games"]:
            entities.append(RetroAchievementsGameSensor(coordinator, username, game))

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

        if self._key != "username" and hasattr(description, "entity_category"):
            self._attr_entity_category = description.entity_category

        self._attr_has_entity_name = True

    @property
    def native_value(self):
        if not self.coordinator.data or "user_summary" not in self.coordinator.data:
            return None
        data = self.coordinator.data["user_summary"]
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
            if data.get("RecentlyPlayed") and len(data.get("RecentlyPlayed", [])) > 0:
                recent_game = data["RecentlyPlayed"][0]
                return f"{recent_game.get('Title')} - {recent_game.get('ConsoleName')}"
            return "None"
        if self._key in _STAT_KEYS:
            return self._stat_value()
        if self._key in _SOCIAL_KEYS:
            return self._social_value()
        return None

    def _social_value(self):
        """Return a value for social keys sourced from top-level coordinator data."""
        data = self.coordinator.data
        following = data.get("following") or {}
        followers = data.get("followers") or {}
        set_requests = data.get("set_requests") or {}
        earned_on_day = data.get("earned_on_day") or []
        recent_game_awards = data.get("recent_game_awards") or {}
        top_ten = data.get("top_ten") or []
        if self._key == "following_count":
            return following.get("Total", 0)
        if self._key == "followers_count":
            return followers.get("Total", 0)
        if self._key == "set_requests":
            return set_requests.get("TotalRequests", 0)
        if self._key == "achievements_earned_today":
            return len(earned_on_day)
        if self._key == "recent_game_awards":
            return recent_game_awards.get("Total", 0)
        if self._key == "top_ten":
            return top_ten[0].get("1") if top_ten else None
        return None

    def _stat_value(self):
        """Return a value for stat keys sourced from top-level coordinator data."""
        points = self.coordinator.data.get("user_points") or {}
        awards = self.coordinator.data.get("awards") or {}
        progress = self.coordinator.data.get("completion_progress") or {}
        return {
            "hardcore_points": points.get("Points", 0),
            "softcore_points": points.get("SoftcorePoints", 0),
            "games_mastered": awards.get("MasteryAwardsCount", 0),
            "games_beaten": (
                awards.get("BeatenHardcoreAwardsCount", 0)
                + awards.get("BeatenSoftcoreAwardsCount", 0)
            ),
            "games_played": progress.get("Total", 0),
            "awards_total": awards.get("TotalAwardsCount", 0),
        }[self._key]

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

        if self._key in _SOCIAL_KEYS:
            return self._social_attributes()

        return {}

    def _social_attributes(self):
        """Return state attributes for social sensors."""
        data = self.coordinator.data
        if self._key == "following_count":
            return {"users": (data.get("following") or {}).get("Results", [])}
        if self._key == "followers_count":
            return {"users": (data.get("followers") or {}).get("Results", [])}
        if self._key == "set_requests":
            set_requests = data.get("set_requests") or {}
            return {
                "points_for_next": set_requests.get("PointsForNext"),
                "requested_sets": set_requests.get("RequestedSets", []),
            }
        if self._key == "achievements_earned_today":
            return {"achievements": data.get("earned_on_day") or []}
        if self._key == "recent_game_awards":
            return {"awards": (data.get("recent_game_awards") or {}).get("Results", [])}
        if self._key == "top_ten":
            return {
                "users": [
                    {
                        "username": entry.get("1"),
                        "points": entry.get("2"),
                        "true_points": entry.get("3"),
                        "id": entry.get("4"),
                    }
                    for entry in (data.get("top_ten") or [])
                ]
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
        if game_achievements:
            attrs["achievements"] = game_achievements
        leaderboards = (
            (self.coordinator.data or {})
            .get("Leaderboards", {})
            .get(str(self._game_id), {})
        )
        results = (
            leaderboards.get("Results") if isinstance(leaderboards, dict) else None
        )
        if results:
            attrs["leaderboards"] = results
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

        LOGGER.debug(
            "Creating recently played sensor for game: %s (ID: %s, Console: %s)",
            self._game_title,
            self._game_id,
            self._console_name,
        )

        self._attr_unique_id = f"{DOMAIN}_{username}_recently_played_{self._game_id}"

        self._attr_name = f"{self._game_title} - {self._console_name}"
        self._attr_icon = "mdi:gamepad-variant"

        self._attr_has_entity_name = False

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
        return f"{self._game_title} - {self._console_name}"

    @property
    def extra_state_attributes(self):
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


class RetroAchievementsAOTWSensor(RetroAchievementsBaseSensor):
    """Representation of the Achievement of the Week sensor."""

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_unique_id = f"{DOMAIN}_{username}_aotw"
        self._attr_translation_key = "aotw"
        self._attr_has_entity_name = True
        self._attr_icon = "mdi:calendar-star"

    @property
    def native_value(self):
        """Return the AOTW title or None."""
        aotw = (self.coordinator.data or {}).get("aotw") or {}
        return (aotw.get("Achievement") or {}).get("Title")

    @property
    def extra_state_attributes(self):
        """Return AOTW attributes."""
        aotw = (self.coordinator.data or {}).get("aotw") or {}
        ach = aotw.get("Achievement") or {}
        game = aotw.get("Game") or {}
        badge = ach.get("BadgeName")
        return {
            "achievement_id": ach.get("ID"),
            "description": ach.get("Description"),
            "points": ach.get("Points"),
            "badge_url": (
                f"https://retroachievements.org/Badge/{badge}.png" if badge else None
            ),
            "game_id": game.get("ID"),
            "game_title": game.get("Title"),
            "console_name": game.get("ConsoleName"),
            "week_start": aotw.get("StartAt"),
            "author": ach.get("Author"),
        }
