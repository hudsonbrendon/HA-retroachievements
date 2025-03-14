"""Constants for the RetroAchievements integration."""

from logging import Logger, getLogger

from homeassistant.const import Platform

DOMAIN = "retroarchievements"
LOGGER: Logger = getLogger(__package__)

# Define platforms that this integration supports
PLATFORMS = [Platform.SENSOR]

# API
BASE_URL = "https://retroachievements.org/API/"

# Configuration
CONF_USERNAME = "username"
CONF_API_KEY = "api_key"
CONF_MONITORED_GAMES = "monitored_games"

# Defaults
DEFAULT_NAME = "RetroAchievements"
DEFAULT_SCAN_INTERVAL = 1  # minutes
UPDATE_INTERVAL = 60  # seconds (1 minute in seconds)

# Entity attributes
ATTR_GAME_ID = "game_id"
ATTR_GAME_TITLE = "game_title"
ATTR_CONSOLE_ID = "console_id"
ATTR_CONSOLE_NAME = "console_name"
ATTR_ACHIEVEMENTS_TOTAL = "achievements_total"
ATTR_ACHIEVEMENTS_EARNED = "achievements_earned"
ATTR_COMPLETION_PERCENTAGE = "completion_percentage"
ATTR_POINTS_TOTAL = "points_total"
ATTR_POINTS_EARNED = "points_earned"
ATTR_RANK = "rank"

# Attribution
ATTRIBUTION = "Data provided by RetroAchievements"
