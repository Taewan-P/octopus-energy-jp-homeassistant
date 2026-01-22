# Octopus Energy Japan - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Taewan-P&repo=octopus-energy-jp-homeassistant&category=integration)

A Home Assistant custom integration for [Octopus Energy Japan](https://octopusenergy.co.jp/) that allows you to monitor your electricity consumption data.

## Features

- 🔌 **Latest Reading**: Shows the most recent half-hourly electricity consumption
- 📊 **Today's Usage**: Total electricity consumed today
- 📈 **Yesterday's Usage**: Total electricity consumed yesterday
- 🔄 **Automatic Updates**: Data refreshes every 30 minutes

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/Taewan-P/octopus-energy-jp-homeassistant`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Octopus Energy Japan" and install it
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/octopus_energy_jp` folder from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Octopus Energy Japan"
4. Enter your Octopus Energy Japan account email and password
5. Click **Submit**

## Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| Latest Electricity Reading | Most recent 30-minute consumption | kWh |
| Today's Electricity Usage | Total consumption since midnight | kWh |
| Yesterday's Electricity Usage | Total consumption for yesterday | kWh |

## Requirements

- Home Assistant 2024.1.0 or newer
- An active Octopus Energy Japan account

## API

This integration uses the Octopus Energy Japan GraphQL API. For more information about the API, see the [official example repository](https://github.com/octoenergy/oejp-api-example).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Octopus Energy Japan.
