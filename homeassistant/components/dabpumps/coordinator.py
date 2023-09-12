"""DataUpdateCoordinator for the DAB Pumps integration."""

from __future__ import annotations

from dataclasses import dataclass

from dabpumps.dconnect import DConnect
from dabpumps.exceptions import DConnectError, WrongCredentialError
from dabpumps.pump import MeasureSystem, Pump

from homeassistant.const import (
    UnitOfPressure,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.unit_conversion import (
    PressureConverter,
    VolumeConverter,
)

from .const import DOMAIN, LOGGER, UPDATE_INTERVAL


@dataclass
class PumpData:
    """Container for cached pump data from the DAB Pumps API."""

    pressure_pa: float
    total_delivered_flow_cubic_meters: float
    flow_cubic_meters_per_hour: float
    total_energy_consumption_kilowatt_hours: float
    signal_level_percent: int
    output_power_watts: int


@dataclass
class DabPumpsData:
    """Container for cached data from the DAB Pumps API."""

    pumps: dict[str, PumpData]


class DabPumpsDataUpdateCoordinator(DataUpdateCoordinator[DabPumpsData]):
    """The DAB Pumps data update coordinator."""

    def __init__(self, hass: HomeAssistant, email: str, dconnect: DConnect) -> None:
        """Initialize the class."""
        super().__init__(
            hass, LOGGER, name=f"{DOMAIN} ({email})", update_interval=UPDATE_INTERVAL
        )
        self.dconnect = dconnect
        self.pumps: dict[str, Pump] | None = None

    async def _async_update_data(self) -> DabPumpsData:
        """Fetch data from API."""
        try:
            if self.pumps:
                for pump in self.pumps.values():
                    await pump.async_update_state()
            else:
                self.pumps = {
                    pump.serial: pump
                    for installation in await self.dconnect.async_get_installations()
                    for pump in await installation.async_get_pumps()
                }
            return DabPumpsData(
                {pump.serial: _get_pump_data(pump) for pump in self.pumps.values()}
            )
        except WrongCredentialError as err:
            raise ConfigEntryAuthFailed from err
        except DConnectError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


def _get_pump_data(pump: Pump) -> PumpData:
    pressure_converter = PressureConverter()
    volume_converter = VolumeConverter()
    if pump.state.measure_system is MeasureSystem.INTERNATIONAL:
        pressure_pa = pressure_converter.convert(
            pump.state.pressure_bar, UnitOfPressure.BAR, UnitOfPressure.PA
        )
        total_delivered_flow_cubic_meters = volume_converter.convert(
            pump.state.total_delivered_flow_liters,
            UnitOfVolume.LITERS,
            UnitOfVolume.CUBIC_METERS,
        )
        flow_cubic_meters_per_hour = (
            volume_converter.convert(
                pump.state.flow_liters_per_minute,
                UnitOfVolume.LITERS,
                UnitOfVolume.CUBIC_METERS,
            )
            * 60
        )
    else:  # pump.state.measure_system is MeasureSystem.ANGLO_AMERICAN
        pressure_pa = pressure_converter.convert(
            pump.state.pressure_psi, UnitOfPressure.PSI, UnitOfPressure.PA
        )
        total_delivered_flow_cubic_meters = volume_converter.convert(
            pump.state.total_delivered_flow_gallons,
            UnitOfVolume.GALLONS,
            UnitOfVolume.CUBIC_METERS,
        )
        flow_cubic_meters_per_hour = (
            volume_converter.convert(
                pump.state.flow_gallons_per_minute,
                UnitOfVolume.GALLONS,
                UnitOfVolume.CUBIC_METERS,
            )
            * 60
        )
    return PumpData(
        pressure_pa=pressure_pa,
        total_delivered_flow_cubic_meters=total_delivered_flow_cubic_meters,
        flow_cubic_meters_per_hour=flow_cubic_meters_per_hour,
        total_energy_consumption_kilowatt_hours=pump.state.total_energy_consumption_kilowatt_hours,
        signal_level_percent=pump.state.signal_level_percent,
        output_power_watts=pump.state.output_power_watts,
    )
