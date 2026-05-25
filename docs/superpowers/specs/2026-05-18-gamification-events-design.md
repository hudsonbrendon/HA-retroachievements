# Sub-Project D — Gamification & Events Design

**Date:** 2026-05-18
**Status:** Approved for planning
**Sub-project of:** RetroAchievements API integration expansion (D of A/B/C/D)

## Goal

Enrich the Home Assistant RetroAchievements integration with real-time gamification primitives: per-achievement event firing with enriched payload, Achievement of the Week (AOTW) tracking, an `is_gaming` binary sensor, and a manual refresh service. The goal is to enable HA automations that react to actual gameplay events (light effects, TTS, notifications) without polling external scrapers.

## Scope

In-scope:
- New API methods: `GetAchievementOfTheWeek`, `GetGameExtended`.
- New entities: `sensor.aotw`, `binary_sensor.is_gaming`, `binary_sensor.aotw_unlocked`.
- New HA events: `retroarchievements_achievement_unlocked`, `retroarchievements_aotw_changed`.
- New service: `retroarchievements.refresh`.
- New option: `gaming_idle_threshold` (minutes, default 5).
- Cleanup of blueprint dead code (`switch.py`, current stub `binary_sensor.py`, plus `entity.py`/`data.py` if confirmed unused).
- Initial pytest test suite using `pytest-homeassistant-custom-component`.
- README + translation updates.
- Bump `manifest.json` version to `0.3.0`.

Out-of-scope (sub-projects A, B, C — separate specs):
- Metrics windows (points per day/week), backlog/want-to-play, leaderboards, social follow lists.

## Architecture

Single-coordinator approach (Abordagem 1). The existing `RetroAchievementsDataUpdateCoordinator` is extended to:

1. Fetch AOTW alongside user summary and game data each refresh cycle (`asyncio.gather`).
2. Maintain `_previous_achievement_ids: set[int]` and `_previous_aotw_id: int | None` in-memory state.
3. On each refresh, diff current vs previous achievement IDs. For each newly-detected achievement, lazily fetch `GetGameExtended(game_id)` (cached per-instance) to enrich payload, then fire `retroarchievements_achievement_unlocked`.
4. On each refresh, compare AOTW ID. If changed, fire `retroarchievements_aotw_changed`.
5. Skip event firing on the very first refresh (boot) to avoid flooding HA with historic achievements every restart.

New `binary_sensor` platform is registered (replaces the blueprint dead-code file). Two binary sensors: `is_gaming` (derived from rich presence + status + recency) and `aotw_unlocked` (derived from coordinator helper).

A service `retroarchievements.refresh` is registered in `__init__.py` that calls `async_request_refresh()` on every coordinator in `hass.data[DOMAIN]`.

### Data Flow

```
HA scheduler tick (every UPDATE_INTERVAL=60s)
  → coordinator._async_update_data
      ├── asyncio.gather:
      │     ├── api.async_get_user_summary()
      │     ├── _get_game_data()  [monitored games progress]
      │     └── api.async_get_achievement_of_the_week()
      ├── current_ids = extract from user_summary.RecentAchievements
      ├── if not _first_run:
      │     ├── new_ids = current_ids - _previous_achievement_ids
      │     ├── for each new_id:
      │     │     ├── game_ext = _get_cached_game_extended(game_id)
      │     │     │     └── (lazy) api.async_get_game_extended(game_id) → cache
      │     │     └── hass.bus.async_fire(EVENT_ACHIEVEMENT_UNLOCKED, payload)
      │     └── if aotw_id != _previous_aotw_id:
      │           └── hass.bus.async_fire(EVENT_AOTW_CHANGED, payload)
      ├── _previous_achievement_ids = current_ids
      ├── _previous_aotw_id = aotw_id
      ├── _first_run = False
      └── return data dict
  → entities re-render via CoordinatorEntity
```

### Components

| File | Responsibility |
|---|---|
| `api.py` | Add `async_get_achievement_of_the_week`, `async_get_game_extended`. |
| `coordinator.py` | Add diff state, enrichment, event firing, AOTW unlocked helper, idle threshold from options. |
| `sensor.py` | Add `RetroAchievementsAOTWSensor`. |
| `binary_sensor.py` | Rewrite from scratch: `IsGamingBinarySensor`, `AOTWUnlockedBinarySensor`. |
| `__init__.py` | Register `retroarchievements.refresh` service; deregister on last unload. |
| `config_flow.py` | Add `gaming_idle_threshold` to options schema. |
| `const.py` | Add `Platform.BINARY_SENSOR`, `CONF_GAMING_IDLE_THRESHOLD`, `DEFAULT_GAMING_IDLE_THRESHOLD`, `SERVICE_REFRESH`, `EVENT_ACHIEVEMENT_UNLOCKED`, `EVENT_AOTW_CHANGED`. |
| `services.yaml` | New file declaring `refresh`. |
| `translations/en.json` | Strings for AOTW sensor/binary sensors, `is_gaming`, options field. |
| `switch.py`, `entity.py`, `data.py` | Delete (blueprint dead code, after grep confirms no live references). |
| `tests/` | New pytest suite (see Testing). |
| `README.md` | Document new entities, events, service. |
| `manifest.json` | Bump version to `0.3.0`. |

## API Endpoints

### New: `API_GetAchievementOfTheWeek.php`

Request: `GET https://retroachievements.org/API/API_GetAchievementOfTheWeek.php?y=<api_key>`

Response shape (relevant fields):
```json
{
  "Achievement": {
    "ID": 12345,
    "Title": "string",
    "Description": "string",
    "Points": 5,
    "BadgeName": "01234",
    "Author": "string"
  },
  "Game": {
    "ID": 678,
    "Title": "string",
    "ConsoleName": "string",
    "ConsoleID": 7,
    "ImageIcon": "/Images/01234.png"
  },
  "StartAt": "2026-05-12T00:00:00.000Z"
}
```

### New: `API_GetGameExtended.php`

Request: `GET https://retroachievements.org/API/API_GetGameExtended.php?i=<game_id>&y=<api_key>`

Response shape (relevant fields):
```json
{
  "ID": 678,
  "Title": "string",
  "NumDistinctPlayers": 1234,
  "Achievements": {
    "12345": {
      "ID": 12345,
      "Title": "string",
      "Description": "string",
      "Points": 5,
      "TrueRatio": 7,
      "BadgeName": "01234",
      "DisplayOrder": 1,
      "Author": "string",
      "NumAwarded": 156,
      "NumAwardedHardcore": 52
    }
  }
}
```

Rarity calculation:
- `rarity_pct = (NumAwarded / NumDistinctPlayers) * 100` (rounded to 2 decimals).
- `rarity_hardcore_pct = (NumAwardedHardcore / NumDistinctPlayers) * 100` (rounded to 2 decimals).
- Guard: if `NumDistinctPlayers <= 0`, both are `None`.

## Coordinator Behavior

### State

```python
self._previous_achievement_ids: set[int] = set()
self._previous_aotw_id: int | None = None
self._game_extended_cache: dict[int, dict] = {}
self._first_run: bool = True
self._idle_threshold_minutes: int = entry.options.get(
    CONF_GAMING_IDLE_THRESHOLD, DEFAULT_GAMING_IDLE_THRESHOLD
)
```

### Diff extraction

`RecentAchievements` from `GetUserSummary` is a dict keyed by `game_id`, whose value is a dict keyed by `achievement_id`. Extract IDs:

```python
def _extract_achievement_ids(user_summary: dict) -> set[int]:
    ids: set[int] = set()
    for _game_id, achievements in (user_summary.get("RecentAchievements") or {}).items():
        for ach_id, _ach in (achievements or {}).items():
            try:
                ids.add(int(ach_id))
            except (TypeError, ValueError):
                continue
    return ids
```

### Find achievement details for firing

Walk `RecentAchievements` to locate the achievement object + its `game_id`:

```python
def _find_achievement(self, ach_id: int, user_summary: dict) -> tuple[dict | None, int | None]:
    for game_id, achievements in (user_summary.get("RecentAchievements") or {}).items():
        if str(ach_id) in achievements:
            return achievements[str(ach_id)], int(game_id)
        if ach_id in achievements:
            return achievements[ach_id], int(game_id)
    return None, None
```

### Enrichment

```python
def _build_enriched_payload(
    self, ach: dict, game_id: int, game_ext: dict, user_summary: dict
) -> dict:
    ach_id = ach.get("ID")
    badge = ach.get("BadgeName")
    game_ach = (game_ext.get("Achievements") or {}).get(str(ach_id), {})
    num_players = game_ext.get("NumDistinctPlayers") or 0
    rarity = None
    rarity_hc = None
    if num_players > 0:
        num_awarded = game_ach.get("NumAwarded")
        num_awarded_hc = game_ach.get("NumAwardedHardcore")
        if num_awarded is not None:
            rarity = round((num_awarded / num_players) * 100, 2)
        if num_awarded_hc is not None:
            rarity_hc = round((num_awarded_hc / num_players) * 100, 2)
    return {
        "achievement_id": ach_id,
        "title": ach.get("Title"),
        "description": ach.get("Description"),
        "points": ach.get("Points"),
        "true_points": game_ach.get("TrueRatio"),
        "badge_url": f"https://retroachievements.org/Badge/{badge}.png" if badge else None,
        "game_id": game_id,
        "game_title": ach.get("GameTitle") or game_ext.get("Title"),
        "console_name": ach.get("ConsoleName") or game_ext.get("ConsoleName"),
        "console_id": game_ext.get("ConsoleID"),
        "date_awarded": ach.get("DateAwarded"),
        "hardcore": bool(ach.get("HardcoreMode") or ach.get("Hardcore")),
        "rarity_pct": rarity,
        "rarity_hardcore_pct": rarity_hc,
        "display_order": game_ach.get("DisplayOrder"),
        "author": game_ach.get("Author") or ach.get("Author"),
        "username": self.api_client._username,
    }
```

Enrichment failure handling: `_get_cached_game_extended` catches all exceptions, logs a warning, returns `{}`. Downstream payload then has `None`/empty values for enriched fields. The event still fires.

### AOTW unlocked helper

```python
def is_aotw_unlocked(self) -> bool:
    if not self.data:
        return False
    aotw = (self.data.get("aotw") or {})
    ach_id = (aotw.get("Achievement") or {}).get("ID")
    if not ach_id:
        return False
    if int(ach_id) in self._previous_achievement_ids:
        return True
    recent = (self.data.get("user_summary") or {}).get("RecentAchievements") or {}
    for _game_id, achievements in recent.items():
        if str(ach_id) in achievements or ach_id in achievements:
            return True
    return False
```

Known limitation (acceptable for v1): if the user unlocked the current AOTW so long ago that it's outside the user-summary `RecentAchievements` window, the sensor reads `False` until the next refresh that detects the achievement via diff (which won't happen since it's not new). This is documented in the README. A future enhancement could call `GetGameInfoAndUserProgress(aotw_game_id)` to check earned achievements directly — out of scope here.

## Entity Specs

### `sensor.retroarchievements_<username>_aotw`

- State: `Achievement.Title` (string) or `None` if no AOTW available.
- Attributes: `achievement_id`, `description`, `points`, `badge_url`, `game_id`, `game_title`, `console_name`, `week_start` (from `StartAt`), `author`.
- Icon: `mdi:calendar-star`.
- Device: existing user device (`(DOMAIN, username)`).
- Translation key: `aotw`.

### `binary_sensor.retroarchievements_<username>_is_gaming`

- `is_on` true iff all hold:
  - `user_summary.RichPresenceMsg` is non-empty (after `.strip()`),
  - `user_summary.Status == "Online"`,
  - `user_summary.LastActivity.timestamp` (or `LastActivity.lastupdate` fallback) parses and is within `_idle_threshold_minutes` of `datetime.now(timezone.utc)`.
- If any condition fails (missing field, parse error, stale timestamp), returns `False`. No exceptions propagate.
- Icon: `mdi:gamepad-circle`.
- Translation key: `is_gaming`.

### `binary_sensor.retroarchievements_<username>_aotw_unlocked`

- `is_on` = `coordinator.is_aotw_unlocked()`.
- Icon: `mdi:trophy-broken` (off) / `mdi:trophy` (on) via dynamic icon property.
- Translation key: `aotw_unlocked`.

## Events

### `retroarchievements_achievement_unlocked`

Fired once per newly-detected achievement (one event per achievement, not batched). Payload schema as defined in `_build_enriched_payload` above.

Suppression: not fired on the first coordinator refresh (`_first_run` gate).

### `retroarchievements_aotw_changed`

Fired when AOTW achievement ID transitions to a new value (including `None` → ID, but not on first run). Payload:

```python
{
    "achievement_id": int,
    "title": str,
    "description": str,
    "points": int,
    "badge_url": str | None,
    "game_id": int,
    "game_title": str,
    "console_name": str,
    "week_start": str | None,
    "author": str | None,
}
```

## Service

### `retroarchievements.refresh`

- No fields.
- Iterates `hass.data[DOMAIN]` values, calls `coordinator.async_request_refresh()` on every coordinator instance.
- Registered once in `async_setup_entry` if not already registered (`hass.services.has_service` guard).
- Deregistered in `async_unload_entry` when no entries remain.

## Configuration / Options

Add to options flow schema:

```python
vol.Optional(
    CONF_GAMING_IDLE_THRESHOLD,
    default=self.config_entry.options.get(
        CONF_GAMING_IDLE_THRESHOLD, DEFAULT_GAMING_IDLE_THRESHOLD
    ),
): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
```

Constants:
- `CONF_GAMING_IDLE_THRESHOLD = "gaming_idle_threshold"`
- `DEFAULT_GAMING_IDLE_THRESHOLD = 5`

Existing `update_listener` already reloads on options change; coordinator picks up new threshold on reload.

## Error Handling

- `GetAchievementOfTheWeek` failure: log warning, treat as `aotw = {}`, skip AOTW event firing this cycle. Existing entities continue.
- `GetGameExtended` failure: log warning, enrichment uses empty dict, event still fires with `None`/empty enriched fields.
- Coordinator-level `_async_update_data` failures already propagate to HA's update coordinator machinery; no change to that contract.

## Testing

Add `pytest-homeassistant-custom-component` test infrastructure.

### Test deps

Add `tests/` directory and dev dependencies. Create:

- `requirements_test.txt`:
  ```
  pytest>=8.0
  pytest-homeassistant-custom-component>=0.13
  pytest-asyncio>=0.23
  aioresponses>=0.7
  ```
- `tests/__init__.py` (empty)
- `tests/conftest.py` with fixtures: `mock_aiohttp` (using `aioresponses`), `mock_config_entry`, `setup_integration` helper.
- Pin `homeassistant` version per `requirements.txt` — `pytest-homeassistant-custom-component` releases are pinned per HA version; pick version that matches HA `2025.2.4`.

### Test files

| File | Tests |
|---|---|
| `tests/test_api.py` | `get_achievement_of_the_week` happy path / 401 / 500 / timeout; `get_game_extended` happy path / 401 / 500. |
| `tests/test_coordinator_diff.py` | First-run skip; new achievement detected → event fired with enriched payload; no new IDs → no event; multiple new in one cycle → multiple events; enrichment failure → event still fires with `None` enrichment. |
| `tests/test_coordinator_aotw.py` | AOTW change → event fired; AOTW unchanged → no event; first run AOTW → no event; `is_aotw_unlocked` true/false branches. |
| `tests/test_binary_sensor_is_gaming.py` | All-conditions-true → on; rich empty → off; status offline → off; stale timestamp → off; missing LastActivity → off; configurable threshold. |
| `tests/test_binary_sensor_aotw_unlocked.py` | Delegates to coordinator helper. |
| `tests/test_sensor_aotw.py` | State + attributes happy path; no AOTW → state `None`. |
| `tests/test_service_refresh.py` | Service registered on setup; calling service triggers coordinator refresh; service removed on last unload. |
| `tests/test_config_flow.py` | Options flow accepts threshold; rejects threshold out of range. |

Approach: use TDD — write failing test, run, implement, run, commit, per writing-plans skill. Mock HTTP via `aioresponses`. No real API calls.

### CI

A `.github/workflows/test.yml` running `pytest tests/` on Python 3.12 + the pinned HA version is **optional** for this sub-project — flag as out of scope but recommend in README. The plan should produce locally-runnable tests; CI wiring is its own follow-up.

## Cleanup

Before deleting, run grep verification:
```bash
grep -rn "IntegrationBlueprintEntity\|BlueprintDataUpdateCoordinator\|IntegrationBlueprintConfigEntry\|IntegrationBlueprintSwitch\|IntegrationBlueprintBinarySensor" custom_components/
```

Expected: only references in the files being deleted (`switch.py`, current `binary_sensor.py`, possibly `entity.py`/`data.py`). If any other file references them, fix in the same task before deletion.

Files to delete (after grep clean):
- `custom_components/retroarchievements/switch.py`
- `custom_components/retroarchievements/entity.py` (if unreferenced)
- `custom_components/retroarchievements/data.py` (if unreferenced)

Files to rewrite:
- `custom_components/retroarchievements/binary_sensor.py` (new content per Entity Specs).

## README Updates

Add sections:
- **New Entities** table: `sensor.aotw`, `binary_sensor.is_gaming`, `binary_sensor.aotw_unlocked`.
- **Events**: document payload of `retroarchievements_achievement_unlocked` and `retroarchievements_aotw_changed` with full field list. Include an example HA automation YAML triggering on a `points >= 25` filter.
- **Service**: `retroarchievements.refresh`.
- **Option**: `gaming_idle_threshold` (minutes).
- **Known limitation**: `aotw_unlocked` may read `False` briefly for long-ago unlocks until next detection cycle.

## Migration / Compatibility

- Existing entities unchanged.
- Existing options (`monitored_games`) still work.
- Users on `0.2.x` upgrading to `0.3.0` get new entities auto-added on next HA reload. No data migration required.
- No breaking config schema changes.

## Out-of-Scope / Follow-ups

- Sub-projects A (metrics), B (backlog), C (competitive) — separate specs.
- CI workflow wiring for `pytest`.
- TTL/eviction on `_game_extended_cache` (current: lives for coordinator lifetime; refreshes on HA restart).
- AOTW unlocked deep-check via `GetGameInfoAndUserProgress` (fixes the long-ago-unlock limitation).
- Translation files beyond `en.json`.
