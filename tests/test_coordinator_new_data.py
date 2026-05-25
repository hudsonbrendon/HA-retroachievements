"""Tests for the coordinator's expanded data fetch + award_earned event."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN, EVENT_AWARD_EARNED
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="test_entry",
    )


async def test_update_data_includes_new_payloads(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    data = coord.data
    assert data["user_points"]["Points"] == 1500
    assert data["completion_progress"]["Total"] == 3
    assert data["awards"]["TotalAwardsCount"] == 12
    assert data["want_to_play"]["Total"] == 2


async def test_first_run_does_not_fire_award_event(hass, mock_api_client, mock_entry):
    fired = []
    hass.bus.async_listen(EVENT_AWARD_EARNED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired == []


async def test_new_award_fires_event(
    hass, mock_api_client, mock_entry, user_awards_fixture
):
    fired = []
    hass.bus.async_listen(EVENT_AWARD_EARNED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()  # baseline = 2 awards
    await hass.async_block_till_done()
    assert fired == []

    new_awards = {
        **user_awards_fixture,
        "VisibleUserAwards": [
            *user_awards_fixture["VisibleUserAwards"],
            {
                "AwardedAt": "2026-05-20T09:00:00.000Z",
                "AwardType": "Mastery/Completion",
                "AwardData": 800,
                "AwardDataExtra": 1,
                "Value": 1,
                "Title": "Aladdin",
                "ConsoleID": 1,
                "ConsoleName": "Mega Drive",
                "ImageIcon": "/Images/aladdin-icon.png",
            },
        ],
    }
    mock_api_client.async_get_user_awards.return_value = new_awards
    await coord.async_refresh()
    await hass.async_block_till_done()

    assert len(fired) == 1
    payload = fired[0].data
    assert payload["game_id"] == 800
    assert payload["title"] == "Aladdin"
    assert payload["award_type"] == "Mastery/Completion"
    assert payload["hardcore"] is True
    assert payload["console_name"] == "Mega Drive"
    assert (
        payload["image_url"] == "https://retroachievements.org/Images/aladdin-icon.png"
    )


async def test_unchanged_awards_fire_no_event(hass, mock_api_client, mock_entry):
    fired = []
    hass.bus.async_listen(EVENT_AWARD_EARNED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired == []
