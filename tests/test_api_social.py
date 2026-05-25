"""Tests for the social / leaderboard / feed API endpoints."""

from __future__ import annotations

import re

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.retroarchievements.api import RetroAchievementsApiClient
from custom_components.retroarchievements.const import BASE_URL


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as s:
        yield s


def _load(name):
    import json
    from pathlib import Path

    return json.loads((Path(__file__).parent / "fixtures" / name).read_text())


async def test_get_top_ten_users(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetTopTenUsers\.php")
    with aioresponses() as m:
        m.get(url, payload=_load("top_ten.json"))
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_top_ten_users()
    assert isinstance(result, list)
    assert result[0]["1"] == "AlphaPlayer"


async def test_get_users_i_follow(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUsersIFollow\.php")
    with aioresponses() as m:
        m.get(url, payload=_load("following.json"))
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_users_i_follow()
    assert result["Total"] == 2
    assert result["Results"][0]["User"] == "FriendOne"


async def test_get_users_following_me(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUsersFollowingMe\.php")
    with aioresponses() as m:
        m.get(url, payload=_load("followers.json"))
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_users_following_me()
    assert result["Total"] == 1


async def test_get_user_set_requests(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserSetRequests\.php")
    with aioresponses() as m:
        m.get(url, payload=_load("set_requests.json"))
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_user_set_requests()
    assert result["PointsForNext"] == 2500


async def test_get_achievements_earned_on_day(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetAchievementsEarnedOnDay\.php")
    with aioresponses() as m:
        m.get(url, payload=_load("earned_on_day.json"))
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_achievements_earned_on_day("2026-05-25")
    assert isinstance(result, list)
    assert len(result) == 2


async def test_get_recent_game_awards(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetRecentGameAwards\.php")
    with aioresponses() as m:
        m.get(url, payload=_load("recent_game_awards.json"))
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_recent_game_awards()
    assert result["Results"][0]["AwardKind"] == "mastered"


async def test_get_user_game_leaderboards(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserGameLeaderboards\.php")
    with aioresponses() as m:
        m.get(url, payload=_load("user_game_leaderboards.json"))
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_user_game_leaderboards(678)
    assert result["Results"][0]["UserEntry"]["Rank"] == 7


async def test_top_ten_non_list_returns_empty(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetTopTenUsers\.php")
    with aioresponses() as m:
        m.get(url, payload={})
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_top_ten_users()
    assert result == []
