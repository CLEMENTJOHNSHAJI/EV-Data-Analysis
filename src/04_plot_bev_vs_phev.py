"""Grouped bar chart of BEV vs PHEV fleet size by city."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kanta", type=Path, default=u.DEFAULT_KANTA)
    parser.add_argument("--end-year", type=int, default=None, help="EV fleet end year. Default: complete years only (drops incomplete 2026).")
    parser.add_argument("--output-dir", type=Path, default=u.FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    kanta = u.load_kanta_registrations(args.kanta)
    fleet = u.fleet_composition(kanta, end_year=args.end_year)
    year_label = args.end_year if args.end_year else int(kanta["Year"].max())

    u.apply_style()
    x = np.arange(len(u.CITIES))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bev = fleet.set_index("City").loc[u.CITIES]
    bars_bev = ax.bar(x - width / 2, bev["BEV"], width, label="BEV", color=u.BEV_COLOR, zorder=3)
    bars_phev = ax.bar(x + width / 2, bev["PHEV"], width, label="PHEV", color=u.PHEV_COLOR, zorder=3)

    for bars, counts, shares in (
        (bars_bev, bev["BEV"], bev["BEV_Share_pct"]),
        (bars_phev, bev["PHEV"], bev["PHEV_Share_pct"]),
    ):
        for bar, count, share in zip(bars, counts, shares):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{int(count):,}\n({share:.1f}%)", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_title("BEV vs PHEV Fleet by City")
    ax.set_xlabel("City")
    ax.set_ylabel("Number of vehicles")
    ax.set_xticks(x)
    ax.set_xticklabels(u.CITIES)
    ax.legend(frameon=False)
    ax.grid(axis="x")
    ax.set_ylim(0, bev[["BEV", "PHEV"]].max().max() * 1.22)
    fig.tight_layout()
    u.save_figure(fig, args.output_dir / "ev_bev_phev_fleet.png")

    csv_path = u.processed_path("ev_bev_phev_fleet.csv")
    fleet.to_csv(csv_path, index=False)
    print(f"Cumulative through {year_label}")
    print(fleet.to_string(index=False))
    print(f"Saved {csv_path}")


if __name__ == "__main__":
    main()
