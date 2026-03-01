# GitHub Copilot Instructions – Pollen Information (polleninformation.at)

## Project overview

This is a **Home Assistant custom integration** (`custom_component`) that exposes
pollen and allergy-risk data from the Austrian
[polleninformation.at](https://www.polleninformation.at) REST API as HA sensor
entities.

- **Domain:** `pollen_information`
- **API base URL:** `https://www.polleninformation.at/api/forecast/public`
- **Auth:** query parameter `apikey`
- **IoT class:** `cloud_polling` (data is fetched on a configurable interval,
  default 240 min)
- **HA integration type:** `service` (no physical device)

---

## Repository layout

```
pollen_information/
├── __init__.py        # Integration setup/teardown, DataUpdateCoordinator
├── api.py             # Async HTTP client (PollenAPI)
├── config_flow.py     # UI config flow (one step)
├── const.py           # All constants, labels, attribute names
├── manifest.json      # Integration metadata
├── sensor.py          # All SensorEntity subclasses
├── strings.json       # Config-flow UI strings (source of truth)
└── translations/
    ├── de.json
    ├── en.json
    ├── es.json
    └── fr.json
```

---

## Architecture

```
ConfigEntry (one per location)
    │
    └─► DataUpdateCoordinator  (__init__.py)
            │   polls PollenAPI every N minutes
            │
            └─► sensor.py creates three sensor types:
                    PollenContaminationSensor   (one per pollen type)
                    AllergyRiskSensor           (one overall risk sensor)
                    AllergyRiskHourlySensor     (one per forecast day, days 1–4)
```

All sensors inherit from both `CoordinatorEntity` and `SensorEntity` and share
one logical HA device (`DeviceEntryType.SERVICE`) per config entry.

---

## API response shape

```jsonc
{
  "contamination": [
    {
      "poll_id": 1,
      "poll_title": "Birke (Betula)",
      "contamination_1": 3,   // today  (0–4)
      "contamination_2": 2,   // tomorrow
      "contamination_3": 1,
      "contamination_4": 0
    }
    // … one entry per pollen type
  ],
  "allergyrisk": {
    "allergyrisk_1": 7,   // today  (0–10)
    "allergyrisk_2": 5,
    "allergyrisk_3": 4,
    "allergyrisk_4": 3
  },
  "allergyrisk_hourly": {
    "allergyrisk_hourly_1": [0,1,2,...],  // 24 ints, index = hour (0–23)
    "allergyrisk_hourly_2": [...],
    "allergyrisk_hourly_3": [...],
    "allergyrisk_hourly_4": [...]
  }
}
```

---

## Sensor types

### `PollenContaminationSensor`
- **State:** `contamination_1` (today, integer 0–4)
- **Unit:** none (dimensionless scale)
- **Icon:** `mdi:flower-pollen`
- **Attributes:** `poll_id`, `level_today` (label string), `today`, `tomorrow`,
  `day_3`, `day_4`, `attribution`
- **Unique ID:** `{entry_id}_contamination_{poll_id}`
- **Name:** `Pollen {title}` – parenthetical scientific name is stripped
  (e.g. `"Birke (Betula)"` → `"Birke"`)

### `AllergyRiskSensor`
- **State:** `allergyrisk_1` (today, integer 0–10)
- **Icon:** `mdi:biohazard`
- **Attributes:** `level_today`, `today`, `tomorrow`, `day_3`, `day_4`,
  `attribution`
- **Unique ID:** `{entry_id}_allergy_risk`

### `AllergyRiskHourlySensor`  (four instances: day_index 1–4)
- **State:** for day 1 (today) uses the current wall-clock hour; for days 2–4
  uses index 0 (midnight)
- **Icon:** `mdi:chart-bar`
- **Attributes:** `level_today`, `hourly` (dict `"HH:00" → int`), `attribution`
- **Unique ID:** `{entry_id}_allergy_risk_hourly_{day_index}`
- **Names:** `"Pollen Allergy Risk Hourly Today"`, `"… Tomorrow"`,
  `"… In 2 Days"`, `"… In 3 Days"`

---

## Key constants (`const.py`)

| Constant | Value / purpose |
|---|---|
| `DOMAIN` | `"pollen_information"` |
| `API_URL` | `"https://www.polleninformation.at/api/forecast/public"` |
| `DEFAULT_UPDATE_INTERVAL` | `240` minutes |
| `COUNTRIES` | List of supported ISO country codes |
| `LANGUAGES` | List of supported language codes |
| `CONTAMINATION_LABELS` | `{0: "none", 1: "low", 2: "moderate", 3: "high", 4: "very high"}` |
| `CONF_API_KEY` | Config entry key for the API key |
| `CONF_COUNTRY` | Config entry key for country |
| `CONF_LANGUAGE` | Config entry key for language |
| `CONF_UPDATE_INTERVAL` | Config entry key for poll interval |

---

## Config flow (`config_flow.py`)

Single step (`async_step_user`). Required fields:

| Field | Type | Notes |
|---|---|---|
| `api_key` | `str` | polleninformation.at API key |
| `country` | `str` | `vol.In(COUNTRIES)` |
| `language` | `str` | `vol.In(LANGUAGES)` |
| `latitude` | `float` | pre-filled from `hass.config.latitude` |
| `longitude` | `float` | pre-filled from `hass.config.longitude` |
| `update_interval` | `int` (optional) | minutes, default 240 |

On submit the flow makes a live API call to validate credentials before creating
the config entry. Errors mapped: `"invalid_api_key"`, `"cannot_connect"`,
`"unknown"`.

---

## API client (`api.py`)

`PollenAPI.async_get_data(session)` is the only public method. It accepts an
`aiohttp.ClientSession` (provided by HA via `async_get_clientsession(hass)`).

Custom exceptions:
- `CannotConnectError` – network / HTTP error
- `InvalidApiKeyError` – API returned an error mentioning "api key"

---

## Coding conventions

- All I/O is **async** (`async def`, `aiohttp`, `await`)
- Use `from __future__ import annotations` in every module
- Logging via `logging.getLogger(__name__)` (`_LOGGER`)
- Do **not** store mutable state in sensor properties; always read from
  `self.coordinator.data`
- Helper functions (`_slug`, `_strip_parenthetical`, `_contamination_label`,
  `_allergy_risk_label`, `_current_hour_value`) live at module level in
  `sensor.py`
- Attribute keys come from constants in `const.py` – never use bare string
  literals for attribute names
- Translations must be kept in sync across `strings.json` and all files under
  `translations/` whenever config-flow strings change

---

## Home Assistant patterns used

- `DataUpdateCoordinator` for centralised polling (one coordinator per entry)
- `CoordinatorEntity` base class for automatic `async_write_ha_state` on update
- `async_config_entry_first_refresh()` to fail fast on bad credentials at setup
- `DeviceEntryType.SERVICE` so the virtual device shows up correctly in the HA
  device registry without implying physical hardware
- `SensorStateClass.MEASUREMENT` on all sensors (numeric, non-cumulative)
- `async_forward_entry_setups` / `async_unload_platforms` for platform lifecycle
