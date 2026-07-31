# Data sourcing — Dubai transport & mobility

**Status: this is the one step blocking the project.** Everything downstream is ready.

Dubai's open-data estate is mid-migration, so this could not be automated. What follows
is what to look for, where to look, and what to do when a source fails.

---

## What a good dataset looks like here

You are not just looking for "a Dubai transport file". You need something the SQL layer
can do real work on. Judge a candidate against these:

| Requirement | Why it matters |
|---|---|
| **A measure to aggregate** — riders, trips, journeys, incidents, revenue | Without a number to sum, there are no KPIs and no dashboard. |
| **A date/time column** | Trends over time are the backbone of the dashboard. Hour-of-day is a bonus — it gives you peak-demand analysis. |
| **2+ dimensions to slice by** — station, line, mode, area, direction, ticket type | These become your filters and your breakdown charts. |
| **Row-per-event or fine grain**, not a pre-summarised total | A single table of yearly totals cannot be normalised into a real schema. |
| **Enough rows** — thousands, ideally more | Demonstrates handling volume, not a toy file. |

**Two or three related files beat one wide file.** A ridership file *plus* a station
reference file *plus* a route file is exactly the shape that justifies a normalised
schema and real joins — which is half of what this project is meant to prove.

---

## Route 1 — `data.dubai` (chosen source)

<https://data.dubai>

1. Register for a free account and sign in — you are in the UAE, so this should be quick.
2. Browse **Transport & Mobility**, or use the portal's search.
3. Search terms worth trying: `metro ridership`, `bus ridership`, `public transport`,
   `taxi trips`, `passenger`, `stations`, `routes`, `traffic incidents`, `Salik`, `RTA`.
4. Download CSV (or Excel) into `data/raw/` — **unmodified**. Never edit raw files by
   hand; all cleaning happens in code so it is reproducible and reviewable.
5. Also save the dataset's **description/metadata page** (PDF or a copy-paste into a
   text file). You need the field definitions, units, update frequency and licence for
   the README, and to know what the columns actually mean.

⚠️ **Known risk:** when checked on 2026-07-31, `data.dubai/en/data-and-statistics`
returned *"This page is under development / No data available"* to an unauthenticated
request. It may well render properly once you are logged in. **If it doesn't, don't push
on it — go to the fallbacks below.** Tell Claude what you see and we'll switch route.

---

## Fallbacks, in the order worth trying

### 2. Dubai RTA GTFS feed — *best structural fit*

GTFS is a transit schedule standard that is **already a normalised relational schema**:
`agency`, `routes`, `trips`, `stops`, `stop_times`, `calendar`, `shapes`. It maps into
MySQL almost one-to-one and gives genuine multi-table joins with hundreds of thousands
of `stop_times` rows.

- Register free at <https://mobilitydatabase.org> for an API key, then pull the Dubai
  RTA feed. (<https://www.transit.land/feeds/f-dubai~rta> also carries it, also key-gated.)
- **Trade-off:** GTFS describes *scheduled service*, not passenger demand. Your KPIs
  become service-supply metrics — network coverage, service frequency by hour, busiest
  interchanges, route directness, mode comparison. That is legitimate operations
  analytics and reads well, but you cannot claim ridership analysis from it.
- **Strongest combination:** GTFS for network structure **plus** any ridership file from
  `data.dubai` for demand. Supply and demand together is a genuinely good dashboard story.

### 3. Dubai Statistics Center

<https://www.dsc.gov.ae> → Themes → Transport

Publishes official statistical tables, usually Excel. Reliable and citable, but often
pre-aggregated to monthly or yearly totals — check the grain against the table above
before committing to it.

### 4. Kaggle

Search "Dubai transport", "Dubai taxi", "Dubai metro", "UAE traffic". Free account, and
the `kaggle` CLI makes the download reproducible in-repo.

- **Trade-off:** a weaker provenance story than a government portal. If you use Kaggle,
  find the dataset's *original* source and cite that in the README.

### 5. OpenStreetMap (Overpass API) — *always available, no account*

Dubai's metro, tram and bus network is mapped in OSM and extractable with no auth via
the Overpass API: stations, lines, routes, coordinates.

- **Use as:** a guaranteed-available supplement — geography for map visuals, or a
  station reference table to join against. Not sufficient alone (no volumes, and
  completeness varies by contributor).

---

## When the data lands

Put files in `data/raw/`, then tell Claude:

- what you downloaded and **the exact source URL**
- the **licence / terms of use** (needed for the README, and to decide whether the file
  can legally be committed to a public GitHub repo)
- anything the portal said about field definitions or units

Claude then inspects the real columns and starts Stage 2 — schema design, ER diagram,
and the loader. **No schema will be written against guessed column names.**

---

## One rule

**Do not synthesise or fabricate data to unblock this.** A portfolio project resting on
invented numbers is worse than no project: the first interviewer who asks "where did this
come from?" ends the conversation. If every route above fails, the honest fix is to widen
the topic — not to invent the data.
