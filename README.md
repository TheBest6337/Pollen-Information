# Pollen Information

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration that exposes pollen contamination and allergy risk data from the Austrian [polleninformation.at](https://www.polleninformation.at) REST API as sensor entities.

> **Disclaimer:** This is an unofficial integration and is not affiliated with or endorsed by polleninformation.at.

## Features

- **Pollen contamination sensors** – one per pollen type (e.g. Birch, Ash, Grasses), showing today's contamination level (0–4 scale) with a 4-day forecast
- **Allergy risk sensor** – overall daily allergy risk (0–10 scale) with a 4-day forecast
- **Hourly allergy risk sensors** – 24-hour forecast for today, tomorrow, and the next two days

## Requirements

- A free API key from [polleninformation.at](https://www.polleninformation.at/datenschnittstelle)
- Home Assistant 2023.1 or newer

## Installation via HACS

1. Open HACS in your Home Assistant instance
2. Go to **Integrations** → three-dot menu → **Custom repositories**
3. Add `https://github.com/TheBest6337/Pollen-Information` with category **Integration**
4. Search for **Pollen Information** and install it
5. Restart Home Assistant

## Manual Installation

1. Copy the `custom_components/pollen_information` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Pollen Information**
3. Enter your API key, country, language, and optionally your coordinates and update interval

## Sensor Overview

| Sensor | State | Range |
|---|---|---|
| `Pollen <name>` | Contamination today | 0–4 (none / low / moderate / high / very high) |
| `Pollen Allergy Risk` | Risk today | 0–10 |
| `Pollen Allergy Risk Hourly Today` | Risk at current hour | 0–10 |
| `Pollen Allergy Risk Hourly Tomorrow` | Risk at midnight | 0–10 |
| `Pollen Allergy Risk Hourly In 2 Days` | Risk at midnight | 0–10 |
| `Pollen Allergy Risk Hourly In 3 Days` | Risk at midnight | 0–10 |

## Links

- [polleninformation.at API documentation](https://www.polleninformation.at/datenschnittstelle)
- [Issue tracker](https://github.com/TheBest6337/Pollen-Information/issues)

## License

MIT
