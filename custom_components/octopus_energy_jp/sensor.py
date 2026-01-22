"""Sensor platform for Octopus Energy Japan."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ACCOUNT_NUMBER
from .coordinator import OctopusEnergyJPCoordinator, OctopusEnergyJPData


@dataclass(frozen=True, kw_only=True)
class OctopusEnergyJPSensorEntityDescription(SensorEntityDescription):
    """Describes an Octopus Energy JP sensor entity."""

    value_fn: Callable[[OctopusEnergyJPData], Decimal | None]


SENSOR_DESCRIPTIONS: tuple[OctopusEnergyJPSensorEntityDescription, ...] = (
    OctopusEnergyJPSensorEntityDescription(
        key="electricity_latest",
        name="Latest Electricity Reading",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.latest_reading,
    ),
    OctopusEnergyJPSensorEntityDescription(
        key="electricity_today",
        name="Today's Electricity Usage",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.today_total,
    ),
    OctopusEnergyJPSensorEntityDescription(
        key="electricity_yesterday",
        name="Yesterday's Electricity Usage",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.yesterday_total,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Octopus Energy Japan sensors from a config entry."""
    coordinator: OctopusEnergyJPCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        OctopusEnergyJPSensor(
            coordinator=coordinator,
            description=description,
            config_entry=config_entry,
        )
        for description in SENSOR_DESCRIPTIONS
    )


class OctopusEnergyJPSensor(
    CoordinatorEntity[OctopusEnergyJPCoordinator], SensorEntity
):
    """Representation of an Octopus Energy Japan sensor."""

    entity_description: OctopusEnergyJPSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OctopusEnergyJPCoordinator,
        description: OctopusEnergyJPSensorEntityDescription,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        
        account_number = config_entry.data[CONF_ACCOUNT_NUMBER]
        self._attr_unique_id = f"{account_number}_{description.key}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_number)},
            name=f"Octopus Energy Japan ({account_number})",
            manufacturer="Octopus Energy Japan",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> Decimal | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.key != "electricity_latest":
            return None
            
        if self.coordinator.data is None:
            return None
            
        data = self.coordinator.data
        attrs = {}
        
        if data.latest_reading_start:
            attrs["reading_start"] = data.latest_reading_start.isoformat()
        if data.latest_reading_end:
            attrs["reading_end"] = data.latest_reading_end.isoformat()
            
        return attrs if attrs else None
