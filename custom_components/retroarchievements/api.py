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

    @property
    def username(self) -> str:
        """Return the configured RetroAchievements username."""
        return self._username

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

    async def async_get_achievement_of_the_week(self) -> dict[str, Any]:
        """Get the current Achievement of the Week."""
        response = await self._api_wrapper(
            endpoint="API_GetAchievementOfTheWeek.php",
            params={"y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_user_points(self) -> dict[str, Any]:
        """Get the user's hardcore and softcore point totals."""
        response = await self._api_wrapper(
            endpoint="API_GetUserPoints.php",
            params={"u": self._username, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_user_completion_progress(self) -> dict[str, Any]:
        """Get metadata about all the user's played games and their awards."""
        response = await self._api_wrapper(
            endpoint="API_GetUserCompletionProgress.php",
            params={"u": self._username, "c": 500, "o": 0, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_user_awards(self) -> dict[str, Any]:
        """Get the user's site awards/badges."""
        response = await self._api_wrapper(
            endpoint="API_GetUserAwards.php",
            params={"u": self._username, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_user_want_to_play_list(self) -> dict[str, Any]:
        """Get the user's 'Want to Play Games' backlog."""
        response = await self._api_wrapper(
            endpoint="API_GetUserWantToPlayList.php",
            params={"u": self._username, "c": 100, "o": 0, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_game_extended(self, game_id: int) -> dict[str, Any]:
        """Get extended game metadata including per-achievement award counts."""
        response = await self._api_wrapper(
            endpoint="API_GetGameExtended.php",
            params={"i": game_id, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

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

    async def async_get_top_ten_users(self) -> list[dict[str, Any]]:
        """Get the top ten users by hardcore points."""
        response = await self._api_wrapper(
            endpoint="API_GetTopTenUsers.php",
            params={"y": self._api_key},
        )
        return response if isinstance(response, list) else []

    async def async_get_users_i_follow(self) -> dict[str, Any]:
        """Get the list of users the configured user follows."""
        response = await self._api_wrapper(
            endpoint="API_GetUsersIFollow.php",
            params={"c": 100, "o": 0, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_users_following_me(self) -> dict[str, Any]:
        """Get the list of users following the configured user."""
        response = await self._api_wrapper(
            endpoint="API_GetUsersFollowingMe.php",
            params={"c": 100, "o": 0, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_user_set_requests(self) -> dict[str, Any]:
        """Get the user's achievement set requests and remaining allowance."""
        response = await self._api_wrapper(
            endpoint="API_GetUserSetRequests.php",
            params={"u": self._username, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_achievements_earned_on_day(
        self, on_date: str
    ) -> list[dict[str, Any]]:
        """Get achievements the user earned on a specific day (YYYY-MM-DD)."""
        response = await self._api_wrapper(
            endpoint="API_GetAchievementsEarnedOnDay.php",
            params={"u": self._username, "d": on_date, "y": self._api_key},
        )
        return response if isinstance(response, list) else []

    async def async_get_recent_game_awards(self) -> dict[str, Any]:
        """Get recent game awards (mastered/completed) across the site."""
        response = await self._api_wrapper(
            endpoint="API_GetRecentGameAwards.php",
            params={"c": 25, "o": 0, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}

    async def async_get_user_game_leaderboards(self, game_id: int) -> dict[str, Any]:
        """Get the user's leaderboard entries for a specific game."""
        response = await self._api_wrapper(
            endpoint="API_GetUserGameLeaderboards.php",
            params={
                "i": game_id,
                "u": self._username,
                "c": 200,
                "o": 0,
                "y": self._api_key,
            },
        )
        return response if isinstance(response, dict) else {}

    async def async_get_user_game_rank_and_score(
        self, game_id: int
    ) -> list[dict[str, Any]]:
        """Get the user's rank and score within a specific game."""
        response = await self._api_wrapper(
            endpoint="API_GetUserGameRankAndScore.php",
            params={
                "g": game_id,
                "u": self._username,
                "y": self._api_key,
            },
        )
        return response if isinstance(response, list) else []

    async def async_get_achievements_earned_between(
        self, from_date: str, to_date: str
    ) -> list[dict[str, Any]]:
        """Get achievements the user earned between two dates (YYYY-MM-DD)."""
        response = await self._api_wrapper(
            endpoint="API_GetAchievementsEarnedBetween.php",
            params={
                "u": self._username,
                "f": from_date,
                "t": to_date,
                "y": self._api_key,
            },
        )
        return response if isinstance(response, list) else []

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
