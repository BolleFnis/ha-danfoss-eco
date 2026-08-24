"""Shared base class so platforms don't re-declare device_info etc."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ETRVCoordinator


class ETRVEntity(CoordinatorEntity[ETRVCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: ETRVCoordinator, key: str) -> None:
        super().__init__(coordinator)
        mac = format_mac(coordinator.address)
        self._attr_unique_id = f"{mac}_{key}"
        # Device Information Service values (read once by the coordinator) enrich
        # the HA device registry when available.
        dis = coordinator.device_information
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            manufacturer=dis.get("manufacturer", "Danfoss"),
            model=dis.get("model_number", "Eco (eTRV)"),
            name=coordinator.entry.title,
            connections={("bluetooth", coordinator.address)},
            sw_version=dis.get("firmware_revision") or dis.get("software_revision"),
            hw_version=dis.get("hardware_revision"),
            serial_number=dis.get("serial_number"),
        )
