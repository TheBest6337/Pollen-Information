"""Async API client for polleninformation.at."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_URL

_LOGGER = logging.getLogger(__name__)


class CannotConnectError(Exception):
    """Raised when the API is unreachable."""


class InvalidApiKeyError(Exception):
    """Raised when the API returns an authentication error."""


class PollenAPI:
    """Wrapper around the polleninformation.at forecast API."""

    def __init__(
        self,
        api_key: str,
        country: str,
        language: str,
        latitude: float,
        longitude: float,
    ) -> None:
        self.api_key = api_key
        self.country = country
        self.language = language
        self.latitude = latitude
        self.longitude = longitude

    async def async_get_data(
        self, session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        """Fetch forecast data from the API.

        Returns the parsed JSON dict which has the shape:
        {
            "contamination": [
                {"poll_id": int, "poll_title": str,
                 "contamination_1": int, ..., "contamination_4": int}, ...
            ],
            "allergyrisk": {
                "allergyrisk_1": int, ..., "allergyrisk_4": int
            },
            "allergyrisk_hourly": {
                "allergyrisk_hourly_1": [24 ints], ..., "allergyrisk_hourly_4": [24 ints]
            }
        }

        Raises CannotConnectError or InvalidApiKeyError on failure.
        """
        params = {
            "country": self.country,
            "lang": self.language,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "apikey": self.api_key,
        }

        try:
            async with session.get(API_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                # The API returns application/json but sometimes without proper content-type
                data: dict[str, Any] = await response.json(content_type=None)
        except aiohttp.ClientError as err:
            _LOGGER.error("Cannot connect to polleninformation.at: %s", err)
            raise CannotConnectError from err

        if "error" in data:
            _LOGGER.error("API error response: %s", data["error"])
            if "api key" in str(data["error"]).lower():
                raise InvalidApiKeyError(data["error"])
            raise CannotConnectError(data["error"])

        return data
