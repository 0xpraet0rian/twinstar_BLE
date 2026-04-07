# Twinstar LED (Home Assistant)

Custom integration for Twinstar Korea aquarium LED controllers over **Bluetooth LE**, using the same text command protocol as the vendor *LightControl* app (GATT write/read on the command and reply characteristics).

## Requirements

- Home Assistant with the **Bluetooth** integration working on the host that runs HA (Linux with BlueZ, or supported HA OS hardware).
- The LED controller in range; pairing is not required for typical BLE GATT access, but adapter permissions must allow connections.

## Installation

1. Copy the entire `twinstar` folder into your Home Assistant configuration directory:

   ```text
   <config>/custom_components/twinstar/
   ```

2. Restart Home Assistant.

3. Add the integration: **Settings → Devices & services → Add integration → Twinstar LED**.

### Manual install checklist

| Path | Purpose |
|------|---------|
| `custom_components/twinstar/__init__.py` | Integration bootstrap |
| `custom_components/twinstar/manifest.json` | Metadata and dependencies |
| `custom_components/twinstar/config_flow.py` | UI configuration |
| `custom_components/twinstar/light.py` | Light entities |
| `custom_components/twinstar/protocol.py` | BLE helpers |
| `custom_components/twinstar/translations/` | UI strings |

Dependencies are declared in `manifest.json` (`bleak`); Home Assistant installs them on load.

## Configuration

During setup you provide:

| Field | Required | Description |
|-------|----------|-------------|
| **Primary MAC address** | Yes | Bluetooth address of the main controller. |
| **Slave MAC address** | No | Second controller when using a linked slave unit. Must differ from the primary address. |

MAC addresses can use `:` or `-` separators; they are normalized to uppercase with colons.

## Entities

- **Main** — light entity for the primary MAC.
- **Slave** — light entity, only if a slave MAC was configured.

State is refreshed on a **60 second** poll interval (power and brightness are read from the device when possible).

### Actions

- **On / brightness** — sends `A{0–100}` then `ON` (brightness mapped to 0–100%).
- **Off** — sends `OFF`.

Internal queries use `powerstatus` and `brightlevel` for polling.

## BLE service (reference)

| Item | UUID |
|------|------|
| Service | `00000180-0000-1000-8000-00805f9b34fb` |
| Write (commands) | `0000dead-0000-1000-8000-00805f9b34fb` |
| Read (replies) | `0000fef4-0000-1000-8000-00805f9b34fb` |
| RTC (not exposed in UI yet) | `0000fef5-0000-1000-8000-00805f9b34fb` |

Commands are UTF-8 text written to the write characteristic; replies are read from the reply characteristic.

## Troubleshooting

- **Unavailable / errors in logs** — check Bluetooth range, that no other adapter/app holds an exclusive connection, and HA Bluetooth diagnostics.
- **Wrong device** — confirm the MAC from your OS Bluetooth tools or router of BLE scanners.

## Related work

Layout and patterns are similar in spirit to community BLE integrations such as [chihiros-led-control](https://github.com/TheMicDiet/chihiros-led-control); the Twinstar protocol and UUIDs are specific to this hardware.

## License

Follow the license of the repository that contains this component (add your `LICENSE` file at repo root if you publish on GitHub).
