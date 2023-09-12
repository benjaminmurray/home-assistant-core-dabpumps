"""Base entity class for DAB Pumps."""

from dabpumps.pump import Pump

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import DabPumpsDataUpdateCoordinator, PumpData


class PumpEntity(CoordinatorEntity[DabPumpsDataUpdateCoordinator]):
    """Base pump entity."""

    _attr_has_entity_name = True
    pump_serial: str

    def __init__(
        self, coordinator: DabPumpsDataUpdateCoordinator, pump_serial: str
    ) -> None:
        """Initialize a pump entity."""
        super().__init__(coordinator=coordinator)
        self.pump_serial = pump_serial

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        if (
            self.coordinator.pumps is not None
            and self.pump_serial in self.coordinator.pumps
        ):
            pump: Pump = self.coordinator.pumps[self.pump_serial]
            return DeviceInfo(
                identifiers={(DOMAIN, self.pump_serial)},
                name=pump.name,
                manufacturer=MANUFACTURER,
                model=pump.product_name,
                sw_version=pump.state.version_dplus,
            )
        raise KeyError(f"Pump with serial '{self.pump_serial}' not found")

    @property
    def data(self) -> PumpData:
        """Fetch the pump data from our coordinator."""
        if self.pump_serial in self.coordinator.data.pumps:
            return self.coordinator.data.pumps[self.pump_serial]
        raise KeyError(f"Pump with serial '{self.pump_serial}' not found")
