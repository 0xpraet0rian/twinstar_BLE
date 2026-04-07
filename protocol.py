"""BLE GATT helpers for Twinstar LightControl protocol."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime

from bleak import BleakClient

from .const import CHAR_READ_REPLY, CHAR_RTC, CHAR_WRITE_CMD, COMMAND_GAP

_MAC_RE = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
)


def normalize_mac(mac: str) -> str:
    """Return MAC as upper-case hex with colons."""
    mac = mac.strip().upper().replace("-", ":")
    parts = mac.split(":")
    if len(parts) != 6:
        return mac
    try:
        return ":".join(f"{int(p, 16):02X}" for p in parts)
    except ValueError:
        return mac


def is_valid_mac(mac: str) -> bool:
    return bool(_MAC_RE.match(mac.strip()))


async def send_command(
    address: str,
    command: str,
    *,
    connect_timeout: float,
) -> str:
    """Write UTF-8 command to the CMD characteristic and read the reply characteristic."""
    async with BleakClient(address, timeout=connect_timeout) as client:
        await client.write_gatt_char(
            CHAR_WRITE_CMD,
            command.encode("utf-8"),
            response=False,
        )
        await asyncio.sleep(COMMAND_GAP)
        raw = await client.read_gatt_char(CHAR_READ_REPLY)
    if isinstance(raw, (bytes, bytearray)):
        return raw.decode("utf-8", errors="replace").strip()
    return str(raw).strip()


async def write_rtc_local_time(
    address: str,
    dt: datetime,
    *,
    connect_timeout: float,
) -> None:
    """Write 14-byte ASCII yyyyMMddHHmmss to FEF5 (matches official app)."""
    payload = dt.strftime("%Y%m%d%H%M%S").encode("ascii")
    if len(payload) != 14:
        raise ValueError("RTC payload must be 14 bytes")

    async with BleakClient(address, timeout=connect_timeout) as client:
        await client.write_gatt_char(
            CHAR_RTC,
            payload,
            response=False,
        )
