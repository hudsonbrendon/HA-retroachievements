"""Tests for the RetroAchievements API client."""
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
