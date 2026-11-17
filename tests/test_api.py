"""Tests for the RetroAchievements API client."""

from __future__ import annotations

import asyncio
import re

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.retroarchievements.api import RetroAchievementsApiClient
from custom_components.retroarchievements.const import BASE_URL

# Anchor a regex on the endpoint path so the mock matches regardless of query
# params like ?y=key.


@pytest.fixture
def m() -> AiohttpClientMocker:
    return AiohttpClientMocker()


@pytest.fixture
async def session(m: AiohttpClientMocker):
    s = m.create_session(asyncio.get_running_loop())
    yield s
    await s.close()


async def test_get_achievement_of_the_week_returns_payload(m, session, aotw_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetAchievementOfTheWeek\.php")
    m.get(url, json=aotw_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_achievement_of_the_week()
    assert result["Achievement"]["ID"] == 99999
    assert result["Game"]["Title"] == "Weekly Challenge Game"


async def test_get_game_extended_returns_payload(m, session, game_extended_fixture):
    url = re.compile(rf"^{re.escape(BASE_URL)}API_GetGameExtended\.php")
    m.get(url, json=game_extended_fixture)
    client = RetroAchievementsApiClient("TestUser", "key", session)
    result = await client.async_get_game_extended(678)
    assert result["NumDistinctPlayers"] == 1000
    assert "12345" in result["Achievements"]
    assert result["Achievements"]["12345"]["NumAwarded"] == 125
