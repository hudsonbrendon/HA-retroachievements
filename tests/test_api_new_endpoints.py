"""Tests for the RetroAchievements API client's expanded endpoints."""

from __future__ import annotations

import asyncio
import re

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.retroarchievements.api import RetroAchievementsApiClient
from custom_components.retroarchievements.const import BASE_URL


@pytest.fixture
def m() -> AiohttpClientMocker:
    return AiohttpClientMocker()


@pytest.fixture
async def session(m: AiohttpClientMocker):
    s = m.create_session(asyncio.get_running_loop())
    yield s
    await s.close()


async def test_get_user_points_returns_payload(m, session, user_points_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserPoints\.php")
    m.get(url, json=user_points_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_user_points()
    assert result["Points"] == 1500
    assert result["SoftcorePoints"] == 200


async def test_get_user_completion_progress_returns_payload(
    m, session, completion_progress_fixture
):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserCompletionProgress\.php")
    m.get(url, json=completion_progress_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_user_completion_progress()
    assert result["Total"] == 3
    assert result["Results"][0]["HighestAwardKind"] == "mastered"


async def test_get_user_awards_returns_payload(m, session, user_awards_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserAwards\.php")
    m.get(url, json=user_awards_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_user_awards()
    assert result["TotalAwardsCount"] == 12
    assert result["MasteryAwardsCount"] == 8


async def test_get_user_want_to_play_list_returns_payload(
    m, session, want_to_play_fixture
):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserWantToPlayList\.php")
    m.get(url, json=want_to_play_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_user_want_to_play_list()
    assert result["Total"] == 2
    assert result["Results"][0]["GameID"] == 900


async def test_get_user_points_non_dict_returns_empty(m, session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserPoints\.php")
    m.get(url, json=[])
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_user_points()
    assert result == {}


async def test_get_achievements_earned_between_returns_payload(
    m, session, earned_between_fixture
):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetAchievementsEarnedBetween\.php")
    m.get(url, json=earned_between_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_achievements_earned_between(
        "2026-05-20", "2026-05-23"
    )
    assert len(result) == 3
    assert result[0]["Title"] == "First Steps"


async def test_get_achievements_earned_between_non_list_returns_empty(m, session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetAchievementsEarnedBetween\.php")
    m.get(url, json={})
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_achievements_earned_between("a", "b")
    assert result == []


async def test_get_user_game_rank_and_score_returns_payload(
    m, session, game_rank_score_fixture
):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserGameRankAndScore\.php")
    m.get(url, json=game_rank_score_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_user_game_rank_and_score(678)
    assert result[0]["UserRank"] == 3
    assert result[0]["TotalScore"] == 400


async def test_get_user_game_rank_and_score_non_list_returns_empty(m, session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserGameRankAndScore\.php")
    m.get(url, json={})
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_user_game_rank_and_score(678)
    assert result == []


async def test_get_console_ids_returns_payload(m, session, console_ids_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetConsoleIDs\.php")
    m.get(url, json=console_ids_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_console_ids()
    assert len(result) == 3
    assert result[0]["Name"] == "Mega Drive"


async def test_get_console_ids_non_list_returns_empty(m, session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetConsoleIDs\.php")
    m.get(url, json={})
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_console_ids()
    assert result == []


async def test_get_game_list_returns_payload(m, session, game_list_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetGameList\.php")
    m.get(url, json=game_list_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_game_list(1)
    assert len(result) == 3
    assert result[0]["ID"] == 678


async def test_get_game_list_non_list_returns_empty(m, session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetGameList\.php")
    m.get(url, json={})
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_game_list(1)
    assert result == []
