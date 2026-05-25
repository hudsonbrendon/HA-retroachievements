# RetroAchievements for Home Assistant

![RetroAchievements Logo](logo.png)

This integration allows you to monitor your RetroAchievements stats and progress in Home Assistant.

## Installation

### HACS (Recommended)
1. Make sure you have [HACS](https://hacs.xyz/) installed.
2. Go to HACS > Integrations > Click the three dots in the top right > Custom repositories.
3. Add this repository URL with category "Integration".
4. Click "Install" on the RetroAchievements integration.
5. Restart Home Assistant.

### Manual Installation
1. Copy the `custom_components/retroarchievements` folder to your Home Assistant's `custom_components` folder.
2. Restart Home Assistant.

## Setup

1. Go to Settings > Devices & Services > Add Integration
2. Search for "RetroAchievements"
3. Enter your RetroAchievements username and API key

## API Key
You can find your RetroAchievements API key in your account settings on the [RetroAchievements website](https://retroachievements.org/).

## Entities

The integration provides the following entities:

### User Profile Sensors

| Sensor | Description | Attributes |
|--------|-------------|------------|
| `sensor.retroachievements_USERNAME_points` | Total points earned across all games | Profile details including ID, member since date, profile URL, profile picture |
| `sensor.retroachievements_USERNAME_true_points` | Total true points (weighted score) | Same as above |
| `sensor.retroachievements_USERNAME_rank` | Global rank on RetroAchievements | Same as above |
| `sensor.retroachievements_USERNAME_status` | Account status (Online/Offline) | Same as above |
| `sensor.retroachievements_USERNAME_rich_presence` | Current gaming activity status | Same as above |
| `sensor.retroachievements_USERNAME_games_count` | Number of games played | Same as above |
| `sensor.retroachievements_USERNAME_completed_games_count` | Number of games completed | Same as above |
| `sensor.retroachievements_USERNAME_completion_percentage` | Overall completion percentage | Same as above |
| `sensor.retroachievements_USERNAME_achievements_unlocked` | Number of achievements unlocked | Same as above |
| `sensor.retroachievements_USERNAME_recent_achievements` | Count of recently unlocked achievements | List of recently unlocked achievements with details |

### Player Stats Sensors

Sourced from the RetroAchievements `GetUserPoints`, `GetUserCompletionProgress`, and `GetUserAwards` endpoints.

| Sensor | Description |
|--------|-------------|
| `sensor.retroachievements_USERNAME_hardcore_points` | Hardcore points total |
| `sensor.retroachievements_USERNAME_softcore_points` | Softcore points total |
| `sensor.retroachievements_USERNAME_games_mastered` | Number of games mastered |
| `sensor.retroachievements_USERNAME_games_beaten` | Number of games beaten (hardcore + softcore) |
| `sensor.retroachievements_USERNAME_games_played` | Number of games played |
| `sensor.retroachievements_USERNAME_awards_total` | Total site awards earned |

### Image, Todo & Button Entities

| Entity | Description |
|--------|-------------|
| `image.retroachievements_USERNAME_current_game_box_art` | Box art of the most recently played game |
| `image.retroachievements_USERNAME_last_achievement_badge` | Badge of the most recently earned achievement |
| `todo.retroachievements_USERNAME_want_to_play` | Read-only backlog mirroring your RetroAchievements "Want to Play" list |
| `button.retroachievements_USERNAME_refresh` | Forces an immediate data refresh |

### Game-specific Sensors

For each recently played game, the integration creates:

| Sensor | Description | Attributes |
|--------|-------------|------------|
| `sensor.retroachievements_game_GAME_ID` | Completion percentage for the game | Game details including ID, console, achievements (total/earned), points (total/earned), last played date, game images, and recently unlocked achievements |

All game sensors are grouped under your RetroAchievements user device for easy organization.

## Attributes

### User Profile Attributes
- `user_id`: Your RetroAchievements user ID
- `username`: Your RetroAchievements username
- `display_name`: Your display name on RetroAchievements
- `member_since`: Date you joined RetroAchievements
- `profile_url`: Link to your RetroAchievements profile
- `profile_image`: URL to your profile picture
- `last_update`: Timestamp of the last data update

### Recent Achievements Attributes
- `recent_achievements`: List of recently unlocked achievements containing:
  - `achievement_id`: Achievement ID
  - `title`: Achievement name
  - `description`: Achievement description
  - `points`: Points value
  - `badge_url`: URL to the achievement badge
  - `game_id`: ID of the game
  - `game_title`: Title of the game
  - `console_name`: Console name
  - `unlocked_date`: When the achievement was unlocked

### Game Sensor Attributes
- `game_id`: RetroAchievements game ID
- `game_title`: Game name
- `console_name`: Console name
- `console_id`: Console ID
- `developer`: Game developer name (if available)
- `publisher`: Game publisher name (if available)
- `genre`: Game genre (if available)
- `release_date`: Game release date (if available)
- `last_played`: Last played timestamp
- `image_icon`: Game icon URL
- `image_box_art`: Game box art URL
- `image_title`: Game title screen image URL
- `image_ingame`: In-game screenshot URL
- `achievements_total`: Total number of achievements
- `achievements_earned`: Number of earned achievements
- `points_total`: Total possible points
- `points_earned`: Points earned
- `completion_percentage`: Game completion percentage
- `recent_achievements`: List of recently unlocked achievements for this game

## Use Cases

- Create a dashboard to track your gaming progress
- Set up automations based on achievement unlocks
- Monitor your RetroAchievements rank and statistics
- Track completion percentages across your game collection
- Display recently unlocked achievements in your dashboard

## Achievement of the Week (AOTW)

| Entity | Description |
|--------|-------------|
| `sensor.retroachievements_USERNAME_aotw` | Title of the current AOTW (attributes: id, points, game, console, badge, week start, author) |
| `binary_sensor.retroachievements_USERNAME_aotw_unlocked` | `on` if the user already unlocked the current AOTW |

> **Limitation:** `aotw_unlocked` may briefly read `off` for unlocks that happened well before the integration was restarted, until the next detection cycle observes the achievement again.

## Is Gaming

| Entity | Description |
|--------|-------------|
| `binary_sensor.retroachievements_USERNAME_is_gaming` | `on` when the user has rich presence, is Online, and has recent activity (within the configured idle threshold) |

## Events

The integration fires HA bus events you can use as automation triggers.

### `retroarchievements_achievement_unlocked`

Fired once for each newly unlocked achievement (skipped on the very first refresh after restart).

Payload fields:

```yaml
achievement_id: int
title: str
description: str
points: int
true_points: int | null
badge_url: str | null
game_id: int
game_title: str
console_name: str
console_id: int | null
date_awarded: str
hardcore: bool
rarity_pct: float | null         # % of game players that unlocked this
rarity_hardcore_pct: float | null
display_order: int | null
author: str | null
username: str
```

Example automation — TTS announcement for rare achievements:

```yaml
automation:
  - alias: Announce rare RetroAchievements unlock
    trigger:
      platform: event
      event_type: retroarchievements_achievement_unlocked
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.rarity_pct is not none and trigger.event.data.rarity_pct < 5 }}"
    action:
      service: tts.cloud_say
      data:
        entity_id: media_player.living_room
        message: >
          Rare achievement unlocked: {{ trigger.event.data.title }}
          in {{ trigger.event.data.game_title }}.
```

### `retroarchievements_aotw_changed`

Fired when the current Achievement of the Week changes ID.

Payload fields: `achievement_id`, `title`, `description`, `points`, `badge_url`, `game_id`, `game_title`, `console_name`, `week_start`, `author`.

### `retroarchievements_award_earned`

Fired when a new site award (mastery, completion, beaten) appears on your profile.

Payload fields: `award_type`, `game_id`, `title`, `console_name`, `console_id`, `awarded_at`, `hardcore`, `image_url`, `username`.

## Automation Blueprint

A ready-made blueprint lives in `blueprints/automation/retroarchievements/achievement_unlocked_notify.yaml`. Import it to get a notification (with the badge image) on every unlocked achievement, with an optional "hardcore only" filter.

## Service: `retroarchievements.refresh`

Forces an immediate refresh of all RetroAchievements data (useful right after unlocking an achievement in your emulator).

```yaml
service: retroarchievements.refresh
```

## Options

In **Settings → Devices & Services → RetroAchievements → Configure**:

- `monitored_games` — game IDs to track in detail (one per line).
- `gaming_idle_threshold` — minutes of inactivity after which `is_gaming` flips off (default `5`, range `1`–`60`).

## Re-authentication & Diagnostics

- If your API key is rotated or rejected, Home Assistant prompts a **Re-authenticate** flow to enter a new key without removing the integration.
- **Download diagnostics** from the device page to get a redacted dump (API key removed) of the config entry and coordinator data for bug reports.

## Troubleshooting

If you encounter issues, please:
1. Enable debug logging for the component in your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.retroarchievements: debug
   ```
2. Check the logs for error messages
3. Open an issue on GitHub with the logs and steps to reproduce

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
