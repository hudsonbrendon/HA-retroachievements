"""Tests for the reauth config flow."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.api import (
    RetroAchievementsApiClientAuthenticationError,
)
from custom_components.retroarchievements.const import CONF_API_KEY, DOMAIN


@pytest.fixture
def mock_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "oldkey"},
        options={},
        entry_id="t",
        unique_id="TestUser",
    )
    entry.add_to_hass(hass)
    return entry


async def test_reauth_success_updates_key(hass, mock_entry, enable_custom_integrations):
    result = await mock_entry.start_reauth_flow(hass)
    assert result["type"] == "form"
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "custom_components.retroarchievements.config_flow."
        "RetroAchievementsApiClient.async_get_user_summary",
        return_value={"User": "TestUser"},
    ), patch(
        "custom_components.retroarchievements.config_flow."
        "async_create_clientsession",
        return_value=MagicMock(),
    ), patch.object(hass.config_entries, "async_schedule_reload"):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_API_KEY: "newkey"}
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "reauth_successful"
    assert mock_entry.data[CONF_API_KEY] == "newkey"


async def test_reauth_invalid_key_shows_error(
    hass, mock_entry, enable_custom_integrations
):
    result = await mock_entry.start_reauth_flow(hass)

    with patch(
        "custom_components.retroarchievements.config_flow."
        "RetroAchievementsApiClient.async_get_user_summary",
        side_effect=RetroAchievementsApiClientAuthenticationError("bad"),
    ), patch(
        "custom_components.retroarchievements.config_flow."
        "async_create_clientsession",
        return_value=MagicMock(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_API_KEY: "stillbad"}
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "auth"}
