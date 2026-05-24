"""Tests for the expanded user-stat sensors."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)
from custom_components.retroarchievements.sensor import (
    USER_SENSORS,
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


def _description(key: str):
    for description in USER_SENSORS:
        if description.key == key:
            return description
    msg = f"no USER_SENSORS description with key {key!r}"
    raise AssertionError(msg)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("hardcore_points", 1500),
        ("softcore_points", 200),
        ("games_mastered", 8),
        ("games_beaten", 3),
        ("games_played", 3),
        ("awards_total", 12),
    ],
)
async def test_stat_sensor_values(hass, mock_api_client, mock_entry, key, expected):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsUserSensor(coord, "TestUser", _description(key))
    assert sensor.native_value == expected


async def test_stat_sensor_handles_missing_data(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_user_points.return_value = {}
    mock_api_client.async_get_user_awards.return_value = {}
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    assert (
        RetroAchievementsUserSensor(
            coord, "TestUser", _description("hardcore_points")
        ).native_value
        == 0
    )
    assert (
        RetroAchievementsUserSensor(
            coord, "TestUser", _description("awards_total")
        ).native_value
        == 0
    )
