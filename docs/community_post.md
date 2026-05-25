# RetroAchievements – bring your retro gaming stats into Home Assistant

**Category:** Projects → Share your Projects
**Suggested title:** RetroAchievements integration – track points, achievements and what you're playing

---

If you use [RetroAchievements](https://retroachievements.org/) (achievements for retro games across dozens of emulated consoles), I've been building a Home Assistant integration that pulls your profile, progress and activity into HA so you can put it on a dashboard or drive automations.

It's a HACS custom integration, open source, with English and Brazilian Portuguese translations.

## What you get

**Profile & stats sensors**
- Total points, true (weighted) points and global rank
- Hardcore vs. softcore points
- Games mastered / beaten / played
- Total site awards
- Status and rich presence (what you're playing right now)
- Recently played games and recent achievements

**Per-game sensors**
- Completion percentage, achievements earned/total, points, last played — one device per monitored game

**Other entity types**
- `image` – box art of the game you're currently playing + the badge of your last unlocked achievement
- `todo` – a read-only mirror of your "Want to Play" backlog
- `binary_sensor` – `is_gaming` (on while you're actively playing) and `aotw_unlocked` (Achievement of the Week done?)
- `button` – force an immediate refresh

## Automations

The integration fires bus events you can trigger on:
- `retroarchievements_achievement_unlocked`
- `retroarchievements_award_earned`
- `retroarchievements_aotw_changed`

There's a ready-made blueprint that notifies you (with the badge image) on every unlock, with an optional "hardcore only" filter. A minimal example:

```yaml
automation:
  - trigger:
      - platform: event
        event_type: retroarchievements_achievement_unlocked
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🏆 Achievement unlocked!"
          message: >
            {{ trigger.event.data.title }} ({{ trigger.event.data.points }} pts)
            — {{ trigger.event.data.game_title }}
          data:
            image: "{{ trigger.event.data.badge_url }}"
```

I use it to flash a light and announce rare unlocks over TTS.

## Install

1. HACS → add `https://github.com/hudsonbrendon/HA-retroachievements` as a custom repository (category: Integration), or search once it's indexed.
2. Restart Home Assistant.
3. Settings → Devices & Services → Add Integration → RetroAchievements.
4. Enter your username and API key (found in your account settings on the RetroAchievements website).

Minimum HA version is `2025.2.4`. The integration ships its own brand icon via the new local brands proxy, which needs **HA 2026.3+** to show on the card.

## Links

- Repo & docs: https://github.com/hudsonbrendon/HA-retroachievements
- RetroAchievements: https://retroachievements.org/

Feedback, bug reports and feature ideas are very welcome — leaderboards, friends and an Achievement-of-the-Week calendar are on my list next. If you try it, I'd love to see your dashboards. 🎮

> _Add 2–3 screenshots here (device page, a dashboard card, a notification) before posting — screenshots get far more engagement on this forum._
