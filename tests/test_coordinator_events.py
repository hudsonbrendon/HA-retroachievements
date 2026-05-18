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
