# Dubai Public Transport Analytics — SQL + Tableau Dashboard

> 🚧 **Work in progress.** The environment and structure are in place; the analysis is not
> built yet. Sections marked `TODO` are placeholders. This banner comes off when the
> dashboard is published.

Modelling a Dubai transport & mobility dataset in **MySQL**, analysing it with SQL, and
publishing an interactive **Tableau Public** dashboard with a written insights report.

**📊 Live dashboard:** `TODO — Tableau Public URL`

---

## The business questions

<!-- TODO: finalise once the dataset is confirmed. Draft direction: -->

1. How does demand vary across the network, and which stations or routes carry the most?
2. When does the network peak — by hour, by day, by season — and where is capacity tightest?
3. How do the different modes (metro, bus, tram, taxi) compare in reach and usage?
4. Which areas of Dubai are underserved relative to their demand?
5. What does the trend over time say about where capacity should go next?

---

## Data

| | |
|---|---|
| **Source** | `TODO` |
| **Licence** | `TODO` |
| **Grain** | `TODO` |
| **Rows** | `TODO` |
| **Period covered** | `TODO` |

See [`docs/DATA-SOURCING.md`](docs/DATA-SOURCING.md) for how the source was selected.

---

## Data model

`TODO — ER diagram + a note on the normalisation choices and why each table exists.`

---

## Headline insights

`TODO — 3-4 findings, each tied to a visual, each phrased as a recommendation rather than
an observation.`

Full write-up: [`reports/insights.md`](reports/insights.md)

---

## How it works

```
data/raw/*.csv  ──load.py──>  MySQL  ──queries.sql──>  data/processed/*.csv  ──>  Tableau Public
   (source)                (modelling +              (query results,            (visualisation)
                            analysis layer)           analysis-ready)
```

MySQL does the modelling and the analysis; Tableau visualises the query outputs. Tableau
Desktop **Public Edition** connects to file-based sources rather than live databases, so
analysis-ready extracts are published from MySQL to `data/processed/`.

**Why Tableau over Power BI:** Tableau Public publishes to a genuinely public URL that
anyone can open, with no licence or work-account friction — which is what makes a
portfolio dashboard worth building. Power BI is more common in UAE corporate postings,
but sharing from it requires a work or school account.

---

## Repo structure

```
├── sql/
│   ├── schema.sql      # CREATE TABLEs, keys, constraints
│   └── queries.sql     # analytical queries, each with its business question
├── scripts/
│   └── load.py         # raw -> MySQL loader
├── data/
│   ├── raw/            # untouched source downloads
│   └── processed/      # analysis-ready extracts for Tableau
├── dashboard/
│   └── screenshots/
├── reports/
│   └── insights.md     # business write-up
└── docs/
    ├── SETUP.md        # MySQL + Tableau setup
    └── DATA-SOURCING.md
```

---

## Running it yourself

Full instructions in [`docs/SETUP.md`](docs/SETUP.md). Short version:

```powershell
# 1. Database
mysql -u root -p -e "CREATE DATABASE dubai_transport CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. Python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 3. Credentials
copy .env.example .env    # then fill in your MySQL password

# 4. Build and load
mysql -u root -p dubai_transport < sql/schema.sql
python scripts/load.py
```

---

## Tech

MySQL 8 · SQL · Python (pandas, SQLAlchemy) · Tableau Public · Git
