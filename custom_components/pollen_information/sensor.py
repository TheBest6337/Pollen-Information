"""Sensor platform for the Pollen Sensor integration."""
from __future__ import annotations

import datetime
import logging
import re
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_IDENTIFIERS, ATTR_MANUFACTURER, ATTR_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTRIBUTION,
    ATTR_ATTRIBUTION,
    ATTR_POLL_ID,
    ATTR_TODAY,
    ATTR_TOMORROW,
    ATTR_DAY_3,
    ATTR_DAY_4,
    ATTR_TODAY_LEVEL,
    ATTR_HOURLY_TODAY,
    ATTR_HOURLY_TOMORROW,
    ATTR_HOURLY_DAY_3,
    ATTR_HOURLY_DAY_4,
    CONTAMINATION_LABELS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pollen sensors for a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    data = coordinator.data or {}

    # ── Per-pollen-type contamination sensors ───────────────────────────
    for pollen in data.get("contamination", []):
        poll_id: int = pollen["poll_id"]
        poll_title: str = pollen["poll_title"]
        entities.append(
            PollenContaminationSensor(coordinator, entry, poll_id, poll_title)
        )

    # ── Overall allergy risk sensor (0–10 scale) ─────────────────────────
    entities.append(AllergyRiskSensor(coordinator, entry))

    # ── Hourly allergy risk sensors (one per forecast day) ───────────────
    for day_idx in range(1, 5):
        entities.append(AllergyRiskHourlySensor(coordinator, entry, day_idx))

    async_add_entities(entities, update_before_add=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _contamination_label(value: int | None) -> str:
    """Return a human-readable contamination label."""
    if value is None:
        return "unknown"
    return CONTAMINATION_LABELS.get(value, str(value))


def _allergy_risk_label(value: int | None) -> str:
    """Return a human-readable allergy risk label for values 0–10."""
    if value is None:
        return "unknown"
    if value == 0:
        return "none"
    if value <= 3:
        return "low"
    if value <= 6:
        return "moderate"
    if value <= 9:
        return "high"
    return "very high"


def _current_hour_value(hourly: list[int]) -> int | None:
    """Return the value for the current hour from a 24-element list."""
    if not hourly:
        return None
    hour = datetime.datetime.now().hour  # 0–23
    if hour < len(hourly):
        return hourly[hour]
    return hourly[-1]


def _slug(text: str) -> str:
    """Convert a pollen title to a safe entity id suffix."""
    return text.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")


def _strip_parenthetical(text: str) -> str:
    """Remove trailing parenthetical from a title, e.g. 'Birke (Betula)' → 'Birke'."""
    return re.sub(r"\s*\(.*?\)\s*$", "", text).strip()


def _device_info(entry: ConfigEntry) -> dict:
    """Return shared device info so all sensors appear under one Dienst."""
    return {
        ATTR_IDENTIFIERS: {(DOMAIN, entry.entry_id)},
        ATTR_NAME: "Polleninformationsdienst",
        ATTR_MANUFACTURER: "polleninformation.at",
        "entry_type": DeviceEntryType.SERVICE,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Sensor: per pollen type – contamination strength
# ──────────────────────────────────────────────────────────────────────────────

class PollenContaminationSensor(CoordinatorEntity, SensorEntity):
    """Contamination strength sensor for one pollen type.

    State:  today's contamination level (0 = none … 4 = very high)
    Attributes include forecasts for the next 3 days.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:flower-pollen"
    _attr_native_unit_of_measurement = None  # dimensionless 0–4 scale

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        poll_id: int,
        poll_title: str,
    ) -> None:
        super().__init__(coordinator)
        self._poll_id = poll_id
        self._poll_title = poll_title
        self._entry_id = entry.entry_id
        self._attr_name = f"Pollen {_strip_parenthetical(poll_title)}"
        self._attr_unique_id = f"{entry.entry_id}_contamination_{poll_id}"
        self._attr_device_info = _device_info(entry)

    def _pollen_entry(self) -> dict[str, Any] | None:
        data = self.coordinator.data or {}
        for item in data.get("contamination", []):
            if item["poll_id"] == self._poll_id:
                return item
        return None

    @property
    def native_value(self) -> int | None:
        """Today's contamination level (0–4)."""
        entry = self._pollen_entry()
        if entry is None:
            return None
        return entry.get("contamination_1")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        entry = self._pollen_entry() or {}
        today = entry.get("contamination_1")
        return {
            ATTR_POLL_ID: self._poll_id,
            ATTR_TODAY_LEVEL: _contamination_label(today),
            ATTR_TODAY: today,
            ATTR_TOMORROW: entry.get("contamination_2"),
            ATTR_DAY_3: entry.get("contamination_3"),
            ATTR_DAY_4: entry.get("contamination_4"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Sensor: overall allergy risk (0–10)
# ──────────────────────────────────────────────────────────────────────────────

class AllergyRiskSensor(CoordinatorEntity, SensorEntity):
    """Overall allergy risk for today (0 = none … 10 = very high).

    Attributes include tomorrow, day 3, and day 4.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:biohazard"
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        self._attr_name = "Pollen Allergy Risk"
        self._attr_unique_id = f"{entry.entry_id}_allergy_risk"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> int | None:
        """Today's allergy risk (0–10)."""
        data = self.coordinator.data or {}
        return data.get("allergyrisk", {}).get("allergyrisk_1")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        ar = data.get("allergyrisk", {})
        today = ar.get("allergyrisk_1")
        return {
            ATTR_TODAY_LEVEL: _allergy_risk_label(today),
            ATTR_TODAY: today,
            ATTR_TOMORROW: ar.get("allergyrisk_2"),
            ATTR_DAY_3: ar.get("allergyrisk_3"),
            ATTR_DAY_4: ar.get("allergyrisk_4"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Sensor: hourly allergy risk for a given forecast day
# ──────────────────────────────────────────────────────────────────────────────

_DAY_LABEL = {1: "Today", 2: "Tomorrow", 3: "In 2 Days", 4: "In 3 Days"}


class AllergyRiskHourlySensor(CoordinatorEntity, SensorEntity):
    """Hourly allergy risk sensor for one forecast day.

    State:  value for the current hour (today) or the first hour (other days).
    Attribute ``hourly`` holds the full 24-element array (index 0 = 0–1 h).
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-bar"
    _attr_native_unit_of_measurement = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        day_index: int,  # 1 = today, 2 = tomorrow, 3 = day 3, 4 = day 4
    ) -> None:
        super().__init__(coordinator)
        self._day_index = day_index
        self._entry_id = entry.entry_id
        label = _DAY_LABEL.get(day_index, f"Day {day_index}")
        self._attr_name = f"Pollen Allergy Risk Hourly {label}"
        self._attr_unique_id = f"{entry.entry_id}_allergy_risk_hourly_{day_index}"
        self._attr_device_info = _device_info(entry)

    def _hourly_list(self) -> list[int]:
        data = self.coordinator.data or {}
        key = f"allergyrisk_hourly_{self._day_index}"
        return data.get("allergyrisk_hourly", {}).get(key, [])

    @property
    def native_value(self) -> int | None:
        """Current-hour value (for today) or 00:00 value (for future days)."""
        hourly = self._hourly_list()
        if not hourly:
            return None
        if self._day_index == 1:
            return _current_hour_value(hourly)
        return hourly[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        hourly = self._hourly_list()
        level = _allergy_risk_label(self.native_value)
        # Build a labelled dict: {"00:00": 5, "01:00": 4, ...}
        hourly_labelled = {
            f"{h:02d}:00": v for h, v in enumerate(hourly)
        }
        return {
            ATTR_TODAY_LEVEL: level,
            "hourly": hourly_labelled,
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
