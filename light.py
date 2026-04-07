"""Light platform for Twinstar LED controllers."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Any

from bleak.exc import BleakError

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    BLE_CONNECT_TIMEOUT,
    CONF_PRIMARY_MAC,
    CONF_SLAVE_MAC,
    DOMAIN,
    SCAN_INTERVAL,
)
from .protocol import send_command

_LOGGER = logging.getLogger(__name__)

_DIGITS = re.compile(r"\d+")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    primary = entry.data[CONF_PRIMARY_MAC]
    slave = (entry.data.get(CONF_SLAVE_MAC) or "").strip()

    entities: list[TwinstarLightEntity] = [
        TwinstarLightEntity(
            entry,
            primary,
            "main",
            "Main",
        )
    ]
    if slave:
        entities.append(
            TwinstarLightEntity(
                entry,
                slave,
                "slave",
                "Slave",
            )
        )
    async_add_entities(entities, update_before_add=True)

    async def _poll(_: datetime | None = None) -> None:
        for entity in entities:
            await entity.async_update_ha_state(True)

    entry.async_on_unload(async_track_time_interval(hass, _poll, SCAN_INTERVAL))


def _parse_brightness_reply(text: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    m = _DIGITS.search(text)
    if not m:
        return None
    try:
        v = int(m.group(0))
    except ValueError:
        return None
    return max(0, min(100, v))


def _parse_power_reply(text: str) -> bool | None:
    t = text.strip().upper()
    if t == "ON":
        return True
    if t == "OFF":
        return False
    if "OFF" in t:
        return False
    if "ON" in t:
        return True
    return None


class TwinstarLightEntity(LightEntity):
    """Representation of a Twinstar LED channel."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(
        self,
        entry: ConfigEntry,
        mac: str,
        role: str,
        label: str,
    ) -> None:
        self._entry = entry
        self._mac = mac
        self._role = role
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{role}_{mac.lower().replace(':', '')}"
        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._lock = asyncio.Lock()
        self._attr_available = True
        self._attr_is_on: bool | None = None
        self._attr_brightness: int | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._mac)},
            name=f"Twinstar {self._attr_name}",
            manufacturer="Twinstar Korea",
            model="LED controller",
            connections={(dr.CONNECTION_BLUETOOTH, self._mac)},
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"mac_address": self._mac}

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        try:
            async with self._lock:
                if brightness is not None:
                    pct = max(0, min(100, round(brightness * 100 / 255)))
                    await send_command(
                        self._mac,
                        f"A{pct}",
                        connect_timeout=BLE_CONNECT_TIMEOUT,
                    )
                    await asyncio.sleep(0.05)
                await send_command(
                    self._mac,
                    "ON",
                    connect_timeout=BLE_CONNECT_TIMEOUT,
                )
        except BleakError as err:
            _LOGGER.error("Twinstar turn_on failed (%s): %s", self._mac, err)
            self._attr_available = False
            return
        self._attr_is_on = True
        if brightness is not None:
            self._attr_brightness = brightness
        self._attr_available = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            async with self._lock:
                await send_command(
                    self._mac,
                    "OFF",
                    connect_timeout=BLE_CONNECT_TIMEOUT,
                )
        except BleakError as err:
            _LOGGER.error("Twinstar turn_off failed (%s): %s", self._mac, err)
            self._attr_available = False
            return
        self._attr_is_on = False
        self._attr_brightness = 0
        self._attr_available = True
        self.async_write_ha_state()

    async def async_update(self) -> None:
        async with self._lock:
            try:
                power_raw = await send_command(
                    self._mac,
                    "powerstatus",
                    connect_timeout=BLE_CONNECT_TIMEOUT,
                )
                await asyncio.sleep(0.05)
                bright_raw = await send_command(
                    self._mac,
                    "brightlevel",
                    connect_timeout=BLE_CONNECT_TIMEOUT,
                )
            except BleakError as err:
                _LOGGER.debug("Twinstar update failed (%s): %s", self._mac, err)
                self._attr_available = False
                return

        power = _parse_power_reply(power_raw)
        pct = _parse_brightness_reply(bright_raw)

        if power is not None:
            self._attr_is_on = power
        if pct is not None:
            self._attr_brightness = round(pct * 255 / 100)
        if self._attr_is_on is False:
            self._attr_brightness = 0
        elif self._attr_is_on and self._attr_brightness is None:
            self._attr_brightness = 255

        self._attr_available = True
