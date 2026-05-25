"""Config flow for RetroAchievements."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

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

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Add game selection to options later
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

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options),
        )
