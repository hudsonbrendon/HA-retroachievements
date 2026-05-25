"""Tests for the retroarchievements.refresh service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN, SERVICE_REFRESH


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="t",
    )


async def test_service_registered_on_setup(
    hass, enable_custom_integrations, mock_api_client, mock_entry
):
    mock_entry.add_to_hass(hass)
    with patch(
        "custom_components.retroarchievements.RetroAchievementsApiClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()
    assert hass.services.has_service(DOMAIN, SERVICE_REFRESH)


async def test_service_calls_coordinator_refresh(
    hass, enable_custom_integrations, mock_api_client, mock_entry
):
    mock_entry.add_to_hass(hass)
    with patch(
        "custom_components.retroarchievements.RetroAchievementsApiClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_entry.entry_id]["coordinator"]
    coordinator.async_request_refresh = AsyncMock()
    await hass.services.async_call(DOMAIN, SERVICE_REFRESH, {}, blocking=True)
    coordinator.async_request_refresh.assert_awaited()


async def test_service_removed_on_last_unload(
    hass, enable_custom_integrations, mock_api_client, mock_entry
):
    mock_entry.add_to_hass(hass)
    with patch(
        "custom_components.retroarchievements.RetroAchievementsApiClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()
        await hass.config_entries.async_unload(mock_entry.entry_id)
        await hass.async_block_till_done()
    assert hass.services.has_service(DOMAIN, SERVICE_REFRESH) is False
