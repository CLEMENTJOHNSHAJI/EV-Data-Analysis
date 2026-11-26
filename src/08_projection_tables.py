#!/usr/bin/env python3
"""Projection, sensitivity and reproduction tables for the EV readiness thesis.

Read-only inputs:
  data/raw/kanta_010_20260727-150017.xlsx  Traficom passenger cars by municipality,
                                                 first-registration year and driving power
  data/raw/<station>.xlsx                  FMI monthly mean temperatures (January check)
  data/inputs/chargers_by_type.csv                   charger counts behind the Infrastructure Capacity Score

Outputs (folder outputs/tables/):
  clean_kanta_annual.csv                      annual additions and cumulative fleet, 2010-2026
  table_A_bev_phev_shares.csv                 BEV and PHEV shares of annual additions, 2010-2025
  table_YoY_cumulative_2013_2025.csv          year-on-year growth of the cumulative series, 2013-2025
  projection_paths_2026_2030.csv              yearly additions, cumulative fleet and growth, three scenarios
  table_B1_linear_trend_2030.csv              projected increase to 2030, linear trend
  table_B2_rate_2025_held_2030.csv            projected increase to 2030, 2025 rate held
  table_B3_additions_2025_held_2030.csv       projected increase to 2030, 2025 additions held
  table_B_projections_2030.csv                the three projection scenarios in one file
  table_C1_linear_trend_cari_2030.csv         CARI in 2030 with infrastructure held constant, linear trend
  table_C2_rate_2025_held_cari_2030.csv       CARI in 2030 with infrastructure held constant, 2025 rate
  table_C3_additions_2025_held_cari_2030.csv  CARI in 2030 with infrastructure held constant, 2025 additions
  table_C_cari_2030_sensitivity.csv           the three CARI scenarios in one file
  check_draft_tables_8_9.csv                  reproduction of draft Tables 8 and 9 (draft method)
  projection_method_sensitivity.csv           2030 cumulative fleet under alternative projection forms

Method (current analysis):
  * Base year 2025. The 2026 stock is the draft value, because 2026 registrations are only partly available.
  * Linear trend: ordinary least squares on the annual year-on-year increase (additions), 2013-2025,
    applied from the 2025 level (the slope is added to the 2025 additions each year).
  * 2025 rate held: the 2025 year-on-year growth of the cumulative fleet (rounded to 0.1 pp) compounded.
  * 2025 additions held: the 2025 year-on-year increase repeated each year.

Standard library only. Run from the project root:  python src/08_projection_tables.py
"""

from __future__ import annotations

import csv
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CODE_DIR.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
KANTA_XLSX = DATA_DIR / "kanta_010_20260727-150017.xlsx"
CHARGERS_CSV = PROJECT_DIR / "data" / "inputs" / "chargers_by_type.csv"
OUT_DIR = PROJECT_DIR / "outputs" / "tables"

CITIES = ["Helsinki", "Tampere", "Oulu"]
FMI_PATTERN = {"Helsinki": "Vantaa*.xlsx", "Tampere": "Pirkkala*.xlsx", "Oulu": "Oulu airport*.xlsx"}
POWER_BEV = "Electricity"
POWER_PETROL = "Petrol/Electricity (plug-in hybrid)"
POWER_DIESEL = "Diesel/Electricity (plug-in hybrid)"
FIRST_YEAR = 2010
YOY_START = 2013  # first year of the year-on-year series used for the projections
LAST_COMPLETE_YEAR = 2025
PARTIAL_YEAR = 2026
TARGET_YEAR = 2030
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Values printed in the draft. The draft's 2026 stock is the current snapshot because 2026 is only
# partly available. The other draft values are used only for the reproduction checks.
DRAFT = {
    "Helsinki": {"jan": -5.15, "cf": 1.26, "cum2025": 54187, "lin": 97355, "rate": 135962,
                 "stock": 58516, "scaled_lin": 105133, "scaled_rate": 146824,
                 "cari_now": 0.0646, "cari_lin": 0.0360, "chg_lin": -44.3,
                 "cari_rate": 0.0258, "chg_rate": -60.1},
    "Tampere": {"jan": -5.98, "cf": 1.30, "cum2025": 15268, "lin": 26400, "rate": 27882,
                "stock": 16258, "scaled_lin": 28112, "scaled_rate": 29690,
                "cari_now": 0.0965, "cari_lin": 0.0558, "chg_lin": -42.2,
                "cari_rate": 0.0529, "chg_rate": -45.2},
    "Oulu": {"jan": -8.90, "cf": 1.45, "cum2025": 12383, "lin": 21293, "rate": 22414,
             "stock": 13037, "scaled_lin": 22418, "scaled_rate": 23598,
             "cari_now": 0.0576, "cari_lin": 0.0335, "chg_lin": -41.8,
             "cari_rate": 0.0318, "chg_rate": -44.8},
}
STOCK_2026 = {c: DRAFT[c]["stock"] for c in CITIES}

SCENARIO_LINEAR = "Linear trend"
SCENARIO_RATE = "2025 rate held"
SCENARIO_ADDITIONS = "2025 additions held"
SCENARIOS = [SCENARIO_LINEAR, SCENARIO_RATE, SCENARIO_ADDITIONS]
SCENARIO_TAGS = {SCENARIO_LINEAR: "linear_trend", SCENARIO_RATE: "rate_2025_held",
                 SCENARIO_ADDITIONS: "additions_2025_held"}


# ---------------------------------------------------------------- spreadsheet reading
def col_index(letters: str) -> int:
    value = 0
    for ch in letters:
        value = value * 26 + (ord(ch) - ord("A") + 1)
    return value


def read_xlsx_grid(path: Path) -> dict[tuple[int, int], str]:
    """Return {(row, column): text} for the first worksheet, handling shared and inline strings."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(NS + "t")) for si in root.iter(NS + "si")]
        sheet_name = sorted(n for n in names if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))[0]
        sheet = ET.fromstring(zf.read(sheet_name))
    grid: dict[tuple[int, int], str] = {}
    for cell in sheet.iter(NS + "c"):
        match = re.fullmatch(r"([A-Z]+)(\d+)", cell.get("r", ""))
        if match is None:
            continue
        col, row = col_index(match.group(1)), int(match.group(2))
        kind = cell.get("t")
        if kind == "s":
            value = shared[int(cell.findtext(NS + "v", "0"))]
        elif kind == "inlineStr":
            value = "".join(t.text or "" for t in cell.iter(NS + "t"))
        else:
            value = cell.findtext(NS + "v", "")
        if value != "":
            grid[(row, col)] = value
    return grid


def load_kanta(path: Path) -> dict[str, dict[int, dict[str, int]]]:
    """Traficom layout: years in row 3 (group start), driving power in row 4, cities in column A."""
    grid = read_xlsx_grid(path)
    last_col = max(col for _, col in grid)
    last_row = max(row for row, _ in grid)
    year_of_col: dict[int, int] = {}
    current_year = None
    for col in range(3, last_col + 1):
        if (3, col) in grid:
            current_year = int(grid[(3, col)])
        if current_year is not None:
            year_of_col[col] = current_year
    data: dict[str, dict[int, dict[str, int]]] = {}
    for row in range(5, last_row + 1):
        city = grid.get((row, 1))
        if city not in CITIES:
            continue
        data[city] = {}
        for col, year in year_of_col.items():
            power, value = grid.get((4, col)), grid.get((row, col))
            if power is None or value is None:
                continue
            data[city].setdefault(year, {})[power] = int(float(value))
    for city in CITIES:
        for year in range(FIRST_YEAR, PARTIAL_YEAR + 1):
            if not {POWER_BEV, POWER_PETROL, POWER_DIESEL} <= set(data[city][year]):
                raise ValueError(f"Missing driving-power column for {city} {year}")
    return data


def load_chargers(path: Path) -> dict[str, tuple[int, int, int]]:
    out: dict[str, tuple[int, int, int]] = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["Municipality"].strip()] = (
                int(row["Type 2 Chargers"]),
                int(row["CHAdeMO Chargers"]),
                int(row["CCS Fast Chargers"]),
            )
    return out


def january_mean(path: Path) -> tuple[float, int]:
    """Mean of January monthly mean temperatures, 2010 to 2026, skipping missing values."""
    grid = read_xlsx_grid(path)
    last_row = max(row for row, _ in grid)
    last_col = max(col for _, col in grid)
    header_row = None
    headers: dict[str, int] = {}
    for row in range(1, last_row + 1):
        texts = {col: grid[(row, col)] for col in range(1, last_col + 1) if (row, col) in grid}
        if any("Monthly mean temperature" in text for text in texts.values()):
            header_row = row
            headers = {text.strip(): col for col, text in texts.items()}
            break
    if header_row is None:
        raise ValueError(f"No temperature header found in {path.name}")
    year_col = headers["Year"]
    month_col = headers["Month"]
    temp_col = next(col for text, col in headers.items() if "Monthly mean temperature" in text)
    values: list[float] = []
    for row in range(header_row + 1, last_row + 1):
        try:
            year = int(float(grid[(row, year_col)]))
            month = int(float(grid[(row, month_col)]))
            temp = float(grid[(row, temp_col)])
        except (KeyError, ValueError):
            continue
        if month == 1 and FIRST_YEAR <= year <= PARTIAL_YEAR:
            values.append(temp)
    return sum(values) / len(values), len(values)


def build_series(kanta: dict[str, dict[int, dict[str, int]]]) -> dict[str, dict[int, dict[str, int]]]:
    series: dict[str, dict[int, dict[str, int]]] = {}
    for city in CITIES:
        cum = 0
        years: dict[int, dict[str, int]] = {}
        for year in range(FIRST_YEAR, PARTIAL_YEAR + 1):
            p = kanta[city][year]
            bev, petrol, diesel = p[POWER_BEV], p[POWER_PETROL], p[POWER_DIESEL]
            total = bev + petrol + diesel
            cum += total
            years[year] = {"bev": bev, "petrol": petrol, "diesel": diesel,
                           "phev": petrol + diesel, "total": total, "cum": cum}
        series[city] = years
    return series


# ---------------------------------------------------------------- statistics
def ols(xs: list[float], ys: list[float]) -> tuple[float, float, float, float, float, float]:
    """Return intercept, slope, mean x, mean y, Sxx and SSE of a simple linear regression."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    sse = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    return intercept, slope, mx, my, sxx, sse


def draft_linear_2030(cum: dict[int, int], start: int, end: int) -> float:
    """Draft method: OLS on the cumulative fleet, evaluated at 2030 (kept for reproduction)."""
    xs = list(range(start, end + 1))
    ys = [float(cum[x]) for x in xs]
    a, b, *_ = ols(xs, ys)
    return a + b * TARGET_YEAR


def cumulative_slope(cum: dict[int, int], start: int, end: int) -> float:
    xs = list(range(start, end + 1))
    ys = [float(cum[x]) for x in xs]
    return ols(xs, ys)[1]


def loglinear_2030(cum: dict[int, int], start: int, end: int) -> float:
    xs = list(range(start, end + 1))
    ys = [math.log(cum[x]) for x in xs]
    a, b, *_ = ols(xs, ys)
    return math.exp(a + b * TARGET_YEAR)


def bev_share_extrapolation(years: dict[int, dict[str, int]]) -> tuple[float, float]:
    xs = list(range(2021, 2026))
    ys = [100 * years[x]["bev"] / years[x]["total"] for x in xs]
    a, b, *_ = ols(xs, ys)
    return a + b * TARGET_YEAR, b


def additions_trend(add: dict[int, int]) -> tuple[float, float]:
    """OLS trend of the year-on-year increase of the cumulative series (annual additions), 2013-2025."""
    xs = list(range(YOY_START, LAST_COMPLETE_YEAR + 1))
    ys = [float(add[x]) for x in xs]
    intercept, slope, *_ = ols(xs, ys)
    return intercept, slope


def yoy_percentage_trend(cum: dict[int, int]) -> tuple[float, float]:
    """OLS trend of the year-on-year percentage growth, 2013-2025 (diagnostic: not used for projections)."""
    xs = list(range(YOY_START, LAST_COMPLETE_YEAR + 1))
    ys = [100 * (cum[x] / cum[x - 1] - 1) for x in xs]
    intercept, slope, *_ = ols(xs, ys)
    return intercept, slope


def compound_fitted_growth(cum: dict[int, int], intercept: float, slope: float) -> dict[int, float]:
    value = float(cum[LAST_COMPLETE_YEAR])
    path: dict[int, float] = {}
    for year in range(LAST_COMPLETE_YEAR + 1, TARGET_YEAR + 1):
        value *= 1 + (intercept + slope * year) / 100
        path[year] = value
    return path


def project_scenarios(cum: dict[int, int], add: dict[int, int]) -> tuple[dict, dict]:
    """Yearly paths 2026-2030 from the 2025 base. Returns {scenario: {year: (additions, cumulative)}}."""
    base_cum = float(cum[LAST_COMPLETE_YEAR])
    base_add = float(add[LAST_COMPLETE_YEAR])
    g_raw = base_add / cum[LAST_COMPLETE_YEAR - 1]
    g_rounded = round(g_raw, 3)
    _, slope = additions_trend(add)
    paths: dict[str, dict[int, tuple[float, float]]] = {s: {} for s in SCENARIOS}
    lin_cum, rate_cum, add_cum = base_cum, base_cum, base_cum
    for k, year in enumerate(range(LAST_COMPLETE_YEAR + 1, TARGET_YEAR + 1), start=1):
        lin_add = base_add + slope * k
        lin_cum += lin_add
        paths[SCENARIO_LINEAR][year] = (lin_add, lin_cum)

        rate_add = rate_cum * g_rounded
        rate_cum += rate_add
        paths[SCENARIO_RATE][year] = (rate_add, rate_cum)

        add_cum += base_add
        paths[SCENARIO_ADDITIONS][year] = (base_add, add_cum)
    params = {"slope": slope, "g_raw": g_raw, "g_rounded": g_rounded, "base_add": base_add}
    return paths, params


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def climate_tie_divisor(stock_h: float, stock_o: float, ics_h: float, ics_o: float,
                        jan_h: float, jan_o: float) -> float | None:
    """Divisor k at which Helsinki and Oulu have equal CARI, with CF = 1 + |January mean| / k."""
    ratio = (stock_o * ics_h) / (stock_h * ics_o)
    if abs(1 - ratio) < 1e-12:
        return None
    return (ratio * abs(jan_o) - abs(jan_h)) / (1 - ratio)


# ---------------------------------------------------------------- main
def main() -> None:
    kanta = load_kanta(KANTA_XLSX)
    series = build_series(kanta)
    chargers = load_chargers(CHARGERS_CSV)
    ics = {c: chargers[c][0] + 3 * chargers[c][1] + 5 * chargers[c][2] for c in CITIES}
    cum = {c: {y: v["cum"] for y, v in series[c].items()} for c in CITIES}
    add = {c: {y: v["total"] for y, v in series[c].items()} for c in CITIES}

    print("== Stock 2025 (workbook), 2026 workbook partial, 2026 draft stock used, ICS ==")
    for c in CITIES:
        print(f"{c:9s} cum2025={cum[c][2025]:6d}  workbook 2026 partial={cum[c][2026]:6d}  "
              f"draft 2026 stock used={STOCK_2026[c]:6d}  ICS={ics[c]}")

    print("== January mean temperature check (FMI workbooks) ==")
    jan_mean: dict[str, float] = {}
    jan_cf: dict[str, float] = {}
    for c in CITIES:
        path = sorted(DATA_DIR.glob(FMI_PATTERN[c]))[0]
        mean, n = january_mean(path)
        jan_mean[c] = mean
        jan_cf[c] = round(1 + abs(mean) / 20, 2)
        print(f"{c:9s} computed={mean:7.3f} (n={n})  draft={DRAFT[c]['jan']:6.2f}  "
              f"CF computed={jan_cf[c]:.2f}  draft={DRAFT[c]['cf']:.2f}")

    # 1. Cleaned annual series
    rows = []
    for c in CITIES:
        for year, v in series[c].items():
            status = "complete" if year <= LAST_COMPLETE_YEAR else "partial (workbook updated 2026-07-07)"
            rows.append([c, year, v["bev"], v["petrol"], v["diesel"], v["phev"], v["total"], v["cum"], status])
    write_csv(OUT_DIR / "clean_kanta_annual.csv",
              ["City", "Year", "BEV", "PHEV petrol", "PHEV diesel", "PHEV total",
               "Additions (BEV+PHEV)", "Cumulative fleet", "Year status"], rows)

    # 2. Table A: shares of annual additions
    header_a = ["Year"]
    for c in CITIES:
        header_a += [f"{c} additions", f"{c} BEV %", f"{c} PHEV %"]
    rows_a = []
    for year in range(FIRST_YEAR, LAST_COMPLETE_YEAR + 1):
        row: list = [year]
        for c in CITIES:
            v = series[c][year]
            total = v["total"]
            if total:
                row += [total, f"{100 * v['bev'] / total:.1f}", f"{100 * v['phev'] / total:.1f}"]
            else:
                row += [0, "n/a", "n/a"]
        rows_a.append(row)
    write_csv(OUT_DIR / "table_A_bev_phev_shares.csv", header_a, rows_a)

    # 3. Year-on-year basis, 2013-2025
    rows_y = []
    for c in CITIES:
        for year in range(YOY_START, LAST_COMPLETE_YEAR + 1):
            pct = 100 * (cum[c][year] / cum[c][year - 1] - 1)
            rows_y.append([c, year, cum[c][year], add[c][year], f"{pct:.1f}"])
    write_csv(OUT_DIR / "table_YoY_cumulative_2013_2025.csv",
              ["City", "Year", "Cumulative fleet", "Year-on-year increase (additions)",
               "Year-on-year growth of cumulative fleet (%)"], rows_y)

    # 4. Projection paths
    proj: dict[str, dict] = {}
    for c in CITIES:
        paths, params = project_scenarios(cum[c], add[c])
        proj[c] = {"paths": paths, "params": params}

    rows_p = []
    for c in CITIES:
        for scen in SCENARIOS:
            prev = float(cum[c][LAST_COMPLETE_YEAR])
            for year in range(LAST_COMPLETE_YEAR + 1, TARGET_YEAR + 1):
                a, f = proj[c]["paths"][scen][year]
                rows_p.append([c, scen, year, round(a), round(f), f"{100 * (f / prev - 1):.1f}"])
                prev = f
    write_csv(OUT_DIR / "projection_paths_2026_2030.csv",
              ["City", "Scenario", "Year", "Additions", "Cumulative fleet", "Year-on-year growth (%)"], rows_p)

    # 5. Projected increase to 2030, one table per scenario
    for i, scen in enumerate(SCENARIOS, start=1):
        header = (["City", "Cumulative 2025"] + [f"Cumulative {y}" for y in range(2026, TARGET_YEAR + 1)]
                  + [f"YoY growth {y} (%)" for y in range(2026, TARGET_YEAR + 1)]
                  + ["Increase 2025-2030 (%)"])
        rows = []
        for c in CITIES:
            base = float(cum[c][LAST_COMPLETE_YEAR])
            vals = [proj[c]["paths"][scen][y][1] for y in range(2026, TARGET_YEAR + 1)]
            prevs = [base] + vals[:-1]
            yoy = [100 * (v / p - 1) for v, p in zip(vals, prevs)]
            rows.append([c, round(base)] + [round(v) for v in vals] + [f"{x:.1f}" for x in yoy]
                        + [f"{100 * (vals[-1] / base - 1):.1f}"])
        write_csv(OUT_DIR / f"table_B{i}_{SCENARIO_TAGS[scen]}_2030.csv", header, rows)

    rows_b = []
    for c in CITIES:
        base = float(cum[c][LAST_COMPLETE_YEAR])
        base_add = float(add[c][LAST_COMPLETE_YEAR])
        for scen in SCENARIOS:
            value = proj[c]["paths"][scen][TARGET_YEAR][1]
            avg = (value - base) / (TARGET_YEAR - LAST_COMPLETE_YEAR)
            rows_b.append([c, scen, round(base), round(value), f"{100 * (value / base - 1):.1f}",
                           round(avg), f"{100 * (avg / base_add - 1):.1f}"])
    write_csv(OUT_DIR / "table_B_projections_2030.csv",
              ["City", "Scenario", "Cumulative 2025", "Cumulative 2030", "Increase 2025-2030 (%)",
               "Average additions 2026-2030 per year", "Change vs 2025 additions (%)"], rows_b)

    # 6. CARI 2030 with infrastructure held at the 2026 snapshot (direct basis, draft 2026 stock)
    cari_now = {c: ics[c] / (STOCK_2026[c] * DRAFT[c]["cf"]) for c in CITIES}
    header_c = ["City", "ICS (held constant)", "Climate factor", "Stock 2026 snapshot (draft)",
                "Stock 2030", "Stock growth (%)", "CARI 2026", "CARI 2030",
                "CARI change (%)", "Rank 2030 (1 = highest)", "ICS needed to hold CARI"]
    sens_all = []
    orders: dict[str, list[str]] = {}
    for i, scen in enumerate(SCENARIOS, start=1):
        cari30 = {c: ics[c] / (proj[c]["paths"][scen][TARGET_YEAR][1] * DRAFT[c]["cf"]) for c in CITIES}
        order = sorted(CITIES, key=lambda c: -cari30[c])
        orders[scen] = order
        rows = []
        for c in CITIES:
            stock26 = STOCK_2026[c]
            stock30 = proj[c]["paths"][scen][TARGET_YEAR][1]
            row = [c, ics[c], DRAFT[c]["cf"], stock26, round(stock30),
                   f"{100 * (stock30 / stock26 - 1):.1f}", f"{cari_now[c]:.4f}", f"{cari30[c]:.4f}",
                   f"{100 * (cari30[c] / cari_now[c] - 1):.1f}", order.index(c) + 1,
                   round(ics[c] * stock30 / stock26)]
            rows.append(row)
            sens_all.append([scen] + row)
        write_csv(OUT_DIR / f"table_C{i}_{SCENARIO_TAGS[scen]}_cari_2030.csv", header_c, rows)
    write_csv(OUT_DIR / "table_C_cari_2030_sensitivity.csv", ["Scenario"] + header_c, sens_all)

    # 7. Reproduction of the draft Tables 8 and 9 (draft method, draft values)
    rows_chk: list[list] = []

    def check(city: str, item: str, draft_value: float, computed: float, tol: float) -> None:
        diff = computed - draft_value
        status = "match" if abs(diff) <= tol + 1e-9 else "DIFFERENT"
        rows_chk.append(["Draft Tables 8-9", city, item, draft_value, round(computed, 5),
                         round(diff, 5), status])

    for c in CITIES:
        d = DRAFT[c]
        stock, cf, cum25 = d["stock"], d["cf"], d["cum2025"]
        g_r = round(add[c][2025] / cum[c][2024], 3)
        lin_draft = draft_linear_2030(cum[c], 2020, 2025)
        rate_draft = cum[c][2025] * (1 + g_r) ** 5
        check(c, "Cumulative 2025", cum25, cum[c][2025], 0)
        check(c, "Linear 2030 (draft OLS 2020-2025)", d["lin"], lin_draft, 0.5)
        check(c, "2025 rate held to 2030", d["rate"], rate_draft, 0.5)
        scaled_lin = stock * d["lin"] / cum25
        scaled_rate = stock * d["rate"] / cum25
        check(c, "Scaled stock, linear", d["scaled_lin"], scaled_lin, 0.5)
        check(c, "Scaled stock, 2025 rate", d["scaled_rate"], scaled_rate, 0.5)
        cari_now_u = ics[c] / (stock * cf)
        cari_lin_u = ics[c] / (scaled_lin * cf)
        cari_rate_u = ics[c] / (scaled_rate * cf)
        check(c, "Current CARI", d["cari_now"], cari_now_u, 0.00005)
        check(c, "Future CARI, linear", d["cari_lin"], cari_lin_u, 0.00005)
        check(c, "Change (%), linear", d["chg_lin"], 100 * (cari_lin_u / cari_now_u - 1), 0.05)
        check(c, "Future CARI, 2025 rate", d["cari_rate"], cari_rate_u, 0.00005)
        check(c, "Change (%), 2025 rate", d["chg_rate"], 100 * (cari_rate_u / cari_now_u - 1), 0.05)
        check(c, "January mean (deg C)", d["jan"], jan_mean[c], 0.01)
        check(c, "Climate factor", d["cf"], jan_cf[c], 0.001)
    write_csv(OUT_DIR / "check_draft_tables_8_9.csv",
              ["Table", "City", "Item", "Draft value", "Recomputed", "Difference", "Status"], rows_chk)

    # 8. Sensitivity to the projection form (2030 cumulative fleet)
    rows_s = []
    for c in CITIES:
        base = float(cum[c][2025])
        a_yoy, b_yoy = yoy_percentage_trend(cum[c])
        compounded = compound_fitted_growth(cum[c], a_yoy, b_yoy)
        g_raw = proj[c]["params"]["g_raw"]
        methods = [
            ("Linear trend, annual increase 2013-2025, anchored at 2025 (used)",
             proj[c]["paths"][SCENARIO_LINEAR][TARGET_YEAR][1]),
            ("Linear trend, cumulative OLS 2020-2025 (draft)", draft_linear_2030(cum[c], 2020, 2025)),
            ("Linear trend, cumulative OLS 2013-2025, trend value at 2030",
             draft_linear_2030(cum[c], 2013, 2025)),
            ("Linear trend, cumulative OLS 2013-2025 slope, anchored at 2025",
             base + (TARGET_YEAR - LAST_COMPLETE_YEAR) * cumulative_slope(cum[c], 2013, 2025)),
            ("Linear trend of YoY % growth 2013-2025, compounded (rejected)", compounded[TARGET_YEAR]),
            ("2025 rate held, rounded to 0.1 pp (used)", proj[c]["paths"][SCENARIO_RATE][TARGET_YEAR][1]),
            ("2025 rate held, unrounded", base * (1 + g_raw) ** (TARGET_YEAR - LAST_COMPLETE_YEAR)),
            ("2025 additions held (used)", proj[c]["paths"][SCENARIO_ADDITIONS][TARGET_YEAR][1]),
            ("Log-linear fit 2020-2025 (draft Section 9.2 form)", loglinear_2030(cum[c], 2020, 2025)),
        ]
        for name, value in methods:
            rows_s.append([c, name, round(value), f"{100 * (value / base - 1):.1f}"])
    write_csv(OUT_DIR / "projection_method_sensitivity.csv",
              ["City", "Projection form", "Cumulative 2030", "Increase vs 2025 (%)"], rows_s)

    # ---------------- diagnostics for the thesis text
    print("== Draft reproduction (Tables 8-9, draft method) ==")
    mismatches = [r for r in rows_chk if r[-1] == "DIFFERENT"]
    print(f"checks flagged DIFFERENT: {len(mismatches)}")
    for r in mismatches:
        print("  ", r)

    print("== Linear trend of annual increase, 2013-2025 ==")
    for c in CITIES:
        a_add, b_add = additions_trend(add[c])
        fitted_2025 = a_add + b_add * 2025
        print(f"{c:9s} slope={b_add:+.1f}/yr  fitted 2025={fitted_2025:.0f}  actual 2025={add[c][2025]}  "
              f"2026 path={proj[c]['paths'][SCENARIO_LINEAR][2026][0]:.0f}  "
              f"2030 cumulative={proj[c]['paths'][SCENARIO_LINEAR][2030][1]:.0f}")

    print("== Why the linear trend of YoY % growth is not used ==")
    for c in CITIES:
        a_g, b_g = yoy_percentage_trend(cum[c])
        neg = next((y for y in range(2026, 2031) if a_g + b_g * y < 0), None)
        comp = compound_fitted_growth(cum[c], a_g, b_g)
        print(f"{c:9s} fitted YoY % 2025={a_g + b_g * 2025:+.1f}  2026={a_g + b_g * 2026:+.1f}  "
              f"first negative year={neg}  compounded 2030 cumulative={comp[2030]:,.0f}")
    for c in CITIES:
        xs = list(range(2013, LAST_COMPLETE_YEAR + 1))
        ys = [float(cum[c][x]) for x in xs]
        intercept, slope_c, *_ = ols(xs, ys)
        print(f"{c:9s} cumulative OLS 2013-2025: fitted 2025={intercept + slope_c * 2025:,.0f} "
              f"vs actual {cum[c][2025]:,}  trend value 2030={intercept + slope_c * TARGET_YEAR:,.0f}")

    print("== Projected increase to 2030 ==")
    for row in rows_b:
        print(f"  {row[0]:9s} {row[1]:24s} 2030={row[3]:>8,}  increase={row[4]:>6}%  "
              f"avg additions={row[5]:>6,}  vs 2025 additions={row[6]:>6}%")

    print("== CARI 2030, infrastructure constant (draft 2026 stock, direct basis) ==")
    for row in sens_all:
        print(f"  {row[0]:19s} {row[1]:9s} stock {row[4]:>6,} -> {row[5]:>7,} (+{row[6]}%)  "
              f"CARI {row[7]} -> {row[8]} ({row[9]}%)  rank {row[10]}  ICS needed {row[11]:,}")
    for scen in SCENARIOS:
        print(f"  rank order 2030, {scen}: {' > '.join(orders[scen])}")

    print("== Climate divisor at which Helsinki and Oulu CARI are equal (draft January means) ==")
    k_2026 = climate_tie_divisor(STOCK_2026["Helsinki"], STOCK_2026["Oulu"], ics["Helsinki"], ics["Oulu"],
                                 DRAFT["Helsinki"]["jan"], DRAFT["Oulu"]["jan"])
    print(f"  2026 snapshot: Helsinki ranks above Oulu only if divisor k < {k_2026:.1f} (draft k = 20)")
    for scen in SCENARIOS:
        s_h = proj["Helsinki"]["paths"][scen][TARGET_YEAR][1]
        s_o = proj["Oulu"]["paths"][scen][TARGET_YEAR][1]
        k_30 = climate_tie_divisor(s_h, s_o, ics["Helsinki"], ics["Oulu"],
                                   DRAFT["Helsinki"]["jan"], DRAFT["Oulu"]["jan"])
        print(f"  2030, {scen}: Helsinki ranks above Oulu only if k < {k_30:.1f}")

    print("== 2026 partial-year check (annualised x2, assumes about six months of coverage) ==")
    for c in CITIES:
        add26 = add[c][PARTIAL_YEAR]
        add25 = add[c][LAST_COMPLETE_YEAR]
        ann = 2 * add26
        print(f"{c:9s} workbook YTD={add26}  annualised={ann:.0f} ({100 * (ann / add25 - 1):+.1f}% vs 2025)  "
              f"2026 values: linear={proj[c]['paths'][SCENARIO_LINEAR][2026][0]:.0f}, "
              f"rate={proj[c]['paths'][SCENARIO_RATE][2026][0]:.0f}, "
              f"additions held={proj[c]['paths'][SCENARIO_ADDITIONS][2026][0]:.0f}")

    print("== BEV share extrapolation (2021-2025 linear trend) ==")
    for c in CITIES:
        value, slope = bev_share_extrapolation(series[c])
        print(f"{c:9s} 2030 projection={value:.1f}%  slope={slope:+.2f} pp per year")

    print(f"\nTables written to {OUT_DIR}")


if __name__ == "__main__":
    main()
