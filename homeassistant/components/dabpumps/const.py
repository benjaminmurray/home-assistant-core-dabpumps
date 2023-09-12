"""Constants for the DAB Pumps integration."""

from datetime import timedelta
import logging

DOMAIN = "dabpumps"
LOGGER = logging.getLogger(__package__)
MANUFACTURER = "DAB Pumps"
UPDATE_INTERVAL = timedelta(seconds=20)
