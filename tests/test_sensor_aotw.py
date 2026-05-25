"""Tests for the AOTW sensor."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)
from custom_components.retroarchievements.sensor import (
    RetroAchievementsAOTWSensor,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="t",
    )


async def test_aotw_sensor_state_and_attributes(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWSensor(coord, "TestUser")
    assert sensor.native_value == "Week Champion"
    attrs = sensor.extra_state_attributes
    assert attrs["achievement_id"] == 99999
    assert attrs["points"] == 10
    assert attrs["game_id"] == 5555
    assert attrs["game_title"] == "Weekly Challenge Game"
    assert attrs["console_name"] == "NES"
    assert attrs["badge_url"] == "https://retroachievements.org/Badge/99999.png"
    assert attrs["week_start"] == "2026-05-12T00:00:00.000Z"
    assert attrs["author"] == "Devname"


async def test_aotw_sensor_state_when_no_aotw(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_achievement_of_the_week.return_value = {}
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWSensor(coord, "TestUser")
    assert sensor.native_value is None
