"""Constants for the RetroAchievements integration."""

from logging import Logger, getLogger

from homeassistant.const import Platform

DOMAIN = "retroarchievements"
LOGGER: Logger = getLogger(__package__)

# Define platforms that this integration supports
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.IMAGE,
    Platform.TODO,
    Platform.BUTTON,
    Platform.CALENDAR,
]

# API
BASE_URL = "https://retroachievements.org/API/"

# Configuration
CONF_USERNAME = "username"
CONF_API_KEY = "api_key"
CONF_MONITORED_GAMES = "monitored_games"

# Defaults
DEFAULT_NAME = "RetroAchievements"
DEFAULT_SCAN_INTERVAL = 5  # minutes
# Each refresh fans out into ~14 API calls (plus 3 per monitored game); the
# RetroAchievements API rate-limits aggressively, so polling faster than this
# produces sustained 429 storms.
UPDATE_INTERVAL = 300  # seconds

# Maximum concurrent requests against the RetroAchievements API. Their edge
# throttles bursts well below the per-minute quota, so keep this low.
MAX_CONCURRENT_REQUESTS = 2

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

# Options
CONF_GAMING_IDLE_THRESHOLD = "gaming_idle_threshold"
DEFAULT_GAMING_IDLE_THRESHOLD = 5  # minutes

# Number of trailing days of unlock history exposed via the calendar entity.
EARNED_HISTORY_DAYS = 14

# Services
SERVICE_REFRESH = "refresh"

# Events
EVENT_ACHIEVEMENT_UNLOCKED = f"{DOMAIN}_achievement_unlocked"
EVENT_AOTW_CHANGED = f"{DOMAIN}_aotw_changed"
EVENT_AWARD_EARNED = f"{DOMAIN}_award_earned"
