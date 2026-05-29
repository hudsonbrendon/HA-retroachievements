"""Tests for the options flow: menu, manage step, and game picker."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.data_entry_flow import InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import (
    CONF_GAMING_IDLE_THRESHOLD,
    CONF_MONITORED_GAMES,
    DOMAIN,
)

from .conftest import load_fixture


@pytest.fixture
def mock_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "k"},
        options={},
        entry_id="t",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def patched_client():
    """Patch the config_flow API client with fixture-backed responses."""
    client = AsyncMock()
    client.async_get_console_ids.return_value = load_fixture("console_ids.json")
    client.async_get_game_list.return_value = load_fixture("game_list.json")
    with patch(
        "custom_components.retroarchievements.config_flow.RetroAchievementsApiClient",
        return_value=client,
    ):
        yield client


async def _open_menu(hass, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "menu"
    return result


async def test_manage_step_accepts_idle_threshold(
    hass, mock_entry, enable_custom_integrations
):
    result = await _open_menu(hass, mock_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "manage"}
    )
    assert result["type"] == "form"
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MONITORED_GAMES: "", CONF_GAMING_IDLE_THRESHOLD: 10},
    )
    assert result2["type"] == "create_entry"
    assert result2["data"][CONF_GAMING_IDLE_THRESHOLD] == 10


async def test_manage_step_rejects_threshold_too_high(
    hass, mock_entry, enable_custom_integrations
):
    result = await _open_menu(hass, mock_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "manage"}
    )
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_MONITORED_GAMES: "", CONF_GAMING_IDLE_THRESHOLD: 999},
        )


async def test_picker_selects_games(
    hass, mock_entry, enable_custom_integrations, patched_client
):
    result = await _open_menu(hass, mock_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "select_games"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "select_games"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"console": "1"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "pick_games"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"games": ["678", "700"]}
    )
    assert result["type"] == "create_entry"
    assert set(result["data"][CONF_MONITORED_GAMES].split()) == {"678", "700"}


async def test_picker_preserves_other_console_games(
    hass, enable_custom_integrations, patched_client
):
    # 999 belongs to a console not in the fixture game list; it must survive.
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "k"},
        options={CONF_MONITORED_GAMES: "999\n800"},
        entry_id="t2",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "select_games"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"console": "1"}
    )
    # Deselect 800, select 678 instead. 999 (other console) preserved.
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"games": ["678"]}
    )
    assert result["type"] == "create_entry"
    assert set(result["data"][CONF_MONITORED_GAMES].split()) == {"678", "999"}


async def test_select_games_falls_back_to_manage_without_consoles(
    hass, mock_entry, enable_custom_integrations
):
    client = AsyncMock()
    client.async_get_console_ids.return_value = []
    with patch(
        "custom_components.retroarchievements.config_flow.RetroAchievementsApiClient",
        return_value=client,
    ):
        result = await _open_menu(hass, mock_entry)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={"next_step_id": "select_games"}
        )
    assert result["type"] == "form"
    assert result["step_id"] == "manage"
    assert result["errors"] == {"base": "cannot_load_games"}
