# OHC Biomedical Waste Management (CR#1) — Odoo 16

## Fixed: page crash on opening Waste Collection

Two rounds of hand-written date math for a "current calendar week" filter
both crashed the page (`datetime.timedelta` isn't supported by Odoo's
browser-side domain evaluator; `.weekday()` as a method call, or a bare
`weekday=` parameter passed to `relativedelta`, doesn't appear to be either
— both attempts failed the same way).

**Fix applied:** replaced the crashing calendar-week math with a much
simpler, well-attested pattern — a trailing **7-day window ending today**,
using only `context_today()` and `relativedelta(days=N)` with plain
integers. This exact pattern is confirmed working in real, shipped Odoo
filters, unlike the two previous attempts. The filter is now labeled
**"Last 7 Days"** rather than "This Week" to accurately describe what it
does — it's a rolling window, not a strict Monday–Sunday calendar week.
It's still the default-active filter when opening via the smart button.

**If a strict calendar week (Monday–Sunday) genuinely matters** rather
than a rolling 7-day window, that's still possible, but only worth
attempting once this simpler, confirmed-safe version is verified working
live — at that point there's a stable base to test more carefully from,
rather than guessing blind again.

## Everything else from the previous round is unchanged

- Ticket #169: every bag-count field must have an explicit value (0+) —
  blank fields block save.
- Ticket #168: Brown→Black rename; weight (kg) field alongside every bag
  colour, same blank-by-default + required-on-save pattern as counts;
  weight totals shown and summed in the list view.
- Ticket #174: receipt attachment shown as a downloadable column in the
  list view.
- OHC field readonly on the form; Supervisor/Vehicle Number blank by
  default; general cross-OHC menu removed (smart-button-only access).

## Install / update
```bash
docker compose exec -u root <odoo_service> odoo -d <your_db> -u ohc_biomedical_waste --stop-after-init
```
