"""Tests for the RetroAchievements achievements calendar."""

from __future__ import annotations

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.calendar import (
    RetroAchievementsAchievementsCalendar,
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
        entry_id="cal",
    )


async def test_event_returns_latest_unlock(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    calendar = RetroAchievementsAchievementsCalendar(coord, "TestUser")
    event = calendar.event
    # earned_between fixture's latest unlock is "Brawler" on 2026-05-22.
    assert event is not None
    assert event.summary == "Brawler (Streets of Rage)"


async def test_get_events_filters_by_range(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    calendar = RetroAchievementsAchievementsCalendar(coord, "TestUser")

    start = dt_util.parse_datetime("2026-05-20 00:00:00").replace(
        tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    end = dt_util.parse_datetime("2026-05-21 00:00:00").replace(
        tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    events = await calendar.async_get_events(hass, start, end)
    # Only the two May-20 unlocks fall in this window.
    assert len(events) == 2
    assert {e.summary for e in events} == {
        "First Steps (Sonic the Hedgehog)",
        "Speed Demon (Sonic the Hedgehog)",
    }


async def test_get_events_empty_when_no_history(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_achievements_earned_between.return_value = []
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    calendar = RetroAchievementsAchievementsCalendar(coord, "TestUser")
    assert calendar.event is None
    start = dt_util.parse_datetime("2026-05-01 00:00:00").replace(
        tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    end = dt_util.parse_datetime("2026-06-01 00:00:00").replace(
        tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    assert await calendar.async_get_events(hass, start, end) == []
