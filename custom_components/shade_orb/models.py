"""The led ble integration models."""
from __future__ import annotations

from dataclasses import dataclass

from shadeorb import ORB

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


@dataclass
class ORBData:
    """Data for the led ble integration."""

    title: str
    device: ORB
    #coordinator: DataUpdateCoordinator[None]