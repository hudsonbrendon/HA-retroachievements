# Gamification & Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Achievement-of-the-Week sensor + binary sensor, achievement-unlocked event firing with enriched payload, an `is_gaming` binary sensor, and a manual `refresh` service to the HA RetroAchievements integration, with a full pytest test suite.

**Architecture:** Single extended `RetroAchievementsDataUpdateCoordinator` performs additional API fetches (AOTW, GetGameExtended), tracks previous achievement IDs and AOTW ID in memory, fires HA events on diffs, and caches enriched game data. A new `binary_sensor` platform replaces blueprint dead code. A `refresh` service is registered at integration setup.

**Tech Stack:** Python 3.12, Home Assistant 2025.2.4, `aiohttp`, `pytest-homeassistant-custom-component`, `aioresponses`.

**Spec:** [2026-05-18-gamification-events-design.md](../specs/2026-05-18-gamification-events-design.md)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `requirements_test.txt` | Create | Test dependencies (pytest, ha-custom-component, aioresponses). |
| `tests/__init__.py` | Create | Empty package marker. |
| `tests/conftest.py` | Create | Shared fixtures: mock API client, sample API payloads. |
| `tests/fixtures/user_summary.json` | Create | Sample `GetUserSummary` response. |
| `tests/fixtures/aotw.json` | Create | Sample `GetAchievementOfTheWeek` response. |
| `tests/fixtures/game_extended.json` | Create | Sample `GetGameExtended` response. |
| `tests/test_api.py` | Create | API client tests for new endpoints. |
| `tests/test_coordinator_helpers.py` | Create | Pure-logic helper tests. |
| `tests/test_coordinator_events.py` | Create | Event firing (achievement_unlocked + aotw_changed). |
| `tests/test_coordinator_is_aotw_unlocked.py` | Create | `is_aotw_unlocked` helper tests. |
| `tests/test_sensor_aotw.py` | Create | AOTW sensor state/attributes. |
| `tests/test_binary_sensor_is_gaming.py` | Create | `is_gaming` binary sensor logic. |
| `tests/test_binary_sensor_aotw_unlocked.py` | Create | `aotw_unlocked` binary sensor logic. |
| `tests/test_service_refresh.py` | Create | Service registration + invocation. |
| `tests/test_config_flow_options.py` | Create | Options flow with `gaming_idle_threshold`. |
| `custom_components/retroarchievements/api.py` | Modify | Add `async_get_achievement_of_the_week`, `async_get_game_extended`. |
| `custom_components/retroarchievements/const.py` | Modify | Add platform, constants, event names, service name. |
| `custom_components/retroarchievements/coordinator.py` | Modify | Diff tracking, event firing, cache, helpers. |
| `custom_components/retroarchievements/sensor.py` | Modify | Add `RetroAchievementsAOTWSensor`. |
| `custom_components/retroarchievements/binary_sensor.py` | Rewrite | `IsGamingBinarySensor`, `AOTWUnlockedBinarySensor`. |
| `custom_components/retroarchievements/__init__.py` | Modify | Register/unregister `refresh` service. |
| `custom_components/retroarchievements/config_flow.py` | Modify | Add `gaming_idle_threshold` to options. |
| `custom_components/retroarchievements/services.yaml` | Create | Declare `refresh` service. |
| `custom_components/retroarchievements/translations/en.json` | Modify | Add strings for new entities and option. |
| `custom_components/retroarchievements/manifest.json` | Modify | Bump version to `0.3.0`. |
| `custom_components/retroarchievements/switch.py` | Delete | Blueprint dead code. |
| `custom_components/retroarchievements/entity.py` | Delete (conditional) | Blueprint dead code if no live references. |
| `custom_components/retroarchievements/data.py` | Delete (conditional) | Blueprint dead code if no live references. |
| `README.md` | Modify | Document new entities, events, service, option. |

---

## Task 1: Set up pytest test infrastructure

**Files:**
- Create: `requirements_test.txt`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/__init__.py`
- Create: `pytest.ini`

- [ ] **Step 1: Create `requirements_test.txt`**

```
pytest>=8.0
pytest-asyncio>=0.23
pytest-homeassistant-custom-component>=0.13.180
aioresponses>=0.7
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
filterwarnings =
    ignore::DeprecationWarning
```

- [ ] **Step 3: Create `tests/__init__.py` and `tests/fixtures/__init__.py`**

Both files: empty content.

- [ ] **Step 4: Create `tests/conftest.py`**

```python
"""Shared pytest fixtures."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict | list:
    """Load a JSON fixture from tests/fixtures/."""
    return json.loads((FIXTURE_DIR / name).read_text())


@pytest.fixture
def user_summary_fixture() -> dict:
    """Return the sample user summary payload."""
    return load_fixture("user_summary.json")


@pytest.fixture
def aotw_fixture() -> dict:
    """Return the sample AOTW payload."""
    return load_fixture("aotw.json")


@pytest.fixture
def game_extended_fixture() -> dict:
    """Return the sample game extended payload."""
    return load_fixture("game_extended.json")


@pytest.fixture
def mock_api_client(user_summary_fixture, aotw_fixture, game_extended_fixture):
    """Return an AsyncMock API client preloaded with fixture responses."""
    client = AsyncMock()
    client._username = "TestUser"
    client.async_get_user_summary.return_value = user_summary_fixture
    client.async_get_user_recent_games.return_value = (
        user_summary_fixture.get("RecentlyPlayed", [])
    )
    client.async_get_achievement_of_the_week.return_value = aotw_fixture
    client.async_get_game_extended.return_value = game_extended_fixture
    client.async_get_user_progress.return_value = {}
    return client
```

- [ ] **Step 5: Install test deps and run pytest to verify discovery**

Run: `pip install -r requirements_test.txt && pytest --collect-only`
Expected: pytest discovers 0 tests but exits cleanly (no import errors).

- [ ] **Step 6: Commit**

```bash
git add requirements_test.txt pytest.ini tests/__init__.py tests/fixtures/__init__.py tests/conftest.py
git commit -m "test: add pytest infrastructure and shared fixtures"
```

---

## Task 2: Add fixture JSON files

**Files:**
- Create: `tests/fixtures/user_summary.json`
- Create: `tests/fixtures/aotw.json`
- Create: `tests/fixtures/game_extended.json`

- [ ] **Step 1: Create `tests/fixtures/user_summary.json`**

```json
{
  "ID": 12345,
  "User": "TestUser",
  "TotalPoints": 1500,
  "TotalTruePoints": 2100,
  "Rank": 5000,
  "Status": "Online",
  "RichPresenceMsg": "Playing Sonic the Hedgehog",
  "UserPic": "/UserPic/TestUser.png",
  "MemberSince": "2020-01-15 12:00:00",
  "LastActivity": {
    "ID": 1,
    "timestamp": "2026-05-18 12:00:00",
    "lastupdate": "2026-05-18 12:00:00"
  },
  "RecentAchievements": {
    "678": {
      "12345": {
        "ID": 12345,
        "GameID": 678,
        "GameTitle": "Sonic the Hedgehog",
        "ConsoleName": "Mega Drive",
        "Title": "First Blood",
        "Description": "Defeat your first enemy",
        "Points": 5,
        "BadgeName": "01234",
        "DateAwarded": "2026-05-18 11:55:00",
        "HardcoreMode": 1,
        "Author": "Devname"
      }
    }
  },
  "RecentlyPlayed": [
    {
      "GameID": 678,
      "ConsoleID": 1,
      "ConsoleName": "Mega Drive",
      "Title": "Sonic the Hedgehog",
      "ImageIcon": "/Images/sonic-icon.png",
      "ImageTitle": "/Images/sonic-title.png",
      "ImageIngame": "/Images/sonic-ingame.png",
      "ImageBoxArt": "/Images/sonic-box.png",
      "LastPlayed": "2026-05-18 11:50:00",
      "AchievementsTotal": 24
    }
  ]
}
```

- [ ] **Step 2: Create `tests/fixtures/aotw.json`**

```json
{
  "Achievement": {
    "ID": 99999,
    "Title": "Week Champion",
    "Description": "Beat the weekly challenge",
    "Points": 10,
    "BadgeName": "99999",
    "Author": "Devname"
  },
  "Game": {
    "ID": 5555,
    "Title": "Weekly Challenge Game",
    "ConsoleName": "NES",
    "ConsoleID": 7,
    "ImageIcon": "/Images/weekly-icon.png"
  },
  "StartAt": "2026-05-12T00:00:00.000Z"
}
```

- [ ] **Step 3: Create `tests/fixtures/game_extended.json`**

```json
{
  "ID": 678,
  "Title": "Sonic the Hedgehog",
  "ConsoleName": "Mega Drive",
  "ConsoleID": 1,
  "NumDistinctPlayers": 1000,
  "Achievements": {
    "12345": {
      "ID": 12345,
      "Title": "First Blood",
      "Description": "Defeat your first enemy",
      "Points": 5,
      "TrueRatio": 7,
      "BadgeName": "01234",
      "DisplayOrder": 1,
      "Author": "Devname",
      "NumAwarded": 125,
      "NumAwardedHardcore": 42
    }
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/
git commit -m "test: add API response fixtures"
```

---

## Task 3: API method `async_get_achievement_of_the_week`

**Files:**
- Modify: `custom_components/retroarchievements/api.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write the failing test in `tests/test_api.py`**

```python
"""Tests for the RetroAchievements API client."""
from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.retroarchievements.api import RetroAchievementsApiClient
from custom_components.retroarchievements.const import BASE_URL


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as s:
        yield s


async def test_get_achievement_of_the_week_returns_payload(
    session, aotw_fixture
):
    url = f"{BASE_URL}API_GetAchievementOfTheWeek.php"
    with aioresponses() as m:
        m.get(url, payload=aotw_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_achievement_of_the_week()
    assert result["Achievement"]["ID"] == 99999
    assert result["Game"]["Title"] == "Weekly Challenge Game"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_get_achievement_of_the_week_returns_payload -v`
Expected: FAIL with `AttributeError: 'RetroAchievementsApiClient' object has no attribute 'async_get_achievement_of_the_week'`.

- [ ] **Step 3: Add method to `custom_components/retroarchievements/api.py` after `async_get_user_recent_games`**

```python
    async def async_get_achievement_of_the_week(self) -> dict[str, Any]:
        """Get the current Achievement of the Week."""
        response = await self._api_wrapper(
            endpoint="API_GetAchievementOfTheWeek.php",
            params={"y": self._api_key},
        )
        return response if isinstance(response, dict) else {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_get_achievement_of_the_week_returns_payload -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/api.py tests/test_api.py
git commit -m "feat(api): add async_get_achievement_of_the_week"
```

---

## Task 4: API method `async_get_game_extended`

**Files:**
- Modify: `custom_components/retroarchievements/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Append failing test to `tests/test_api.py`**

```python
async def test_get_game_extended_returns_payload(session, game_extended_fixture):
    url = f"{BASE_URL}API_GetGameExtended.php"
    with aioresponses() as m:
        m.get(url, payload=game_extended_fixture)
        client = RetroAchievementsApiClient("TestUser", "key", session)
        result = await client.async_get_game_extended(678)
    assert result["NumDistinctPlayers"] == 1000
    assert "12345" in result["Achievements"]
    assert result["Achievements"]["12345"]["NumAwarded"] == 125
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_get_game_extended_returns_payload -v`
Expected: FAIL with `AttributeError: ... async_get_game_extended`.

- [ ] **Step 3: Add method to `custom_components/retroarchievements/api.py`**

```python
    async def async_get_game_extended(self, game_id: int) -> dict[str, Any]:
        """Get extended game metadata including per-achievement award counts."""
        response = await self._api_wrapper(
            endpoint="API_GetGameExtended.php",
            params={"i": game_id, "y": self._api_key},
        )
        return response if isinstance(response, dict) else {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_get_game_extended_returns_payload -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/api.py tests/test_api.py
git commit -m "feat(api): add async_get_game_extended"
```

---

## Task 5: Add new constants

**Files:**
- Modify: `custom_components/retroarchievements/const.py`

- [ ] **Step 1: Edit `custom_components/retroarchievements/const.py` — replace the `PLATFORMS = [Platform.SENSOR]` line and append new constants**

Replace:
```python
PLATFORMS = [Platform.SENSOR]
```
With:
```python
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
```

Append at the end of the file:
```python
# Options
CONF_GAMING_IDLE_THRESHOLD = "gaming_idle_threshold"
DEFAULT_GAMING_IDLE_THRESHOLD = 5  # minutes

# Services
SERVICE_REFRESH = "refresh"

# Events
EVENT_ACHIEVEMENT_UNLOCKED = f"{DOMAIN}_achievement_unlocked"
EVENT_AOTW_CHANGED = f"{DOMAIN}_aotw_changed"
```

- [ ] **Step 2: Run quick import check**

Run: `python -c "from custom_components.retroarchievements import const; print(const.EVENT_ACHIEVEMENT_UNLOCKED, const.EVENT_AOTW_CHANGED, const.SERVICE_REFRESH, const.DEFAULT_GAMING_IDLE_THRESHOLD)"`
Expected: output `retroarchievements_achievement_unlocked retroarchievements_aotw_changed refresh 5`.

- [ ] **Step 3: Commit**

```bash
git add custom_components/retroarchievements/const.py
git commit -m "feat: add constants for events, refresh service, idle threshold option"
```

---

## Task 6: Coordinator helper — `_extract_achievement_ids`

**Files:**
- Modify: `custom_components/retroarchievements/coordinator.py`
- Create: `tests/test_coordinator_helpers.py`

- [ ] **Step 1: Write failing test in `tests/test_coordinator_helpers.py`**

```python
"""Tests for pure-logic helpers on the coordinator."""
from __future__ import annotations

from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


def test_extract_achievement_ids_from_recent_achievements():
    user_summary = {
        "RecentAchievements": {
            "678": {
                "12345": {"ID": 12345},
                "67890": {"ID": 67890},
            },
            "999": {
                "55555": {"ID": 55555},
            },
        }
    }
    result = RetroAchievementsDataUpdateCoordinator._extract_achievement_ids(
        user_summary
    )
    assert result == {12345, 67890, 55555}


def test_extract_achievement_ids_empty_input():
    assert (
        RetroAchievementsDataUpdateCoordinator._extract_achievement_ids({}) == set()
    )
    assert (
        RetroAchievementsDataUpdateCoordinator._extract_achievement_ids(
            {"RecentAchievements": None}
        )
        == set()
    )


def test_extract_achievement_ids_skips_non_integer_keys():
    user_summary = {
        "RecentAchievements": {
            "678": {"abc": {"ID": 0}, "12345": {"ID": 12345}}
        }
    }
    result = RetroAchievementsDataUpdateCoordinator._extract_achievement_ids(
        user_summary
    )
    assert result == {12345}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_coordinator_helpers.py::test_extract_achievement_ids_from_recent_achievements -v`
Expected: FAIL with `AttributeError: type object 'RetroAchievementsDataUpdateCoordinator' has no attribute '_extract_achievement_ids'`.

- [ ] **Step 3: Add static method to `custom_components/retroarchievements/coordinator.py`**

Inside the class body (e.g. just before `_async_update_data`):
```python
    @staticmethod
    def _extract_achievement_ids(user_summary: dict) -> set[int]:
        """Return set of achievement IDs across all games in RecentAchievements."""
        ids: set[int] = set()
        for _game_id, achievements in (
            (user_summary or {}).get("RecentAchievements") or {}
        ).items():
            for ach_id in (achievements or {}).keys():
                try:
                    ids.add(int(ach_id))
                except (TypeError, ValueError):
                    continue
        return ids
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_coordinator_helpers.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/coordinator.py tests/test_coordinator_helpers.py
git commit -m "feat(coordinator): add _extract_achievement_ids helper"
```

---

## Task 7: Coordinator helper — `_find_achievement`

**Files:**
- Modify: `custom_components/retroarchievements/coordinator.py`
- Modify: `tests/test_coordinator_helpers.py`

- [ ] **Step 1: Append failing tests**

```python
def test_find_achievement_returns_payload_and_game_id():
    user_summary = {
        "RecentAchievements": {
            "678": {
                "12345": {"ID": 12345, "Title": "First Blood"},
            }
        }
    }
    ach, game_id = RetroAchievementsDataUpdateCoordinator._find_achievement(
        12345, user_summary
    )
    assert ach == {"ID": 12345, "Title": "First Blood"}
    assert game_id == 678


def test_find_achievement_missing_returns_none():
    ach, game_id = RetroAchievementsDataUpdateCoordinator._find_achievement(
        99999, {"RecentAchievements": {}}
    )
    assert ach is None
    assert game_id is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_coordinator_helpers.py::test_find_achievement_returns_payload_and_game_id -v`
Expected: FAIL `AttributeError ... _find_achievement`.

- [ ] **Step 3: Add static method to coordinator**

```python
    @staticmethod
    def _find_achievement(
        ach_id: int, user_summary: dict
    ) -> tuple[dict | None, int | None]:
        """Locate achievement payload and its game_id in RecentAchievements."""
        for game_id, achievements in (
            (user_summary or {}).get("RecentAchievements") or {}
        ).items():
            if not isinstance(achievements, dict):
                continue
            if str(ach_id) in achievements:
                try:
                    return achievements[str(ach_id)], int(game_id)
                except (TypeError, ValueError):
                    return achievements[str(ach_id)], None
            if ach_id in achievements:
                try:
                    return achievements[ach_id], int(game_id)
                except (TypeError, ValueError):
                    return achievements[ach_id], None
        return None, None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_coordinator_helpers.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/coordinator.py tests/test_coordinator_helpers.py
git commit -m "feat(coordinator): add _find_achievement helper"
```

---

## Task 8: Coordinator helper — `_build_enriched_payload`

**Files:**
- Modify: `custom_components/retroarchievements/coordinator.py`
- Modify: `tests/test_coordinator_helpers.py`

- [ ] **Step 1: Append failing tests**

```python
def test_build_enriched_payload_full(user_summary_fixture, game_extended_fixture):
    coord = RetroAchievementsDataUpdateCoordinator.__new__(
        RetroAchievementsDataUpdateCoordinator
    )

    class _C:
        _username = "TestUser"

    coord.api_client = _C()
    ach = user_summary_fixture["RecentAchievements"]["678"]["12345"]
    payload = coord._build_enriched_payload(ach, 678, game_extended_fixture)
    assert payload["achievement_id"] == 12345
    assert payload["title"] == "First Blood"
    assert payload["description"] == "Defeat your first enemy"
    assert payload["points"] == 5
    assert payload["true_points"] == 7
    assert payload["badge_url"] == "https://retroachievements.org/Badge/01234.png"
    assert payload["game_id"] == 678
    assert payload["game_title"] == "Sonic the Hedgehog"
    assert payload["console_name"] == "Mega Drive"
    assert payload["console_id"] == 1
    assert payload["date_awarded"] == "2026-05-18 11:55:00"
    assert payload["hardcore"] is True
    assert payload["rarity_pct"] == 12.5
    assert payload["rarity_hardcore_pct"] == 4.2
    assert payload["display_order"] == 1
    assert payload["author"] == "Devname"
    assert payload["username"] == "TestUser"


def test_build_enriched_payload_handles_empty_game_ext():
    coord = RetroAchievementsDataUpdateCoordinator.__new__(
        RetroAchievementsDataUpdateCoordinator
    )

    class _C:
        _username = "TestUser"

    coord.api_client = _C()
    ach = {
        "ID": 1,
        "Title": "t",
        "Description": "d",
        "Points": 5,
        "BadgeName": "00001",
        "GameTitle": "g",
        "ConsoleName": "c",
        "DateAwarded": "2026-05-18 12:00:00",
        "HardcoreMode": 0,
        "Author": "a",
    }
    payload = coord._build_enriched_payload(ach, 678, {})
    assert payload["achievement_id"] == 1
    assert payload["true_points"] is None
    assert payload["rarity_pct"] is None
    assert payload["rarity_hardcore_pct"] is None
    assert payload["hardcore"] is False
    assert payload["author"] == "a"


def test_build_enriched_payload_zero_players_returns_none_rarity():
    coord = RetroAchievementsDataUpdateCoordinator.__new__(
        RetroAchievementsDataUpdateCoordinator
    )

    class _C:
        _username = "TestUser"

    coord.api_client = _C()
    ach = {"ID": 1, "BadgeName": "x"}
    game_ext = {"NumDistinctPlayers": 0, "Achievements": {"1": {"NumAwarded": 0}}}
    payload = coord._build_enriched_payload(ach, 678, game_ext)
    assert payload["rarity_pct"] is None
    assert payload["rarity_hardcore_pct"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_coordinator_helpers.py::test_build_enriched_payload_full -v`
Expected: FAIL `AttributeError ... _build_enriched_payload`.

- [ ] **Step 3: Add method to coordinator**

```python
    def _build_enriched_payload(
        self, ach: dict, game_id: int, game_ext: dict
    ) -> dict:
        """Build the enriched event payload for an unlocked achievement."""
        ach_id = ach.get("ID")
        badge = ach.get("BadgeName")
        game_ach = (game_ext.get("Achievements") or {}).get(str(ach_id), {}) or {}
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
            "badge_url": (
                f"https://retroachievements.org/Badge/{badge}.png" if badge else None
            ),
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_coordinator_helpers.py -v`
Expected: 8 PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/coordinator.py tests/test_coordinator_helpers.py
git commit -m "feat(coordinator): add _build_enriched_payload"
```

---

## Task 9: Coordinator state + AOTW fetch + first-run gate

**Files:**
- Modify: `custom_components/retroarchievements/coordinator.py`
- Create: `tests/test_coordinator_events.py`

- [ ] **Step 1: Write failing test in `tests/test_coordinator_events.py`**

```python
"""Tests for coordinator event firing (achievement_unlocked, aotw_changed)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import (
    DOMAIN,
    EVENT_ACHIEVEMENT_UNLOCKED,
    EVENT_AOTW_CHANGED,
)
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="test_entry",
    )


async def test_first_run_does_not_fire_events(
    hass, mock_api_client, mock_entry
):
    """On the very first refresh, no achievement_unlocked events fire."""
    fired = []
    hass.bus.async_listen(EVENT_ACHIEVEMENT_UNLOCKED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_coordinator_events.py::test_first_run_does_not_fire_events -v`
Expected: FAIL — coordinator does not fetch AOTW or set `_first_run` yet.

- [ ] **Step 3: Modify `custom_components/retroarchievements/coordinator.py`**

Replace the imports + class body. New full content:

```python
"""Data update coordinator for the RetroAchievements integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import RetroAchievementsApiClient
from .const import (
    CONF_GAMING_IDLE_THRESHOLD,
    DEFAULT_GAMING_IDLE_THRESHOLD,
    DOMAIN,
    EVENT_ACHIEVEMENT_UNLOCKED,
    EVENT_AOTW_CHANGED,
    LOGGER,
    UPDATE_INTERVAL,
)


class RetroAchievementsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RetroAchievements data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: RetroAchievementsApiClient,
        entry: ConfigEntry,
        update_interval: int = UPDATE_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        self.api_client = api_client
        self.entry = entry
        self.monitored_games: set[int] = set()
        self._previous_achievement_ids: set[int] = set()
        self._previous_aotw_id: int | None = None
        self._game_extended_cache: dict[int, dict] = {}
        self._first_run: bool = True
        self._idle_threshold_minutes: int = (entry.options or {}).get(
            CONF_GAMING_IDLE_THRESHOLD, DEFAULT_GAMING_IDLE_THRESHOLD
        )

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    @staticmethod
    def _extract_achievement_ids(user_summary: dict) -> set[int]:
        """Return set of achievement IDs across all games in RecentAchievements."""
        ids: set[int] = set()
        for _game_id, achievements in (
            (user_summary or {}).get("RecentAchievements") or {}
        ).items():
            for ach_id in (achievements or {}).keys():
                try:
                    ids.add(int(ach_id))
                except (TypeError, ValueError):
                    continue
        return ids

    @staticmethod
    def _find_achievement(
        ach_id: int, user_summary: dict
    ) -> tuple[dict | None, int | None]:
        """Locate achievement payload and its game_id in RecentAchievements."""
        for game_id, achievements in (
            (user_summary or {}).get("RecentAchievements") or {}
        ).items():
            if not isinstance(achievements, dict):
                continue
            if str(ach_id) in achievements:
                try:
                    return achievements[str(ach_id)], int(game_id)
                except (TypeError, ValueError):
                    return achievements[str(ach_id)], None
            if ach_id in achievements:
                try:
                    return achievements[ach_id], int(game_id)
                except (TypeError, ValueError):
                    return achievements[ach_id], None
        return None, None

    def _build_enriched_payload(
        self, ach: dict, game_id: int, game_ext: dict
    ) -> dict:
        """Build the enriched event payload for an unlocked achievement."""
        ach_id = ach.get("ID")
        badge = ach.get("BadgeName")
        game_ach = (game_ext.get("Achievements") or {}).get(str(ach_id), {}) or {}
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
            "badge_url": (
                f"https://retroachievements.org/Badge/{badge}.png" if badge else None
            ),
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

    async def _get_cached_game_extended(self, game_id: int) -> dict:
        """Return cached GetGameExtended response for game_id, fetching once."""
        if game_id in self._game_extended_cache:
            return self._game_extended_cache[game_id]
        try:
            data = await self.api_client.async_get_game_extended(game_id)
            if isinstance(data, dict):
                self._game_extended_cache[game_id] = data
                return data
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.warning(
                "Failed to fetch GetGameExtended for game_id=%s: %s", game_id, err
            )
        return {}

    async def _async_update_data(self):
        try:
            user_summary, game_data, aotw = await asyncio.gather(
                self.api_client.async_get_user_summary(),
                self._get_game_data(),
                self._safe_get_aotw(),
            )

            current_ids = self._extract_achievement_ids(user_summary)
            aotw_id = ((aotw or {}).get("Achievement") or {}).get("ID")

            if not self._first_run:
                new_ids = current_ids - self._previous_achievement_ids
                for ach_id in new_ids:
                    await self._fire_achievement_unlocked(ach_id, user_summary)
                if aotw_id and aotw_id != self._previous_aotw_id:
                    self._fire_aotw_changed(aotw)

            self._previous_achievement_ids = current_ids
            self._previous_aotw_id = aotw_id
            self._first_run = False

            return {
                "user_summary": user_summary,
                "recent_games": user_summary.get("RecentlyPlayed", []),
                "RecentAchievements": user_summary.get("RecentAchievements", {}),
                "aotw": aotw or {},
                **game_data,
            }
        except Exception as error:
            LOGGER.error("Unexpected error fetching retroachievements data: %s", error)
            raise

    async def _safe_get_aotw(self) -> dict:
        """Fetch AOTW; return empty dict on error so refresh continues."""
        try:
            data = await self.api_client.async_get_achievement_of_the_week()
            return data if isinstance(data, dict) else {}
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.warning("Failed to fetch Achievement of the Week: %s", err)
            return {}

    async def _fire_achievement_unlocked(
        self, ach_id: int, user_summary: dict
    ) -> None:
        """Look up, enrich, and fire the achievement_unlocked event."""
        ach, game_id = self._find_achievement(ach_id, user_summary)
        if ach is None or game_id is None:
            LOGGER.debug(
                "Achievement %s detected but payload not found in user summary",
                ach_id,
            )
            return
        game_ext = await self._get_cached_game_extended(game_id)
        payload = self._build_enriched_payload(ach, game_id, game_ext)
        self.hass.bus.async_fire(EVENT_ACHIEVEMENT_UNLOCKED, payload)

    def _fire_aotw_changed(self, aotw: dict) -> None:
        """Fire the aotw_changed event."""
        ach = aotw.get("Achievement", {}) or {}
        game = aotw.get("Game", {}) or {}
        badge = ach.get("BadgeName")
        self.hass.bus.async_fire(
            EVENT_AOTW_CHANGED,
            {
                "achievement_id": ach.get("ID"),
                "title": ach.get("Title"),
                "description": ach.get("Description"),
                "points": ach.get("Points"),
                "badge_url": (
                    f"https://retroachievements.org/Badge/{badge}.png"
                    if badge
                    else None
                ),
                "game_id": game.get("ID"),
                "game_title": game.get("Title"),
                "console_name": game.get("ConsoleName"),
                "week_start": aotw.get("StartAt"),
                "author": ach.get("Author"),
            },
        )

    def is_aotw_unlocked(self) -> bool:
        """Return True if the user already unlocked the current AOTW."""
        if not self.data:
            return False
        aotw = (self.data.get("aotw") or {})
        ach_id = (aotw.get("Achievement") or {}).get("ID")
        if not ach_id:
            return False
        try:
            ach_id_int = int(ach_id)
        except (TypeError, ValueError):
            return False
        if ach_id_int in self._previous_achievement_ids:
            return True
        recent = (self.data.get("user_summary") or {}).get(
            "RecentAchievements"
        ) or {}
        for _game_id, achievements in recent.items():
            if not isinstance(achievements, dict):
                continue
            if str(ach_id) in achievements or ach_id in achievements:
                return True
        return False

    async def _get_game_data(self):
        monitored_game_ids: set[int] = set()
        if self.entry.options:
            game_ids_str = self.entry.options.get("monitored_games", "")
            for game_id in game_ids_str.splitlines():
                if game_id.strip():
                    try:
                        monitored_game_ids.add(int(game_id.strip()))
                    except ValueError:
                        LOGGER.warning("Invalid game ID: %s", game_id)

        self.monitored_games = monitored_game_ids

        game_data = {"Awarded": {}}
        if not monitored_game_ids:
            return game_data

        tasks = [
            self.api_client.async_get_user_progress(game_id)
            for game_id in monitored_game_ids
        ]

        if tasks:
            game_progresses = await asyncio.gather(*tasks, return_exceptions=True)

            for i, game_progress in enumerate(game_progresses):
                if isinstance(game_progress, Exception):
                    LOGGER.error("Error fetching game progress: %s", game_progress)
                    continue

                game_id = str(list(monitored_game_ids)[i])
                game_data["Awarded"][game_id] = game_progress

        return game_data
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_coordinator_events.py::test_first_run_does_not_fire_events -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/coordinator.py tests/test_coordinator_events.py
git commit -m "feat(coordinator): add AOTW fetch + first-run event gate"
```

---

## Task 10: Coordinator — fire `achievement_unlocked` on diff

**Files:**
- Modify: `tests/test_coordinator_events.py`

- [ ] **Step 1: Append failing test**

```python
async def test_new_achievement_fires_event_with_enriched_payload(
    hass, mock_api_client, mock_entry, user_summary_fixture
):
    """After first refresh sets baseline, a new achievement fires the event."""
    fired = []
    hass.bus.async_listen(EVENT_ACHIEVEMENT_UNLOCKED, lambda e: fired.append(e))

    # First refresh: baseline contains achievement 12345
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired == []

    # Second refresh: add a new achievement
    new_summary = {
        **user_summary_fixture,
        "RecentAchievements": {
            "678": {
                **user_summary_fixture["RecentAchievements"]["678"],
                "12346": {
                    "ID": 12346,
                    "GameID": 678,
                    "GameTitle": "Sonic the Hedgehog",
                    "ConsoleName": "Mega Drive",
                    "Title": "Second Blood",
                    "Description": "Defeat your second enemy",
                    "Points": 10,
                    "BadgeName": "01235",
                    "DateAwarded": "2026-05-18 12:05:00",
                    "HardcoreMode": 0,
                    "Author": "Devname",
                },
            }
        },
    }
    mock_api_client.async_get_user_summary.return_value = new_summary
    await coord.async_refresh()
    await hass.async_block_till_done()

    assert len(fired) == 1
    payload = fired[0].data
    assert payload["achievement_id"] == 12346
    assert payload["title"] == "Second Blood"
    assert payload["points"] == 10
    assert payload["hardcore"] is False
    assert payload["badge_url"] == "https://retroachievements.org/Badge/01235.png"
    assert payload["game_id"] == 678
    assert payload["rarity_pct"] is None  # 12346 not in game_extended fixture
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_coordinator_events.py::test_new_achievement_fires_event_with_enriched_payload -v`
Expected: PASS (logic already implemented in Task 9; this test just verifies the path).

- [ ] **Step 3: Append failing test for no-diff path**

```python
async def test_no_new_achievements_fires_no_events(
    hass, mock_api_client, mock_entry
):
    fired = []
    hass.bus.async_listen(EVENT_ACHIEVEMENT_UNLOCKED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await coord.async_refresh()  # same data, no diff
    await hass.async_block_till_done()
    assert fired == []
```

- [ ] **Step 4: Run all event tests**

Run: `pytest tests/test_coordinator_events.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_coordinator_events.py
git commit -m "test(coordinator): verify achievement_unlocked event diff behaviour"
```

---

## Task 11: Coordinator — fire `aotw_changed` on AOTW ID change

**Files:**
- Modify: `tests/test_coordinator_events.py`

- [ ] **Step 1: Append failing tests**

```python
async def test_aotw_change_fires_event(
    hass, mock_api_client, mock_entry, aotw_fixture
):
    fired = []
    hass.bus.async_listen(EVENT_AOTW_CHANGED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()  # baseline AOTW = 99999
    assert fired == []

    new_aotw = {
        **aotw_fixture,
        "Achievement": {**aotw_fixture["Achievement"], "ID": 88888, "Title": "New"},
    }
    mock_api_client.async_get_achievement_of_the_week.return_value = new_aotw
    await coord.async_refresh()
    await hass.async_block_till_done()

    assert len(fired) == 1
    assert fired[0].data["achievement_id"] == 88888
    assert fired[0].data["title"] == "New"


async def test_aotw_unchanged_fires_no_event(hass, mock_api_client, mock_entry):
    fired = []
    hass.bus.async_listen(EVENT_AOTW_CHANGED, lambda e: fired.append(e))
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    await coord.async_refresh()
    await hass.async_block_till_done()
    assert fired == []
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_coordinator_events.py -v`
Expected: 5 PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_coordinator_events.py
git commit -m "test(coordinator): verify aotw_changed event firing"
```

---

## Task 12: Coordinator — `is_aotw_unlocked` helper tests

**Files:**
- Create: `tests/test_coordinator_is_aotw_unlocked.py`

- [ ] **Step 1: Create test file with failing tests**

```python
"""Tests for RetroAchievementsDataUpdateCoordinator.is_aotw_unlocked."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="t",
    )


async def test_is_aotw_unlocked_false_when_no_data(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    assert coord.is_aotw_unlocked() is False


async def test_is_aotw_unlocked_true_when_in_recent_achievements(
    hass, mock_api_client, mock_entry, aotw_fixture, user_summary_fixture
):
    # Make AOTW ID match an ID in user_summary RecentAchievements
    aotw = {
        **aotw_fixture,
        "Achievement": {**aotw_fixture["Achievement"], "ID": 12345},
    }
    mock_api_client.async_get_achievement_of_the_week.return_value = aotw
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    assert coord.is_aotw_unlocked() is True


async def test_is_aotw_unlocked_false_when_not_in_recent(
    hass, mock_api_client, mock_entry
):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    # AOTW fixture ID = 99999, user summary fixture does not contain it
    assert coord.is_aotw_unlocked() is False
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_coordinator_is_aotw_unlocked.py -v`
Expected: 3 PASS (logic already implemented in Task 9).

- [ ] **Step 3: Commit**

```bash
git add tests/test_coordinator_is_aotw_unlocked.py
git commit -m "test(coordinator): verify is_aotw_unlocked helper"
```

---

## Task 13: AOTW sensor entity

**Files:**
- Modify: `custom_components/retroarchievements/sensor.py`
- Create: `tests/test_sensor_aotw.py`

- [ ] **Step 1: Write failing test in `tests/test_sensor_aotw.py`**

```python
"""Tests for the AOTW sensor."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)
from custom_components.retroarchievements.sensor import (
    RetroAchievementsAOTWSensor,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="t",
    )


async def test_aotw_sensor_state_and_attributes(
    hass, mock_api_client, mock_entry
):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWSensor(coord, "TestUser")
    assert sensor.native_value == "Week Champion"
    attrs = sensor.extra_state_attributes
    assert attrs["achievement_id"] == 99999
    assert attrs["points"] == 10
    assert attrs["game_id"] == 5555
    assert attrs["game_title"] == "Weekly Challenge Game"
    assert attrs["console_name"] == "NES"
    assert attrs["badge_url"] == "https://retroachievements.org/Badge/99999.png"
    assert attrs["week_start"] == "2026-05-12T00:00:00.000Z"
    assert attrs["author"] == "Devname"


async def test_aotw_sensor_state_when_no_aotw(hass, mock_api_client, mock_entry):
    mock_api_client.async_get_achievement_of_the_week.return_value = {}
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWSensor(coord, "TestUser")
    assert sensor.native_value is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sensor_aotw.py -v`
Expected: FAIL `ImportError: cannot import name 'RetroAchievementsAOTWSensor'`.

- [ ] **Step 3: Add AOTW sensor to `custom_components/retroarchievements/sensor.py`**

Add this class at the bottom of the file (after `RetroAchievementsRecentlyPlayedSensor`):

```python
class RetroAchievementsAOTWSensor(RetroAchievementsBaseSensor):
    """Representation of the Achievement of the Week sensor."""

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_unique_id = f"{DOMAIN}_{username}_aotw"
        self._attr_translation_key = "aotw"
        self._attr_has_entity_name = True
        self._attr_icon = "mdi:calendar-star"

    @property
    def native_value(self):
        """Return the AOTW title or None."""
        aotw = (self.coordinator.data or {}).get("aotw") or {}
        return (aotw.get("Achievement") or {}).get("Title")

    @property
    def extra_state_attributes(self):
        """Return AOTW attributes."""
        aotw = (self.coordinator.data or {}).get("aotw") or {}
        ach = aotw.get("Achievement") or {}
        game = aotw.get("Game") or {}
        badge = ach.get("BadgeName")
        return {
            "achievement_id": ach.get("ID"),
            "description": ach.get("Description"),
            "points": ach.get("Points"),
            "badge_url": (
                f"https://retroachievements.org/Badge/{badge}.png" if badge else None
            ),
            "game_id": game.get("ID"),
            "game_title": game.get("Title"),
            "console_name": game.get("ConsoleName"),
            "week_start": aotw.get("StartAt"),
            "author": ach.get("Author"),
        }
```

- [ ] **Step 4: Wire the sensor into `async_setup_entry`**

In `custom_components/retroarchievements/sensor.py`, inside `async_setup_entry`, after the `RecentAchievementsSensor` block (around line 105), add:

```python
        entities.append(
            RetroAchievementsAOTWSensor(
                coordinator=coordinator,
                username=username,
            )
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_sensor_aotw.py -v`
Expected: 2 PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/retroarchievements/sensor.py tests/test_sensor_aotw.py
git commit -m "feat(sensor): add Achievement of the Week sensor"
```

---

## Task 14: Delete blueprint dead code

**Files:**
- Delete: `custom_components/retroarchievements/switch.py`
- Delete (conditional): `custom_components/retroarchievements/entity.py`
- Delete (conditional): `custom_components/retroarchievements/data.py`

- [ ] **Step 1: Verify no live references**

Run:
```bash
grep -rn "IntegrationBlueprintEntity\|BlueprintDataUpdateCoordinator\|IntegrationBlueprintConfigEntry\|IntegrationBlueprintSwitch\|IntegrationBlueprintBinarySensor" custom_components/
```
Expected: matches only in `switch.py`, `binary_sensor.py`, `entity.py`, `data.py` (the files being removed/rewritten). If anything else matches, STOP and fix that file first.

- [ ] **Step 2: Delete `switch.py`**

```bash
rm custom_components/retroarchievements/switch.py
```

- [ ] **Step 3: Check `entity.py` references**

Run: `grep -rn "from .entity\|from custom_components.retroarchievements.entity" custom_components/ tests/`
If empty → safe to delete. If anything references it, leave the file alone for now.

- [ ] **Step 4: Delete `entity.py` if unreferenced**

```bash
rm custom_components/retroarchievements/entity.py
```

- [ ] **Step 5: Check `data.py` references**

Run: `grep -rn "from .data\|from custom_components.retroarchievements.data" custom_components/ tests/`
If empty → safe to delete.

- [ ] **Step 6: Delete `data.py` if unreferenced**

```bash
rm custom_components/retroarchievements/data.py
```

- [ ] **Step 7: Run full test suite to ensure nothing broke**

Run: `pytest tests/ -v`
Expected: all previously-passing tests still pass; integration imports clean.

- [ ] **Step 8: Commit**

```bash
git add -A custom_components/retroarchievements/
git commit -m "chore: remove blueprint dead code (switch/entity/data)"
```

---

## Task 15: Rewrite `binary_sensor.py` — `is_gaming`

**Files:**
- Rewrite: `custom_components/retroarchievements/binary_sensor.py`
- Create: `tests/test_binary_sensor_is_gaming.py`

- [ ] **Step 1: Write failing test in `tests/test_binary_sensor_is_gaming.py`**

```python
"""Tests for the is_gaming binary sensor."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.binary_sensor import (
    RetroAchievementsIsGamingBinarySensor,
)
from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


def _make_coord_with_data(hass, summary: dict, idle_threshold: int = 5):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "k"},
        options={"gaming_idle_threshold": idle_threshold},
        entry_id="t",
    )
    api_client = MagicMock()
    coord = RetroAchievementsDataUpdateCoordinator(hass, api_client, entry)
    coord.data = {"user_summary": summary}
    return coord


def _ts_minutes_ago(minutes: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


async def test_is_gaming_true_when_all_conditions_met(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(1)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is True


async def test_is_gaming_false_when_rich_presence_empty(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(1)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_false_when_status_offline(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Offline",
            "LastActivity": {"timestamp": _ts_minutes_ago(1)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_false_when_activity_stale(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(30)},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_respects_configurable_threshold(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": _ts_minutes_ago(20)},
        },
        idle_threshold=30,
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is True


async def test_is_gaming_false_when_last_activity_missing(hass):
    coord = _make_coord_with_data(
        hass,
        {"RichPresenceMsg": "Playing Sonic", "Status": "Online"},
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False


async def test_is_gaming_false_on_unparseable_timestamp(hass):
    coord = _make_coord_with_data(
        hass,
        {
            "RichPresenceMsg": "Playing Sonic",
            "Status": "Online",
            "LastActivity": {"timestamp": "not-a-date"},
        },
    )
    sensor = RetroAchievementsIsGamingBinarySensor(coord, "TestUser")
    assert sensor.is_on is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_binary_sensor_is_gaming.py -v`
Expected: FAIL `ImportError: cannot import name 'RetroAchievementsIsGamingBinarySensor'`.

- [ ] **Step 3: Write new `custom_components/retroarchievements/binary_sensor.py` from scratch**

```python
"""Binary sensors for the RetroAchievements integration."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_USERNAME, DOMAIN
from .coordinator import RetroAchievementsDataUpdateCoordinator


def _user_device_info(username: str) -> DeviceInfo:
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, f"{username}")},
        manufacturer="RetroAchievements",
        name=f"RetroAchievements {username}",
        configuration_url=f"https://retroachievements.org/user/{username}",
        model="User Profile",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors based on a config entry."""
    username = entry.data[CONF_USERNAME]
    coordinator: RetroAchievementsDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]["coordinator"]
    async_add_entities(
        [
            RetroAchievementsIsGamingBinarySensor(coordinator, username),
            RetroAchievementsAOTWUnlockedBinarySensor(coordinator, username),
        ],
        True,
    )


class RetroAchievementsIsGamingBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that is ON while the user is actively gaming."""

    _attr_has_entity_name = True
    _attr_translation_key = "is_gaming"
    _attr_icon = "mdi:gamepad-circle"

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        super().__init__(coordinator)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_is_gaming"
        self._attr_device_info = _user_device_info(username)

    @property
    def is_on(self) -> bool:
        data = (self.coordinator.data or {}).get("user_summary") or {}
        rich = (data.get("RichPresenceMsg") or "").strip()
        status = data.get("Status", "")
        if not rich or status != "Online":
            return False
        last_activity = data.get("LastActivity") or {}
        ts = last_activity.get("timestamp") or last_activity.get("lastupdate")
        if not ts:
            return False
        try:
            normalized = ts.replace("Z", "+00:00").replace(" ", "T")
            last = datetime.fromisoformat(normalized)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            return False
        threshold_seconds = self.coordinator._idle_threshold_minutes * 60
        now = datetime.now(timezone.utc)
        return (now - last).total_seconds() <= threshold_seconds


class RetroAchievementsAOTWUnlockedBinarySensor(
    CoordinatorEntity, BinarySensorEntity
):
    """Binary sensor that is ON when the user has unlocked the current AOTW."""

    _attr_has_entity_name = True
    _attr_translation_key = "aotw_unlocked"

    def __init__(
        self,
        coordinator: RetroAchievementsDataUpdateCoordinator,
        username: str,
    ) -> None:
        super().__init__(coordinator)
        self.username = username
        self._attr_unique_id = f"{DOMAIN}_{username}_aotw_unlocked"
        self._attr_device_info = _user_device_info(username)

    @property
    def icon(self) -> str:
        return "mdi:trophy" if self.is_on else "mdi:trophy-broken"

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_aotw_unlocked()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_binary_sensor_is_gaming.py -v`
Expected: 7 PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/binary_sensor.py tests/test_binary_sensor_is_gaming.py
git commit -m "feat(binary_sensor): add is_gaming + aotw_unlocked binary sensors"
```

---

## Task 16: Binary sensor — `aotw_unlocked` test

**Files:**
- Create: `tests/test_binary_sensor_aotw_unlocked.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for the aotw_unlocked binary sensor."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.retroarchievements.binary_sensor import (
    RetroAchievementsAOTWUnlockedBinarySensor,
)
from custom_components.retroarchievements.const import DOMAIN
from custom_components.retroarchievements.coordinator import (
    RetroAchievementsDataUpdateCoordinator,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"username": "TestUser", "api_key": "key"},
        options={},
        entry_id="t",
    )


async def test_aotw_unlocked_true(
    hass, mock_api_client, mock_entry, aotw_fixture
):
    aotw = {
        **aotw_fixture,
        "Achievement": {**aotw_fixture["Achievement"], "ID": 12345},
    }
    mock_api_client.async_get_achievement_of_the_week.return_value = aotw
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWUnlockedBinarySensor(coord, "TestUser")
    assert sensor.is_on is True
    assert sensor.icon == "mdi:trophy"


async def test_aotw_unlocked_false(hass, mock_api_client, mock_entry):
    coord = RetroAchievementsDataUpdateCoordinator(hass, mock_api_client, mock_entry)
    await coord.async_refresh()
    sensor = RetroAchievementsAOTWUnlockedBinarySensor(coord, "TestUser")
    assert sensor.is_on is False
    assert sensor.icon == "mdi:trophy-broken"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_binary_sensor_aotw_unlocked.py -v`
Expected: 2 PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_binary_sensor_aotw_unlocked.py
git commit -m "test(binary_sensor): verify aotw_unlocked behaviour"
```

---

## Task 17: Register `refresh` service

**Files:**
- Modify: `custom_components/retroarchievements/__init__.py`
- Create: `tests/test_service_refresh.py`
- Create: `custom_components/retroarchievements/services.yaml`

- [ ] **Step 1: Write failing test in `tests/test_service_refresh.py`**

```python
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


async def test_service_registered_on_setup(hass, mock_api_client, mock_entry):
    mock_entry.add_to_hass(hass)
    with patch(
        "custom_components.retroarchievements.RetroAchievementsApiClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()
    assert hass.services.has_service(DOMAIN, SERVICE_REFRESH)


async def test_service_calls_coordinator_refresh(
    hass, mock_api_client, mock_entry
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
    hass, mock_api_client, mock_entry
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_service_refresh.py -v`
Expected: FAIL — service not registered.

- [ ] **Step 3: Modify `custom_components/retroarchievements/__init__.py`**

Replace file content with:

```python
"""The RetroAchievements integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RetroAchievementsApiClient
from .const import CONF_USERNAME, DOMAIN, LOGGER, PLATFORMS, SERVICE_REFRESH
from .coordinator import RetroAchievementsDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RetroAchievements from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_client = RetroAchievementsApiClient(
        username=entry.data[CONF_USERNAME],
        api_key=entry.data[CONF_API_KEY],
        session=async_get_clientsession(hass),
    )

    coordinator = RetroAchievementsDataUpdateCoordinator(
        hass=hass, api_client=api_client, entry=entry
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api_client": api_client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):

        async def _handle_refresh(_call: ServiceCall) -> None:
            for store in hass.data.get(DOMAIN, {}).values():
                if isinstance(store, dict) and "coordinator" in store:
                    await store["coordinator"].async_request_refresh()

        hass.services.async_register(DOMAIN, SERVICE_REFRESH, _handle_refresh)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # remove service when no entries remain
        remaining = [v for v in hass.data.get(DOMAIN, {}).values() if isinstance(v, dict)]
        if not remaining and hass.services.has_service(DOMAIN, SERVICE_REFRESH):
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)
```

- [ ] **Step 4: Create `custom_components/retroarchievements/services.yaml`**

```yaml
refresh:
  name: Refresh data
  description: Force an immediate refresh of all RetroAchievements data.
  fields: {}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_service_refresh.py -v`
Expected: 3 PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/retroarchievements/__init__.py custom_components/retroarchievements/services.yaml tests/test_service_refresh.py
git commit -m "feat: register retroarchievements.refresh service"
```

---

## Task 18: Options flow — `gaming_idle_threshold`

**Files:**
- Modify: `custom_components/retroarchievements/config_flow.py`
- Create: `tests/test_config_flow_options.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for the options flow with gaming_idle_threshold."""
from __future__ import annotations

import pytest
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


async def test_options_flow_accepts_idle_threshold(hass, mock_entry):
    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    assert result["type"] == "form"
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"monitored_games": "", CONF_GAMING_IDLE_THRESHOLD: 10},
    )
    assert result2["type"] == "create_entry"
    assert result2["data"][CONF_GAMING_IDLE_THRESHOLD] == 10


async def test_options_flow_rejects_threshold_too_high(hass, mock_entry):
    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    with pytest.raises(Exception):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"monitored_games": "", CONF_GAMING_IDLE_THRESHOLD: 999},
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_flow_options.py -v`
Expected: FAIL — option key not in schema.

- [ ] **Step 3: Modify `custom_components/retroarchievements/config_flow.py`**

Update the import line for constants:
```python
from .const import (
    CONF_API_KEY,
    CONF_GAMING_IDLE_THRESHOLD,
    CONF_MONITORED_GAMES,
    DEFAULT_GAMING_IDLE_THRESHOLD,
    DOMAIN,
    LOGGER,
)
```

Replace the `options` dict in `async_step_init` with:

```python
        options = {
            vol.Optional(
                CONF_MONITORED_GAMES,
                default=self.config_entry.options.get(CONF_MONITORED_GAMES, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                    multiline=True,
                ),
            ),
            vol.Optional(
                CONF_GAMING_IDLE_THRESHOLD,
                default=self.config_entry.options.get(
                    CONF_GAMING_IDLE_THRESHOLD, DEFAULT_GAMING_IDLE_THRESHOLD
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config_flow_options.py -v`
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/retroarchievements/config_flow.py tests/test_config_flow_options.py
git commit -m "feat(config_flow): add gaming_idle_threshold option (1-60 min)"
```

---

## Task 19: Translations + manifest version

**Files:**
- Modify: `custom_components/retroarchievements/translations/en.json`
- Modify: `custom_components/retroarchievements/manifest.json`

- [ ] **Step 1: Update `translations/en.json` — add entries under `entity.sensor` and `entity.binary_sensor` and under `options.step.init.data`**

Inside the existing `"entity": { "sensor": { ... } }` block, add a sibling key `"aotw"` to `sensor`:

```json
            "aotw": {
                "name": "Achievement of the Week",
                "state_attributes": {
                    "achievement_id": { "name": "Achievement ID" },
                    "description": { "name": "Description" },
                    "points": { "name": "Points" },
                    "badge_url": { "name": "Badge URL" },
                    "game_id": { "name": "Game ID" },
                    "game_title": { "name": "Game Title" },
                    "console_name": { "name": "Console" },
                    "week_start": { "name": "Week Start" },
                    "author": { "name": "Author" }
                }
            }
```

Add a `"binary_sensor"` sibling alongside `"sensor"` under `"entity"`:

```json
        "binary_sensor": {
            "is_gaming": { "name": "Is Gaming" },
            "aotw_unlocked": { "name": "AOTW Unlocked" }
        }
```

Inside `"options.step.init.data"`, add:

```json
                    "gaming_idle_threshold": "Gaming idle threshold (minutes)"
```

- [ ] **Step 2: Validate JSON**

Run: `python -m json.tool custom_components/retroarchievements/translations/en.json > /dev/null && echo OK`
Expected: `OK`.

- [ ] **Step 3: Bump version in `custom_components/retroarchievements/manifest.json`**

Change `"version": "0.2.1"` to `"version": "0.3.0"`.

- [ ] **Step 4: Commit**

```bash
git add custom_components/retroarchievements/translations/en.json custom_components/retroarchievements/manifest.json
git commit -m "chore: translations for new entities + bump version to 0.3.0"
```

---

## Task 20: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Append a new section to `README.md` after the existing `## Use Cases` section**

```markdown
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

## Service: `retroarchievements.refresh`

Forces an immediate refresh of all RetroAchievements data (useful right after unlocking an achievement in your emulator).

```yaml
service: retroarchievements.refresh
```

## Options

In **Settings → Devices & Services → RetroAchievements → Configure**:

- `monitored_games` — game IDs to track in detail (one per line).
- `gaming_idle_threshold` — minutes of inactivity after which `is_gaming` flips off (default `5`, range `1`–`60`).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document new entities, events, service, and option"
```

---

## Task 21: Final sweep — full suite + integration smoke

**Files:** none (verification only)

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: all tests PASS (no failures, no errors). Expected count ≥ 25 tests:
- test_api.py: 2
- test_coordinator_helpers.py: 8
- test_coordinator_events.py: 5
- test_coordinator_is_aotw_unlocked.py: 3
- test_sensor_aotw.py: 2
- test_binary_sensor_is_gaming.py: 7
- test_binary_sensor_aotw_unlocked.py: 2
- test_service_refresh.py: 3
- test_config_flow_options.py: 2

- [ ] **Step 2: Ruff lint**

Run: `ruff check custom_components/ tests/`
Expected: no issues. If issues found, fix in this task and re-commit.

- [ ] **Step 3: Verify no leftover blueprint references**

Run:
```bash
grep -rn "IntegrationBlueprintEntity\|BlueprintDataUpdateCoordinator\|IntegrationBlueprintConfigEntry\|IntegrationBlueprintSwitch\|IntegrationBlueprintBinarySensor" custom_components/ tests/
```
Expected: no matches.

- [ ] **Step 4: HACS validation (best-effort — local check)**

Run: `python -c "import json; json.load(open('custom_components/retroarchievements/manifest.json')); json.load(open('custom_components/retroarchievements/translations/en.json')); json.load(open('hacs.json'))"`
Expected: no exceptions raised.

- [ ] **Step 5: Commit any lint fixes**

```bash
git add -A
git diff --cached --quiet || git commit -m "chore: lint fixes from final sweep"
```

(If nothing to commit, the second command exits silently.)

---

## Self-Review Notes (executed during plan authoring)

**Spec coverage:** All 6 features in the spec (AOTW sensor, AOTW unlocked binary sensor, AOTW changed event, achievement unlocked event with enriched payload, is_gaming binary sensor, refresh service, idle threshold option, cleanup, tests, README, version bump) have at least one task each.

**Placeholder scan:** No "TBD", no vague "add error handling". Every step contains either a concrete code block or an exact command.

**Type consistency:** Helper names match across tasks: `_extract_achievement_ids`, `_find_achievement`, `_build_enriched_payload`, `_get_cached_game_extended`, `_safe_get_aotw`, `_fire_achievement_unlocked`, `_fire_aotw_changed`, `is_aotw_unlocked`. Constants match: `EVENT_ACHIEVEMENT_UNLOCKED`, `EVENT_AOTW_CHANGED`, `SERVICE_REFRESH`, `CONF_GAMING_IDLE_THRESHOLD`, `DEFAULT_GAMING_IDLE_THRESHOLD`. Entity class names consistent: `RetroAchievementsAOTWSensor`, `RetroAchievementsIsGamingBinarySensor`, `RetroAchievementsAOTWUnlockedBinarySensor`.

**Known caveats baked into the plan:**
- Task 9 introduces the complete coordinator (helpers from Tasks 6–8 are re-included). This is intentional — the task-9 patch replaces the file wholesale to add new state, gather, and event-firing in one focused commit. Tests from earlier tasks continue to pass.
- Task 14 deletion of `entity.py` and `data.py` is conditional on grep confirming no live references. The plan instructs to skip deletion if any reference remains.
