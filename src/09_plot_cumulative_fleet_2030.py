"""Cumulative first registrations of EV passenger cars, 2010-2025 actual and 2026-2030 projected.

The figure uses bold Arial with the dark text of ev_per_capacity_unit_part2.png (near-black #1a1a1a
for titles and labels, grey #5a5a5a for the tick numbers), Chart.js-style smoothed lines (tension
0.25), hollow circle markers with a tinted centre, a legend centred at the top, light horizontal
gridlines and no vertical gridlines. The x axis runs from 2010 to 2030 with a label every two years.

Inputs (written by 08_projection_tables.py):
    outputs/tables/clean_kanta_annual.csv          complete years, cumulative fleet by city
    outputs/tables/projection_paths_2026_2030.csv  cumulative fleet by city and projection scenario

The projection starts from the 2025 actual value. The dashed line is the linear-trend scenario. The
other two scenarios are not drawn; their 2030 range is printed to the console.

Run from the project root:
    python src/09_plot_cumulative_fleet_2030.py
    python src/09_plot_cumulative_fleet_2030.py --out cumulative_ev_fleet_2030.png
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import to_rgba  # noqa: E402
from matplotlib.font_manager import FontProperties, findfont  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANNUAL = ROOT / "outputs" / "tables" / "clean_kanta_annual.csv"
DEFAULT_PROJECTIONS = ROOT / "outputs" / "tables" / "projection_paths_2026_2030.csv"
DEFAULT_OUT = ROOT / "outputs" / "figures" / "analysis" / "cumulative_ev_fleet_2030.png"

CITIES = ("Helsinki", "Tampere", "Oulu")
CITY_COLORS = {"Helsinki": "#2563eb", "Tampere": "#ef4444", "Oulu": "#10b981"}
CENTRAL = "Linear trend"
SCENARIOS = ("Linear trend", "2025 rate held", "2025 additions held")

FIRST_YEAR, LAST_ACTUAL, LAST_YEAR = 2010, 2025, 2030
TICK_EVERY = 2                 # x-axis labels every two years
Y_MAX, Y_STEP = 140_000, 20_000

# Layout in pixels at 96 dpi (1 px = 0.75 pt), with y increasing downwards. The PNG is saved at twice
# that resolution. The margins leave room for the bold text, which is as large as in the reference chart.
DPI, SAVE_DPI = 96, 192
WIDTH, HEIGHT = 1024, 474
PT = 72 / DPI
X_LEFT, X_RIGHT = 128.0, 988.0  # pixel x of 2010 and 2030
Y_ZERO, Y_TOP = 400.0, 64.0     # pixel y of 0 and of Y_MAX

# Type from the reference chart ev_per_capacity_unit_part2.png; lines and markers from annual_ev_additions.png.
FONT_FAMILY, FONT_WEIGHT = "Arial", "bold"
TEXT_PX = 19.5                 # axis titles, key and tick numbers: 14 pt at 96 dpi, as the reference
LEGEND_PX = 19.5
CAP_RATIO = 0.716              # Arial cap height as a fraction of the em size
TEXT_COLOR = "#1a1a1a"         # dark text, as the reference chart's labels and titles
TICK_COLOR = "#5a5a5a"         # grey tick numbers, as the reference chart's tick labels
GRID_COLOR = "#f0f0f0"
ZERO_COLOR = "#d8d8d8"         # bottom axis line at 0
LEFT_COLOR = "#e5e5e5"         # left axis line
LINE_PX = 2.5
MARKER_PX, MARKER_EDGE_PX = 8.0, 2.0    # outer marker diameter 10 px
RING_PX, RING_EDGE_PX = 18.0, 2.0       # legend ring, outer diameter 20 px
TINT_ALPHA = 0.135             # tint of the hollow centres (#e2eafc for Helsinki)
DASH_PX = (6.0, 4.0)
TENSION = 0.25                 # Chart.js line tension


def read_actual(path: Path) -> dict[str, dict[int, float]]:
    """Cumulative fleet by city and year, complete years only."""
    series: dict[str, dict[int, float]] = {city: {} for city in CITIES}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            year = int(row["Year"])
            if row["City"] in series and year <= LAST_ACTUAL:
                series[row["City"]][year] = float(row["Cumulative fleet"])
    return series


def read_projections(path: Path) -> dict[tuple[str, str], dict[int, float]]:
    """Cumulative fleet by (city, scenario) for 2026-2030."""
    paths: dict[tuple[str, str], dict[int, float]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = (row["City"], row["Scenario"])
            paths.setdefault(key, {})[int(row["Year"])] = float(row["Cumulative fleet"])
    return paths


def check_inputs(actual, projections) -> None:
    for city in CITIES:
        missing = [y for y in range(FIRST_YEAR, LAST_ACTUAL + 1) if y not in actual[city]]
        if missing:
            raise SystemExit(f"{city}: missing actual years {missing}")
        for scenario in SCENARIOS:
            key = (city, scenario)
            if key not in projections:
                raise SystemExit(f"Missing projection {key}")
            years = sorted(projections[key])
            if years != list(range(LAST_ACTUAL + 1, LAST_YEAR + 1)):
                raise SystemExit(f"{key}: unexpected years {years}")


def city_series(city: str, scenario: str, actual, projections) -> dict[int, float]:
    """Actual values to 2025, then the scenario values to 2030."""
    series = dict(actual[city])
    series.update(projections[(city, scenario)])
    return series


def px_x(year: float) -> float:
    return X_LEFT + (year - FIRST_YEAR) * (X_RIGHT - X_LEFT) / (LAST_YEAR - FIRST_YEAR)


def px_y(value: float) -> float:
    return Y_ZERO - value * (Y_ZERO - Y_TOP) / Y_MAX


def clamp_to_plot(x: float, y: float) -> tuple[float, float]:
    return min(max(x, X_LEFT), X_RIGHT), min(max(y, Y_TOP), Y_ZERO)


def smooth_segments(points):
    """Cubic Bezier segments through pixel points, using the Chart.js splineCurve rule.

    Control points are scaled by the tension and clamped to the plot box, as Chart.js does.
    Returns one (control1, control2, end) tuple per gap between consecutive points.
    """
    last = len(points) - 1
    back, forward = [], []
    for i, (x, y) in enumerate(points):
        px, py = points[i - 1] if i > 0 else (x, y)
        nx, ny = points[i + 1] if i < last else (x, y)
        d_prev = math.hypot(x - px, y - py)
        d_next = math.hypot(nx - x, ny - y)
        total = d_prev + d_next
        s_prev = d_prev / total if total else 0.0
        s_next = d_next / total if total else 0.0
        dx, dy = nx - px, ny - py
        back.append(clamp_to_plot(x - TENSION * s_prev * dx, y - TENSION * s_prev * dy))
        forward.append(clamp_to_plot(x + TENSION * s_next * dx, y + TENSION * s_next * dy))
    return [(forward[i], back[i + 1], points[i + 1]) for i in range(last)]


def path_from(start, segments) -> MplPath:
    verts, codes = [start], [MplPath.MOVETO]
    for c1, c2, end in segments:
        verts += [c1, c2, end]
        codes += [MplPath.CURVE4] * 3
    return MplPath(verts, codes)


def label(ax, x: float, y: float, text: str, px: float = TEXT_PX, **kwargs):
    kwargs.setdefault("ha", "center")
    kwargs.setdefault("va", "baseline")
    kwargs.setdefault("color", TEXT_COLOR)
    kwargs.setdefault("fontweight", FONT_WEIGHT)
    return ax.text(x, y, text, fontsize=px * PT, zorder=6, **kwargs)


def measure_width(ax, renderer, text: str, px: float) -> float:
    artist = ax.text(0, 0, text, fontsize=px * PT, fontweight=FONT_WEIGHT)
    width = artist.get_window_extent(renderer=renderer).width
    artist.remove()
    return width


def draw_figure(actual, projections, out_path: Path) -> None:
    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(HEIGHT, 0)
    ax.axis("off")

    # Horizontal gridlines, the zero line and the left axis line.
    for value in range(0, Y_MAX + 1, Y_STEP):
        y = px_y(value)
        ax.plot([X_LEFT, X_RIGHT], [y, y], color=ZERO_COLOR if value == 0 else GRID_COLOR,
                lw=PT, solid_capstyle="butt", zorder=1)
    ax.plot([X_LEFT, X_LEFT], [Y_TOP, Y_ZERO], color=LEFT_COLOR, lw=PT, zorder=1)

    years = list(range(FIRST_YEAR, LAST_YEAR + 1))
    for city in CITIES:
        colour = CITY_COLORS[city]
        tint = to_rgba(colour, TINT_ALPHA)

        # Central line: solid through 2025, dashed for the projection.
        central = city_series(city, CENTRAL, actual, projections)
        pts = [(px_x(y), px_y(central[y])) for y in years]
        segs = smooth_segments(pts)
        solid = path_from(pts[0], [s for i, s in enumerate(segs) if years[i + 1] <= LAST_ACTUAL])
        dashed = path_from(pts[LAST_ACTUAL - FIRST_YEAR],
                           [s for i, s in enumerate(segs) if years[i] >= LAST_ACTUAL])

        ax.add_patch(PathPatch(solid, facecolor="none", edgecolor=colour, lw=LINE_PX * PT,
                               capstyle="round", joinstyle="round", zorder=3))
        ax.add_patch(PathPatch(dashed, facecolor="none", edgecolor=colour, lw=LINE_PX * PT,
                               linestyle=(0, (DASH_PX[0] * PT, DASH_PX[1] * PT)), capstyle="butt",
                               joinstyle="round", zorder=3))
        ax.plot([p[0] for p in pts], [p[1] for p in pts], linestyle="none", marker="o",
                markersize=MARKER_PX * PT, markerfacecolor=tint, markeredgecolor=colour,
                markeredgewidth=MARKER_EDGE_PX * PT, zorder=4)

    # Text positions, measured from the cap height of the bold text, so that every gap is clear.
    cap = CAP_RATIO * TEXT_PX
    x_tick_y = Y_ZERO + 14.0 + cap      # x tick numbers: 14 px below the zero line
    x_title_y = x_tick_y + 18.0 + cap   # x-axis title: 18 px below the x tick numbers
    y_title_x = 10.0 + cap              # y-axis title: 10 px from the left edge of the canvas

    # Y tick labels (right-aligned) and X tick labels (every TICK_EVERY years).
    for value in range(0, Y_MAX + 1, Y_STEP):
        label(ax, X_LEFT - 12, px_y(value) + cap / 2, f"{value:,}", ha="right", color=TICK_COLOR)
    for year in range(FIRST_YEAR, LAST_YEAR + 1, TICK_EVERY):
        label(ax, px_x(year), x_tick_y, str(year), color=TICK_COLOR)

    # Axis titles.
    label(ax, (X_LEFT + X_RIGHT) / 2, x_title_y, "Year of first registration")
    label(ax, y_title_x, (Y_TOP + Y_ZERO) / 2, "Cumulative EV fleet", rotation=90, rotation_mode="anchor")

    # Legend centred at the top, as in annual_ev_additions.png.
    renderer = fig.canvas.get_renderer()
    ring_outer = RING_PX + RING_EDGE_PX
    ring_gap, item_gap, ring_y = 4.0, 14.0, 22.0  # ring spans y 12-32; the top gridline is at Y_TOP (64)
    widths = {city: measure_width(ax, renderer, city, LEGEND_PX) for city in CITIES}
    total = sum(ring_outer + ring_gap + widths[c] for c in CITIES) + item_gap * (len(CITIES) - 1)
    x = (WIDTH - total) / 2
    for city in CITIES:
        colour = CITY_COLORS[city]
        ax.plot([x + ring_outer / 2], [ring_y], linestyle="none", marker="o",
                markersize=RING_PX * PT, markerfacecolor=to_rgba(colour, TINT_ALPHA),
                markeredgecolor=colour, markeredgewidth=RING_EDGE_PX * PT, zorder=5)
        label(ax, x + ring_outer + ring_gap, ring_y + CAP_RATIO * LEGEND_PX / 2, city,
              px=LEGEND_PX, ha="left")
        x += ring_outer + ring_gap + widths[city] + item_gap

    # Key for the solid and dashed lines, in the empty upper-left of the plot.
    key_lines = [
        "Solid: actual registrations, 2010–2025",
        "Dashed: linear-trend projection, 2026–2030",
    ]
    for i, text in enumerate(key_lines):
        label(ax, X_LEFT + 12, Y_TOP + 24 + 27 * i, text, ha="left",
              bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=SAVE_DPI, facecolor="white")
    plt.close(fig)


def check_font() -> None:
    try:
        findfont(FontProperties(family=FONT_FAMILY, weight=FONT_WEIGHT), fallback_to_default=False)
    except ValueError:
        print("Warning: Arial Bold not found; the figure will use a fallback font.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--annual", type=Path, default=DEFAULT_ANNUAL,
                        help="clean annual CSV with cumulative fleet (default: outputs/tables/clean_kanta_annual.csv)")
    parser.add_argument("--projections", type=Path, default=DEFAULT_PROJECTIONS,
                        help="projection paths CSV (default: outputs/tables/projection_paths_2026_2030.csv)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output PNG (default: cumulative_ev_fleet_2030.png)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    actual = read_actual(args.annual)
    projections = read_projections(args.projections)
    check_inputs(actual, projections)
    check_font()
    with plt.rc_context({"lines.scale_dashes": False, "font.family": FONT_FAMILY}):
        draw_figure(actual, projections, args.out)
    print(f"Wrote {args.out}")
    for city in CITIES:
        values = {s: city_series(city, s, actual, projections)[LAST_YEAR] for s in SCENARIOS}
        low, high = min(values.values()), max(values.values())
        print(f"{city:9s} 2025 actual {actual[city][LAST_ACTUAL]:>9,.0f}  "
              f"2030 linear trend {values[CENTRAL]:>9,.0f}  range {low:,.0f}-{high:,.0f}")


if __name__ == "__main__":
    main()
