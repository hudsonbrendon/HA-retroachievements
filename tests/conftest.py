"""Shared pytest fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict | list:
    """
    Load a JSON fixture from tests/fixtures/.

    Each call re-reads the file, so tests may mutate the returned dict safely.
    """
    return json.loads((FIXTURE_DIR / name).read_text())


@pytest.fixture
def user_summary_fixture() -> dict:
    """Return the sample user summary payload."""
    return load_fixture("user_summary.json")


@pytest.fixture
def aotw_fixture() -> dict:
    """Return the sample AOTW payload."""
    return load_fixture("aotw.json")


@pytest.fixture
def game_extended_fixture() -> dict:
    """Return the sample game extended payload."""
    return load_fixture("game_extended.json")


@pytest.fixture
def user_points_fixture() -> dict:
    """Return the sample GetUserPoints payload."""
    return load_fixture("user_points.json")


@pytest.fixture
def completion_progress_fixture() -> dict:
    """Return the sample GetUserCompletionProgress payload."""
    return load_fixture("completion_progress.json")


@pytest.fixture
def user_awards_fixture() -> dict:
    """Return the sample GetUserAwards payload."""
    return load_fixture("user_awards.json")


@pytest.fixture
def want_to_play_fixture() -> dict:
    """Return the sample GetUserWantToPlayList payload."""
    return load_fixture("want_to_play.json")


@pytest.fixture
def top_ten_fixture() -> list:
    """Return the sample GetTopTenUsers payload."""
    return load_fixture("top_ten.json")


@pytest.fixture
def following_fixture() -> dict:
    """Return the sample GetUsersIFollow payload."""
    return load_fixture("following.json")


@pytest.fixture
def followers_fixture() -> dict:
    """Return the sample GetUsersFollowingMe payload."""
    return load_fixture("followers.json")


@pytest.fixture
def set_requests_fixture() -> dict:
    """Return the sample GetUserSetRequests payload."""
    return load_fixture("set_requests.json")


@pytest.fixture
def earned_on_day_fixture() -> list:
    """Return the sample GetAchievementsEarnedOnDay payload."""
    return load_fixture("earned_on_day.json")


@pytest.fixture
def recent_game_awards_fixture() -> dict:
    """Return the sample GetRecentGameAwards payload."""
    return load_fixture("recent_game_awards.json")


@pytest.fixture
def user_game_leaderboards_fixture() -> dict:
    """Return the sample GetUserGameLeaderboards payload."""
    return load_fixture("user_game_leaderboards.json")


@pytest.fixture
def earned_between_fixture() -> list:
    """Return the sample GetAchievementsEarnedBetween payload."""
    return load_fixture("earned_between.json")


@pytest.fixture
def game_rank_score_fixture() -> list:
    """Return the sample GetUserGameRankAndScore payload."""
    return load_fixture("game_rank_score.json")


@pytest.fixture
def console_ids_fixture() -> list:
    """Return the sample GetConsoleIDs payload."""
    return load_fixture("console_ids.json")


@pytest.fixture
def game_list_fixture() -> list:
    """Return the sample GetGameList payload."""
    return load_fixture("game_list.json")


@pytest.fixture
def mock_api_client(
    user_summary_fixture,
    aotw_fixture,
    game_extended_fixture,
    user_points_fixture,
    completion_progress_fixture,
    user_awards_fixture,
    want_to_play_fixture,
    top_ten_fixture,
    following_fixture,
    followers_fixture,
    set_requests_fixture,
    earned_on_day_fixture,
    recent_game_awards_fixture,
    user_game_leaderboards_fixture,
    earned_between_fixture,
    game_rank_score_fixture,
):
    """Return an AsyncMock API client preloaded with fixture responses."""
    # Local import to keep the heavy HA import out of fixture-discovery time
    from custom_components.retroarchievements.api import RetroAchievementsApiClient

    client = AsyncMock(spec=RetroAchievementsApiClient)
    client.username = "TestUser"
    client._username = "TestUser"
    client.async_get_user_summary.return_value = user_summary_fixture
    client.async_get_user_recent_games.return_value = user_summary_fixture.get(
        "RecentlyPlayed", []
    )
    client.async_get_achievement_of_the_week.return_value = aotw_fixture
    client.async_get_game_extended.return_value = game_extended_fixture
    client.async_get_user_progress.return_value = {}
    client.async_get_user_points.return_value = user_points_fixture
    client.async_get_user_completion_progress.return_value = completion_progress_fixture
    client.async_get_user_awards.return_value = user_awards_fixture
    client.async_get_user_want_to_play_list.return_value = want_to_play_fixture
    client.async_get_top_ten_users.return_value = top_ten_fixture
    client.async_get_users_i_follow.return_value = following_fixture
    client.async_get_users_following_me.return_value = followers_fixture
    client.async_get_user_set_requests.return_value = set_requests_fixture
    client.async_get_achievements_earned_on_day.return_value = earned_on_day_fixture
    client.async_get_recent_game_awards.return_value = recent_game_awards_fixture
    client.async_get_user_game_leaderboards.return_value = (
        user_game_leaderboards_fixture
    )
    client.async_get_achievements_earned_between.return_value = earned_between_fixture
    client.async_get_user_game_rank_and_score.return_value = game_rank_score_fixture
    client.async_get_console_ids.return_value = load_fixture("console_ids.json")
    client.async_get_game_list.return_value = load_fixture("game_list.json")
    return client
