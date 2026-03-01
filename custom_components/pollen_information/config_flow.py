"""Config flow for the Pollen Sensor integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PollenAPI, CannotConnectError, InvalidApiKeyError
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_COUNTRY,
    CONF_LANGUAGE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_LANGUAGE,
    DEFAULT_COUNTRY,
    COUNTRIES,
    LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


class PollenInformationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the UI config flow for Pollen Sensor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial (and only) configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = PollenAPI(
                api_key=user_input[CONF_API_KEY],
                country=user_input[CONF_COUNTRY],
                language=user_input[CONF_LANGUAGE],
                latitude=user_input[CONF_LATITUDE],
                longitude=user_input[CONF_LONGITUDE],
            )
            try:
                await api.async_get_data(session)
            except InvalidApiKeyError:
                errors["base"] = "invalid_api_key"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during config flow validation")
                errors["base"] = "unknown"
            else:
                # Derive a human-readable title from country + coordinates
                title = (
                    f"Pollen {user_input[CONF_COUNTRY]} "
                    f"({user_input[CONF_LATITUDE]:.4f}, {user_input[CONF_LONGITUDE]:.4f})"
                )
                return self.async_create_entry(title=title, data=user_input)

        # Pre-fill lat/long from the HA home location
        default_lat: float = self.hass.config.latitude
        default_lon: float = self.hass.config.longitude

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_COUNTRY, default=DEFAULT_COUNTRY): vol.In(COUNTRIES),
                vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(LANGUAGES),
                vol.Required(CONF_LATITUDE, default=default_lat): vol.Coerce(float),
                vol.Required(CONF_LONGITUDE, default=default_lon): vol.Coerce(float),
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=1440)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
