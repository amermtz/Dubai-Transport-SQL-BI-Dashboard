# CLAUDE.md — Project State & Progress

> **Purpose of this file.** It is the memory of this project. Any new Claude Code session
> should read this first to know what was decided, what is built, and what comes next.
> Update the Progress Log at the bottom whenever a stage completes.
>
> **This is not the project brief.** The brief is `project-3-sql-bi-dashboard.md`.
> This file records what actually happened against it.

---

## 1. What this project is

**Dubai Public Transport Analytics — SQL + Tableau BI Dashboard.**

A Dubai transport & mobility dataset modelled in a normalised MySQL schema, analysed
through commented SQL queries, and surfaced as an interactive Tableau Public dashboard
with a written business-insights report.

Built as a **CV / portfolio piece** targeting **UAE Data Analyst roles**. The keywords it
is meant to evidence: SQL, MySQL, Tableau, data visualisation, dashboard, business
intelligence, EDA, data cleaning, ER modelling, normalisation, KPIs, business insights.

---

## 2. Locked decisions

These were decided with the user. Do not silently revisit them.

| Decision | Choice | Why |
|---|---|---|
| **BI tool** | **Tableau Public** | Free, and publishes to a real public URL a recruiter can click from the CV. Chosen over Power BI, whose sharing needs a work/school account. |
| **Topic** | **Dubai transport & mobility** | User is targeting the UAE job market, so local relevance is a plus. Naturally multi-entity (routes, stops, trips, ridership) so the SQL modelling is non-trivial. |
| **Excluded topic** | **Real estate — OFF LIMITS** | User has already built a Dubai real-estate project and does not want to repeat the topic. Do not propose DLD / property / rental datasets. |
| **Database** | **MySQL, for real** | MySQL is the single most-named skill in UAE analyst postings. The CV bullet must be literally true, including if an interviewer asks the user to run it live. No SQLite substitute. |
| **Data source** | **User downloads from `data.dubai`** | An authentic Dubai government source is nameable in interviews. See §4 for the access problem. |
| **Commits** | **The USER makes all git commits** | Explicit instruction. Claude must scaffold and write files but **never run `git commit`, `git push`, or create the GitHub repo.** Staging/inspection commands are fine. |
| **GitHub repo name** | **`Dubai-Transport-SQL-BI-Dashboard`** (public) | Chosen by the user. Reads as a portfolio piece on a CV; the local folder stays `project3`. Owner: `amermtz` (`gh` CLI already authenticated). |

---

## 3. Environment (verified 2026-07-31)

| Tool | Status |
|---|---|
| git | ✅ `C:\Program Files\Git\cmd\git.exe` — repo initialised in project root |
| Python | ✅ 3.12 at `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` |
| Python venv | ✅ `.venv/` created, `requirements.txt` installed & import-verified (pandas 3.0.5, SQLAlchemy 2.0.51, PyMySQL, python-dotenv, openpyxl) |
| MySQL | ❌ **not installed** — required, see `docs/SETUP.md` |
| Tableau Public | ❌ **not installed** — required, see `docs/SETUP.md` |
| Node / SQLite CLI | ❌ not installed (not needed) |

Git identity already configured: `amermtz <amermurtuza@gmail.com>`.

Platform: Windows 11. Shell: PowerShell 5.1 (no `&&` chaining — use `;` / `if ($?)`).

⚠️ The project folder lives under **OneDrive**. If OneDrive sync causes file locks during
MySQL or Tableau work, that is the cause.

---

## 4. The open blocker: getting the data

**Status: BLOCKED ON USER.** Everything else can proceed without it.

Dubai's open-data estate is mid-migration and could not be scraped programmatically:

- `dubaipulse.gov.ae` — **retired.** Every URL 301-redirects to `data.dubai`.
- `data.dubai/en/data-and-statistics` — catalog page returns *"This page is under
  development / No data available"* to an unauthenticated fetch. May render for a
  logged-in browser; unverified.
- `rta.ae` open-data page — hosts only PDF annual reports, and points back to Dubai Pulse.
- `bayanat.ae`, `opendata.fcsc.gov.ae` — 403 to programmatic requests (WAF).
- Dubai RTA GTFS feed exists and is well-structured, but both catalogs hosting it
  (Mobility Database, Transitland) now require a free API key.

**What the user needs to supply:** see `docs/DATA-SOURCING.md` for the exact shopping list
and the ranked fallbacks if `data.dubai` yields nothing.

**Do not fabricate or synthesise a dataset to unblock this.** A CV project built on invented
numbers is worse than no project — it collapses in an interview. If `data.dubai` fails,
work down the documented fallbacks with the user.

---

## 5. Build stages & status

| Stage | Description | Status |
|---|---|---|
| 0 | Repo scaffold, docs, progress file | ✅ Done |
| 1 | Data acquisition | ⛔ **Blocked on user** — see §4 |
| 2 | Schema design + ER diagram, `sql/schema.sql` | ⬜ Not started — needs real columns |
| 3 | Load pipeline (`scripts/load.py`) + cleaning | ⬜ Not started |
| 4 | Analytical queries, `sql/queries.sql` | ⬜ Not started |
| 5 | Tableau dashboard + publish to Tableau Public | ⬜ Not started |
| 6 | Insights write-up, `reports/insights.md` | ⬜ Not started |
| 7 | Final README with dashboard link + screenshots | ⬜ Not started |

---

## 6. Repo layout

```
project3/
├── CLAUDE.md                      # this file — project memory
├── project-3-sql-bi-dashboard.md  # the original brief
├── README.md                      # the portfolio front door
├── .gitignore
├── requirements.txt
├── data/
│   ├── raw/                       # untouched source downloads
│   └── processed/                 # cleaned exports (Tableau reads these)
├── sql/
│   ├── schema.sql                 # CREATE TABLEs, keys, constraints
│   └── queries.sql                # analytical queries, each with its business question
├── scripts/
│   └── load.py                    # raw -> MySQL loader
├── dashboard/
│   └── screenshots/               # dashboard images for the README
├── reports/
│   └── insights.md                # the business write-up
└── docs/
    ├── SETUP.md                   # MySQL + Tableau install steps
    └── DATA-SOURCING.md           # what to download and from where
```

---

## 7. Standing rules for Claude in this project

1. **Never commit.** The user owns all git history. Scaffold, write, stage if asked — stop there.
2. **Never invent data.** See §4.
3. **No real-estate topics.** See §2.
4. **Keep §5 and the Progress Log current** — this file is the handoff to the next session.
5. **MySQL dialect**, not generic SQL. Every query in `sql/queries.sql` carries a comment
   stating the business question it answers — those comments are interview prep.
6. **Narrative over chart count.** Per the brief: fewer visuals, clear story. A hiring
   manager should get it in 10 seconds.
7. Don't claim a stage is done in README or here until it is actually verified working.

---

## 8. Progress log

### 2026-07-31 — Session 1
- Read the brief; confirmed the goal is a CV portfolio piece for UAE analyst roles.
- Audited the machine: git + Python present; **MySQL, Tableau, Power BI all absent**.
- Locked the four decisions in §2 with the user.
- Investigated Dubai data access in depth and hit the migration wall documented in §4.
  Real estate was ruled out by the user mid-investigation, so DLD transactions
  (the one dataset with a known direct CSV) was abandoned.
- Initialised the git repo and scaffolded the directory structure.
- Wrote this file, `README.md`, `.gitignore`, `docs/SETUP.md`, `docs/DATA-SOURCING.md`.
- **Next:** user installs MySQL + Tableau Public (`docs/SETUP.md`) and sources the data
  (`docs/DATA-SOURCING.md`). Then Stage 2 begins.
