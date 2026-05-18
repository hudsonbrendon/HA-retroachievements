"""Tests for RetroAchievementsDataUpdateCoordinator.is_aotw_unlocked."""
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
        entry_id="t",
    )


async def test_is_aotw_unlocked_false_when_no_data(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    assert coord.is_aotw_unlocked() is False


async def test_is_aotw_unlocked_true_when_in_recent_achievements(
    hass, mock_api_client, mock_entry, aotw_fixture, user_summary_fixture
):
    # Make AOTW ID match an ID in user_summary RecentAchievements
    aotw = {
        **aotw_fixture,
        "Achievement": {**aotw_fixture["Achievement"], "ID": 12345},
    }
    mock_api_client.async_get_achievement_of_the_week.return_value = aotw
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    assert coord.is_aotw_unlocked() is True


async def test_is_aotw_unlocked_false_when_not_in_recent(
    hass, mock_api_client, mock_entry
):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    # AOTW fixture ID = 99999, user summary fixture does not contain it
    assert coord.is_aotw_unlocked() is False
