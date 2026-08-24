# Danfoss Eco (eTRV) for Home Assistant

![Danfoss Eco](custom_components/danfoss_eco/brand/icon%402x.png)

Home Assistant custom integration for **Danfoss Eco** Bluetooth Thermostatic Radiator Valves (eTRV). Local-only, talks directly to the TRV over BLE. This integration aims to transform your TRVs from a programmable device into a connected one.

## Features

Exposes connected TRV's as home-assistant thermostats. Devices can be paired directly from the integration ui. The integration polls valves every hour to get updates on ambient temperatures and manual temperature set point changes.

Features :

- Heat and Off (frost protection) modes
- Pin (untested)
- Child lock
- Vacation preset (untested)
- Battery level reporting
- Ambient temperature reporting
- On-device weekly schedules (read + write, see [Setting a schedule](#setting-a-schedule))

## Requirements

- Home Assistant `2024.1.0`+
- A working Bluetooth adapter known to Home Assistant (ESPHome BT proxy works too).
- The TRV's 4-digit PIN (default `0000`).

## Install

### HACS (recommended)

1. HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/Clap404/ha-danfoss-eco` as type _Integration_.
2. Install **Danfoss Eco (eTRV)**, restart Home Assistant.

### Manual

Copy `custom_components/danfoss_eco/` into your HA `config/custom_components/` directory, restart.

## Pairing a device

1. Settings → Devices & Services → **Add Integration** → _Danfoss Eco_. Discovered TRVs appear automatically; otherwise pick from the list.
2. Enter the 4-digit PIN (`0000` if never changed).
3. When prompted, **short-press the button on the TRV** — its LED goes solid. The integration reads the device's secret key during that window.
4. If pairing times out, press the button again and retry. The window is only a few seconds.

## Setting a schedule

The TRV runs a weekly heating program on-device: it holds a **home** temperature during comfort periods and falls back to an **away** temperature the rest of the time. Set it with the `danfoss_eco.set_schedule` service.

Go to **Settings → Devices & Services → Danfoss Eco → Configure**. Set the **home** and **away** temperatures, then type each day's comfort periods into its box:

- Morning + evening block: `06:00-08:30, 16:30-22:30`
- Up to 3 periods per day: `07:30-10:00, 12:00-14:00, 17:00-23:00`
- Warm all day: `07:30-23:00`
- Leave a day empty for away temperature all day.

Times must land on a **30-minute grid** (`06:00`, `06:30`, …); use `00:00` as an end time to mean end-of-day. Fields are prefilled with the schedule currently on the device.

The schedule only drives temperature while the thermostat is in **Auto** (schedule) mode. In **Heat** (manual) mode the TRV holds your set point and ignores the program.

> The same schedule can also be set from automations/scripts via the `danfoss_eco.set_schedule` action, using the same `"start-end"` text per day.

## Notes

- Scan interval is set to one hour because these TRV were not originally made for frequent communication. Increasing poll rate may drain the battery faster. Using the default, you should at least a year of battery life.

## Credits

This project has been largely AI generated. As such, I consider it a derivative work : protocol decoding, crypto handling, and characteristic mapping were lifted and ported from:

- [AdamStrojek/libetrv](https://github.com/AdamStrojek/libetrv.git) (Apache 2.0)
- [keton/etrv2mqtt](https://github.com/keton/etrv2mqtt) (MIT)
- [dmitry-cherkas/esphome-danfoss-eco](https://github.com/dmitry-cherkas/esphome-danfoss-eco) (MIT)

Huge thanks to the original authors for reverse engineering and publishing their projects many years ago.

## License

MIT — see [`LICENSE`](LICENSE.md). Compatible with upstream MIT licensing of the projects above.
