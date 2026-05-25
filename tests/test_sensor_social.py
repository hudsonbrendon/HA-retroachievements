"""Tests for the social user-stat sensors."""

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
        entry_id="t",
    )


@pytest.fixture
def mock_entry_with_game():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={"monitored_games": "678"},
        entry_id="tg",
    )


def _description(key: str):
    for description in USER_SENSORS:
        if description.key == key:
            return description
    msg = f"no USER_SENSORS description with key {key!r}"
    raise AssertionError(msg)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("following_count", 2),
        ("followers_count", 1),
        ("set_requests", 5),
        ("achievements_earned_today", 2),
        ("recent_game_awards", 2),
        ("top_ten", "AlphaPlayer"),
    ],
)
async def test_social_sensor_values(hass, mock_api_client, mock_entry, key, expected):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(coord, "TestUser", _description(key))
    assert sensor.native_value == expected


async def test_following_sensor_attributes(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(
        coord, "TestUser", _description("following_count")
    )
    attrs = sensor.extra_state_attributes
    assert attrs["users"][0]["User"] == "FriendOne"


async def test_set_requests_sensor_attributes(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(
        coord, "TestUser", _description("set_requests")
    )
    attrs = sensor.extra_state_attributes
    assert attrs["points_for_next"] == 2500
    assert len(attrs["requested_sets"]) == 2


async def test_top_ten_sensor_attributes(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(coord, "TestUser", _description("top_ten"))
    attrs = sensor.extra_state_attributes
    assert len(attrs["users"]) == 3
    assert attrs["users"][0]["username"] == "AlphaPlayer"
    assert attrs["users"][0]["points"] == 500000


async def test_game_sensor_exposes_leaderboards(
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
    assert attrs["leaderboards"][0]["UserEntry"]["Rank"] == 7


async def test_social_sensor_handles_missing_data(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_users_i_follow.return_value = {}
    mock_api_client.async_get_top_ten_users.return_value = []
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    assert (
        RetroAchievementsUserSensor(
            coord, "TestUser", _description("following_count")
        ).native_value
        == 0
    )
    assert (
        RetroAchievementsUserSensor(
            coord, "TestUser", _description("top_ten")
        ).native_value
        is None
    )
