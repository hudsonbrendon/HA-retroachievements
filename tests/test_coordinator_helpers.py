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


def test_build_enriched_payload_full(user_summary_fixture, game_extended_fixture):
    coord = RetroAchievementsDataUpdateCoordinator.__new__(
        RetroAchievementsDataUpdateCoordinator
    )

    class _C:
        _username = "TestUser"

    coord.api_client = _C()
    ach = user_summary_fixture["RecentAchievements"]["678"]["12345"]
    payload = coord._build_enriched_payload(ach, 678, game_extended_fixture)
    assert payload["achievement_id"] == 12345
    assert payload["title"] == "First Blood"
    assert payload["description"] == "Defeat your first enemy"
    assert payload["points"] == 5
    assert payload["true_points"] == 7
    assert payload["badge_url"] == "https://retroachievements.org/Badge/01234.png"
    assert payload["game_id"] == 678
    assert payload["game_title"] == "Sonic the Hedgehog"
    assert payload["console_name"] == "Mega Drive"
    assert payload["console_id"] == 1
    assert payload["date_awarded"] == "2026-05-18 11:55:00"
    assert payload["hardcore"] is True
    assert payload["rarity_pct"] == 12.5
    assert payload["rarity_hardcore_pct"] == 4.2
    assert payload["display_order"] == 1
    assert payload["author"] == "Devname"
    assert payload["username"] == "TestUser"


def test_build_enriched_payload_handles_empty_game_ext():
    coord = RetroAchievementsDataUpdateCoordinator.__new__(
        RetroAchievementsDataUpdateCoordinator
    )

    class _C:
        _username = "TestUser"

    coord.api_client = _C()
    ach = {
        "ID": 1,
        "Title": "t",
        "Description": "d",
        "Points": 5,
        "BadgeName": "00001",
        "GameTitle": "g",
        "ConsoleName": "c",
        "DateAwarded": "2026-05-18 12:00:00",
        "HardcoreMode": 0,
        "Author": "a",
    }
    payload = coord._build_enriched_payload(ach, 678, {})
    assert payload["achievement_id"] == 1
    assert payload["true_points"] is None
    assert payload["rarity_pct"] is None
    assert payload["rarity_hardcore_pct"] is None
    assert payload["hardcore"] is False
    assert payload["author"] == "a"


def test_build_enriched_payload_zero_players_returns_none_rarity():
    coord = RetroAchievementsDataUpdateCoordinator.__new__(
        RetroAchievementsDataUpdateCoordinator
    )

    class _C:
        _username = "TestUser"

    coord.api_client = _C()
    ach = {"ID": 1, "BadgeName": "x"}
    game_ext = {"NumDistinctPlayers": 0, "Achievements": {"1": {"NumAwarded": 0}}}
    payload = coord._build_enriched_payload(ach, 678, game_ext)
    assert payload["rarity_pct"] is None
    assert payload["rarity_hardcore_pct"] is None
