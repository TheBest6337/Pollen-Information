"""Pollen Information integration – polleninformation.at."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PollenAPI, CannotConnectError, InvalidApiKeyError
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_COUNTRY,
    CONF_LANGUAGE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


class PollenInformationCoordinator(DataUpdateCoordinator):
    """Coordinator that polls polleninformation.at on a configurable interval."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PollenAPI,
        update_interval_minutes: int,
    ) -> None:
        self._api = api
        self._session = async_get_clientsession(hass)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval_minutes),
        )

    async def _async_update_data(self):
        """Fetch fresh data from the API."""
        try:
            return await self._api.async_get_data(self._session)
        except (CannotConnectError, InvalidApiKeyError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pollen Information from a config entry."""

    api = PollenAPI(
        api_key=entry.data[CONF_API_KEY],
        country=entry.data[CONF_COUNTRY],
        language=entry.data[CONF_LANGUAGE],
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
    )

    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    coordinator = PollenInformationCoordinator(hass, api, update_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok