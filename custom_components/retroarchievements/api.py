"""RetroAchievements API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout

from .const import BASE_URL


class RetroAchievementsApiClientError(Exception):
    """Exception to indicate a general API error."""


class RetroAchievementsApiClientCommunicationError(
    RetroAchievementsApiClientError,
):
    """Exception to indicate a communication error."""


class RetroAchievementsApiClientAuthenticationError(
    RetroAchievementsApiClientError,
):
    """Exception to indicate an authentication error."""


class RetroAchievementsApiClient:
    """RetroAchievements API Client."""

    def __init__(
        self,
        username: str,
        api_key: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._username = username
        self._api_key = api_key
        self._session = session

    async def async_get_user_summary(self) -> dict[str, Any]:
        """Get user summary from the API."""
        response = await self._api_wrapper(
            endpoint="API_GetUserSummary.php",
            params={
                "u": self._username,
                "g": 10,  # Get more recent games (increased from 5)
                "a": 5,  # Get 5 recent achievements
                "y": self._api_key,
            },
        )

        # Ensure we have a dictionary
        if not isinstance(response, dict):
            response = {}

        # Add RecentlyPlayed if not present
        if "RecentlyPlayed" not in response:
            # Try to fetch recent games separately
            try:
                recent_games = await self.async_get_user_recent_games()
                response["RecentlyPlayed"] = recent_games
            except Exception:
                response["RecentlyPlayed"] = []

        return response

    async def async_get_user_recent_games(
        self, count: int = 10
    ) -> list[dict[str, Any]]:
        """Get user's recently played games."""
        response = await self._api_wrapper(
            endpoint="API_GetUserRecentlyPlayedGames.php",
            params={
                "u": self._username,
                "c": count,  # number of games to return
                "y": self._api_key,
            },
        )

        # The API returns a list directly, not a dict with a "RecentlyPlayed" key
        return response if isinstance(response, list) else []

    async def async_get_game_info(self, game_id: int) -> dict[str, Any]:
        """Get information about a specific game."""
        return await self._api_wrapper(
            endpoint="API_GetGameInfoAndUserProgress.php",
            params={
                "u": self._username,
                "g": game_id,
                "y": self._api_key,
            },
        )

    async def async_get_user_progress(self, game_id: int) -> dict[str, Any]:
        """Get user's progress in a specific game."""
        response = await self._api_wrapper(
            endpoint="API_GetUserProgress.php",
            params={
                "u": self._username,
                "g": game_id,
                "y": self._api_key,
            },
        )
        # Get the first item since the response is a dict with game_id as key
        return list(response.values())[0] if response else {}

    async def async_get_game_achievements(self, game_id: int) -> list[dict[str, Any]]:
        """Get achievements for a specific game."""
        response = await self._api_wrapper(
            endpoint="API_GetGameInfoAndUserProgress.php",
            params={
                "u": self._username,
                "g": game_id,
                "y": self._api_key,
            },
        )
        return response.get("Achievements", [])

    async def _api_wrapper(
        self,
        endpoint: str,
        params: dict = None,
    ) -> Any:
        """Get information from the API."""
        url = f"{BASE_URL}{endpoint}"

        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(url=url, params=params)

                if response.status == 401:
                    raise RetroAchievementsApiClientAuthenticationError(
                        "Invalid API key or username",
                    )
                response.raise_for_status()

                data = await response.json()

                # The API might return success: false for some errors
                if isinstance(data, dict) and data.get("Success") is False:
                    raise RetroAchievementsApiClientError(
                        data.get("Error", "Unknown error"),
                    )

                return data

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise RetroAchievementsApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise RetroAchievementsApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise RetroAchievementsApiClientError(
                msg,
            ) from exception
