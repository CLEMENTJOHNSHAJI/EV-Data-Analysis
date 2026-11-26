"""Stacked ICS bars and EVs per infrastructure capacity unit."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chargers", type=Path, default=u.DEFAULT_CHARGERS)
    parser.add_argument("--kanta", type=Path, default=u.DEFAULT_KANTA)
    parser.add_argument("--end-year", type=int, default=None, help="EV fleet end year. Default: complete years only (drops incomplete 2026).")
    parser.add_argument("--output-dir", type=Path, default=u.FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chargers = u.load_chargers(args.chargers)
    kanta = u.load_kanta_registrations(args.kanta)
    fleet = u.fleet_composition(kanta, end_year=args.end_year)
    table = u.infrastructure_table(chargers, fleet).set_index("City").loc[u.CITIES].reset_index()

    u.apply_style()
    fig, axes = plt.subplots(2, 1, figsize=(11, 8.6), gridspec_kw={"height_ratios": [1.15, 1]})
    fig.suptitle("EVs per Infrastructure Capacity Unit", fontsize=15, fontweight="bold", y=0.98)
    fig.text(0.5, 0.935, "ICS = Type 2 + (3 × CHAdeMO) + (5 × CCS)   |   EVs per Capacity Unit = Total EV Fleet / ICS   |   Lower = better availability", ha="center", fontsize=9, color="#555555")

    ax = axes[0]
    x = np.arange(len(u.CITIES))
    type2 = table["Type2"]
    chad = u.CHADEMO_WEIGHT * table["CHAdeMO"]
    ccs = u.CCS_WEIGHT * table["CCS"]
    ax.bar(x, type2, color=u.CHARGER_COLORS["Type 2"], label="Type 2 (×1)", zorder=3)
    ax.bar(x, chad, bottom=type2, color=u.CHARGER_COLORS["CHAdeMO"], label="CHAdeMO (×3)", zorder=3)
    ax.bar(x, ccs, bottom=type2 + chad, color=u.CHARGER_COLORS["CCS Fast"], label="CCS Fast (×5)", zorder=3)
    for i, ics in enumerate(table["ICS"]):
        ax.text(i, ics, f"ICS = {int(ics):,}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_title("A. Weighted Infrastructure Capacity Score (ICS) by City")
    ax.set_xticks(x)
    ax.set_xticklabels(u.CITIES)
    ax.set_ylabel("Weighted capacity score")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(axis="x")

    ax = axes[1]
    colors = ["#dc2626", "#16a34a", "#ea580c"]
    bars = ax.barh(u.CITIES, table["EVs_per_Capacity_Unit"], color=colors, height=0.55, zorder=3)
    ax.invert_yaxis()
    for bar, row in zip(bars, table.itertuples()):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2, f"{row.EVs_per_Capacity_Unit:.2f} EVs / unit\n{int(row.Total_EV_Fleet):,} / {int(row.ICS):,} = {row.EVs_per_Capacity_Unit:.2f}", va="center", fontsize=8)
    ax.set_title("B. EVs per Infrastructure Capacity Unit (lower = better availability)")
    ax.set_xlabel("EVs per Infrastructure Capacity Unit")
    ax.grid(axis="y")
    ax.set_xlim(0, max(table["EVs_per_Capacity_Unit"]) * 1.45)

    fig.tight_layout(rect=(0, 0, 1, 0.91))
    u.save_figure(fig, args.output_dir / "ev_per_capacity_unit.png")

    csv_path = u.processed_path("ev_per_capacity_unit.csv")
    table.to_csv(csv_path, index=False)
    print(table[["City", "Type2", "CHAdeMO", "CCS", "ICS", "Total_EV_Fleet", "EVs_per_Capacity_Unit"]].to_string(index=False))
    print(f"Saved {csv_path}")


if __name__ == "__main__":
    main()
