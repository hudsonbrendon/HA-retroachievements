"""Config flow for RetroAchievements."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
    async_get_clientsession,
)

from .api import (
    RetroAchievementsApiClient,
    RetroAchievementsApiClientAuthenticationError,
    RetroAchievementsApiClientCommunicationError,
    RetroAchievementsApiClientError,
)
from .const import (
    CONF_API_KEY,
    CONF_GAMING_IDLE_THRESHOLD,
    CONF_MONITORED_GAMES,
    DEFAULT_GAMING_IDLE_THRESHOLD,
    DOMAIN,
    LOGGER,
)

CONF_CONSOLE = "console"
CONF_GAMES = "games"


class RetroAchievementsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for RetroAchievements."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    api_key=user_input[CONF_API_KEY],
                )
            except RetroAchievementsApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except RetroAchievementsApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except RetroAchievementsApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_API_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def async_step_reauth(
        self, _entry_data: dict
    ) -> config_entries.ConfigFlowResult:
        """Handle re-authentication when the stored API key is rejected."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Prompt for a new API key and validate it."""
        entry = self._reauth_entry
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    username=entry.data[CONF_USERNAME],
                    api_key=user_input[CONF_API_KEY],
                )
            except RetroAchievementsApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except RetroAchievementsApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except RetroAchievementsApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_API_KEY: user_input[CONF_API_KEY]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=_errors,
        )

    async def _test_credentials(self, username: str, api_key: str) -> None:
        """Validate credentials."""
        client = RetroAchievementsApiClient(
            username=username,
            api_key=api_key,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_user_summary()

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return RetroAchievementsOptionsFlowHandler(config_entry)


class RetroAchievementsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for RetroAchievements."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        raw = config_entry.options.get(CONF_MONITORED_GAMES, "") or ""
        self._monitored: set[str] = {
            line.strip() for line in raw.splitlines() if line.strip()
        }
        self._idle_threshold: int = config_entry.options.get(
            CONF_GAMING_IDLE_THRESHOLD, DEFAULT_GAMING_IDLE_THRESHOLD
        )
        self._selected_console: str | None = None
        self._console_games: list[dict] = []

    def _client(self) -> RetroAchievementsApiClient:
        """Build an API client from the stored credentials."""
        return RetroAchievementsApiClient(
            username=self.config_entry.data[CONF_USERNAME],
            api_key=self.config_entry.data[CONF_API_KEY],
            session=async_get_clientsession(self.hass),
        )

    def _serialize_monitored(self) -> str:
        """Return monitored game IDs as a newline-separated string, numerically sorted."""

        def _key(value: str) -> tuple[int, str]:
            return (int(value), "") if value.isdigit() else (1 << 62, value)

        return "\n".join(sorted(self._monitored, key=_key))

    def _save(self) -> config_entries.ConfigFlowResult:
        """Persist the current monitored games and settings."""
        return self.async_create_entry(
            title="",
            data={
                CONF_MONITORED_GAMES: self._serialize_monitored(),
                CONF_GAMING_IDLE_THRESHOLD: self._idle_threshold,
            },
        )

    async def async_step_init(
        self, _user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["select_games", "manage"],
        )

    async def async_step_select_games(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Pick a console to browse its games."""
        try:
            consoles = await self._client().async_get_console_ids()
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.warning("Failed to fetch console list: %s", err)
            consoles = []

        if not consoles:
            # No console data available; fall back to manual editing.
            return await self.async_step_manage(error="cannot_load_games")

        if user_input is not None:
            self._selected_console = user_input[CONF_CONSOLE]
            return await self.async_step_pick_games()

        options = [
            selector.SelectOptionDict(
                value=str(console.get("ID")),
                label=console.get("Name") or str(console.get("ID")),
            )
            for console in consoles
            if console.get("ID") is not None
        ]
        return self.async_show_form(
            step_id="select_games",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONSOLE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            sort=True,
                        ),
                    ),
                },
            ),
        )

    async def async_step_pick_games(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Select which games of the chosen console to monitor."""
        console_id = self._selected_console
        try:
            self._console_games = await self._client().async_get_game_list(
                int(console_id)
            )
        except (ValueError, TypeError):
            self._console_games = []
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.warning(
                "Failed to fetch game list for console %s: %s", console_id, err
            )
            self._console_games = []

        console_game_ids = {
            str(game.get("ID")) for game in self._console_games if game.get("ID")
        }

        if user_input is not None:
            selected = {str(g) for g in user_input.get(CONF_GAMES, [])}
            # Replace only this console's games; keep games from other consoles.
            self._monitored = (self._monitored - console_game_ids) | selected
            return self._save()

        options = [
            selector.SelectOptionDict(
                value=str(game.get("ID")),
                label=game.get("Title") or str(game.get("ID")),
            )
            for game in self._console_games
            if game.get("ID") is not None
        ]
        current = sorted(self._monitored & console_game_ids)
        return self.async_show_form(
            step_id="pick_games",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_GAMES, default=current): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            multiple=True,
                            sort=True,
                        ),
                    ),
                },
            ),
        )

    async def async_step_manage(
        self, user_input: dict | None = None, error: str | None = None
    ) -> config_entries.ConfigFlowResult:
        """Edit the raw monitored-game list and idle threshold."""
        if user_input is not None:
            raw = user_input.get(CONF_MONITORED_GAMES, "") or ""
            self._monitored = {
                line.strip() for line in raw.splitlines() if line.strip()
            }
            self._idle_threshold = user_input[CONF_GAMING_IDLE_THRESHOLD]
            return self._save()

        options = {
            vol.Optional(
                CONF_MONITORED_GAMES,
                default=self._serialize_monitored(),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                    multiline=True,
                ),
            ),
            vol.Optional(
                CONF_GAMING_IDLE_THRESHOLD,
                default=self._idle_threshold,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        }
        return self.async_show_form(
            step_id="manage",
            data_schema=vol.Schema(options),
            errors={"base": error} if error else None,
        )
