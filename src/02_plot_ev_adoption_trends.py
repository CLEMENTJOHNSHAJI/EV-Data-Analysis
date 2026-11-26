"""Time-series of annual EV additions and cumulative EV fleet, 2010-2025."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kanta", type=Path, default=u.DEFAULT_KANTA)
    parser.add_argument("--end-year", type=int, default=2025, help="Exclude incomplete later years.")
    parser.add_argument("--output-dir", type=Path, default=u.FIGURES_DIR)
    return parser.parse_args()


def plot_line(table, value_col: str, title: str, ylabel: str, output: Path) -> Path:
    u.apply_style()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for city in u.CITIES:
        part = table[table["City"] == city].sort_values("Year")
        ax.plot(part["Year"], part[value_col], marker="o", linewidth=2.4, markersize=4.5, color=u.CITY_COLORS[city], label=city)
    ax.set_title(title)
    ax.set_xlabel("Year of first registration")
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return u.save_figure(fig, output)


def main() -> None:
    args = parse_args()
    kanta = u.load_kanta_registrations(args.kanta)
    table = u.annual_and_cumulative(kanta, end_year=args.end_year)
    plot_line(table, "Annual_EV", f"Annual EV Additions by City (2010–{args.end_year})", "Annual EV additions", args.output_dir / "annual_ev_additions.png")
    plot_line(table, "Cumulative_EV", f"Cumulative EV Fleet by City (2010–{args.end_year})", "Cumulative EV fleet", args.output_dir / "cumulative_ev_fleet.png")
    csv_path = u.processed_path("ev_adoption_analysis.csv")
    wide = table.pivot(index="Year", columns="City", values=["BEV", "Annual_EV", "Cumulative_EV"])
    wide.columns = [f"{city} {metric}" for metric, city in wide.columns]
    wide.to_csv(csv_path)
    print(f"Saved {csv_path}")
    print(table.pivot(index="Year", columns="City", values="Cumulative_EV").to_string())


if __name__ == "__main__":
    main()
