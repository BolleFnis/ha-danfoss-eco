"""Domain-level services for Danfoss Eco."""

from __future__ import annotations

import logging
from copy import deepcopy
from datetime import time

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN
from .coordinator import ETRVCoordinator
from .etrv.properties import DaySchedule, Schedule

_LOGGER = logging.getLogger(__name__)

SYNC_CLOCK_SCHEMA = vol.Schema({vol.Required("device_id"): cv.string})

# WeekdayIndex convention from the device: Sunday=0 .. Saturday=6.
_DAY_TO_INDEX = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 0,
}

_PERIOD_SCHEMA = vol.Schema({vol.Required("start"): cv.time, vol.Required("end"): cv.time})
_DAY_SCHEMA = vol.All(cv.ensure_list, [_PERIOD_SCHEMA], vol.Length(max=3))

SET_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Optional("home_temperature"): vol.All(vol.Coerce(float), vol.Range(min=4, max=35)),
        vol.Optional("away_temperature"): vol.All(vol.Coerce(float), vol.Range(min=4, max=35)),
        **{vol.Optional(day): _DAY_SCHEMA for day in _DAY_TO_INDEX},
    }
)


def _coordinator_for_device(hass: HomeAssistant, device_id: str) -> ETRVCoordinator:
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise vol.Invalid(f"unknown device_id {device_id}")
    for entry_id in device.config_entries:
        coord = hass.data.get(DOMAIN, {}).get(entry_id)
        if coord is not None:
            return coord
    raise vol.Invalid(f"device {device_id} is not a Danfoss Eco device")


def _minutes(t: time, *, is_end: bool) -> int:
    """Minutes since midnight. A 00:00 *end* means end-of-day (1440)."""
    m = t.hour * 60 + t.minute
    if is_end and m == 0:
        return 1440
    return m


def _day_from_periods(periods: list[dict]) -> DaySchedule:
    day = DaySchedule()
    slots = (
        ("p1_start", "p1_end"),
        ("p2_start", "p2_end"),
        ("p3_start", "p3_end"),
    )
    for (start_attr, end_attr), period in zip(slots, periods):
        setattr(day, start_attr, _minutes(period["start"], is_end=False))
        setattr(day, end_attr, _minutes(period["end"], is_end=True))
    day.validate()  # raise early with a clear message before we hit BLE
    return day


async def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "sync_clock"):
        return

    async def handle_sync_clock(call: ServiceCall) -> None:
        coord = _coordinator_for_device(hass, call.data["device_id"])
        await coord.async_sync_clock()

    async def handle_set_schedule(call: ServiceCall) -> None:
        coord = _coordinator_for_device(hass, call.data["device_id"])
        # Start from the last-read schedule so callers can patch a single day.
        base = coord.data.schedule if coord.data else None
        schedule = deepcopy(base) if base is not None else Schedule.empty()
        if "home_temperature" in call.data:
            schedule.home_temperature = call.data["home_temperature"]
        if "away_temperature" in call.data:
            schedule.away_temperature = call.data["away_temperature"]
        for day, index in _DAY_TO_INDEX.items():
            if day in call.data:
                schedule.days[index] = _day_from_periods(call.data[day])
        await coord.async_write_schedule(schedule)

    hass.services.async_register(DOMAIN, "sync_clock", handle_sync_clock, schema=SYNC_CLOCK_SCHEMA)
    hass.services.async_register(
        DOMAIN, "set_schedule", handle_set_schedule, schema=SET_SCHEDULE_SCHEMA
    )


def async_unload_services(hass: HomeAssistant) -> None:
    if not hass.data.get(DOMAIN):
        for service in ("sync_clock", "set_schedule"):
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)
