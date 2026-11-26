"""Bar chart of public EV chargers by city and connector type."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chargers", type=Path, default=u.DEFAULT_CHARGERS)
    parser.add_argument("--output-dir", type=Path, default=u.FIGURES_DIR)
    return parser.parse_args()


def plot_chargers(chargers, output_dir: Path) -> Path:
    u.apply_style()
    cities = [c for c in u.CITIES if c in set(chargers["City"])]
    df = chargers.set_index("City").loc[cities]
    x = np.arange(len(cities))
    width = 0.25
    series = [
        ("Type 2", df["Type2"], u.CHARGER_COLORS["Type 2"]),
        ("CHAdeMO", df["CHAdeMO"], u.CHARGER_COLORS["CHAdeMO"]),
        ("CCS Fast", df["CCS"], u.CHARGER_COLORS["CCS Fast"]),
    ]

    fig, ax = plt.subplots(figsize=(10, 5.6))
    for i, (label, values, color) in enumerate(series):
        bars = ax.bar(x + (i - 1) * width, values, width, label=f"{label} Chargers", color=color, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 40, f"{int(value):,}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_title("Public EV Chargers by City and Connector Type")
    ax.set_xticks(x)
    ax.set_xticklabels(cities)
    ax.set_ylabel("Number of chargers")
    ax.set_axisbelow(True)
    ax.grid(axis="x")
    ax.legend(frameon=False, loc="upper right")
    ax.set_ylim(0, max(df[["Type2", "CHAdeMO", "CCS"]].max()) * 1.18)
    fig.tight_layout()
    return u.save_figure(fig, output_dir / "ev_chargers_by_city.png")


def main() -> None:
    args = parse_args()
    chargers = u.load_chargers(args.chargers)
    plot_chargers(chargers, args.output_dir)
    print(chargers.to_string(index=False))


if __name__ == "__main__":
    main()
