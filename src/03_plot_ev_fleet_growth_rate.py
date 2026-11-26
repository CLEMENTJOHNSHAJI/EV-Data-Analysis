"""Annual growth rate of the cumulative EV fleet, 2013-2025."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kanta", type=Path, default=u.DEFAULT_KANTA)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--start-year", type=int, default=2013, help="Skip tiny-base early years.")
    parser.add_argument("--output-dir", type=Path, default=u.FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    kanta = u.load_kanta_registrations(args.kanta)
    cumulative = u.annual_and_cumulative(kanta, end_year=args.end_year)
    growth = u.growth_rate(cumulative)
    plot = growth[(growth["Year"] >= args.start_year) & (growth["Year"] <= args.end_year)]

    u.apply_style()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for city in u.CITIES:
        part = plot[plot["City"] == city]
        ax.plot(part["Year"], part["Growth_pct"], marker="o", linewidth=2.4, markersize=4.5, color=u.CITY_COLORS[city], label=city)
    ax.set_title(f"Annual Growth Rate of Cumulative EV Fleet ({args.start_year}–{args.end_year})")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual growth rate (%)")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    u.save_figure(fig, args.output_dir / "ev_fleet_growth_rate.png")

    csv_path = u.processed_path("ev_fleet_growth_rate.csv")
    wide = growth.pivot(index="Year", columns="City", values=["Cumulative_EV", "Growth_pct"])
    wide.columns = [f"{city} {metric}" for metric, city in wide.columns]
    wide.to_csv(csv_path)
    print(f"Saved {csv_path}")
    print(plot.pivot(index="Year", columns="City", values="Growth_pct").round(1).to_string())


if __name__ == "__main__":
    main()
