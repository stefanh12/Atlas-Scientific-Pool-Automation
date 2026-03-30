"""Shared Home Assistant device metadata for Atlas Scientific Pool."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def integration_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the single integration-level device info for all entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"integration_{entry.entry_id}")},
        name=entry.title,
        manufacturer="Atlas Scientific",
        model="Pool Automation",
    )
