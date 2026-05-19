"""Tests for coordinator event firing (achievement_unlocked, aotw_changed)."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import (
    DOMAIN,
    EVENT_ACHIEVEMENT_UNLOCKED,
    EVENT_AOTW_CHANGED,
)
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


async def test_first_run_does_not_fire_events(
    hass, mock_api_client, mock_entry
):
    """On the very first refresh, neither event type fires."""
    fired_achievement = []
    fired_aotw = []
    hass.bus.async_listen(
        EVENT_ACHIEVEMENT_UNLOCKED, lambda e: fired_achievement.append(e)
    )
    hass.bus.async_listen(
        EVENT_AOTW_CHANGED, lambda e: fired_aotw.append(e)
    )
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired_achievement == []
    assert fired_aotw == []


async def test_new_achievement_fires_event_with_enriched_payload(
    hass, mock_api_client, mock_entry, user_summary_fixture
):
    """After first refresh sets baseline, a new achievement fires the event."""
    fired = []
    hass.bus.async_listen(EVENT_ACHIEVEMENT_UNLOCKED, lambda e: fired.append(e))

    # First refresh: baseline contains achievement 12345
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired == []

    # Second refresh: add a new achievement
    new_summary = {
        **user_summary_fixture,
        "RecentAchievements": {
            "678": {
                **user_summary_fixture["RecentAchievements"]["678"],
                "12346": {
                    "ID": 12346,
                    "GameID": 678,
                    "GameTitle": "Sonic the Hedgehog",
                    "ConsoleName": "Mega Drive",
                    "Title": "Second Blood",
                    "Description": "Defeat your second enemy",
                    "Points": 10,
                    "BadgeName": "01235",
                    "DateAwarded": "2026-05-18 12:05:00",
                    "HardcoreMode": 0,
                    "Author": "Devname",
                },
            }
        },
    }
    mock_api_client.async_get_user_summary.return_value = new_summary
    await coord.async_refresh()
    await hass.async_block_till_done()

    assert len(fired) == 1
    payload = fired[0].data
    assert payload["achievement_id"] == 12346
    assert payload["title"] == "Second Blood"
    assert payload["points"] == 10
    assert payload["hardcore"] is False
    assert payload["badge_url"] == "https://retroachievements.org/Badge/01235.png"
    assert payload["game_id"] == 678
    assert payload["rarity_pct"] is None  # 12346 not in game_extended fixture


async def test_no_new_achievements_fires_no_events(
    hass, mock_api_client, mock_entry
):
    fired = []
    hass.bus.async_listen(EVENT_ACHIEVEMENT_UNLOCKED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await coord.async_refresh()  # same data, no diff
    await hass.async_block_till_done()
    assert fired == []


async def test_aotw_change_fires_event(
    hass, mock_api_client, mock_entry, aotw_fixture
):
    fired = []
    hass.bus.async_listen(EVENT_AOTW_CHANGED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()  # baseline AOTW = 99999
    assert fired == []

    new_aotw = {
        **aotw_fixture,
        "Achievement": {**aotw_fixture["Achievement"], "ID": 88888, "Title": "New"},
    }
    mock_api_client.async_get_achievement_of_the_week.return_value = new_aotw
    await coord.async_refresh()
    await hass.async_block_till_done()

    assert len(fired) == 1
    assert fired[0].data["achievement_id"] == 88888
    assert fired[0].data["title"] == "New"


async def test_aotw_unchanged_fires_no_event(hass, mock_api_client, mock_entry):
    fired = []
    hass.bus.async_listen(EVENT_AOTW_CHANGED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired == []
