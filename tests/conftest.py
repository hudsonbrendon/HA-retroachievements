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
def mock_api_client(user_summary_fixture, aotw_fixture, game_extended_fixture):
    """Return an AsyncMock API client preloaded with fixture responses."""
    # Local import to keep the heavy HA import out of fixture-discovery time
    from custom_components.retroarchievements.api import RetroAchievementsApiClient

    client = AsyncMock(spec=RetroAchievementsApiClient)
    client.username = "TestUser"
    client._username = "TestUser"
    client.async_get_user_summary.return_value = user_summary_fixture
    client.async_get_user_recent_games.return_value = (
        user_summary_fixture.get("RecentlyPlayed", [])
    )
    client.async_get_achievement_of_the_week.return_value = aotw_fixture
    client.async_get_game_extended.return_value = game_extended_fixture
    client.async_get_user_progress.return_value = {}
    return client
