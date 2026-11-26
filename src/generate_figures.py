"""Publication figures for the Oamk master's thesis.

Underlying charger, fleet, temperature, ICS and CARI values are taken from the
cleaned local datasets and are not altered. Titles, axis labels, colours and
annotation placement are standardised for print.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
FIG_DIR = PROJECT_DIR / "outputs" / "figures" / "thesis"
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"

CITIES = ["Helsinki", "Tampere", "Oulu"]
CITY_COLORS = {"Helsinki": "#1f4e79", "Tampere": "#c45911", "Oulu": "#548235"}
CHARGER_COLORS = {"Type 2": "#1f4e79", "CHAdeMO": "#c45911", "CCS Fast": "#548235"}

FLEET = {"Helsinki": 58516, "Tampere": 16258, "Oulu": 13037}
ICS = {"Helsinki": 4765, "Tampere": 2040, "Oulu": 1089}
CLIMATE = {"Helsinki": 1.26, "Tampere": 1.30, "Oulu": 1.45}
JAN_TEMP = {"Helsinki": -5.15, "Tampere": -5.98, "Oulu": -8.90}
CARI = {"Tampere": 0.0965, "Helsinki": 0.0646, "Oulu": 0.0576}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "Times", "serif"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "grid.color": "#d9d9d9",
            "grid.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "legend.frameon": False,
        }
    )


def save(fig: plt.Figure, name: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved {path}")
    return path


def load_adoption() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "ev_adoption_analysis.csv")
    return df


def load_growth() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "ev_fleet_growth_rate.csv")


def plot_chargers() -> None:
    apply_style()
    type2 = [2690, 975, 377]
    chademo = [40, 10, 14]
    ccs = [391, 207, 134]
    x = np.arange(len(CITIES))
    width = 0.26
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    series = [
        ("Type 2 (AC)", type2, CHARGER_COLORS["Type 2"]),
        ("CHAdeMO (DC)", chademo, CHARGER_COLORS["CHAdeMO"]),
        ("CCS (DC fast)", ccs, CHARGER_COLORS["CCS Fast"]),
    ]
    for i, (label, values, color) in enumerate(series):
        bars = ax.bar(x + (i - 1) * width, values, width, label=label, color=color, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 35,
                f"{value:,}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(CITIES)
    ax.set_ylabel("Number of public charging outlets")
    ax.set_xlabel("Municipality")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 3200)
    ax.grid(axis="x")
    fig.tight_layout()
    save(fig, "figure_01_chargers_by_type.png")


def plot_annual_and_cumulative() -> None:
    apply_style()
    df = load_adoption()
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    for city, col in (
        ("Helsinki", "Helsinki Added"),
        ("Tampere", "Tampere Added"),
        ("Oulu", "Oulu Added"),
    ):
        ax.plot(df["Year"], df[col], marker="o", linewidth=2.0, markersize=4, color=CITY_COLORS[city], label=city)
    ax.set_xlabel("Year of first registration")
    ax.set_ylabel("Annual additions of BEVs and PHEVs")
    ax.legend()
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "figure_02_annual_ev_additions.png")

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    for city, col in (
        ("Helsinki", "Helsinki Cumulative"),
        ("Tampere", "Tampere Cumulative"),
        ("Oulu", "Oulu Cumulative"),
    ):
        ax.plot(df["Year"], df[col], marker="o", linewidth=2.0, markersize=4, color=CITY_COLORS[city], label=city)
    ax.set_xlabel("Year of first registration")
    ax.set_ylabel("Cumulative first registrations (BEVs and PHEVs)")
    ax.legend()
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "figure_03_cumulative_ev_fleet.png")


def plot_growth() -> None:
    apply_style()
    df = load_growth()
    plot = df[df["Year"] >= 2013]
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    for city, col in (
        ("Helsinki", "Helsinki Growth %"),
        ("Tampere", "Tampere Growth %"),
        ("Oulu", "Oulu Growth %"),
    ):
        ax.plot(plot["Year"], plot[col], marker="o", linewidth=2.0, markersize=4, color=CITY_COLORS[city], label=city)
    ax.set_xlabel("Year")
    ax.set_ylabel("Year-on-year growth of the cumulative series (%)")
    ax.legend()
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "figure_04_ev_fleet_growth_rate.png")


def plot_bev_phev() -> None:
    apply_style()
    bev = [31408, 8189, 6857]
    phev = [27108, 8069, 6180]
    bev_share = [53.7, 50.4, 52.6]
    phev_share = [46.3, 49.6, 47.4]
    x = np.arange(len(CITIES))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    bars_b = ax.bar(x - width / 2, bev, width, label="Battery electric (BEV)", color="#1f4e79", zorder=3)
    bars_p = ax.bar(x + width / 2, phev, width, label="Plug-in hybrid (PHEV)", color="#c45911", zorder=3)
    for bars, counts, shares in (
        (bars_b, bev, bev_share),
        (bars_p, phev, phev_share),
    ):
        for bar, count, share in zip(bars, counts, shares):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 400,
                f"{count:,}\n({share:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(CITIES)
    ax.set_ylabel("Passenger cars in the electrified fleet")
    ax.set_xlabel("Municipality")
    ax.legend()
    ax.set_ylim(0, 39000)
    ax.grid(axis="x")
    fig.tight_layout()
    save(fig, "figure_05_bev_vs_phev.png")


def plot_ics_and_pressure() -> None:
    apply_style()
    type2 = np.array([2690, 975, 377])
    chad = 3 * np.array([40, 10, 14])
    ccs = 5 * np.array([391, 207, 134])
    ics = type2 + chad + ccs
    evs_per = [12.28, 7.97, 11.97]
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 7.2), gridspec_kw={"height_ratios": [1.15, 1]})
    ax = axes[0]
    x = np.arange(len(CITIES))
    ax.bar(x, type2, color=CHARGER_COLORS["Type 2"], label="Type 2 × 1", zorder=3)
    ax.bar(x, chad, bottom=type2, color=CHARGER_COLORS["CHAdeMO"], label="CHAdeMO × 3", zorder=3)
    ax.bar(x, ccs, bottom=type2 + chad, color=CHARGER_COLORS["CCS Fast"], label="CCS × 5", zorder=3)
    for i, value in enumerate(ics):
        ax.text(i, value + 40, f"ICS = {int(value):,}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(CITIES)
    ax.set_ylabel("Weighted infrastructure capacity score")
    ax.legend(loc="upper right")
    ax.grid(axis="x")

    ax = axes[1]
    colors = ["#a31b1b", "#2e7d32", "#c45911"]
    bars = ax.barh(CITIES, evs_per, color=colors, height=0.5, zorder=3)
    ax.invert_yaxis()
    labels = [
        "58,516 / 4,765 = 12.28",
        "16,258 / 2,040 = 7.97",
        "13,037 / 1,089 = 11.97",
    ]
    for bar, text in zip(bars, labels):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2, text, va="center", fontsize=8)
    ax.set_xlabel("Electrified vehicles per infrastructure capacity unit")
    ax.set_xlim(0, 18)
    ax.grid(axis="y")
    fig.tight_layout()
    save(fig, "figure_06_ics_and_evs_per_unit.png")


def plot_climate() -> None:
    apply_style()
    temps = [JAN_TEMP[c] for c in CITIES]
    factors = [CLIMATE[c] for c in CITIES]
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 6.6))
    ax = axes[0]
    bars = ax.barh(CITIES, temps, color=[CITY_COLORS[c] for c in CITIES], height=0.5, zorder=3)
    ax.invert_yaxis()
    for bar, temp in zip(bars, temps):
        ax.text(temp + 0.12, bar.get_y() + bar.get_height() / 2, f"{temp:.2f} °C", va="center", fontsize=9)
    ax.set_xlabel("Mean January air temperature, 2010–2026 (°C)")
    ax.grid(axis="y")

    ax = axes[1]
    bars = ax.barh(CITIES, factors, color=["#c45911", "#c45911", "#843c0c"], height=0.5, zorder=3)
    ax.invert_yaxis()
    calcs = [
        "1 + 5.15 / 20 = 1.26",
        "1 + 5.98 / 20 = 1.30",
        "1 + 8.90 / 20 = 1.45",
    ]
    for bar, factor, calc in zip(bars, factors, calcs):
        ax.text(bar.get_width() + 0.015, bar.get_y() + bar.get_height() / 2, f"{factor:.2f}  ({calc})", va="center", fontsize=8)
    ax.set_xlabel("Climate severity factor")
    ax.set_xlim(1.0, 1.75)
    ax.grid(axis="y")
    fig.tight_layout()
    save(fig, "figure_07_climate_factor.png")


def plot_cari() -> None:
    apply_style()
    order = ["Tampere", "Helsinki", "Oulu"]
    values = [CARI[c] for c in order]
    colors = ["#2e7d32", "#c45911", "#a31b1b"]
    labels = [f"Rank {i}  {c}" for i, c in enumerate(order, start=1)]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    bars = ax.barh(labels, values, color=colors, height=0.5, zorder=3)
    ax.invert_yaxis()
    texts = [
        "2,040 / (16,258 × 1.30) = 0.0965",
        "4,765 / (58,516 × 1.26) = 0.0646",
        "1,089 / (13,037 × 1.45) = 0.0576",
    ]
    for bar, text in zip(bars, texts):
        ax.text(bar.get_width() + 0.0015, bar.get_y() + bar.get_height() / 2, text, va="center", fontsize=8)
    ax.set_xlabel("Climate-adjusted readiness index (CARI)")
    ax.set_xlim(0, 0.145)
    ax.grid(axis="y")
    fig.tight_layout()
    save(fig, "figure_08_cari.png")


def forecast_table() -> pd.DataFrame:
    """Fit linear and exponential models to 2020–2025 cumulative first registrations."""
    df = load_adoption()
    recent = df[df["Year"].between(2020, 2025)].copy()
    years = recent["Year"].to_numpy(dtype=float)
    t = years - 2020.0
    rows = []
    for city, col in (
        ("Helsinki", "Helsinki Cumulative"),
        ("Tampere", "Tampere Cumulative"),
        ("Oulu", "Oulu Cumulative"),
    ):
        y = recent[col].to_numpy(dtype=float)
        b_lin, a_lin = np.polyfit(t, y, 1)
        y2030_lin = a_lin + b_lin * (2030 - 2020)
        ln_y = np.log(y)
        b_exp, a_ln = np.polyfit(t, ln_y, 1)
        y2030_exp = float(np.exp(a_ln + b_exp * (2030 - 2020)))
        y2025 = float(y[-1])
        cagr = (y[-1] / y[0]) ** (1 / 5) - 1
        y2030_cagr = y2025 * (1 + cagr) ** 5
        growth_2025 = float(load_growth().loc[load_growth()["Year"] == 2025, f"{city} Growth %"].iloc[0]) / 100
        y2030_last = y2025 * (1 + growth_2025) ** 5
        rows.append(
            {
                "City": city,
                "Cumulative_2025": int(round(y2025)),
                "Linear_a": round(a_lin, 1),
                "Linear_b": round(b_lin, 1),
                "Linear_2030": int(round(y2030_lin)),
                "Exp_a": round(float(np.exp(a_ln)), 4),
                "Exp_b": round(b_exp, 4),
                "Exponential_2030": int(round(y2030_exp)),
                "CAGR_2020_2025": round(cagr * 100, 1),
                "CAGR_2030": int(round(y2030_cagr)),
                "Last_growth_2025_pct": round(growth_2025 * 100, 1),
                "LastRate_2030": int(round(y2030_last)),
            }
        )
    out = pd.DataFrame(rows)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLE_DIR / "forecast_2030.csv", index=False)

    cari_rows = []
    for _, row in out.iterrows():
        city = row["City"]
        ics = ICS[city]
        cf = CLIMATE[city]
        current_cari = CARI[city]
        for scenario, fleet_key in (
            ("Linear 2020–2025", "Linear_2030"),
            ("Exponential 2020–2025", "Exponential_2030"),
            ("2020–2025 CAGR", "CAGR_2030"),
            ("2025 growth held constant", "LastRate_2030"),
        ):
            fleet = int(row[fleet_key])
            future = ics / (fleet * cf)
            cari_rows.append(
                {
                    "City": city,
                    "Scenario": scenario,
                    "Forecast_fleet_2030": fleet,
                    "ICS": ics,
                    "Climate_Factor": cf,
                    "Current_CARI": current_cari,
                    "Future_CARI": round(future, 4),
                    "CARI_change_pct": round((future - current_cari) / current_cari * 100, 1),
                }
            )
    cari_out = pd.DataFrame(cari_rows)
    cari_out.to_csv(TABLE_DIR / "future_cari_2030.csv", index=False)
    return out, cari_out


def plot_forecast(out: pd.DataFrame, cari_out: pd.DataFrame) -> None:
    apply_style()
    x = np.arange(len(CITIES))
    width = 0.18
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    series = [
        ("First-registration series, 2025", [out.loc[out["City"] == c, "Cumulative_2025"].iloc[0] for c in CITIES], "#7f7f7f"),
        ("Linear projection, 2030", [out.loc[out["City"] == c, "Linear_2030"].iloc[0] for c in CITIES], "#1f4e79"),
        ("Exponential projection, 2030", [out.loc[out["City"] == c, "Exponential_2030"].iloc[0] for c in CITIES], "#c45911"),
        ("2025 growth held constant", [out.loc[out["City"] == c, "LastRate_2030"].iloc[0] for c in CITIES], "#548235"),
    ]
    for i, (label, values, color) in enumerate(series):
        bars = ax.bar(x + (i - 1.5) * width, values, width, label=label, color=color, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 800, f"{int(value):,}", ha="center", va="bottom", fontsize=6.5, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels(CITIES)
    ax.set_ylabel("Cumulative first registrations")
    ax.set_xlabel("Municipality")
    ax.legend(fontsize=8, loc="upper left")
    ymax = max(out["Exponential_2030"].max(), out["LastRate_2030"].max())
    ax.set_ylim(0, ymax * 1.28)
    ax.grid(axis="x")
    fig.tight_layout()
    save(fig, "figure_09_forecast_2030.png")

    apply_style()
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    current = [CARI[c] for c in CITIES]
    linear = [cari_out[(cari_out["City"] == c) & (cari_out["Scenario"] == "Linear 2020–2025")]["Future_CARI"].iloc[0] for c in CITIES]
    last = [cari_out[(cari_out["City"] == c) & (cari_out["Scenario"] == "2025 growth held constant")]["Future_CARI"].iloc[0] for c in CITIES]
    width = 0.26
    ax.bar(x - width, current, width, label="Current CARI (infrastructure snapshot)", color="#1f4e79", zorder=3)
    ax.bar(x, linear, width, label="2030 CARI, linear fleet growth, current ICS", color="#c45911", zorder=3)
    ax.bar(x + width, last, width, label="2030 CARI, 2025 growth held constant, current ICS", color="#548235", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(CITIES)
    ax.set_ylabel("Climate-adjusted readiness index")
    ax.legend(fontsize=8)
    ax.grid(axis="x")
    fig.tight_layout()
    save(fig, "figure_10_future_cari.png")


def main() -> None:
    plot_chargers()
    plot_annual_and_cumulative()
    plot_growth()
    plot_bev_phev()
    plot_ics_and_pressure()
    plot_climate()
    plot_cari()
    out, cari_out = forecast_table()
    plot_forecast(out, cari_out)
    print(out.to_string(index=False))
    print(cari_out.to_string(index=False))


if __name__ == "__main__":
    main()
