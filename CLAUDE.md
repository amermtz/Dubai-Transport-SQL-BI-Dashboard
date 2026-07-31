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

### ⚠️ Project location — READ FIRST

**The project lives at `D:\dev\vscode\project3`.** It was migrated there from
`C:\Users\amerm\OneDrive\Desktop\vscode\project3` on 2026-07-31.

**Why:** the C: drive had only **1.96 GB free** (166 GB used of ~169 GB). That is not
enough to install Tableau, and — more dangerously — not enough headroom for MySQL to
load a dataset without a mid-load disk-full failure. D: has ~153 GB free.

The old C: copy **may still exist**. It is stale. Never work in it. If a session finds
itself in the OneDrive path, stop and move to `D:\dev\vscode\project3`.

Moving off OneDrive also removes the file-locking risk that OneDrive sync posed during
MySQL and Tableau work. The trade-off is no OneDrive backup — GitHub is now the only
off-machine copy, so **push regularly.**

| Tool | Status |
|---|---|
| git | ✅ `C:\Program Files\Git\cmd\git.exe` — repo on branch `main`, remote `origin` set |
| Python | ✅ 3.12 at `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` |
| Python venv | ✅ `.venv/` **rebuilt at `D:\dev\vscode\project3\.venv`** and re-verified after the migration. (Venvs bake in absolute paths, so the C: one was not copied — it was recreated.) |
| MySQL | ✅ **8.0.46 Community**, binaries at `C:\Program Files\MySQL\MySQL Server 8.0\bin` (on user PATH). DB `dubai_transport`, `utf8mb4` / `utf8mb4_unicode_ci`. **Target 8.0 syntax, not 8.4.** |
| MySQL connection | ✅ End-to-end verified from Python via `scripts/db.py`, from the D: location |
| MySQL data dir | ⏳ **Migration to `D:\MySQL\Data` pending** — see §3.1 |
| Tableau Public | ⏳ **Install pending** — first attempt failed, see §3.1 |
| Node / SQLite CLI | ❌ not installed (not needed) |

Git identity: `amermtz <amermurtuza@gmail.com>`. GitHub CLI authenticated as `amermtz`.

Platform: Windows 11. Shell: PowerShell 5.1 (no `&&` chaining — use `;` / `if ($?)`).

### 3.1 Outstanding actions (need an ELEVATED PowerShell)

Both require admin, so Claude cannot run them — the user must.

**1. Move the MySQL data directory to D:**
```powershell
powershell -ExecutionPolicy Bypass -File D:\dev\move-mysql-data.ps1
```
The script stops `MySQL80`, copies the data dir to `D:\MySQL\Data`, grants
`NT AUTHORITY\NetworkService` full control on it (the service runs as NetworkService;
without this it fails to start with a generic error 1067), backs up and repoints
`datadir` in `my.ini` (which is **UTF-16 LE** — read/write it with that encoding or
mysqld cannot parse it), sets the service to **Automatic**, and restarts.
It copies rather than moves; the C: data dir survives until verified.

⚠️ This also clears the previously-logged issue that `MySQL80` was set to **Manual**
start and would not survive a reboot.

**2. Install Tableau Public to D:**
```powershell
& "C:\Users\amerm\AppData\Local\Temp\WinGet\Tableau.Public.25.1.463\TableauPublicDesktop-64bit-2025-1-0.exe" /passive ACCEPTEULA=1 INSTALLDIR="D:\Tableau\Tableau Public 2025.1"
```
`winget install Tableau.Public` **fails with exit code 1603.** Diagnosed from the MSI
log: `OutOfDiskSpace = 1` — it defaults to `C:\Program Files` and C: is full. The
537 MB installer is already downloaded and cached at the path above, so there is no
need to re-download. (A `TRANSFORMS=" "` argument in the winget log looks suspicious
but is a red herring — the property is added then cleanly deleted.)

**3. After both succeed:** Claude verifies, then the stale C: copy at
`C:\Users\amerm\OneDrive\Desktop\vscode` can be deleted to reclaim space.
⚠️ Before deleting: that folder also holds **project1 and project2**. Deletion will sync
to OneDrive and remove the cloud copies. Confirm those two are pushed to GitHub first.
Also note `project1\uae-real-estate-prediction\.venv` was **not** copied to D: and will
need recreating when that project is next opened.

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
| 3 | Load pipeline (`scripts/load_gtfs.py`) + cleaning | 🟡 **Skeleton written & tested** — see §8 (2026-07-31 Session 2). Runs only if Stage 1 lands GTFS. |
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
│   ├── db.py                      # shared SQLAlchemy engine — ALL db code imports from here
│   ├── gtfs_spec.py               # GTFS file/column map + type rules (data, not logic)
│   └── load_gtfs.py               # GTFS -> MySQL loader; --inspect and --load modes
├── dashboard/
│   └── screenshots/               # dashboard images for the README
├── tests/
│   ├── conftest.py                # puts scripts/ on sys.path; feed fixtures
│   ├── test_load_gtfs.py          # loader regression tests — no DB needed
│   └── fixtures/mini_gtfs/        # ⚠️ SYNTHETIC test feed. Not project data.
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

### 2026-07-31 — Session 1 (continued)
- User committed the scaffold and pushed to
  <https://github.com/amermtz/Dubai-Transport-SQL-BI-Dashboard> (public).
- MySQL 8.0.46 installed via the official GUI installer. Two snags, both resolved:
  1. `mysql` not on PATH → appended the server `bin` folder to the **user** PATH.
     VS Code needed a full restart to inherit it (new terminal tabs keep the stale env);
     `$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + ...("Path","User")`
     is the in-session workaround.
  2. ⚠️ Service `MySQL80` StartType is **Manual** — it will not come back after a reboot.
     Fix with an elevated `Set-Service -Name MySQL80 -StartupType Automatic`.
     **Still outstanding.** If a future session hits "can't connect", check this first.
- `dubai_transport` database created; `.env` filled in.
- **Gotcha worth remembering:** the user's MySQL password contains a URL-delimiter
  character (`@`). Interpolated raw into a SQLAlchemy URL it breaks the connection string
  and produces the misleading error `Can't connect to MySQL server on '@localhost'` —
  which looks like a network fault, not a credentials-formatting one. Fixed permanently by
  `quote_plus()`-encoding user and password in `scripts/db.py`. **All DB code must import
  `get_engine()` from `scripts/db.py` rather than building its own URL.**
- Wrote and verified `scripts/db.py`. Connection confirmed end-to-end.
- **Topic wobble, resolved:** the user asked whether real estate would have been easier,
  and briefly switched to it, then reverted to transport within the same session.
  Worth recording *why*, so this isn't relitigated a third time:
  - Real estate's apparent advantage — a documented direct CSV for DLD transactions —
    was tested and is **already dead** (redirects to `data.dubai`, same migration).
  - Its genuine advantage is that DLD data is widely mirrored *outside* the government
    portal (Kaggle, third-party APIs), so it has fallbacks transport lacks.
  - Its cost: the user already has a Dubai real-estate project. A second one demonstrates
    one domain twice rather than two capabilities, and Dubai property dashboards are among
    the most common portfolio projects in existence. Transport is distinctive.
  - **Decision: transport stands.** Real estate remains available as a fallback if data
    sourcing fails outright — but as a deliberate choice, not a retreat.
- **Next:** Step 5 (Tableau Public account + install) and Step 6 (data sourcing).
  Stage 2 is blocked only on real data.

### 2026-07-31 — Session 1 (disk crisis + migration to D:)
- `winget install Tableau.Public` failed, exit **1603**. Root cause was **not** obvious
  from the winget output; found by reading the nested MSI log
  (`...DiagOutputDir\Tableau.Public.*_000_Tableau.log`) down to the property dump:
  `OutOfDiskSpace = 1`. **C: had 1.96 GB free.**
  - Lesson for future installer failures here: the bundle log gives only `0x80070643`.
    The real cause is in the nested `_000_*.log`, near the end, in the `Property(S):` block.
- User declined to free 20 GB on C: (not realistic) and chose to migrate to D: instead.
- **Migrated `C:\Users\amerm\OneDrive\Desktop\vscode` → `D:\dev\vscode`** via robocopy:
  285 files / 206 MB / 0 failures, excluding `.venv`, `venv`, `node_modules`, `__pycache__`.
  Verified afterwards: git history, branch `main`, `origin` remote and `.env` all intact.
  Source folder was 1.20 GB / 26,540 files, with **0 OneDrive cloud-only placeholders**,
  so the copy triggered no sync downloads.
- Rebuilt `.venv` at the D: location and re-verified the MySQL connection from there.
- **Nothing has been deleted from C: yet.** The migration was a copy, deliberately.
- Wrote `D:\dev\move-mysql-data.ps1` (see §3.1). Not yet run — needs elevation.
- Context noted: `project1` is `uae-real-estate-prediction` (Streamlit/altair stack).
  This confirms the §2 reasoning — project 3 being SQL + BI on a *different* domain
  demonstrates a second capability rather than repeating the first.
- **Open thread for the next session:** the user asked how to answer an interviewer who
  questions using real-estate data twice. That answer was cut off mid-delivery and the
  user then reverted to transport, which makes it moot *unless* they switch back. The
  short version if it comes up: same domain is defensible as deliberate depth, but only
  if the two projects demonstrably answer different questions with different techniques —
  and never justify it with "the data was easier to find."
- **Next:** user runs the two elevated commands in §3.1, then Step 6 (data sourcing).

### 2026-07-31 — Session 2 (GTFS loader skeleton)

Verified first that **nothing had changed on the machine since Session 1**: MySQL80 still
`Manual`, no `D:\MySQL\Data`, no Tableau, `data/raw/` still empty. All three §3.1 actions
are still outstanding. The 538 MB Tableau installer **is still cached** at the Temp path
in §3.1 — Windows has not cleaned it, so no re-download is needed.

Wrote the GTFS loader ahead of the data, on the grounds that GTFS **column names are a
published standard**, so this is not the guessing that rule §7.2 forbids. Two files:

- **`scripts/gtfs_spec.py`** — the file/column map as *data*: per file, its table, whether
  the spec requires it, load order, and which columns are ids / times / dates / ints /
  floats. Kept separate from the loader so `sql/schema.sql` can later be generated or
  checked against it.
- **`scripts/load_gtfs.py`** — `--inspect` (reports the feed's real contents, no DB access)
  and `--load` (streams into existing tables, parents first).

**Design decisions worth not relitigating:**

1. **`--inspect` runs before any schema is written.** GTFS defines many optional columns
   and every feed ships a different subset. The schema gets written against what the RTA
   feed *actually has*, not against the standard in the abstract.
2. **The loader refuses to create tables.** `pandas.to_sql` would infer all-TEXT columns
   with no keys, constraints or indexes — which would silently throw away the
   normalisation and ER modelling that is half of what this project is meant to evidence.
   Missing tables produce an error naming them and pointing at `sql/schema.sql`.
3. **Times are stored as seconds-after-midnight `INT`, not `TIME`.** This is the single
   biggest GTFS trap. Times legally exceed 24:00:00 — `25:05:00` means 01:05 the next
   morning but still on the *previous service day*. Any time-of-day parser either errors
   or wraps, and wrapping turns a 75-minute trip into a negative duration. Seconds keep
   the arithmetic correct; `hour_of_day = (secs DIV 3600) MOD 24` recovers the clock hour.
4. **All `*_id` columns are forced to string.** Feeds use ids like `007` and `01`; pandas
   infers int64 and strips the leading zeros, after which the joins silently under-match.
5. **`stops.txt` is sorted stations-first before insert.** `parent_station` is a
   self-referencing FK within one file and feeds do not order parents first — so a
   correct final table can still fail on insert order alone.
6. `encoding="utf-8-sig"`, because a BOM otherwise attaches to the first header and
   renames the first column invisibly.

**Tested end-to-end** against a throwaway fixture in the scratchpad (never in `data/raw/`,
never committed — it is a code test, not project data). Confirmed against a scratch MySQL
DB with the real FK constraints in place, including the self-FK on `stops`:
`007` survived as text; `24:20:00` → `87600`; a cross-midnight trip measured **+75 min,
not negative**; blanks became `NULL`; the platform-before-parent row ordering loaded
cleanly; `--truncate` made re-runs idempotent (it truncates child-first with
`FOREIGN_KEY_CHECKS=0`, session-scoped). Both feed forms work — `.zip` (including one
nested in a top-level folder) and an extracted directory. The scratch DB was dropped;
`dubai_transport` was never written to and is still empty.

### 2026-07-31 — Session 2 (continued: tests)

Promoted the throwaway fixture into permanent in-repo coverage: `tests/` with
`conftest.py`, `test_load_gtfs.py` (**63 tests, all passing, ~0.7s**) and
`tests/fixtures/mini_gtfs/`. Added `pytest>=8.0` to `requirements.txt`.

Run with: `python -m pytest tests -q`

**The tests need no database.** Everything they cover happens before MySQL is involved,
which is precisely where GTFS data gets corrupted — and none of those failures raise.
Leading zeros vanish, midnight wraps, dates become large integers: the load "succeeds"
and the dashboard numbers are simply wrong. That is the case for testing this layer at all.

⚠️ **`tests/fixtures/mini_gtfs/` is synthetic and is NOT project data.** It is committed,
so the boundary matters: it exists only to exercise the loader, its `README.md` says so,
and nothing in `reports/insights.md` may ever rest on it. This does not weaken rule §7.2 —
a test double is not a fabricated dataset. Real data still comes from `data/raw/` with a
citation.

**Two things found by writing the tests, both now fixed:**

1. **pandas 3.0.5 is installed, not 2.x.** pandas 3 made `str` the default dtype for text
   columns, so the blank-to-NULL backstop in `coerce_frame` — guarded by
   `dtype == object` — had silently stopped matching anything. Harmless in practice
   (`na_values` already handles blanks on read) but it was dead code reading as live.
   Now checks `is_string_dtype` as well. **Worth remembering: this project is on pandas 3,
   where several dtype defaults differ from the 2.x behaviour most examples assume.**
2. **A code comment was wrong.** It claimed that without `encoding="utf-8-sig"` a BOM
   would corrupt the first column name. pandas' C parser strips the BOM anyway, so
   `utf-8-sig` is insurance, not load-bearing. Comment corrected, and the test renamed to
   `test_bom_does_not_corrupt_first_column` with a docstring stating it asserts the
   invariant rather than guarding that setting.

**Verified the suite actually fails on broken code** rather than just passing. Deliberately
introduced five regressions; the tests caught four — time wrap-at-24h, id type inference,
stops not reordered parents-first, dates left as strings. The fifth (BOM) was *missed*,
which is what exposed finding 2 above. That check was a scratchpad throwaway and is not
in the repo; re-do it by hand if the loader changes substantially.

- **Next:** unchanged — the two elevated commands in §3.1, and **data sourcing is still
  the only real blocker.** When a GTFS feed lands in `data/raw/`, the first command to
  run is `python scripts/load_gtfs.py --inspect`; its output is what Stage 2's
  `sql/schema.sql` gets written against.
