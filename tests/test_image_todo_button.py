"""Tests for the image, todo, and button platforms."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.button import (
    RetroAchievementsRefreshButton,
)
from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)
from custom_components.retroarchievements.image import (
    RetroAchievementsBoxArtImage,
    RetroAchievementsLastBadgeImage,
)
from custom_components.retroarchievements.todo import (
    RetroAchievementsWantToPlayTodoList,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="t",
    )


async def _coordinator(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    return coord


async def test_box_art_image_url(hass, mock_api_client, mock_entry):
    coord = await _coordinator(hass, mock_api_client, mock_entry)
    entity = RetroAchievementsBoxArtImage(hass, coord, "TestUser")
    assert (
        entity.image_url
        == "https://retroachievements.org/Images/sonic-box.png"
    )


async def test_last_badge_image_url(hass, mock_api_client, mock_entry):
    coord = await _coordinator(hass, mock_api_client, mock_entry)
    entity = RetroAchievementsLastBadgeImage(hass, coord, "TestUser")
    assert entity.image_url == "https://retroachievements.org/Badge/01234.png"


async def test_image_url_none_when_no_data(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_user_summary.return_value = {}
    mock_api_client.async_get_user_recent_games.return_value = []
    coord = await _coordinator(hass, mock_api_client, mock_entry)
    entity = RetroAchievementsBoxArtImage(hass, coord, "TestUser")
    assert entity.image_url is None


async def test_want_to_play_todo_items(hass, mock_api_client, mock_entry):
    coord = await _coordinator(hass, mock_api_client, mock_entry)
    entity = RetroAchievementsWantToPlayTodoList(coord, "TestUser")
    items = entity.todo_items
    assert len(items) == 2
    assert items[0].uid == "900"
    assert "Gunstar Heroes" in items[0].summary


async def test_want_to_play_todo_empty(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_user_want_to_play_list.return_value = {}
    coord = await _coordinator(hass, mock_api_client, mock_entry)
    entity = RetroAchievementsWantToPlayTodoList(coord, "TestUser")
    assert entity.todo_items == []


async def test_refresh_button_requests_refresh(hass, mock_api_client, mock_entry):
    coord = await _coordinator(hass, mock_api_client, mock_entry)
    coord.async_request_refresh = AsyncMock()
    button = RetroAchievementsRefreshButton(coord, "TestUser")
    await button.async_press()
    coord.async_request_refresh.assert_awaited_once()
