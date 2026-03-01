"""Constants for the Pollen Information integration (polleninformation.at)."""

DOMAIN = "pollen_information"

# Config keys (custom ones not in homeassistant.const)
CONF_API_KEY = "api_key"
CONF_COUNTRY = "country"
CONF_LANGUAGE = "language"
CONF_UPDATE_INTERVAL = "update_interval"

# API
API_URL = "https://www.polleninformation.at/api/forecast/public"

# Defaults
DEFAULT_UPDATE_INTERVAL = 240  # minutes – API recommends max every 4 h
DEFAULT_LANGUAGE = "en"
DEFAULT_COUNTRY = "AT"

# Valid option lists from the API docs
COUNTRIES = ["AT", "CH", "DE", "ES", "FR", "GB", "IT", "LV", "LT", "PL", "SE", "TR", "UA"]
LANGUAGES = ["de", "en", "fi", "sv", "fr", "it", "lv", "lt", "pl", "pt", "ru", "sk", "es", "tr", "uk", "hu"]

# Contamination scale (0–4)
CONTAMINATION_LABELS = {
    0: "none",
    1: "low",
    2: "moderate",
    3: "high",
    4: "very high",
}

# Allergy-risk scale (0–10)
ALLERGY_RISK_LABELS = {
    (0, 0): "none",
    (1, 3): "low",
    (4, 6): "moderate",
    (7, 9): "high",
    (10, 10): "very high",
}

# Attribute names
ATTR_POLL_ID = "poll_id"
ATTR_TODAY = "today"
ATTR_TOMORROW = "tomorrow"
ATTR_DAY_3 = "day_3"
ATTR_DAY_4 = "day_4"
ATTR_TODAY_LEVEL = "level_today"
ATTR_HOURLY_TODAY = "hourly_today"
ATTR_HOURLY_TOMORROW = "hourly_tomorrow"
ATTR_HOURLY_DAY_3 = "hourly_day_3"
ATTR_HOURLY_DAY_4 = "hourly_day_4"
ATTR_ATTRIBUTION = "attribution"
ATTRIBUTION = "Data provided by Österreichischer Polleninformationsdienst (www.polleninformation.at)"