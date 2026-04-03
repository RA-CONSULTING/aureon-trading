#!/usr/bin/env python3
"""Deep battery probe — direct IOCTL for mWh, mV, mW at 50Hz."""
import sys, io, ctypes, ctypes.wintypes, time, struct, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("DEEP BATTERY PROBE — IOCTL direct hardware access")
print("=" * 60)

setupapi = ctypes.windll.setupapi
kernel32 = ctypes.windll.kernel32

# GUID_DEVINTERFACE_BATTERY {72631E54-78A4-11D0-BCF7-00AA00B7B32A}
guid_raw = struct.pack('<IHH', 0x72631E54, 0x78A4, 0x11D0) + b'\xBC\xF7\x00\xAA\x00\xB7\xB3\x2A'
GUID = (ctypes.c_byte * 16)(*guid_raw)

hdev = setupapi.SetupDiGetClassDevsW(ctypes.byref(GUID), None, None, 0x12)
print(f"  SetupDi handle: {hdev}")

class IFDATA(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_ulong), ('Guid', ctypes.c_byte * 16),
                ('Flags', ctypes.c_ulong), ('Rsvd', ctypes.c_void_p)]

ifd = IFDATA()
ifd.cbSize = ctypes.sizeof(ifd)

found = setupapi.SetupDiEnumDeviceInterfaces(hdev, None, ctypes.byref(GUID), 0, ctypes.byref(ifd))
print(f"  Found interface: {found}")

if not found:
    print(f"  Error: {ctypes.GetLastError()}")
    # Try without PRESENT flag
    setupapi.SetupDiDestroyDeviceInfoList(hdev)
    hdev = setupapi.SetupDiGetClassDevsW(ctypes.byref(GUID), None, None, 0x10)  # DEVICEINTERFACE only
    found = setupapi.SetupDiEnumDeviceInterfaces(hdev, None, ctypes.byref(GUID), 0, ctypes.byref(ifd))
    print(f"  Retry without PRESENT: {found}")

if found:
    req = ctypes.c_ulong(0)
    setupapi.SetupDiGetDeviceInterfaceDetailW(hdev, ctypes.byref(ifd), None, 0, ctypes.byref(req), None)
    print(f"  Detail size: {req.value}")

    buf = ctypes.create_string_buffer(req.value)
    struct.pack_into('I', buf, 0, 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6)

    ok = setupapi.SetupDiGetDeviceInterfaceDetailW(hdev, ctypes.byref(ifd), buf, req, None, None)
    if ok:
        path = ctypes.wstring_at(ctypes.addressof(buf) + 4)
        print(f"  Path: {path[:80]}")

        h = kernel32.CreateFileW(path, 0xC0000000, 3, None, 3, 0, None)
        if h and h != -1 and h != 0xFFFFFFFF:
            print(f"  Device OPEN")

            # Get tag
            tag = ctypes.c_ulong(0)
            timeout_val = ctypes.c_ulong(0)
            br = ctypes.c_ulong(0)
            ok = kernel32.DeviceIoControl(h, 0x294040, ctypes.byref(timeout_val), 4,
                                          ctypes.byref(tag), 4, ctypes.byref(br), None)
            print(f"  Tag: {tag.value} (ok={ok})")

            if ok:
                # Battery information
                class BQUERY(ctypes.Structure):
                    _fields_ = [('Tag', ctypes.c_ulong), ('InfoLevel', ctypes.c_ulong), ('AtRate', ctypes.c_long)]
                class BINFO(ctypes.Structure):
                    _fields_ = [('Capabilities', ctypes.c_ulong), ('Technology', ctypes.c_ubyte),
                                ('Reserved', ctypes.c_ubyte * 3), ('Chemistry', ctypes.c_char * 4),
                                ('DesignedCapacity', ctypes.c_ulong), ('FullChargedCapacity', ctypes.c_ulong),
                                ('DefaultAlert1', ctypes.c_ulong), ('DefaultAlert2', ctypes.c_ulong),
                                ('CriticalBias', ctypes.c_ulong), ('CycleCount', ctypes.c_ulong)]

                bq = BQUERY(Tag=tag.value, InfoLevel=0, AtRate=0)
                bi = BINFO()
                ok2 = kernel32.DeviceIoControl(h, 0x294044, ctypes.byref(bq), ctypes.sizeof(bq),
                                               ctypes.byref(bi), ctypes.sizeof(bi), ctypes.byref(br), None)
                if ok2:
                    print(f"\n  === BATTERY HARDWARE ===")
                    print(f"  Chemistry:     {bi.Chemistry}")
                    print(f"  Design:        {bi.DesignedCapacity} mWh")
                    print(f"  Full charge:   {bi.FullChargedCapacity} mWh")
                    print(f"  Cycles:        {bi.CycleCount}")
                    print(f"  Technology:    {bi.Technology}")
                    print(f"  Capabilities:  {bi.Capabilities:#x}")

                # Battery status — THE REAL DATA
                class BWAIT(ctypes.Structure):
                    _fields_ = [('Tag', ctypes.c_ulong), ('Timeout', ctypes.c_ulong),
                                ('PS', ctypes.c_ulong), ('Lo', ctypes.c_ulong), ('Hi', ctypes.c_ulong)]
                class BSTAT(ctypes.Structure):
                    _fields_ = [('PowerState', ctypes.c_ulong), ('Capacity', ctypes.c_ulong),
                                ('Voltage', ctypes.c_ulong), ('Rate', ctypes.c_long)]

                bw = BWAIT(Tag=tag.value, Timeout=0, PS=0, Lo=0, Hi=0)
                bs = BSTAT()
                ok3 = kernel32.DeviceIoControl(h, 0x29404C, ctypes.byref(bw), ctypes.sizeof(bw),
                                               ctypes.byref(bs), ctypes.sizeof(bs), ctypes.byref(br), None)
                if ok3:
                    print(f"\n  === LIVE STATUS ===")
                    print(f"  Capacity:  {bs.Capacity} mWh")
                    print(f"  Voltage:   {bs.Voltage} mV ({bs.Voltage/1000:.3f}V)")
                    print(f"  Rate:      {bs.Rate} mW ({abs(bs.Rate)/1000:.3f}W)")
                    ps = bs.PowerState
                    states = []
                    if ps & 1: states.append("AC_ONLINE")
                    if ps & 2: states.append("DISCHARGING")
                    if ps & 4: states.append("CHARGING")
                    if ps & 8: states.append("CRITICAL")
                    print(f"  State:     {' | '.join(states) if states else f'{ps}'}")

                    if ok2 and bi.FullChargedCapacity > 0:
                        exact = bs.Capacity / bi.FullChargedCapacity * 100
                        res = bi.FullChargedCapacity / 10000
                        print(f"  EXACT %:   {exact:.4f}%")
                        print(f"  Resolution: {res:.2f} mWh per 0.01%")

                    # LIVE STREAM at 50Hz
                    print(f"\n  === 50Hz LIVE STREAM (20 seconds) ===")
                    print(f"  {'t':>7s} {'mWh':>7s} {'mV':>6s} {'mW':>7s} {'W':>6s}")

                    prev_cap = bs.Capacity
                    prev_v = bs.Voltage
                    t0 = time.perf_counter()
                    readings = []

                    for i in range(1000):
                        bw.Tag = tag.value
                        kernel32.DeviceIoControl(h, 0x29404C, ctypes.byref(bw), ctypes.sizeof(bw),
                                                 ctypes.byref(bs), ctypes.sizeof(bs), ctypes.byref(br), None)
                        t = time.perf_counter() - t0
                        d_cap = bs.Capacity - prev_cap
                        d_v = bs.Voltage - prev_v

                        readings.append({"t": t, "mwh": bs.Capacity, "mv": bs.Voltage, "mw": bs.Rate})

                        if d_cap != 0 or d_v != 0 or i % 100 == 0:
                            ev = ""
                            if d_cap: ev += f" CAP:{d_cap:+d}mWh"
                            if d_v: ev += f" V:{d_v:+d}mV"
                            print(f"  {t:6.2f}s {bs.Capacity:6d} {bs.Voltage:5d} {bs.Rate:6d} {abs(bs.Rate)/1000:5.2f}{ev}", flush=True)

                        prev_cap = bs.Capacity
                        prev_v = bs.Voltage
                        time.sleep(0.02)

                    elapsed = time.perf_counter() - t0
                    caps = [r["mwh"] for r in readings]
                    volts = [r["mv"] for r in readings]
                    rates = [r["mw"] for r in readings]

                    print(f"\n  === 20s SUMMARY ===")
                    print(f"  Readings:   {len(readings)} at {len(readings)/elapsed:.0f}Hz")
                    print(f"  Capacity:   {min(caps)} - {max(caps)} mWh (swing: {max(caps)-min(caps)})")
                    print(f"  Voltage:    {min(volts)} - {max(volts)} mV (swing: {max(volts)-min(volts)})")
                    print(f"  Rate:       {min(rates)} to {max(rates)} mW")
                    print(f"  Avg rate:   {sum(rates)/len(rates):.1f} mW = {abs(sum(rates)/len(rates))/1000:.3f}W")
                    print(f"  Cap change: {readings[-1]['mwh'] - readings[0]['mwh']:+d} mWh in {elapsed:.1f}s")

                    # Save
                    json.dump({
                        "hardware": {"chemistry": bi.Chemistry.decode('ascii','replace') if ok2 else "?",
                                     "design_mwh": bi.DesignedCapacity if ok2 else 0,
                                     "full_charge_mwh": bi.FullChargedCapacity if ok2 else 0,
                                     "cycles": bi.CycleCount if ok2 else 0},
                        "summary": {"readings": len(readings), "hz": len(readings)/elapsed,
                                    "cap_min": min(caps), "cap_max": max(caps), "cap_swing": max(caps)-min(caps),
                                    "volt_min": min(volts), "volt_max": max(volts),
                                    "rate_min": min(rates), "rate_max": max(rates),
                                    "rate_avg": sum(rates)/len(rates)},
                    }, open("state/deep_battery_probe.json", "w"), indent=2)

                else:
                    print(f"  Status query failed: {ctypes.GetLastError()}")
            else:
                print(f"  Tag query failed: {ctypes.GetLastError()}")

            kernel32.CloseHandle(h)
        else:
            print(f"  Cannot open device: {ctypes.GetLastError()}")
    else:
        print(f"  Detail query failed: {ctypes.GetLastError()}")

setupapi.SetupDiDestroyDeviceInfoList(hdev)
print(f"\n{'='*60}")
