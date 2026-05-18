"""Data update coordinator for the RetroAchievements integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import RetroAchievementsApiClient
from .const import (
    CONF_GAMING_IDLE_THRESHOLD,
    DEFAULT_GAMING_IDLE_THRESHOLD,
    DOMAIN,
    EVENT_ACHIEVEMENT_UNLOCKED,
    EVENT_AOTW_CHANGED,
    LOGGER,
    UPDATE_INTERVAL,
)


class RetroAchievementsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RetroAchievements data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: RetroAchievementsApiClient,
        entry: ConfigEntry,
        update_interval: int = UPDATE_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        self.api_client = api_client
        self.entry = entry
        self.monitored_games: set[int] = set()
        self._previous_achievement_ids: set[int] = set()
        self._previous_aotw_id: int | None = None
        self._game_extended_cache: dict[int, dict] = {}
        self._first_run: bool = True
        self._idle_threshold_minutes: int = (entry.options or {}).get(
            CONF_GAMING_IDLE_THRESHOLD, DEFAULT_GAMING_IDLE_THRESHOLD
        )

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    @staticmethod
    def _extract_achievement_ids(user_summary: dict) -> set[int]:
        """Return set of achievement IDs across all games in RecentAchievements."""
        ids: set[int] = set()
        for _game_id, achievements in (
            (user_summary or {}).get("RecentAchievements") or {}
        ).items():
            for ach_id in (achievements or {}).keys():
                try:
                    ids.add(int(ach_id))
                except (TypeError, ValueError):
                    continue
        return ids

    @staticmethod
    def _find_achievement(
        ach_id: int, user_summary: dict
    ) -> tuple[dict | None, int | None]:
        """Locate achievement payload and its game_id in RecentAchievements."""
        for game_id, achievements in (
            (user_summary or {}).get("RecentAchievements") or {}
        ).items():
            if not isinstance(achievements, dict):
                continue
            if str(ach_id) in achievements:
                try:
                    return achievements[str(ach_id)], int(game_id)
                except (TypeError, ValueError):
                    return achievements[str(ach_id)], None
            if ach_id in achievements:
                try:
                    return achievements[ach_id], int(game_id)
                except (TypeError, ValueError):
                    return achievements[ach_id], None
        return None, None

    def _build_enriched_payload(
        self, ach: dict, game_id: int, game_ext: dict
    ) -> dict:
        """Build the enriched event payload for an unlocked achievement."""
        ach_id = ach.get("ID")
        badge = ach.get("BadgeName")
        game_ach = (game_ext.get("Achievements") or {}).get(str(ach_id), {}) or {}
        num_players = game_ext.get("NumDistinctPlayers") or 0
        rarity = None
        rarity_hc = None
        if num_players > 0:
            num_awarded = game_ach.get("NumAwarded")
            num_awarded_hc = game_ach.get("NumAwardedHardcore")
            if num_awarded is not None:
                rarity = round((num_awarded / num_players) * 100, 2)
            if num_awarded_hc is not None:
                rarity_hc = round((num_awarded_hc / num_players) * 100, 2)
        return {
            "achievement_id": ach_id,
            "title": ach.get("Title"),
            "description": ach.get("Description"),
            "points": ach.get("Points"),
            "true_points": game_ach.get("TrueRatio"),
            "badge_url": (
                f"https://retroachievements.org/Badge/{badge}.png" if badge else None
            ),
            "game_id": game_id,
            "game_title": ach.get("GameTitle") or game_ext.get("Title"),
            "console_name": ach.get("ConsoleName") or game_ext.get("ConsoleName"),
            "console_id": game_ext.get("ConsoleID"),
            "date_awarded": ach.get("DateAwarded"),
            "hardcore": bool(ach.get("HardcoreMode") or ach.get("Hardcore")),
            "rarity_pct": rarity,
            "rarity_hardcore_pct": rarity_hc,
            "display_order": game_ach.get("DisplayOrder"),
            "author": game_ach.get("Author") or ach.get("Author"),
            "username": self.api_client.username,
        }

    async def _get_cached_game_extended(self, game_id: int) -> dict:
        """Return cached GetGameExtended response for game_id, fetching once."""
        if game_id in self._game_extended_cache:
            return self._game_extended_cache[game_id]
        try:
            data = await self.api_client.async_get_game_extended(game_id)
            if isinstance(data, dict):
                self._game_extended_cache[game_id] = data
                return data
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.warning(
                "Failed to fetch GetGameExtended for game_id=%s: %s", game_id, err
            )
        return {}

    async def _safe_get_aotw(self) -> dict:
        """Fetch AOTW; return empty dict on error so refresh continues."""
        try:
            data = await self.api_client.async_get_achievement_of_the_week()
            return data if isinstance(data, dict) else {}
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.warning("Failed to fetch Achievement of the Week: %s", err)
            return {}

    async def _async_update_data(self):
        try:
            user_summary, game_data, aotw = await asyncio.gather(
                self.api_client.async_get_user_summary(),
                self._get_game_data(),
                self._safe_get_aotw(),
            )

            current_ids = self._extract_achievement_ids(user_summary)
            aotw_id = ((aotw or {}).get("Achievement") or {}).get("ID")

            if not self._first_run:
                new_ids = current_ids - self._previous_achievement_ids
                for ach_id in new_ids:
                    await self._fire_achievement_unlocked(ach_id, user_summary)
                if aotw_id and aotw_id != self._previous_aotw_id:
                    self._fire_aotw_changed(aotw)

            self._previous_achievement_ids = current_ids
            self._previous_aotw_id = aotw_id
            self._first_run = False

            return {
                "user_summary": user_summary,
                "recent_games": user_summary.get("RecentlyPlayed", []),
                "RecentAchievements": user_summary.get("RecentAchievements", {}),
                "aotw": aotw or {},
                **game_data,
            }
        except Exception as error:
            LOGGER.error("Unexpected error fetching retroachievements data: %s", error)
            raise

    async def _fire_achievement_unlocked(
        self, ach_id: int, user_summary: dict
    ) -> None:
        """Look up, enrich, and fire the achievement_unlocked event."""
        ach, game_id = self._find_achievement(ach_id, user_summary)
        if ach is None or game_id is None:
            LOGGER.debug(
                "Achievement %s detected but payload not found in user summary",
                ach_id,
            )
            return
        game_ext = await self._get_cached_game_extended(game_id)
        payload = self._build_enriched_payload(ach, game_id, game_ext)
        self.hass.bus.async_fire(EVENT_ACHIEVEMENT_UNLOCKED, payload)

    def _fire_aotw_changed(self, aotw: dict) -> None:
        """Fire the aotw_changed event."""
        ach = aotw.get("Achievement", {}) or {}
        game = aotw.get("Game", {}) or {}
        badge = ach.get("BadgeName")
        self.hass.bus.async_fire(
            EVENT_AOTW_CHANGED,
            {
                "achievement_id": ach.get("ID"),
                "title": ach.get("Title"),
                "description": ach.get("Description"),
                "points": ach.get("Points"),
                "badge_url": (
                    f"https://retroachievements.org/Badge/{badge}.png"
                    if badge
                    else None
                ),
                "game_id": game.get("ID"),
                "game_title": game.get("Title"),
                "console_name": game.get("ConsoleName"),
                "week_start": aotw.get("StartAt"),
                "author": ach.get("Author"),
            },
        )

    def is_aotw_unlocked(self) -> bool:
        """Return True if the user already unlocked the current AOTW."""
        if not self.data:
            return False
        aotw = (self.data.get("aotw") or {})
        ach_id = (aotw.get("Achievement") or {}).get("ID")
        if not ach_id:
            return False
        try:
            ach_id_int = int(ach_id)
        except (TypeError, ValueError):
            return False
        if ach_id_int in self._previous_achievement_ids:
            return True
        recent = (self.data.get("user_summary") or {}).get(
            "RecentAchievements"
        ) or {}
        for _game_id, achievements in recent.items():
            if not isinstance(achievements, dict):
                continue
            if str(ach_id) in achievements or ach_id in achievements:
                return True
        return False

    async def _get_game_data(self):
        monitored_game_ids: set[int] = set()
        if self.entry.options:
            game_ids_str = self.entry.options.get("monitored_games", "")
            for game_id in game_ids_str.splitlines():
                if game_id.strip():
                    try:
                        monitored_game_ids.add(int(game_id.strip()))
                    except ValueError:
                        LOGGER.warning("Invalid game ID: %s", game_id)

        self.monitored_games = monitored_game_ids

        game_data = {"Awarded": {}}
        if not monitored_game_ids:
            return game_data

        tasks = [
            self.api_client.async_get_user_progress(game_id)
            for game_id in monitored_game_ids
        ]

        if tasks:
            game_progresses = await asyncio.gather(*tasks, return_exceptions=True)

            for i, game_progress in enumerate(game_progresses):
                if isinstance(game_progress, Exception):
                    LOGGER.error("Error fetching game progress: %s", game_progress)
                    continue

                game_id = str(list(monitored_game_ids)[i])
                game_data["Awarded"][game_id] = game_progress

        return game_data
