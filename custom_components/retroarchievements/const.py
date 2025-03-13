"""Constants for the RetroAchievements integration."""

from logging import Logger, getLogger

DOMAIN = "retroarchievements"
LOGGER: Logger = getLogger(__package__)

# API
BASE_URL = "https://retroachievements.org/API/"

# Configuration
CONF_USERNAME = "username"
CONF_API_KEY = "api_key"
CONF_MONITORED_GAMES = "monitored_games"

# Defaults
DEFAULT_NAME = "RetroAchievements"

# Default update interval
DEFAULT_UPDATE_INTERVAL = 30  # minutes

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
