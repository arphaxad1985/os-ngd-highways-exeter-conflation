# OS MasterMap Highways Network — Roads: Conflation Quality (Exeter)

A reproducible data science investigation into the **conflation quality** between OS RoadLinks and the **National Street Gazetteer (NSG)** for the Exeter sample.

This project demonstrates the core technical task described in the Streets Data Scientist role: **conflation and matching of external network data against the NSG**, followed by root-cause investigation of any mismatches.

---

## 📊 Live Dashboard

Interactive Streamlit dashboard presenting the findings.

**Live demo:** [https://os-ngd-highways-exeter-conflation.streamlit.app](https://os-ngd-highways-exeter-conflation.streamlit.app)

**Run locally:**

```bash
conda activate geo
streamlit run app.py
```

The dashboard offers three modes:

| Mode | Input | Purpose |
|------|-------|---------|
| **Demo (Exeter sample)** | Bundled files | Show the analysis working out of the box |
| **Quick Check** | RoadLink file only | For users who only have `matchStatus` |
| **Full Analysis** | Street + RoadLink | Adds NSG street count for context |

All modes present the same six tabs:

- **Executive Summary** — headline findings, flags, and recommendation
- **Conflation Status** — distribution of `matchStatus`
- **Unmatched Analysis** — profiles by classification, form of way, provenance, length
- **Discrepancies** — matched but attributes disagree
- **Review Queue** — records awaiting human review
- **Data** — supporting RoadLink table

---

## 🎯 Objective

To assess the quality of the conflation between OS MasterMap Highways Network RoadLinks and the NSG, and to investigate the root cause of any unmatched records.

Three research questions guided the investigation:

1. **What proportion of RoadLinks are successfully matched to an NSG street?**
2. **What are the unmatched links, and why are they unmatched?**
3. **Are there genuine data quality issues, or are the exclusions correct?**

---

## 📁 Data

| Property | Value |
|----------|-------|
| Product | OS MasterMap Highways Network — Roads |
| Provider | Ordnance Survey, via OS Data Hub |
| Sample area | Exeter |
| Format | GML 3.2 |
| Streets (NSG) | 2,547 |
| RoadLinks (OS) | 7,860 |
| CRS | EPSG:27700 (British National Grid) |

Two files are used:

- `data/Highways_Roads_Street_FULL_001.gml` — NSG-defined streets with USRNs
- `data/Highways_Roads_RoadLink_FULL_001.gml` — OS road geometry with `matchStatus`

The other three files in the download (Road, RoadNode, RoadJunction) are not used in this analysis.

---

## 🧪 Methodology

The workflow is available in two forms — **Python/GeoPandas** and **SQL** — both producing the same findings.

### Step 1 — Profile `matchStatus`

Count the distribution of `matchStatus` across all RoadLinks.

### Step 2 — Profile unmatched links

Break down the unmatched links by:

- `roadClassification`
- `formOfWay`
- `provenance`
- `length` (distribution)

### Step 3 — Identify anomalies

Flag unmatched classified roads (A, B, Motorway) and attribute discrepancies.

### Step 4 — Form a root-cause hypothesis

Examine the evidence for a consistent explanation.

---

## 🔍 Findings

### Finding 1 — Conflation coverage is 88.6%

| matchStatus | Count | % |
|-------------|-------|---|
| Matched | 6,966 | 88.63 |
| No Match | 873 | 11.11 |
| Matched With Attribute Discrepancy | 12 | 0.15 |
| Not Matched Awaiting Review | 9 | 0.11 |

### Finding 2 — Most unmatched links are not NSG streets

| Classification | Count |
|----------------|-------|
| Unknown | 871 |
| A Road | 2 |

99.8% of unmatched links are unclassified. They are single carriageways, tracks, and enclosed traffic areas — physical roads, but not "streets" in the NSG sense (no name, no USRN, no highway authority responsibility).

### Finding 3 — All unmatched links come from OS survey

| Provenance | Count |
|------------|-------|
| OS Urban And OS Height | 819 |
| OS Rural And OS Height | 32 |
| OS Urban And Interpolated OS Height | 17 |
| OS Rural And Interpolated OS Height | 5 |

Every unmatched link comes from OS survey data. None were submitted by a highway authority. They were never registered in the Local Street Gazetteer.

### Finding 4 — A small number of genuine exceptions exist

- **2 unmatched classified roads** — Bonhay Road and Western Way (A-roads), both under 5 m — geometry stubs
- **12 attribute discrepancies** — 6 cluster on Wayside Crescent
- **9 awaiting review** — unnamed, unclassified
- **1 named exception** — Hamlyns Lane (344 m, unclassified) is the only named road in the unmatched set

---

## 🧠 Root-Cause Hypothesis

The unmatched RoadLinks are **not a data quality failure**. They are correctly excluded from the NSG because:

1. **They have no name** (or an unclassified name)
2. **They have no USRN** — never registered by a highway authority
3. **They come from OS survey data**, not from LSG submissions
4. **They are physical features** (tracks, car park spurs, rural lanes) rather than streets

The `No Match` status reflects the correct boundary of the NSG, not a gap in the data.

---

## ✅ Recommendation

| Action | Rationale |
|--------|-----------|
| **No action for 871 unclassified unmatched links** | Correctly excluded from NSG |
| **Review 2 unmatched A-road stubs** | Confirm they are geometry artefacts |
| **Investigate 12 attribute discrepancies** | Particularly the Wayside Crescent cluster |
| **Clear 9 awaiting-review records** | Confirm they should remain unmatched |
| **Check Hamlyns Lane** | The only named road in the unmatched set |

---

## 🛠️ Technical Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.11 |
| Geospatial | GeoPandas 1.0.1, Shapely 2.1.1 |
| Data | Pandas 2.3.1 |
| Database | SQLite 3 |
| Visualisation | Matplotlib 3.10.0 |
| Dashboard | Streamlit |
| GIS (inspection) | QGIS |

---

## 📂 Project Structure

```
exeter_highways_conflation/
├── app.py                            # Streamlit dashboard (3 modes)
├── exeter_conflation.py              # Python analysis script
├── exeter_conflation.sql             # SQL analysis queries
├── load_to_sqlite.py                 # Loads GML into SQLite
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── Highways_Roads_Street_FULL_001.gml
│   ├── Highways_Roads_RoadLink_FULL_001.gml
│   └── exeter.db                     # SQLite database (generated)
└── outputs/
    ├── exeter_conflation_report.md
    ├── conflation_status.png
    ├── unmatched_length_histogram.png
    └── sql_results.txt
```

---

## 🚀 Reproducing the Analysis

### Environment setup

This project uses a dedicated conda environment called `geo`.

```bash
conda create -n geo python=3.11 geopandas matplotlib tabulate streamlit
conda activate geo
```

> **Note on mamba:** If you have `mamba` installed, use `conda activate geo`
> rather than `mamba activate geo`. Mamba 2.x looks for environments in its
> own directory, but this environment was created in conda's default location.

> **Note on PATH:** If `python` resolves to `/usr/bin/python` instead of the
> conda environment, run `conda activate geo` first, or use the full path:
> `/opt/anaconda3/envs/geo/bin/python`.

### Run the Python analysis

```bash
python exeter_conflation.py
```

Outputs are written to `outputs/`:

| File | Purpose |
|------|---------|
| `exeter_conflation_report.md` | Full written report |
| `conflation_status.png` | Status distribution chart |
| `unmatched_length_histogram.png` | Length distribution of unmatched links |

### Run the SQL analysis

```bash
python load_to_sqlite.py
sqlite3 data/exeter.db < exeter_conflation.sql > outputs/sql_results.txt
```

This loads the GML data into a SQLite database, then runs the SQL analysis. The output is written to `outputs/sql_results.txt`.

### Run the dashboard

```bash
streamlit run app.py
```

Then open `http://localhost:8501`.

---

## 📌 What This Project Demonstrates

| Skill | Evidence |
|-------|----------|
| **Conflation and matching** | `matchStatus` profile of OS RoadLinks vs NSG |
| **Root-cause investigation** | Evidence chain from classification → name → provenance |
| **Data quality profiling** | Multi-dimensional analysis of unmatched records |
| **SQL against relational data** | `exeter_conflation.sql` with GROUP BY, COUNT, subqueries, UNION |
| **Python + GeoPandas** | `exeter_conflation.py`, `load_to_sqlite.py` |
| **Geospatial formats** | GML, GeoPandas, CRS awareness |
| **Interactive tooling** | Streamlit dashboard with three input modes |
| **Communication** | Written findings, dashboard, recommendation |
| **Reproducible workflow** | Scripted, documented, version-controlled |

---

## 📜 Licence and Attribution

Data: © Ordnance Survey, OS MasterMap Highways Network — Roads, used under the Open Government Licence.

Analysis, code, and documentation: © Arphaxad Nguka Owange, 2026.