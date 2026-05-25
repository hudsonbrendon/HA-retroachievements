"""Shared helpers for RetroAchievements entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN


def user_device_info(username: str) -> DeviceInfo:
    """Return the DeviceInfo for the user's RetroAchievements profile device."""
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, f"{username}")},
        manufacturer="RetroAchievements",
        name=f"RetroAchievements {username}",
        configuration_url=f"https://retroachievements.org/user/{username}",
        model="User Profile",
    )
