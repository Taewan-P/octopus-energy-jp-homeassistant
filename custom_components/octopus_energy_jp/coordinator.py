"""Data update coordinator for Octopus Energy Japan."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import (
    OctopusEnergyJPApi,
    OctopusEnergyJPApiError,
    OctopusEnergyJPAuthError,
)
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Japan timezone
JST = ZoneInfo("Asia/Tokyo")


@dataclass
class OctopusEnergyJPData:
    """Data class to hold energy consumption data."""

    latest_reading: Decimal | None = None
    latest_reading_start: datetime | None = None
    latest_reading_end: datetime | None = None
    today_total: Decimal = Decimal("0")
    yesterday_total: Decimal = Decimal("0")
    readings: list[dict[str, Any]] | None = None


class OctopusEnergyJPCoordinator(DataUpdateCoordinator[OctopusEnergyJPData]):
    """Coordinator to manage data updates from Octopus Energy Japan API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: OctopusEnergyJPApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> OctopusEnergyJPData:
        """Fetch data from API."""
        try:
            # Get readings for the last 48 hours
            now = datetime.now(JST)
            from_datetime = now - timedelta(hours=48)
            
            readings = await self.api.get_half_hourly_readings(
                from_datetime=from_datetime,
                to_datetime=now,
            )

            return self._process_readings(readings, now)

        except OctopusEnergyJPAuthError as err:
            # Authentication failed - trigger reauth
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except OctopusEnergyJPApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def _process_readings(
        self, readings: list[dict[str, Any]], now: datetime
    ) -> OctopusEnergyJPData:
        """Process raw readings into structured data."""
        data = OctopusEnergyJPData(readings=readings)

        if not readings:
            return data

        # Parse and sort readings by start time
        parsed_readings = []
        for reading in readings:
            try:
                start_at = datetime.fromisoformat(reading["startAt"].replace("Z", "+00:00"))
                end_at = datetime.fromisoformat(reading["endAt"].replace("Z", "+00:00"))
                value = Decimal(str(reading["value"]))
                parsed_readings.append({
                    "start_at": start_at.astimezone(JST),
                    "end_at": end_at.astimezone(JST),
                    "value": value,
                })
            except (KeyError, ValueError) as err:
                _LOGGER.warning("Failed to parse reading: %s - %s", reading, err)
                continue

        if not parsed_readings:
            return data

        # Sort by start time
        parsed_readings.sort(key=lambda x: x["start_at"])

        # Get the latest reading
        latest = parsed_readings[-1]
        data.latest_reading = latest["value"]
        data.latest_reading_start = latest["start_at"]
        data.latest_reading_end = latest["end_at"]

        # Calculate today's total
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_total = Decimal("0")
        for reading in parsed_readings:
            if reading["start_at"] >= today_start:
                today_total += reading["value"]
        data.today_total = today_total

        # Calculate yesterday's total
        yesterday_start = today_start - timedelta(days=1)
        yesterday_total = Decimal("0")
        for reading in parsed_readings:
            if yesterday_start <= reading["start_at"] < today_start:
                yesterday_total += reading["value"]
        data.yesterday_total = yesterday_total

        _LOGGER.debug(
            "Processed readings: latest=%s, today=%s, yesterday=%s",
            data.latest_reading,
            data.today_total,
            data.yesterday_total,
        )

        return data
