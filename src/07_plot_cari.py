"""Climate-Adjusted Readiness Index (CARI) ranking chart."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chargers", type=Path, default=u.DEFAULT_CHARGERS)
    parser.add_argument("--kanta", type=Path, default=u.DEFAULT_KANTA)
    parser.add_argument("--helsinki-weather", type=Path, default=u.DEFAULT_HELSINKI_WEATHER)
    parser.add_argument("--tampere-weather", type=Path, default=u.DEFAULT_TAMPERE_WEATHER)
    parser.add_argument("--oulu-weather", type=Path, default=u.DEFAULT_OULU_WEATHER)
    parser.add_argument("--end-year", type=int, default=None, help="EV fleet end year. Default: complete years only (drops incomplete 2026).")
    parser.add_argument("--climate-end-year", type=int, default=2026)
    parser.add_argument("--output-dir", type=Path, default=u.FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chargers = u.load_chargers(args.chargers)
    kanta = u.load_kanta_registrations(args.kanta)
    fleet = u.fleet_composition(kanta, end_year=args.end_year)
    infra = u.infrastructure_table(chargers, fleet)
    climate = u.climate_table(
        {
            "Helsinki": args.helsinki_weather,
            "Tampere": args.tampere_weather,
            "Oulu": args.oulu_weather,
        },
        end_year=args.climate_end_year,
    )
    cari = u.cari_table(infra, climate)

    labels = [f"#{int(row.Rank)}  {row.City}" for row in cari.itertuples()]
    colors = [u.CARI_COLORS[city] for city in cari["City"]]

    u.apply_style()
    fig, ax = plt.subplots(figsize=(10, 4.8))
    bars = ax.barh(labels, cari["CARI"], color=colors, height=0.55, zorder=3)
    ax.invert_yaxis()
    for bar, row in zip(bars, cari.itertuples()):
        ax.text(
            bar.get_width() + 0.0015,
            bar.get_y() + bar.get_height() / 2,
            f"{row.CARI:.4f}\n{int(row.ICS):,} / ({int(row.Total_EV_Fleet):,} × {row.Climate_Factor:.2f}) = {row.CARI:.4f}",
            va="center",
            fontsize=8,
        )
    ax.set_title("Climate-Adjusted Readiness Index (CARI)")
    ax.set_xlabel("Climate-Adjusted Readiness Index (CARI)")
    ax.set_xlim(0, max(cari["CARI"]) * 1.45)
    ax.grid(axis="y")
    fig.tight_layout()
    u.save_figure(fig, args.output_dir / "cari.png")
    u.save_figure(fig, args.output_dir / "cari_ranking.png")

    csv_path = u.processed_path("cari.csv")
    cari.to_csv(csv_path, index=False)
    print(cari[["Rank", "City", "Total_EV_Fleet", "ICS", "Climate_Factor", "CARI"]].to_string(index=False))
    print(f"Saved {csv_path}")


if __name__ == "__main__":
    main()
