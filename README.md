# EV Charging Readiness in Helsinki, Tampere and Oulu: Data Analysis Project

This project computes the Climate-Adjusted Readiness Index (CARI) for three Finnish cities and produces the tables and figures used in the thesis *Strategic Evaluation of Electric Vehicle Infrastructure Readiness in Finland* (Oamk, 2026). It is a batch data-analysis project: raw data are read, cleaned into intermediate files, analysed, and written out as CSV tables and PNG figures. It has no web component.

## Folder structure

```
Appendix_Submission/
├── README.md                  this file
├── requirements.txt           Python packages
├── run_all.py                 runs the pipeline, scripts 00-09, in order
├── src/                       analysis code
│   ├── 00_clean_inputs.py ... 09_plot_cumulative_fleet_2030.py
│   ├── ev_utils.py            shared loaders, cleaning rules, formulas, plot style
│   ├── generate_figures.py    thesis figures 1-10 and 2030 forecast tables
│   ├── make_map_composite.py  composite of the three charger-map screenshots
│   └── assets/composite/      fonts and pin icon used by make_map_composite.py
├── data/
│   ├── raw/                   original files, read-only
│   ├── inputs/                hand-entered charger counts
│   ├── processed/             cleaned and derived intermediate CSVs
│   └── interim/               Excel internals from the data inspection step
├── outputs/
│   ├── tables/                result tables (CSV)
│   └── figures/
│       ├── analysis/          charts from scripts 01-09 (all versions kept)
│       └── thesis/            figures used in the thesis, plus map composite
└── archive/                   superseded tools, kept for the audit trail
    ├── web_dashboards/        HTML charts (load Chart.js from a CDN) and serve.ps1
    └── powershell_renderers/  Windows-only chart renderers with fixed paths
```

Folders named `rerun_2026-11-26` (in `data/processed/`, `outputs/tables/`, `outputs/figures/analysis/` and `outputs/figures/thesis/`) hold outputs from the re-run on 26 November 2026. They sit beside the earlier outputs, which are kept unchanged. See "Known discrepancies" below.

## Raw data

| File (in `data/raw/`) | Content | Used by |
|---|---|---|
| `kanta_010_20260727-150017.xlsx` | Traficom: passenger cars in traffic by municipality, year of first registration and driving power (extracted 27 July 2026) | 00, 02-05, 07, 08 |
| `Vantaa Helsinki-Vantaa airport_…xlsx` | FMI monthly mean temperature, Helsinki-Vantaa airport, 1 Jan 2010 to 27 Jul 2026 | 00, 06, 07, 08 |
| `Pirkkala Tampere-Pirkkala airport_…xlsx` | FMI monthly mean temperature, Tampere-Pirkkala airport, same period | 00, 06, 07, 08 |
| `Oulu airport_…xlsx` | FMI monthly mean temperature, Oulu airport, same period | 00, 06, 07, 08 |
| `Helsinki railway station square_…xlsx` | FMI monthly mean temperature, Helsinki railway station square (alternative station, not used in the final analysis) | none |
| `Helsinki.png`, `Tampere.png`, `Oulu.png` (and `*_small.png`) | Latauskartta.fi charger-map screenshots, 27 July 2026 | evidence for the charger counts |

Charger counts for the 2026 snapshot are entered by hand in `data/inputs/chargers_by_type.csv` (Type 2, CHAdeMO and CCS outlets for each city).

## Environment and setup

Tested on Windows with Python 3.15.2, pandas 3.1.1, matplotlib 3.11.2, Pillow 13.0.0 (openpyxl and numpy as resolved by pip).

```
pip install -r requirements.txt
```

All paths are resolved from each script's own location, so the project folder can be moved or copied as a whole.

## How to run

From the project root:

```
python run_all.py                  # scripts 00-09: cleaning, charts, tables
python src/generate_figures.py     # thesis figures 1-10 and 2030 forecast tables
python src/make_map_composite.py   # composite map figure (needs Pillow)
```

`run_all.py` stops at the first failing script. Original files in `data/raw/` and `data/inputs/` are never overwritten; the code refuses to write into them.

## Pipeline

| Step | Script | Reads | Writes |
|---|---|---|---|
| 0 | `00_clean_inputs.py` | raw Excel and CSV files | `data/processed/`: cleaned copies of the registration, charger, weather and January-temperature data |
| 1 | `01_plot_chargers_by_type.py` | charger inputs | `outputs/figures/analysis/ev_chargers_by_city.png` |
| 2 | `02_plot_ev_adoption_trends.py` | registration data | annual and cumulative charts; `data/processed/ev_adoption_analysis.csv` |
| 3 | `03_plot_ev_fleet_growth_rate.py` | registration data | growth-rate chart; `data/processed/ev_fleet_growth_rate.csv` |
| 4 | `04_plot_bev_vs_phev.py` | registration data | BEV vs PHEV chart; `data/processed/ev_bev_phev_fleet.csv` |
| 5 | `05_plot_evs_per_capacity_unit.py` | registration and charger data | EVs per capacity unit chart; `data/processed/ev_per_capacity_unit.csv` |
| 6 | `06_plot_climate_factor.py` | FMI temperatures | climate-factor charts; `data/processed/climate_factor.csv` |
| 7 | `07_plot_cari.py` | all of the above | CARI charts; `data/processed/cari.csv` |
| 8 | `08_projection_tables.py` | registration, FMI and charger data | 14 CSV tables in `outputs/tables/` (projections, sensitivities, checks) |
| 9 | `09_plot_cumulative_fleet_2030.py` | `outputs/tables/` | `outputs/figures/analysis/cumulative_ev_fleet_2030.png` |
| thesis | `generate_figures.py` | `data/processed/` | `outputs/figures/thesis/figure_01…10`; `outputs/tables/forecast_2030.csv`, `future_cari_2030.csv` |
| thesis | `make_map_composite.py` | `outputs/figures/thesis/figure_map_*` | `outputs/figures/thesis/figure_map_composite.png` |

## Definitions

- **ICS (Infrastructure Capacity Score):** Type 2 + 3 × CHAdeMO + 5 × CCS outlets.
- **Climate factor:** 1 + |mean January temperature (°C)| / 20.
- **CARI:** ICS / (EV fleet × climate factor).
- **EV fleet:** BEV + PHEV passenger cars in traffic. HEVs are excluded.

