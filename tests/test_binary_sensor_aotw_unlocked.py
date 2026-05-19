"""Tests for the aotw_unlocked binary sensor."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.binary_sensor import (
    RetroAchievementsAOTWUnlockedBinarySensor,
)
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
        entry_id="t",
    )


async def test_aotw_unlocked_true(
    hass, mock_api_client, mock_entry, aotw_fixture
):
    aotw = {
        **aotw_fixture,
        "Achievement": {**aotw_fixture["Achievement"], "ID": 12345},
    }
    mock_api_client.async_get_achievement_of_the_week.return_value = aotw
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWUnlockedBinarySensor(coord, "TestUser")
    assert sensor.is_on is True
    assert sensor.icon == "mdi:trophy"


async def test_aotw_unlocked_false(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWUnlockedBinarySensor(coord, "TestUser")
    assert sensor.is_on is False
    assert sensor.icon == "mdi:trophy-broken"
