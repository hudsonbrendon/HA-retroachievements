"""Tests for the is_gaming binary sensor."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.binary_sensor import (
    RetroAchievementsIsGamingBinarySensor,
)
from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


def _make_coord_with_data(hass, summary: dict, idle_threshold: int = 5):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "k"},
        options={"gaming_idle_threshold": idle_threshold},
        entry_id="t",
    )
    api_client = MagicMock()
    coord = RetroAchievementsDataUpdateCoordinator(hass, api_client, entry)
    coord.data = {"user_summary": summary}
    return coord


def _ts_minutes_ago(minutes: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


async def test_is_gaming_true_when_all_conditions_met(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(1)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is True


async def test_is_gaming_false_when_rich_presence_empty(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(1)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_false_when_status_offline(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Offline",
            "LastActivity": {"timestamp": _ts_minutes_ago(1)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_false_when_activity_stale(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(30)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_respects_configurable_threshold(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(20)},
        },
        idle_threshold=30,
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is True


async def test_is_gaming_false_when_last_activity_missing(hass):
    coord = _make_coord_with_data(
        hass,
        {"RichPresenceMsg": "Playing Sonic", "Status": "Online"},
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_false_on_unparseable_timestamp(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": "not-a-date"},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False
