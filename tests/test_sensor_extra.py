"""Tests for the derived extra sensors (want_to_play_count, last_achievement)."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)
from custom_components.retroarchievements.sensor import (
    USER_SENSORS,
    RetroAchievementsGameSensor,
    RetroAchievementsUserSensor,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="x",
    )


@pytest.fixture
def mock_entry_with_game():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={"monitored_games": "678"},
        entry_id="xg",
    )


def _description(key: str):
    for description in USER_SENSORS:
        if description.key == key:
            return description
    msg = f"no USER_SENSORS description with key {key!r}"
    raise AssertionError(msg)


async def test_want_to_play_count_value_and_attrs(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(
        coord, "TestUser", _description("want_to_play_count")
    )
    assert sensor.native_value == 2
    assert len(sensor.extra_state_attributes["games"]) == 2


async def test_last_achievement_value_and_attrs(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(
        coord, "TestUser", _description("last_achievement")
    )
    assert sensor.native_value == "First Blood"
    attrs = sensor.extra_state_attributes
    assert attrs["id"] == 12345
    assert attrs["game"] == "Sonic the Hedgehog"
    assert attrs["badge_url"].endswith("/Badge/01234.png")


async def test_last_achievement_handles_no_recent(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_user_summary.return_value = {
        "RecentlyPlayed": [],
        "RecentAchievements": {},
    }
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(
        coord, "TestUser", _description("last_achievement")
    )
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


async def test_game_sensor_exposes_rank_and_score(
    hass, mock_api_client, mock_entry_with_game
):
    coord = RetroAchievementsDataUpdateCoordinator(
        hass, mock_api_client, mock_entry_with_game
    )
    await coord.async_refresh()
    sensor = RetroAchievementsGameSensor(
        coord, "TestUser", {"GameID": 678, "Title": "Sonic", "ConsoleName": "MD"}
    )
    attrs = sensor.extra_state_attributes
    assert attrs["user_rank"] == 3
    assert attrs["user_total_score"] == 400
