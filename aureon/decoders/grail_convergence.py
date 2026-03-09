"""
grail_convergence.py — Full-System Triangulation
=================================================
Combines FOUR relay layers to find the convergence point:

  Layer 1 — 10 Civilizational DNA sequences  (civilizational_dna.py)
  Layer 2 — Emerald Tablet multi-site alignments (emerald_spec.py)
  Layer 3 — Stone ring relay corridor axes
  Layer 4 — Kircher Labyrinth zone axes (Oedipus Aegyptiacus, 1652)
             Athanasius Kircher's reconstruction of the Hawara Labyrinth
             — 12 Egyptian nome capitals as opposing-zone axis pairs
             passing through the Labyrinth centre at 29.27°N, 30.90°E.

Great-circle cross-track minimisation across all 26 axes.
Search is constrained to 0–75°N, 30°W–90°E (sacred-site cluster region)
then refined to 0.05° resolution.

Layer 4 convergence result: 28.80°N, 30.90°E
Nearest site: Ihnasya el-Medina / Heracleopolis Magna (10 km)
  = Kircher's own Zone IX (Zona IX Heracleoupolis) in the Labyrinth plan.
  The system resolves to the node labelled within the source document itself.
"""
from __future__ import annotations
import math
import sys
from dataclasses import dataclass

sys.path.insert(0, ".")
from aureon.decoders.emerald_spec import map_geometric_pattern


# ── Site coordinate table ────────────────────────────────────────────────────
SITE_COORDS: dict[str, tuple[float, float]] = {
    "Newgrange":           (53.6947,  -6.4755),
    "Stonehenge":          (51.1789,  -1.8262),
    "Ring of Brodgar":     (58.9988,  -2.9611),
    "Chaco Canyon":        (36.0608,-107.9922),
    "Bandelier":           (35.7780,-106.2690),
    "Mohenjo-Daro":        (27.3290,  68.1380),
    "Delphi":              (38.4824,  22.5010),
    "Temple of Karnak":    (25.7188,  32.6573),
    "Abu Simbel":          (22.3372,  31.6258),
    "Machu Picchu":        (-13.1631,-72.5450),
    "Easter Island":       (-27.1127,-109.3497),
    "Angkor Wat":          (13.4125, 103.8670),
    "Great Zimbabwe":     (-20.2670,  30.9330),
    "Cahokia Mounds":      (38.6550, -90.0620),
    "Carnac Stones":       (47.6115,  -3.0167),
    "Baalbek":             (34.0040,  36.2160),
    "Göbekli Tepe":        (37.2233,  38.9222),
    "Beltany":             (54.8800,  -7.6700),
    "Ballynoe":            (54.2500,  -5.8300),
    "Nabta Playa":         (22.5100,  30.7200),
    "Gilgal Refaim":       (32.9000,  35.8000),
    "Almendres":           (38.5630,  -8.0780),
    "Malta":               (35.8267,  14.4367),
    "Ales Stenar":         (55.3833,  14.0597),
    "Goseck":              (51.1996,  11.8757),
    "Maeshowe":            (58.9932,  -3.1886),
    "City of Ur":          (30.9626,  46.1019),
    "Chichen Itza":        (20.6843, -88.5678),
    "Alexandria":          (31.2001,  29.9187),
}

# ── Candidate reference sites ────────────────────────────────────────────────
CANDIDATES: list[tuple[str, float, float]] = [
    ("Great Pyramid, Giza",     29.9792,  31.1342),
    ("Nabta Playa",             22.5100,  30.7200),
    ("Gilgal Refaim",           32.9000,  35.8000),
    ("Jerusalem Temple Mount",  31.7781,  35.2354),
    ("Göbekli Tepe",            37.2233,  38.9222),
    ("Baalbek",                 34.0040,  36.2160),
    ("Çatalhöyük",              37.6680,  32.8270),
    ("Mount Hermon",            33.4150,  35.8570),
    ("Delphi",                  38.4824,  22.5010),
    ("Malta Temples",           35.8267,  14.4367),
    ("Carnac Stones",           47.6115,  -3.0167),
    ("Stonehenge",              51.1789,  -1.8262),
    ("Newgrange",               53.6947,  -6.4755),
    ("Hawara / Labyrinth",             29.2700,  30.9000),
    ("Faiyum / Lake Moeris",           29.3000,  30.5500),
    # Kircher nome capitals (Layer 4)
    ("Heracleopolis / Ihnasya",        28.7100,  30.9200),
    ("Memphis / Mit Rahina",           29.8500,  31.2500),
    ("Hermopolis / Ashmunein",         27.7800,  30.8000),
    ("Canopus / Aboukir",              31.3200,  30.0800),
    ("Abydos / Araba el-Madfuna",      26.1800,  31.9200),
    ("Kom Ombo",                       24.4500,  32.9300),
]


# ── Geometry helpers ─────────────────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2)
         * math.sin(math.radians((lon2 - lon1) / 2)) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    la1, lo1, la2, lo2 = map(math.radians, [lat1, lon1, lat2, lon2])
    return math.atan2(
        math.sin(lo2 - lo1) * math.cos(la2),
        math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1),
    )


def cross_track(
    alat: float, alon: float,
    blat: float, blon: float,
    plat: float, plon: float,
) -> float:
    """Cross-track distance from point P to great circle A→B (km)."""
    R = 6371.0
    d13 = haversine(alat, alon, plat, plon) / R
    bt = _bearing(alat, alon, plat, plon) - _bearing(alat, alon, blat, blon)
    return abs(R * math.asin(max(-1.0, min(1.0, math.sin(d13) * math.sin(bt)))))


# ── Axis definition ──────────────────────────────────────────────────────────
@dataclass
class RelayAxis:
    origin: str
    terminus: str
    weight: float
    label: str


def build_axes() -> list[RelayAxis]:
    """Build the full set of relay-chain axes from all three layers."""
    axes: list[RelayAxis] = []

    # Layer 2 — Emerald engine multi-site alignments through Giza
    geom = map_geometric_pattern()
    for a in geom.alignments:
        if "Great Pyramid of Giza" not in a.sites:
            continue
        s0, s1 = a.sites[0], a.sites[-1]
        if s0 in SITE_COORDS and s1 in SITE_COORDS and s0 != s1:
            w = len(a.sites) / 9.0
            axes.append(RelayAxis(
                origin=s0, terminus=s1, weight=w,
                label=f"Emerald {len(a.sites)}-site [{s0}→{s1}]",
            ))

    # Layer 3 — Stone ring relay corridors
    stone_ring_axes = [
        ("Beltany",        "Nabta Playa",   0.80, "Atlantic ring corridor"),
        ("Ballynoe",       "Nabta Playa",   0.80, "Ballynoe ring corridor"),
        ("Ring of Brodgar","Nabta Playa",   0.70, "Orkney ring corridor"),
        ("Almendres",      "Malta",         0.70, "Iberian ring corridor"),
        ("Ales Stenar",    "Gilgal Refaim", 0.60, "Nordic ring corridor"),
        ("Goseck",         "Gilgal Refaim", 0.60, "Central European ring corridor"),
    ]
    for o, t, w, lbl in stone_ring_axes:
        axes.append(RelayAxis(origin=o, terminus=t, weight=w, label=lbl))

    # Layer 4 — Kircher Labyrinth zone axes (opposing nome-capital pairs)
    SITE_COORDS.update({
        "Hawara_Centre":    (29.2700, 30.9000),
        "Faiyum_Arsinoe":   (29.3000, 30.8500),
        "Memphis_MR":       (29.8500, 31.2500),
        "Araba_Abydos":     (26.1800, 31.9200),
        "Ihnasya":          (28.7100, 30.9200),
        "Hermopolis":       (27.7800, 30.8000),
        "Nile_Delta":       (30.5000, 31.1500),
        "Girga_Abydos":     (26.1800, 31.9200),
        "Canopus":          (31.3200, 30.0800),
        "Kom_Ombo":         (24.4500, 32.9300),
        "Sais":             (30.9600, 30.7700),
        "El_Qeis":          (28.2000, 30.7300),
        "Atfih":            (29.4100, 31.2200),
    })
    kircher_axes = [
        ("Araba_Abydos", "Memphis_MR",  0.85, "Kircher Z-X/V axis   (35km err at Hawara)"),
        ("Ihnasya",      "Canopus",     0.95, "Kircher Z-IX/XII axis (15km err at Hawara)"),
        ("Faiyum_Arsinoe","El_Qeis",    0.99, "Kircher Z-XI/III axis  (5km err at Hawara)"),
        ("Girga_Abydos", "Atfih",       0.85, "Kircher Z-VI/IV axis  (33km err at Hawara)"),
        ("Hermopolis",   "Kom_Ombo",    0.60, "Kircher Z-VIII/I axis (92km err at Hawara)"),
        ("Nile_Delta",   "Sais",        0.60, "Kircher Z-VII/II axis (99km err at Hawara)"),
        ("Kom_Ombo",     "Canopus",     0.90, "Kircher N-S Nile spine"),
        ("El_Qeis",      "Memphis_MR",  0.80, "Kircher W-E lateral axis"),
        ("Hawara_Centre","Faiyum_Arsinoe", 0.75, "Labyrinth→Faiyum radial"),
    ]
    for o, t, w, lbl in kircher_axes:
        axes.append(RelayAxis(origin=o, terminus=t, weight=w, label=lbl))

    # Layer 1 — CivDNA bearings projected as site-to-site axes
    civdna_axes = [
        ("Alexandria",   "Abu Simbel",  0.90, "Hermetic N-S axis"),
        ("Newgrange",    "Nabta Playa", 0.70, "Celtic-Egypt axis"),
        ("City of Ur",   "Nabta Playa", 0.60, "Sumerian axis"),
        ("Maeshowe",     "Gilgal Refaim", 0.50, "Norse axis"),
        ("Chichen Itza", "Delphi",      0.60, "Maya-Mediterranean axis"),
    ]
    for o, t, w, lbl in civdna_axes:
        axes.append(RelayAxis(origin=o, terminus=t, weight=w, label=lbl))

    return axes


# ── Triangulation engine ─────────────────────────────────────────────────────
def triangulate(axes: list[RelayAxis]) -> dict:
    """
    Grid search + refinement in the Old-World sacred-site region.
    Returns dict with lat, lon, total_err, per_axis errors, nearest sites.
    """
    best: dict = {"lat": 0.0, "lon": 0.0, "err": float("inf")}

    def score(la: float, lo: float) -> float:
        return sum(
            cross_track(
                SITE_COORDS[ax.origin][0], SITE_COORDS[ax.origin][1],
                SITE_COORDS[ax.terminus][0], SITE_COORDS[ax.terminus][1],
                la, lo,
            ) * ax.weight
            for ax in axes
        )

    # Pass 1: coarse 1° grid
    for lat_i in range(0, 76):
        for lon_i in range(-30, 91):
            e = score(float(lat_i), float(lon_i))
            if e < best["err"]:
                best = {"lat": float(lat_i), "lon": float(lon_i), "err": e}

    # Pass 2: fine 0.05° refinement
    for dlat in [x * 0.05 for x in range(-30, 31)]:
        for dlon in [x * 0.05 for x in range(-30, 31)]:
            la, lo = best["lat"] + dlat, best["lon"] + dlon
            e = score(la, lo)
            if e < best["err"]:
                best = {"lat": la, "lon": lo, "err": e}

    lat, lon = best["lat"], best["lon"]

    per_axis = []
    for ax in axes:
        c = cross_track(
            SITE_COORDS[ax.origin][0], SITE_COORDS[ax.origin][1],
            SITE_COORDS[ax.terminus][0], SITE_COORDS[ax.terminus][1],
            lat, lon,
        )
        per_axis.append({"axis": ax.label, "weight": ax.weight, "cross_track_km": round(c, 1)})

    nearest = sorted(
        [(nm, round(haversine(lat, lon, nlat, nlon), 1), nlat, nlon)
         for nm, nlat, nlon in CANDIDATES],
        key=lambda x: x[1],
    )

    return {
        "lat": round(lat, 2),
        "lon": round(lon, 2),
        "total_weighted_err_km": round(best["err"], 1),
        "n_axes": len(axes),
        "per_axis": per_axis,
        "nearest_sites": [{"name": n, "dist_km": d} for n, d, *_ in nearest[:8]],
    }


# ── CLI / pretty-print ───────────────────────────────────────────────────────
def render(result: dict) -> None:
    lat, lon = result["lat"], result["lon"]
    lat_str = f"{abs(lat):.2f}°{'N' if lat >= 0 else 'S'}"
    lon_str = f"{abs(lon):.2f}°{'E' if lon >= 0 else 'W'}"

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          GRAIL CONVERGENCE — FULL-SYSTEM RESULT             ║")
    print("║  CivDNA · Emerald · Ring corridors · Kircher Labyrinth zones ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Convergence point : {lat_str:>8}  {lon_str:<8}              ║")
    print(f"║  Total wtd error   : {result['total_weighted_err_km']:>8.0f} km                     ║")
    print(f"║  Axes used         : {result['n_axes']:>8}                             ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  RELAY AXIS CROSS-TRACK ERRORS:                             ║")
    for ax in sorted(result["per_axis"], key=lambda x: x["cross_track_km"]):
        bar = "█" * min(8, int(ax["cross_track_km"] / 100)) + "░" * max(0, 8 - int(ax["cross_track_km"] / 100))
        label = ax["axis"][:38]
        print(f"║  {ax['cross_track_km']:>6.0f}km  {bar}  {label:<38}║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  NEAREST SACRED SITES:                                      ║")
    for s in result["nearest_sites"]:
        print(f"║  {s['dist_km']:>7.0f} km  ·  {s['name']:<42}║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Qualitative assessment
    nearest_name = result["nearest_sites"][0]["name"]
    nearest_km   = result["nearest_sites"][0]["dist_km"]
    print(f"PRIMARY CONVERGENCE: {nearest_name}  ({nearest_km:.0f} km from computed point)")
    print()
    print("INTERPRETATION:")
    print("  The weighted cross-track minimisation across all relay layers")
    print(f"  pins the grail locus at {lat_str}, {lon_str}.")
    print()
    print("  Axes with ≤50 km cross-track (highest-confidence intercepts):")
    high_conf = [ax for ax in result["per_axis"] if ax["cross_track_km"] <= 50]
    for ax in sorted(high_conf, key=lambda x: x["cross_track_km"]):
        print(f"    {ax['cross_track_km']:>5.1f} km  [{ax['axis']}]")


def main() -> None:
    axes = build_axes()
    print(f"Built {len(axes)} relay-chain axes across all three layers.")
    result = triangulate(axes)
    render(result)
    return result


if __name__ == "__main__":
    main()
