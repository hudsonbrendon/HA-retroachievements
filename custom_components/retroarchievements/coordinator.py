"""DataUpdateCoordinator for RetroAchievements."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    RetroAchievementsApiClientAuthenticationError,
    RetroAchievementsApiClientError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER


class RetroAchievementsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RetroAchievements data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from RetroAchievements API."""
        try:
            client = self.hass.data[DOMAIN][self.config_entry.entry_id]["client"]

            # Get user summary data
            user_summary = await client.async_get_user_summary()

            # Get recent games
            recent_games = await client.async_get_user_recent_games()

            # Get monitored games data if any are configured
            monitored_games_data = {}
            monitored_game_ids = self.config_entry.options.get(
                "monitored_games", ""
            ).split("\n")
            monitored_game_ids = [g.strip() for g in monitored_game_ids if g.strip()]

            for game_id in monitored_game_ids:
                try:
                    game_id_int = int(game_id)
                    game_info = await client.async_get_game_info(game_id_int)
                    user_progress = await client.async_get_user_progress(game_id_int)

                    monitored_games_data[game_id] = {
                        "info": game_info,
                        "progress": user_progress,
                    }
                except ValueError:
                    LOGGER.warning(f"Invalid game ID: {game_id}")
                except Exception as e:
                    LOGGER.error(f"Error fetching data for game {game_id}: {e}")

            # Combine all data
            return {
                "user_summary": user_summary,
                "recent_games": recent_games,
                "monitored_games": monitored_games_data,
            }

        except RetroAchievementsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except RetroAchievementsApiClientError as exception:
            raise UpdateFailed(
                f"Error communicating with API: {exception}"
            ) from exception
