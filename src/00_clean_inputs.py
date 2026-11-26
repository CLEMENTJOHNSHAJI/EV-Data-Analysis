"""Clean original EV, charger, and weather inputs into processed copies.

Original files under data/raw/ and data/inputs/ are read only and never overwritten.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kanta", type=Path, default=u.DEFAULT_KANTA)
    parser.add_argument("--chargers", type=Path, default=u.DEFAULT_CHARGERS)
    parser.add_argument("--helsinki-weather", type=Path, default=u.DEFAULT_HELSINKI_WEATHER)
    parser.add_argument("--tampere-weather", type=Path, default=u.DEFAULT_TAMPERE_WEATHER)
    parser.add_argument("--oulu-weather", type=Path, default=u.DEFAULT_OULU_WEATHER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("Reading original files (not modified):")
    for label, path in {
        "kanta": args.kanta,
        "chargers": args.chargers,
        "helsinki weather": args.helsinki_weather,
        "tampere weather": args.tampere_weather,
        "oulu weather": args.oulu_weather,
    }.items():
        print(f"  {label}: {path}")

    outputs = u.clean_all_inputs(
        kanta=args.kanta,
        chargers=args.chargers,
        helsinki_weather=args.helsinki_weather,
        tampere_weather=args.tampere_weather,
        oulu_weather=args.oulu_weather,
    )
    print(f"\nCleaned copies written to {outputs['processed_dir']}")
    print("Cleaning rules applied:")
    print("  - Traficom kanta: keep Helsinki/Tampere/Oulu, years 2010-2026, numeric counts, no negatives")
    print("  - Incomplete 2026 EV year flagged as Year_Complete=False")
    print("  - Chargers: study cities only, non-negative integer counts")
    print("  - Weather: replace '-', '..', blanks with missing; drop invalid months and out-of-range temperatures")
    print("  - January climate averages skip missing months instead of treating them as zero")


if __name__ == "__main__":
    main()
