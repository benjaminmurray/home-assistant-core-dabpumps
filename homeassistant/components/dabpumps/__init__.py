"""The DAB Pumps integration."""
from __future__ import annotations

from dabpumps.auth import Auth
from dabpumps.dconnect import DConnect
from dabpumps.exceptions import CannotConnectError, WrongCredentialError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, LOGGER
from .coordinator import DabPumpsDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DAB Pumps from a config entry."""

    email = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    try:
        session = aiohttp_client.async_create_clientsession(hass, verify_ssl=False)
        auth = Auth(session, email, password)
        await auth.authenticate()
    except CannotConnectError as ex:
        LOGGER.error("Cannot connect: %s", ex)
        raise ConfigEntryNotReady from ex
    except WrongCredentialError as ex:
        LOGGER.error("Authentication failed: %s", ex)
        return False

    coordinator = DabPumpsDataUpdateCoordinator(hass, email, DConnect(auth))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
