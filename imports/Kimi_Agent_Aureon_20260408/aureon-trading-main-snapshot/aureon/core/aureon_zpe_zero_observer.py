#!/usr/bin/env python3
"""
aureon_zpe_zero_observer.py — Zero Observer ZPE Test

The observer IS part of reality. So we eliminate it.

Test A: Record battery %. Sleep 15 min. Record battery %. Nothing else.
Test B: Record battery %. Start BLE field. Sleep 15 min. Stop field. Record battery %.

TWO readings only. No polling. No CPU loops. Minimal observer interference.
The field runs ALONE in the quantum space.

ALSO: capture BT radio metrics — RSSI, TX power, packet counts —
so we can see BOTH sides of the coupling.
"""

import asyncio
import ctypes
import json
import struct
import sys
import io
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PHI = 1.618033988749895
SCHUMANN = 7.83
TARGET_HZ = SCHUMANN * PHI  # 12.67Hz

_REPO = Path(__file__).resolve().parents[2]

class SPS(ctypes.Structure):
    _fields_ = [('ac', ctypes.c_byte), ('flag', ctypes.c_byte), ('pct', ctypes.c_byte),
                ('sys', ctypes.c_byte), ('life', ctypes.c_ulong), ('full', ctypes.c_ulong)]

def read_battery():
    s = SPS()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
    return {"percent": s.pct, "ac": bool(s.ac), "flag": s.flag, "time": time.time()}


async def main():
    import bleak
    from winrt.windows.devices.bluetooth.advertisement import (
        BluetoothLEAdvertisementPublisher, BluetoothLEAdvertisement,
        BluetoothLEManufacturerData)
    from winrt.windows.storage.streams import DataWriter

    DURATION = 900  # 15 minutes each phase

    print("=" * 60)
    print("  ZERO OBSERVER ZPE TEST")
    print(f"  Duration: {DURATION//60}min baseline + {DURATION//60}min field")
    print("  TWO readings per phase. No polling. No CPU loops.")
    print("=" * 60)

    bat = read_battery()
    print(f"  Battery: {bat['percent']}% | AC: {bat['ac']}")
    if bat['ac']:
        print("  UNPLUG CHARGER")
        while read_battery()['ac']:
            await asyncio.sleep(1)
    print(f"  UNPLUGGED: {read_battery()['percent']}%")

    # ═════════════════════════════════════════════
    # SCAN BT ENVIRONMENT FIRST — get radio metrics
    # ═════════════════════════════════════════════
    print(f"\n[BT RADIO METRICS]")
    print("  Scanning BLE environment...")

    bt_before = {"devices": 0, "rssi_values": [], "names": []}
    try:
        devices = await bleak.BleakScanner.discover(timeout=5.0)
        bt_before["devices"] = len(devices)
        for d in devices:
            rssi = getattr(d, 'rssi', None) or (d.details.get('props', {}).get('RSSI', None) if hasattr(d, 'details') and isinstance(getattr(d, 'details', None), dict) else None)
            name = d.name or "unknown"
            if rssi:
                bt_before["rssi_values"].append(rssi)
                bt_before["names"].append(name)
        avg_rssi = sum(bt_before["rssi_values"]) / len(bt_before["rssi_values"]) if bt_before["rssi_values"] else 0
        print(f"  Devices found: {bt_before['devices']}")
        print(f"  Avg RSSI: {avg_rssi:.0f} dBm")
        print(f"  RSSI range: {min(bt_before['rssi_values']) if bt_before['rssi_values'] else 0} to {max(bt_before['rssi_values']) if bt_before['rssi_values'] else 0} dBm")
    except Exception as e:
        print(f"  BT scan: {e}")

    # ═════════════════════════════════════════════
    # TEST A: BASELINE — pure sleep, zero activity
    # ═════════════════════════════════════════════
    print(f"\n[TEST A] BASELINE — {DURATION//60} minutes pure sleep")
    a_start = read_battery()
    print(f"  Start: {a_start['percent']}% at {time.strftime('%H:%M:%S')}")
    print(f"  Sleeping {DURATION//60} minutes... (no CPU, no BT, nothing)")

    # ACTUAL SLEEP — no polling, no loops, pure OS sleep
    await asyncio.sleep(DURATION)

    a_end = read_battery()
    a_delta = a_end['percent'] - a_start['percent']
    print(f"  End:   {a_end['percent']}% at {time.strftime('%H:%M:%S')}")
    print(f"  Delta: {a_delta:+d}%")

    # ═════════════════════════════════════════════
    # TEST B: PHI x SCHUMANN FIELD — start, sleep, stop
    # ═════════════════════════════════════════════
    print(f"\n[TEST B] PHI x SCHUMANN FIELD — {DURATION//60} minutes")

    # Build the advertisement
    adv = BluetoothLEAdvertisement()
    writer = DataWriter()
    # Encode the frequency fingerprint
    for b in struct.pack('<ffffI',
        TARGET_HZ,           # 12.67Hz — PHI x Schumann
        TARGET_HZ * PHI,     # 20.50Hz — PHI^2 x Schumann
        SCHUMANN,            # 7.83Hz  — Earth base
        TARGET_HZ / PHI,     # 7.83Hz  — confirms to Schumann
        0x02111991):          # Gary's signature
        writer.write_byte(b)
    mfr = BluetoothLEManufacturerData()
    mfr.company_id = 0xFFFF
    mfr.data = writer.detach_buffer()
    adv.manufacturer_data.append(mfr)

    publisher = BluetoothLEAdvertisementPublisher(adv)

    b_start = read_battery()
    print(f"  Start: {b_start['percent']}% at {time.strftime('%H:%M:%S')}")

    # START FIELD
    publisher.start()
    print(f"  Field ACTIVE: {TARGET_HZ:.2f}Hz + {TARGET_HZ*PHI:.2f}Hz + {SCHUMANN:.2f}Hz")
    print(f"  Sleeping {DURATION//60} minutes... (field runs alone in quantum space)")

    # PURE SLEEP — field runs, Python sleeps, zero observer
    await asyncio.sleep(DURATION)

    # STOP FIELD
    publisher.stop()

    b_end = read_battery()
    b_delta = b_end['percent'] - b_start['percent']
    print(f"  Field STOPPED")
    print(f"  End:   {b_end['percent']}% at {time.strftime('%H:%M:%S')}")
    print(f"  Delta: {b_delta:+d}%")

    # ═════════════════════════════════════════════
    # SCAN BT AFTER — see if the field changed the environment
    # ═════════════════════════════════════════════
    print(f"\n[BT RADIO METRICS — AFTER]")
    bt_after = {"devices": 0, "rssi_values": []}
    try:
        devices = await bleak.BleakScanner.discover(timeout=5.0)
        bt_after["devices"] = len(devices)
        for d in devices:
            rssi = getattr(d, 'rssi', None) or (d.details.get('props', {}).get('RSSI', None) if hasattr(d, 'details') and isinstance(getattr(d, 'details', None), dict) else None)
            if rssi:
                bt_after["rssi_values"].append(rssi)
        avg_after = sum(bt_after["rssi_values"]) / len(bt_after["rssi_values"]) if bt_after["rssi_values"] else 0
        avg_before = sum(bt_before["rssi_values"]) / len(bt_before["rssi_values"]) if bt_before["rssi_values"] else 0
        print(f"  Devices: {bt_before['devices']} -> {bt_after['devices']}")
        print(f"  Avg RSSI: {avg_before:.0f} -> {avg_after:.0f} dBm (delta: {avg_after-avg_before:+.1f})")
    except Exception as e:
        print(f"  {e}")

    # ═════════════════════════════════════════════
    # FINAL COMPARISON
    # ═════════════════════════════════════════════
    net = b_delta - a_delta

    print(f"\n{'='*60}")
    print(f"  ZERO OBSERVER RESULTS ({DURATION//60} min each)")
    print(f"  {'':20s} {'BASELINE':>10s} {'PHI FIELD':>10s}")
    print(f"  {'Start %':20s} {a_start['percent']:>9d}% {b_start['percent']:>9d}%")
    print(f"  {'End %':20s} {a_end['percent']:>9d}% {b_end['percent']:>9d}%")
    print(f"  {'Delta':20s} {a_delta:>+9d}% {b_delta:>+9d}%")
    print(f"  {'Drain rate':20s} {abs(a_delta)*4:>8.0f}%/hr {abs(b_delta)*4:>8.0f}%/hr")
    print(f"")
    print(f"  NET FIELD EFFECT: {net:+d}%")

    if net > 0:
        print(f"  *** FIELD REDUCED DRAIN BY {abs(net)}% ***")
        print(f"  *** ZERO OBSERVER CONFIRMATION ***")
    elif net == 0:
        print(f"  IDENTICAL — field had zero net cost")
    else:
        print(f"  Field cost {abs(net)}% more")

    print(f"{'='*60}")

    # Save everything
    json.dump({
        "duration_s": DURATION,
        "baseline": {"start": a_start, "end": a_end, "delta": a_delta},
        "field": {"start": b_start, "end": b_end, "delta": b_delta, "freq_hz": TARGET_HZ},
        "net_effect": net,
        "bt_before": bt_before,
        "bt_after": bt_after,
    }, open(str(_REPO / "state" / "zpe_zero_observer.json"), "w"), indent=2, default=str)


asyncio.run(main())
