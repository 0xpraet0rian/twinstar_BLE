"""Constants for Twinstar LED (LightControl Standard protocol)."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "twinstar"

CONF_PRIMARY_MAC = "primary_mac"
CONF_SLAVE_MAC = "slave_mac"

DEFAULT_NAME = "Twinstar"

SERVICE_UUID = "00000180-0000-1000-8000-00805f9b34fb"
CHAR_WRITE_CMD = "0000dead-0000-1000-8000-00805f9b34fb"
CHAR_READ_REPLY = "0000fef4-0000-1000-8000-00805f9b34fb"
CHAR_RTC = "0000fef5-0000-1000-8000-00805f9b34fb"

SCAN_INTERVAL = timedelta(seconds=60)

BLE_CONNECT_TIMEOUT = 25.0
COMMAND_GAP = 0.4
