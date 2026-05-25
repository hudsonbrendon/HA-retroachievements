"""Tests for the RetroAchievements API client's expanded endpoints."""

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


async def test_get_user_points_returns_payload(session, user_points_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserPoints\.php")
    with aioresponses() as m:
        m.get(url, payload=user_points_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_user_points()
    assert result["Points"] == 1500
    assert result["SoftcorePoints"] == 200


async def test_get_user_completion_progress_returns_payload(
    session, completion_progress_fixture
):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserCompletionProgress\.php")
    with aioresponses() as m:
        m.get(url, payload=completion_progress_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_user_completion_progress()
    assert result["Total"] == 3
    assert result["Results"][0]["HighestAwardKind"] == "mastered"


async def test_get_user_awards_returns_payload(session, user_awards_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserAwards\.php")
    with aioresponses() as m:
        m.get(url, payload=user_awards_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_user_awards()
    assert result["TotalAwardsCount"] == 12
    assert result["MasteryAwardsCount"] == 8


async def test_get_user_want_to_play_list_returns_payload(
    session, want_to_play_fixture
):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserWantToPlayList\.php")
    with aioresponses() as m:
        m.get(url, payload=want_to_play_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_user_want_to_play_list()
    assert result["Total"] == 2
    assert result["Results"][0]["GameID"] == 900


async def test_get_user_points_non_dict_returns_empty(session):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetUserPoints\.php")
    with aioresponses() as m:
        m.get(url, payload=[])
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_user_points()
    assert result == {}
