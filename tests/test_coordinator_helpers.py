"""Tests for pure-logic helpers on the coordinator."""
from __future__ import annotations

from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


def test_extract_achievement_ids_from_recent_achievements():
    user_summary = {
        "RecentAchievements": {
            "678": {
                "12345": {"ID": 12345},
                "67890": {"ID": 67890},
            },
            "999": {
                "55555": {"ID": 55555},
            },
        }
    }
    result = RetroAchievementsDataUpdateCoordinator._extract_achievement_ids(
        user_summary
    )
    assert result == {12345, 67890, 55555}


def test_extract_achievement_ids_empty_input():
    assert (
        RetroAchievementsDataUpdateCoordinator._extract_achievement_ids({}) == set()
    )
    assert (
        RetroAchievementsDataUpdateCoordinator._extract_achievement_ids(
            {"RecentAchievements": None}
        )
        == set()
    )


def test_extract_achievement_ids_skips_non_integer_keys():
    user_summary = {
        "RecentAchievements": {
            "678": {"abc": {"ID": 0}, "12345": {"ID": 12345}}
        }
    }
    result = RetroAchievementsDataUpdateCoordinator._extract_achievement_ids(
        user_summary
    )
    assert result == {12345}


def test_find_achievement_returns_payload_and_game_id():
    user_summary = {
        "RecentAchievements": {
            "678": {
                "12345": {"ID": 12345, "Title": "First Blood"},
            }
        }
    }
    ach, game_id = RetroAchievementsDataUpdateCoordinator._find_achievement(
        12345, user_summary
    )
    assert ach == {"ID": 12345, "Title": "First Blood"}
    assert game_id == 678


def test_find_achievement_missing_returns_none():
    ach, game_id = RetroAchievementsDataUpdateCoordinator._find_achievement(
        99999, {"RecentAchievements": {}}
    )
    assert ach is None
    assert game_id is None
