"""Tests for the options flow with gaming_idle_threshold."""
from __future__ import annotations

import pytest
from homeassistant.data_entry_flow import InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import (
    CONF_GAMING_IDLE_THRESHOLD,
    DOMAIN,
)


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


async def test_options_flow_accepts_idle_threshold(hass, mock_entry, enable_custom_integrations):
    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    assert result["type"] == "form"
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"monitored_games": "", CONF_GAMING_IDLE_THRESHOLD: 10},
    )
    assert result2["type"] == "create_entry"
    assert result2["data"][CONF_GAMING_IDLE_THRESHOLD] == 10


async def test_options_flow_rejects_threshold_too_high(hass, mock_entry, enable_custom_integrations):
    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"monitored_games": "", CONF_GAMING_IDLE_THRESHOLD: 999},
        )
