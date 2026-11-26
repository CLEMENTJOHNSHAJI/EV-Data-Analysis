"""Climate severity factor from January mean temperatures."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

import ev_utils as u


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helsinki-weather", type=Path, default=u.DEFAULT_HELSINKI_WEATHER)
    parser.add_argument("--tampere-weather", type=Path, default=u.DEFAULT_TAMPERE_WEATHER)
    parser.add_argument("--oulu-weather", type=Path, default=u.DEFAULT_OULU_WEATHER)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--output-dir", type=Path, default=u.FIGURES_DIR)
    return parser.parse_args()


def plot_temperature(climate, output: Path) -> None:
    u.apply_style()
    fig, ax = plt.subplots(figsize=(9, 4.4))
    colors = [u.CITY_COLORS[c] if c != "Tampere" else "#2563eb" for c in climate["City"]]
    bars = ax.barh(climate["City"], climate["Avg_January_Temp_C"], color=colors, height=0.55, zorder=3)
    ax.invert_yaxis()
    for bar, temp in zip(bars, climate["Avg_January_Temp_C"]):
        ax.text(temp + 0.12, bar.get_y() + bar.get_height() / 2, f"{temp:.2f} °C", va="center", fontsize=9, fontweight="bold")
    ax.set_title("Average January Temperature by Municipality (2010–2026)")
    ax.set_xlabel("Average January temperature (°C)")
    ax.grid(axis="y")
    fig.tight_layout()
    u.save_figure(fig, output)


def plot_factor(climate, output: Path) -> None:
    u.apply_style()
    fig, ax = plt.subplots(figsize=(9, 4.4))
    colors = ["#fb923c", "#f97316", "#ea580c"]
    bars = ax.barh(climate["City"], climate["Climate_Factor"], color=colors, height=0.55, zorder=3)
    ax.invert_yaxis()
    for bar, row in zip(bars, climate.itertuples()):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2, f"{row.Climate_Factor:.2f}\n1 + {abs(row.Avg_January_Temp_C):.2f} / 20 = {row.Climate_Factor:.2f}", va="center", fontsize=8)
    ax.set_title("Climate Severity Factor by Municipality")
    ax.set_xlabel("Climate Factor")
    ax.set_xlim(1.0, max(climate["Climate_Factor"]) + 0.18)
    ax.grid(axis="y")
    fig.tight_layout()
    u.save_figure(fig, output)


def plot_combined(climate, output: Path) -> None:
    u.apply_style()
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.4))
    fig.suptitle("Climate Severity Factor by Municipality", fontsize=15, fontweight="bold")
    fig.text(0.5, 0.93, "Climate Factor = 1 + |Average January Temperature| / 20   |   Higher value = more severe winter conditions", ha="center", fontsize=9, color="#555555")

    ax = axes[0]
    colors = ["#3b82f6", "#2563eb", "#1d4ed8"]
    bars = ax.barh(climate["City"], climate["Avg_January_Temp_C"], color=colors, height=0.55, zorder=3)
    ax.invert_yaxis()
    for bar, temp in zip(bars, climate["Avg_January_Temp_C"]):
        ax.text(temp + 0.12, bar.get_y() + bar.get_height() / 2, f"{temp:.2f} °C", va="center", fontsize=9, fontweight="bold")
    ax.set_title("A. Average January Temperature (2010–2026)")
    ax.set_xlabel("Average January temperature (°C)")
    ax.grid(axis="y")

    ax = axes[1]
    colors = ["#fb923c", "#f97316", "#ea580c"]
    bars = ax.barh(climate["City"], climate["Climate_Factor"], color=colors, height=0.55, zorder=3)
    ax.invert_yaxis()
    for bar, row in zip(bars, climate.itertuples()):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2, f"{row.Climate_Factor:.2f}\n1 + {abs(row.Avg_January_Temp_C):.2f} / 20 = {row.Climate_Factor:.2f}", va="center", fontsize=8)
    ax.set_title("B. Climate Severity Factor")
    ax.set_xlabel("Climate Factor")
    ax.set_xlim(1.0, max(climate["Climate_Factor"]) + 0.18)
    ax.grid(axis="y")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    u.save_figure(fig, output)


def main() -> None:
    args = parse_args()
    weather_paths = {
        "Helsinki": args.helsinki_weather,
        "Tampere": args.tampere_weather,
        "Oulu": args.oulu_weather,
    }
    climate = u.climate_table(weather_paths, end_year=args.end_year)
    climate = climate.set_index("City").loc[u.CITIES].reset_index()
    plot_combined(climate, args.output_dir / "climate_factor.png")
    plot_temperature(climate, args.output_dir / "climate_january_temperature.png")
    plot_factor(climate, args.output_dir / "climate_factor_score.png")
    csv_path = u.processed_path("climate_factor.csv")
    climate.to_csv(csv_path, index=False)
    print(climate.to_string(index=False))
    print(f"Saved {csv_path}")


if __name__ == "__main__":
    main()
