# mini_gtfs — synthetic test fixture

**This is not project data and must never be treated as such.** It is a hand-written,
deliberately tiny GTFS feed whose only purpose is to exercise `scripts/load_gtfs.py`.
The stop names, coordinates and times are invented. Nothing here is analysed, nothing
here reaches the dashboard, and no finding in `reports/insights.md` rests on it.

Real data lives in `data/raw/` and comes from a cited source — see `docs/DATA-SOURCING.md`.

Each file encodes a specific trap the loader has to survive:

| File | The trap |
|---|---|
| `routes.txt` | `route_id` values `007` and `10` — type inference strips the leading zero and breaks every join downstream. |
| `stops.txt` | A platform is listed *before* the station it references via `parent_station`, a self-referencing FK. Correct data, insert order that fails anyway. |
| `stop_times.txt` | Trip `T2` runs `23:50 → 24:20 → 25:05`. Past-midnight times are legal GTFS; parsing them as clock times wraps the value and turns a 75-minute trip negative. |
| `calendar.txt` | `YYYYMMDD` dates, which are integers until something converts them. |
| `routes.txt`, `stop_times.txt` | Blank optional fields, which must land as `NULL` rather than `""`. |
| `levels.txt` | In the GTFS standard but deliberately not modelled — must be reported as such, not as an error. |
| `vendor_extras.txt` | Not in the standard at all — must be reported as unexpected. |
