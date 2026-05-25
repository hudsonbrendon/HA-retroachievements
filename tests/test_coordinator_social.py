"""Tests for the coordinator's social / leaderboard data fetch."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="social_entry",
    )


@pytest.fixture
def mock_entry_with_game():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={"monitored_games": "678"},
        entry_id="social_entry_game",
    )


async def test_update_data_includes_social_payloads(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    data = coord.data
    assert data["top_ten"][0]["1"] == "AlphaPlayer"
    assert data["following"]["Total"] == 2
    assert data["followers"]["Total"] == 1
    assert data["set_requests"]["TotalRequests"] == 5
    assert len(data["earned_on_day"]) == 2
    assert data["recent_game_awards"]["Results"][0]["AwardKind"] == "mastered"


async def test_social_payloads_resilient_to_errors(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_top_ten_users.side_effect = RuntimeError("boom")
    mock_api_client.async_get_users_i_follow.side_effect = RuntimeError("boom")
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    assert coord.last_update_success is True
    assert coord.data["top_ten"] == []
    assert coord.data["following"] == {}


async def test_monitored_game_leaderboards_fetched(
    hass, mock_api_client, mock_entry_with_game
):
    coord = RetroAchievementsDataUpdateCoordinator(
        hass, mock_api_client, mock_entry_with_game
    )
    await coord.async_refresh()
    leaderboards = coord.data["Leaderboards"]
    assert "678" in leaderboards
    assert leaderboards["678"]["Results"][0]["UserEntry"]["Rank"] == 7


async def test_no_monitored_games_leaves_leaderboards_empty(
    hass, mock_api_client, mock_entry
):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    assert coord.data["Leaderboards"] == {}
