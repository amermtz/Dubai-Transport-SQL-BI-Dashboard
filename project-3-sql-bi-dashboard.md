# Project 3 — SQL + Interactive BI Dashboard

> Project brief. This is the Data Analyst door-opener. It fills the single biggest gap
> in the current skill set (BI tools) and matches analyst-posting language almost word
> for word.

## 1. Goal

Take a real dataset, model it in a SQL database, write the analytical queries behind
it, and build an interactive dashboard with a written insights summary. The dashboard
tool is Power BI or Tableau (pick one — see §5).

**Definition of done:** a published/shareable dashboard (or a recorded walkthrough +
exported file if the free tier can't publish), a SQL script that builds and queries
the database, and a short insights write-up. Repo ties it together.

## 2. Why this project (context — do not skip)

UAE data-analyst postings name SQL and a BI tool (Power BI / Tableau) in nearly every
listing, and the current skill set has neither BI tool — Streamlit does not substitute.
This is fast to build, opens the Data Analyst role (a lower barrier for a fresher than
Data Scientist), and the SQL-plus-dashboard combination is exactly the phrasing those
postings use. It also demonstrates the "business insight" framing analysts are hired for.

## 3. Target roles / keywords this project serves

SQL, MySQL, Power BI, Tableau, data visualization, dashboard, business intelligence,
EDA, data cleaning, ER modeling, normalization, KPIs, business insights, stakeholder
reporting.

## 4. Data sources (pick one with real business framing)

1. **UAE / Dubai open economic or transport data** — Dubai Pulse, Dubai Statistics
   Center, or federal open data (e.g. tourism, transport ridership, trade). Local
   relevance is a plus.
2. **Retail / supply-chain dataset** — a public sales dataset (orders, products,
   customers, regions) works well because it has clear KPIs and multiple tables for
   a real schema.
3. **E-commerce / Olist-style relational data** — good for showing joins and ER
   modelling.

Pick something with at least 2-3 relatable entities (e.g. orders, customers,
products) so the SQL modelling is non-trivial.

## 5. Tool choice: Power BI vs Tableau

- **Power BI** — more common in UAE corporate/finance job postings; free Desktop on
  Windows. Choose this if targeting corporate analyst roles.
- **Tableau** — strong in visualization-heavy roles; Tableau Public is free and
  publishes to a shareable URL easily (good for portfolios).
- If you want a guaranteed public link with no license friction, Tableau Public is
  the pragmatic pick. If targeting corporates specifically, Power BI.
- Pick ONE and go deep. Listing both without depth is worse than one done well.

## 6. Build sequence

**Stage 1 — Data + schema**
- Load raw data. Design a normalised relational schema (ER diagram).
- Create the MySQL database; write `schema.sql` (CREATE TABLEs, keys, constraints).
- Load the data (`load.sql` or a small Python loader).

**Stage 2 — SQL analysis**
- Write the analytical queries that answer real business questions:
  revenue by region/month, top products, customer segments, growth rates, etc.
- Keep them in `queries.sql`, each with a comment stating the business question.
- These queries are interview fuel — be ready to explain the joins and aggregations.

**Stage 3 — Dashboard**
- Connect the BI tool to the data (or to a cleaned export).
- Build 1-2 dashboard pages: KPIs up top, trends and breakdowns below, at least one
  interactive filter (date/region/category).
- Design for clarity: a hiring manager should grasp the story in 10 seconds.

**Stage 4 — Insights write-up**
- 5-7 findings in plain business English, each tied to a visual.
- Frame as recommendations, not just observations ("revenue dips every Q1 in region
  X — investigate seasonal supply" beats "region X is lower").

**Stage 5 — Publish**
- Tableau Public: publish and grab the URL.
- Power BI: publish to Power BI Service if possible, else export the .pbix and record
  a short screen walkthrough (GIF/video) for the README.

## 7. Suggested repo structure

```
sql-bi-dashboard/
├── README.md
├── data/
│   ├── raw/
│   └── processed/
├── sql/
│   ├── schema.sql       # CREATE TABLEs, keys
│   ├── load.sql         # or loader.py
│   └── queries.sql      # analytical queries, each commented
├── dashboard/
│   ├── dashboard.pbix   # or Tableau .twbx / public link
│   └── screenshots/
├── reports/
│   └── insights.md      # the business write-up
└── er_diagram.png
```

## 8. README must include

- Dashboard link (or embedded screenshots + walkthrough) at the top.
- The business questions the project answers.
- ER diagram + a note on normalisation choices.
- 3-4 headline insights with visuals.
- The SQL queries (or a link to them) with the questions they answer.
- Tool choice justified (why Power BI or Tableau).

## 9. Stretch goals (after it ships)

- Add a calculated forecast (simple trend line / moving average).
- Row-level detail drill-through.
- A second page for a different stakeholder (exec vs operations view).

## 10. Anti-patterns to avoid

- Don't dump one flat CSV into the BI tool with no SQL layer — the SQL modelling is
  half the point and the half analysts get hired for.
- Don't build 12 charts with no narrative. Fewer visuals, clear story.
- Don't leave it un-shareable. A dashboard nobody can open is invisible.
- Don't list both Power BI and Tableau on the CV unless both are genuinely used.
- Don't skip the insights write-up — the analysis is the deliverable, not the charts.

## 11. CV bullet (fill in real numbers when done)

> Modelled a [domain] dataset in MySQL (normalised [N]-table schema) and built an
> interactive [Power BI/Tableau] dashboard surfacing [X] business KPIs, with a written
> insights summary translating findings into recommendations.
