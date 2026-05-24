"""Tests for config entry diagnostics."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)
from custom_components.retroarchievements.diagnostics import (
    async_get_config_entry_diagnostics,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "supersecret"},
        options={"monitored_games": ""},
        entry_id="t",
    )


async def test_diagnostics_redacts_api_key(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    hass.data.setdefault(DOMAIN, {})[mock_entry.entry_id] = {"coordinator": coord}

    result = await async_get_config_entry_diagnostics(hass, mock_entry)

    assert result["entry"]["data"]["api_key"] == "**REDACTED**"
    assert result["entry"]["data"]["username"] == "TestUser"
    assert result["coordinator_data"]["user_points"]["Points"] == 1500
