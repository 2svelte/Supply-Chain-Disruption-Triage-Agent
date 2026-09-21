# Supply Chain Disruption Triage Agent

A lightweight Streamlit showcase for reducing decision latency when inbound freight is delayed. It combines deterministic inventory and financial analysis with optional AI-assisted emergency PO drafting.

## Business workflow

1. Read the local shipment, inventory, and backup-vendor workbooks.
2. Identify delayed inbound shipments.
3. Calculate days of supply, estimated stockout date, coverage gap, shortfall units, SLA penalty, expedite cost, and projected net savings.
4. Prioritize the disruption and recommend monitoring, expediting, or further review.
5. Draft an emergency PO email from the calculated facts. The LLM formats the decision; it does not calculate or invent the numbers.
6. Download or approve the draft for demonstration. No external order, ERP update, or email is sent.

## Run locally

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```

The dashboard works without an OpenAI key. To enable AI-written wording, add a rotated key to `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-rotated-key"
```

Never commit this file or reuse a key that has appeared in source control or screenshots. The included `.gitignore` excludes it.

## Workbook contract

The app expects these files under `data/`:

- `shipments.xlsx`: `status`, `sku`, `original_eta`, `revised_eta`, `po_number`, `vessel_id`, `destination_port`
- `inventory.xlsx`: `sku`, `part_name`, `facility_location`, `current_stock`, `daily_burn_rate`, `sla_penalty_per_day`
- `backup_vendors.xlsx`: `sku`, `vendor_name`, `contact_email`, `unit_cost`, `expedite_shipping_flat_fee`, `lead_time_days`

Each delayed shipment must have exactly one matching inventory record and one approved backup-vendor record.

## Calculation assumptions

- The current inventory runway is anchored to the shipment's original ETA, matching the supplied demonstration data.
- `days_of_supply = floor(current_stock / daily_burn_rate)`.
- A shipment is critical when the revised ETA is later than the calculated stockout date.
- `shortfall_units = coverage_gap_days * daily_burn_rate`.
- `total_expedite_cost = shortfall_units * unit_cost + expedited freight fee`.
- `projected net savings = SLA penalty - total expedite cost`.
- A backup vendor is considered time-feasible when its lead time is no longer than the available inventory runway.

The deterministic engine validates columns, dates, numeric values, duplicate matches, missing matches, zero burn rates, and empty delay results.

## Example result

The supplied workbooks contain a four-day delay for `PO-9021`. The engine calculates three days of supply, a stockout on `2026-10-08`, a one-day coverage gap, 150 backup units, $12,000 in estimated SLA exposure, $10,250 in expedite cost, and $1,750 in projected net savings.

## Scope

This is intentionally a portfolio-scale analyst tool using static Excel inputs. It does not include a database, authentication, real-time vessel tracking, ERP write-back, email delivery, or real purchase-order submission.
