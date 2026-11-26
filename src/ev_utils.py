"""Shared cleaning, loaders, formulas, and plot styling for the EV thesis figures.

Original input files are read only. Cleaned copies are written under data/processed/.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CITIES = ["Helsinki", "Tampere", "Oulu"]
CITY_ALIASES = {
    "helsinki": "Helsinki",
    "tampere": "Tampere",
    "oulu": "Oulu",
}
CITY_COLORS = {
    "Helsinki": "#2563eb",
    "Tampere": "#ef4444",
    "Oulu": "#10b981",
}
CHARGER_COLORS = {
    "Type 2": "#2563eb",
    "CHAdeMO": "#f59e0b",
    "CCS Fast": "#10b981",
}
BEV_COLOR = "#2563eb"
PHEV_COLOR = "#f59e0b"
CARI_COLORS = {
    "Tampere": "#16a34a",
    "Helsinki": "#f97316",
    "Oulu": "#dc2626",
}

TYPE2_WEIGHT = 1
CHADEMO_WEIGHT = 3
CCS_WEIGHT = 5
CLIMATE_SCALE = 20
MIN_YEAR = 2010
MAX_YEAR = 2026
TEMP_MIN_C = -50
TEMP_MAX_C = 40
MISSING_TOKENS = {
    "",
    "-",
    "–",
    "—",
    ".",
    "..",
    "*",
    "na",
    "n/a",
    "nan",
    "null",
    "none",
    "missing",
}

CODE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CODE_DIR.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
INPUTS_DIR = PROJECT_DIR / "data" / "inputs"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
FIGURES_DIR = PROJECT_DIR / "outputs" / "figures" / "analysis"
THESIS_FIGURES_DIR = PROJECT_DIR / "outputs" / "figures" / "thesis"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"

DEFAULT_KANTA = DATA_DIR / "kanta_010_20260727-150017.xlsx"
DEFAULT_CHARGERS = INPUTS_DIR / "chargers_by_type.csv"
DEFAULT_HELSINKI_WEATHER = DATA_DIR / (
    "Vantaa Helsinki-Vantaa airport_ 1.1.2010 - 27.7.2026_"
    "ab0c60b4-d272-48fb-98a3-cb04299bd9a8.xlsx"
)
DEFAULT_TAMPERE_WEATHER = DATA_DIR / (
    "Pirkkala Tampere-Pirkkala airport_ 1.1.2010 - 27.7.2026_"
    "6daa952f-7660-4cac-b613-51df15958507.xlsx"
)
DEFAULT_OULU_WEATHER = DATA_DIR / (
    "Oulu airport_ 1.1.2010 - 27.7.2026_"
    "b89c5114-c4f2-4069-ae07-93420b3475ca.xlsx"
)


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#969696",
            "axes.grid": True,
            "grid.color": "#e6e6e6",
            "grid.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "figure.dpi": 140,
            "savefig.dpi": 180,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    print(f"Saved {path}")
    return path


def processed_path(filename: str) -> Path:
    """Path for a derived CSV in data/processed/, creating the folder if needed."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return PROCESSED_DIR / filename


def _original_paths() -> set[Path]:
    return {
        DEFAULT_KANTA.resolve(),
        DEFAULT_CHARGERS.resolve(),
        DEFAULT_HELSINKI_WEATHER.resolve(),
        DEFAULT_TAMPERE_WEATHER.resolve(),
        DEFAULT_OULU_WEATHER.resolve(),
    }


def write_processed(df: pd.DataFrame, filename: str) -> Path:
    """Write a cleaned dataset. Never overwrites original input files."""
    path = PROCESSED_DIR / filename
    if path.resolve() in _original_paths() or DATA_DIR.resolve() in path.resolve().parents:
        raise ValueError(f"Refusing to write cleaned data over an original input: {path}")
    if path.resolve().parent == INPUTS_DIR.resolve():
        raise ValueError(f"Refusing to overwrite files in inputs/: {path}")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Saved cleaned copy {path}")
    return path


def _is_year(value) -> bool:
    try:
        year = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return False
    return 1990 <= year <= 2100


def to_numeric_clean(series: pd.Series) -> pd.Series:
    """Coerce a column to numeric without changing the source file."""
    text = series.astype(str).str.strip()
    text = text.str.replace("\u00a0", "", regex=False)
    text = text.str.replace(",", "", regex=False)
    text = text.str.replace(" ", "", regex=False)
    lowered = text.str.lower()
    text = text.mask(lowered.isin(MISSING_TOKENS))
    return pd.to_numeric(text, errors="coerce")


def normalize_city(value) -> str | None:
    if pd.isna(value):
        return None
    key = str(value).strip().lower()
    return CITY_ALIASES.get(key)


def read_table(path: Path) -> pd.DataFrame:
    """Read an original table into memory. The file is never modified."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def clean_kanta_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Keep study cities/years, coerce counts, drop empty and duplicate rows."""
    out = df.copy()
    out["City"] = out["City"].map(normalize_city)
    out = out[out["City"].isin(CITIES)]
    out["Year"] = to_numeric_clean(out["Year"]).astype("Int64")
    out = out[out["Year"].between(MIN_YEAR, MAX_YEAR)]
    for col in ["BEV", "Petrol_PHEV", "Diesel_PHEV"]:
        out[col] = to_numeric_clean(out[col]).fillna(0).clip(lower=0).round().astype(int)
    out = out.dropna(subset=["Year", "City"])
    out["Year"] = out["Year"].astype(int)
    out = (
        out.groupby(["City", "Year"], as_index=False)[["BEV", "Petrol_PHEV", "Diesel_PHEV"]]
        .sum()
        .sort_values(["City", "Year"])
        .reset_index(drop=True)
    )
    out["Annual_EV"] = out["BEV"] + out["Petrol_PHEV"] + out["Diesel_PHEV"]
    out["Year_Complete"] = out["Year"] < MAX_YEAR
    return out


def clean_chargers_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["City"] = out["City"].map(normalize_city)
    out = out[out["City"].isin(CITIES)]
    for col in ["Type2", "CHAdeMO", "CCS"]:
        out[col] = to_numeric_clean(out[col]).fillna(0).clip(lower=0).round().astype(int)
    out = out.dropna(subset=["City"])
    out = out.groupby("City", as_index=False)[["Type2", "CHAdeMO", "CCS"]].sum()
    out["ICS"] = (
        TYPE2_WEIGHT * out["Type2"]
        + CHADEMO_WEIGHT * out["CHAdeMO"]
        + CCS_WEIGHT * out["CCS"]
    )
    return out.set_index("City").loc[[c for c in CITIES if c in set(out["City"])]].reset_index()


def clean_weather_dataframe(df: pd.DataFrame, station: str | None = None) -> pd.DataFrame:
    """Drop missing FMI placeholders, invalid months, and out-of-range temperatures."""
    out = df.copy()
    out["Year"] = to_numeric_clean(out["Year"])
    out["Month"] = to_numeric_clean(out["Month"])
    out["Temperature"] = to_numeric_clean(out["Temperature"])
    if "Station" in out.columns:
        out["Station"] = out["Station"].astype(str).str.strip()
    elif station:
        out["Station"] = station
    before = len(out)
    out = out.dropna(subset=["Year", "Month"])
    out = out[out["Month"].between(1, 12)]
    out = out[out["Year"].between(MIN_YEAR, MAX_YEAR)]
    out = out[out["Temperature"].isna() | out["Temperature"].between(TEMP_MIN_C, TEMP_MAX_C)]
    out["Year"] = out["Year"].astype(int)
    out["Month"] = out["Month"].astype(int)
    out = (
        out.groupby(["Station", "Year", "Month"], as_index=False, dropna=False)["Temperature"]
        .mean()
        .sort_values(["Year", "Month"])
        .reset_index(drop=True)
    )
    dropped = before - len(out)
    if dropped:
        print(f"Weather cleaning dropped {dropped} invalid or placeholder rows")
    return out


def load_kanta_registrations(path: Path | str, save_cleaned: bool = True) -> pd.DataFrame:
    """Load Traficom kanta Excel or CSV, then clean a working copy."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = read_table(path)
        rename = {c: c.strip() for c in df.columns}
        df = df.rename(columns=rename)
        lower = {c.lower().replace(" ", "_"): c for c in df.columns}
        mapping = {}
        for key, dest in {
            "year": "Year",
            "city": "City",
            "municipality": "City",
            "bev": "BEV",
            "electricity": "BEV",
            "petrol_phev": "Petrol_PHEV",
            "diesel_phev": "Diesel_PHEV",
        }.items():
            if key in lower:
                mapping[lower[key]] = dest
        df = df.rename(columns=mapping)
        required = ["Year", "City", "BEV", "Petrol_PHEV", "Diesel_PHEV"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"{path} is missing columns: {missing}")
    else:
        df = _parse_kanta_excel(path)

    cleaned = clean_kanta_dataframe(df)
    if save_cleaned:
        write_processed(cleaned, "kanta_ev_registrations_clean.csv")
    return cleaned


def _parse_kanta_excel(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None)
    year_counts = [(sum(_is_year(v) for v in row), i) for i, row in raw.iterrows()]
    year_row = max(year_counts)[1]
    if max(year_counts)[0] < 3:
        raise ValueError(f"Could not find a year header row in {path}")

    year_cols: dict[int, int] = {}
    for col, value in raw.iloc[year_row].items():
        if _is_year(value):
            year_cols[int(float(str(value).strip()))] = int(col)

    city_rows: dict[str, int] = {}
    for i, row in raw.iterrows():
        for value in row.tolist():
            city = normalize_city(value) if pd.notna(value) else None
            if city:
                city_rows[city] = i
                break
    missing_cities = [c for c in CITIES if c not in city_rows]
    if missing_cities:
        raise ValueError(f"Could not find city rows for {missing_cities} in {path}")

    records = []
    for city, row_idx in city_rows.items():
        row = raw.iloc[row_idx]
        for year, col in year_cols.items():
            records.append(
                {
                    "Year": year,
                    "City": city,
                    "BEV": row.iloc[col] if col < len(row) else np.nan,
                    "Petrol_PHEV": row.iloc[col + 1] if col + 1 < len(row) else np.nan,
                    "Diesel_PHEV": row.iloc[col + 2] if col + 2 < len(row) else np.nan,
                }
            )
    return pd.DataFrame(records)


def annual_and_cumulative(kanta: pd.DataFrame, end_year: int = 2025) -> pd.DataFrame:
    df = kanta[kanta["Year"].between(MIN_YEAR, end_year)].copy()
    frames = []
    for city in CITIES:
        part = df[df["City"] == city].sort_values("Year")
        part["Cumulative_EV"] = part["Annual_EV"].cumsum()
        frames.append(part)
    return pd.concat(frames, ignore_index=True)


def fleet_composition(kanta: pd.DataFrame, end_year: int | None = None) -> pd.DataFrame:
    df = kanta.copy()
    if end_year is not None:
        df = df[df["Year"] <= end_year]
    else:
        df = df[df["Year_Complete"]] if "Year_Complete" in df.columns else df
    rows = []
    for city in CITIES:
        part = df[df["City"] == city]
        bev = int(part["BEV"].sum())
        phev = int(part["Petrol_PHEV"].sum() + part["Diesel_PHEV"].sum())
        total = bev + phev
        rows.append(
            {
                "City": city,
                "BEV": bev,
                "PHEV": phev,
                "Total_EV_Fleet": total,
                "BEV_Share_pct": round(100 * bev / total, 1) if total else np.nan,
                "PHEV_Share_pct": round(100 * phev / total, 1) if total else np.nan,
            }
        )
    return pd.DataFrame(rows)


def growth_rate(cumulative: pd.DataFrame) -> pd.DataFrame:
    records = []
    for city in CITIES:
        part = cumulative[cumulative["City"] == city].sort_values("Year")
        prev = part["Cumulative_EV"].shift(1)
        rate = np.where(prev > 0, (part["Cumulative_EV"] - prev) / prev * 100, np.nan)
        out = part[["Year", "City", "Cumulative_EV"]].copy()
        out["Growth_pct"] = rate
        records.append(out)
    return pd.concat(records, ignore_index=True)


def load_chargers(path: Path | str, save_cleaned: bool = True) -> pd.DataFrame:
    path = Path(path)
    df = read_table(path)
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "")
        if key in {"municipality", "city"}:
            rename[col] = "City"
        elif "type2" in key:
            rename[col] = "Type2"
        elif "chademo" in key:
            rename[col] = "CHAdeMO"
        elif "ccs" in key:
            rename[col] = "CCS"
    df = df.rename(columns=rename)
    missing = [c for c in ["City", "Type2", "CHAdeMO", "CCS"] if c not in df.columns]
    if missing:
        raise ValueError(f"Could not find columns {missing} in {path}")
    cleaned = clean_chargers_dataframe(df)
    if save_cleaned:
        write_processed(cleaned, "chargers_by_type_clean.csv")
    return cleaned


def load_monthly_temperature(path: Path | str, save_cleaned: bool = True, city_label: str | None = None) -> pd.DataFrame:
    path = Path(path)
    df = read_table(path)
    mapping = {}
    for col in df.columns:
        low = str(col).strip().lower()
        # Temperature must be tested first: 'Monthly mean temperature' also contains 'month'.
        if "temperature" in low:
            mapping[col] = "Temperature"
        elif low == "year":
            mapping[col] = "Year"
        elif low == "month":
            mapping[col] = "Month"
        elif "station" in low:
            mapping[col] = "Station"
    df = df.rename(columns=mapping)
    missing = [c for c in ["Year", "Month", "Temperature"] if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    station = df["Station"].dropna().astype(str).iloc[0] if "Station" in df.columns and df["Station"].notna().any() else path.stem
    cleaned = clean_weather_dataframe(df, station=station)
    if save_cleaned:
        slug = (city_label or station).lower().replace(" ", "_")
        write_processed(cleaned, f"weather_{slug}_clean.csv")
    return cleaned


def average_january_temperature(path: Path | str, end_year: int = 2026, city_label: str | None = None) -> float:
    df = load_monthly_temperature(path, city_label=city_label)
    jan = df[(df["Month"] == 1) & (df["Year"] >= MIN_YEAR) & (df["Year"] <= end_year)]
    temps = jan["Temperature"].dropna()
    if temps.empty:
        raise ValueError(f"No January temperatures found in {path} after cleaning")
    return float(temps.mean())


def climate_factor_from_temperature(temp_c: float) -> float:
    return 1 + abs(temp_c) / CLIMATE_SCALE


def climate_table(weather_paths: dict[str, Path | str], end_year: int = 2026, save_cleaned: bool = True) -> pd.DataFrame:
    rows = []
    for city in CITIES:
        temp = average_january_temperature(weather_paths[city], end_year=end_year, city_label=city)
        temp_r = round(temp, 2)
        factor = round(climate_factor_from_temperature(temp_r), 2)
        rows.append(
            {
                "City": city,
                "Avg_January_Temp_C": temp_r,
                "Climate_Factor": factor,
            }
        )
    out = pd.DataFrame(rows)
    if save_cleaned:
        write_processed(out, "january_temperature_clean.csv")
    return out


def infrastructure_table(chargers: pd.DataFrame, fleet: pd.DataFrame) -> pd.DataFrame:
    merged = chargers.merge(fleet, on="City", how="inner")
    merged["EVs_per_Capacity_Unit"] = merged["Total_EV_Fleet"] / merged["ICS"]
    merged["EVs_per_Capacity_Unit"] = merged["EVs_per_Capacity_Unit"].round(2)
    return merged


def cari_table(infra: pd.DataFrame, climate: pd.DataFrame) -> pd.DataFrame:
    merged = infra.merge(climate, on="City", how="inner")
    merged["Climate_Adjusted_Demand"] = merged["Total_EV_Fleet"] * merged["Climate_Factor"]
    merged["CARI"] = merged["ICS"] / merged["Climate_Adjusted_Demand"]
    merged["CARI"] = merged["CARI"].round(4)
    merged = merged.sort_values("CARI", ascending=False).reset_index(drop=True)
    merged["Rank"] = merged.index + 1
    return merged


def clean_all_inputs(
    kanta: Path | str = DEFAULT_KANTA,
    chargers: Path | str = DEFAULT_CHARGERS,
    helsinki_weather: Path | str = DEFAULT_HELSINKI_WEATHER,
    tampere_weather: Path | str = DEFAULT_TAMPERE_WEATHER,
    oulu_weather: Path | str = DEFAULT_OULU_WEATHER,
) -> dict[str, Path]:
    """Clean every source file into data/processed/ without editing originals."""
    load_kanta_registrations(kanta, save_cleaned=True)
    load_chargers(chargers, save_cleaned=True)
    climate_table(
        {
            "Helsinki": helsinki_weather,
            "Tampere": tampere_weather,
            "Oulu": oulu_weather,
        },
        save_cleaned=True,
    )
    return {
        "processed_dir": PROCESSED_DIR,
        "kanta": PROCESSED_DIR / "kanta_ev_registrations_clean.csv",
        "chargers": PROCESSED_DIR / "chargers_by_type_clean.csv",
        "climate": PROCESSED_DIR / "january_temperature_clean.csv",
    }
