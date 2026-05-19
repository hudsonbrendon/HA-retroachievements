"""Tests for the RetroAchievements API client."""
from __future__ import annotations

import re

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.retroarchievements.api import RetroAchievementsApiClient
from custom_components.retroarchievements.const import BASE_URL

# aioresponses 0.7.x matches query strings strictly; we anchor a regex on the
# endpoint path so the mock matches regardless of query params like ?y=key.


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as s:
        yield s


async def test_get_achievement_of_the_week_returns_payload(
    session, aotw_fixture
):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetAchievementOfTheWeek\.php")
    with aioresponses() as m:
        m.get(url, payload=aotw_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_achievement_of_the_week()
    assert result["Achievement"]["ID"] == 99999
    assert result["Game"]["Title"] == "Weekly Challenge Game"


async def test_get_game_extended_returns_payload(session, game_extended_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetGameExtended\.php")
    with aioresponses() as m:
        m.get(url, payload=game_extended_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_game_extended(678)
    assert result["NumDistinctPlayers"] == 1000
    assert "12345" in result["Achievements"]
    assert result["Achievements"]["12345"]["NumAwarded"] == 125
