"""Platform for DAB Pumps sensor integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DabPumpsDataUpdateCoordinator
from .entity import PumpEntity

SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="pressure_pa",
        name="Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="total_delivered_flow_cubic_meters",
        name="Total delivered flow",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="flow_cubic_meters_per_hour",
        name="Flow rate",
        icon="mdi:water-pump",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="total_energy_consumption_kilowatt_hours",
        name="Total energy consumption",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="output_power_watts",
        name="Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
]


class PumpSensor(PumpEntity, SensorEntity):
    """A pump sensor."""

    def __init__(
        self,
        coordinator: DabPumpsDataUpdateCoordinator,
        description: SensorEntityDescription,
        pump_serial: str,
    ) -> None:
        """Initialize a pump sensor."""
        super().__init__(coordinator=coordinator, pump_serial=pump_serial)
        self.entity_description = description

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.pump_serial}_{self.entity_description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return getattr(self.data, self.entity_description.key)


class SignalSensor(PumpSensor):
    """A wireless signal sensor."""

    def __init__(
        self,
        coordinator: DabPumpsDataUpdateCoordinator,
        pump_serial: str,
    ) -> None:
        """Initialize a wireless signal sensor."""
        super().__init__(
            coordinator=coordinator,
            description=SensorEntityDescription(
                key="signal_level_percent",
                name="Signal level",
                entity_category=EntityCategory.DIAGNOSTIC,
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            pump_serial=pump_serial,
        )

    @property
    def icon(self) -> str:
        """Return a representative icon."""
        if self.native_value is not None:
            if self.native_value >= 80:
                return "mdi:wifi-strength-4"
            if self.native_value >= 60:
                return "mdi:wifi-strength-3"
            if self.native_value >= 40:
                return "mdi:wifi-strength-2"
            if self.native_value >= 20:
                return "mdi:wifi-strength-1"
        return "mdi:wifi-strength-outline"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors based on a config entry."""
    coordinator: DabPumpsDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        PumpSensor(
            coordinator=coordinator,
            description=description,
            pump_serial=pump_serial,
        )
        for description in SENSOR_DESCRIPTIONS
        for pump_serial in coordinator.data.pumps
    )
    async_add_entities(
        SignalSensor(
            coordinator=coordinator,
            pump_serial=pump_serial,
        )
        for pump_serial in coordinator.data.pumps
    )
