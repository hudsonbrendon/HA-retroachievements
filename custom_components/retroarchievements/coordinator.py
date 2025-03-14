"""Data update coordinator for the RetroAchievements integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import RetroAchievementsApiClient
from .const import DOMAIN, LOGGER, UPDATE_INTERVAL


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
        self.monitored_games = set()

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Fetch data from RetroAchievements API."""
        try:
            # Make multiple API calls concurrently
            user_summary, game_data = await asyncio.gather(
                self.api_client.async_get_user_summary(), self._get_game_data()
            )

            return {
                "user_summary": user_summary,
                "recent_games": user_summary.get("RecentlyPlayed", []),
                "RecentAchievements": user_summary.get("RecentAchievements", {}),
                **game_data,
            }
        except Exception as error:
            LOGGER.error("Unexpected error fetching retroachievements data: %s", error)
            raise

    async def _get_game_data(self):
        """Fetch data for monitored games."""
        # Get monitored games from options
        monitored_game_ids = set()
        if self.entry.options:
            game_ids_str = self.entry.options.get("monitored_games", "")
            for game_id in game_ids_str.splitlines():
                if game_id.strip():
                    try:
                        monitored_game_ids.add(int(game_id.strip()))
                    except ValueError:
                        LOGGER.warning("Invalid game ID: %s", game_id)

        self.monitored_games = monitored_game_ids

        # Fetch game data for each monitored game
        game_data = {"Awarded": {}}
        if not monitored_game_ids:
            return game_data

        tasks = []
        for game_id in monitored_game_ids:
            tasks.append(self.api_client.async_get_user_progress(game_id))

        if tasks:
            game_progresses = await asyncio.gather(*tasks, return_exceptions=True)

            for i, game_progress in enumerate(game_progresses):
                if isinstance(game_progress, Exception):
                    LOGGER.error("Error fetching game progress: %s", game_progress)
                    continue

                game_id = str(list(monitored_game_ids)[i])
                game_data["Awarded"][game_id] = game_progress

        return game_data
