import pandas as pd
from datetime import timedelta
from pathlib import Path

class TriageDataError(ValueError):
    """Raised when an input workbook cannot support the triage calculation."""

REQUIRED_COLUMNS = {
    "shipments": {
        "status", "sku", "original_eta", "revised_eta", "po_number",
        "vessel_id", "destination_port",
    },
    "inventory": {
        "sku", "part_name", "facility_location", "current_stock",
        "daily_burn_rate", "sla_penalty_per_day",
    },
    "vendors": {
        "sku", "vendor_name", "contact_email", "unit_cost",
        "expedite_shipping_flat_fee", "lead_time_days",
    },
}


def _validate_columns(frame, name):
    missing = REQUIRED_COLUMNS[name] - set(frame.columns)
    if missing:
        raise TriageDataError(
            f"{name.title()} workbook is missing: {', '.join(sorted(missing))}"
        )


def _number(value, field, sku):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise TriageDataError(f"{field} must be numeric for SKU {sku}.") from None
    if pd.isna(number):
        raise TriageDataError(f"{field} is blank for SKU {sku}.")
    return number


def _single_match(frame, sku, name):
    matches = frame[frame["sku"].astype(str).str.strip() == str(sku).strip()]
    if matches.empty:
        raise TriageDataError(f"No {name} record exists for SKU {sku}.")
    if len(matches) > 1:
        raise TriageDataError(
            f"Multiple {name} records exist for SKU {sku}; choose one approved record."
        )
    return matches.iloc[0]


def triage_dataframes(shipments_df, inventory_df, vendors_df):
    """Calculate auditable disruption metrics from the three input tables."""
    _validate_columns(shipments_df, "shipments")
    _validate_columns(inventory_df, "inventory")
    _validate_columns(vendors_df, "vendors")

    delayed = shipments_df[
        shipments_df["status"].astype(str).str.strip().str.lower() == "delayed"
    ]
    results = []

    for _, shipment in delayed.iterrows():
        sku = shipment["sku"]
        inventory = _single_match(inventory_df, sku, "inventory")
        vendor = _single_match(vendors_df, sku, "backup vendor")

        try:
            original_eta = pd.to_datetime(shipment["original_eta"]).date()
            revised_eta = pd.to_datetime(shipment["revised_eta"]).date()
        except (TypeError, ValueError):
            raise TriageDataError(
                f"Invalid ETA date for shipment {shipment['po_number']}."
            ) from None
        if revised_eta < original_eta:
            raise TriageDataError(
                f"Revised ETA cannot be before original ETA for shipment {shipment['po_number']}."
            )

        current_stock = _number(inventory["current_stock"], "current_stock", sku)
        daily_burn_rate = _number(inventory["daily_burn_rate"], "daily_burn_rate", sku)
        if daily_burn_rate <= 0:
            raise TriageDataError(f"daily_burn_rate must be greater than zero for SKU {sku}.")

        days_of_supply = int(current_stock // daily_burn_rate)
        stockout_date = original_eta + timedelta(days=days_of_supply)
        gap_days = max(0, (revised_eta - stockout_date).days)
        is_critical = gap_days > 0
        daily_penalty = _number(inventory["sla_penalty_per_day"], "sla_penalty_per_day", sku)
        unit_cost = _number(vendor["unit_cost"], "unit_cost", sku)
        expedite_fee = _number(vendor["expedite_shipping_flat_fee"], "expedite_shipping_flat_fee", sku)
        lead_time_days = int(_number(vendor["lead_time_days"], "lead_time_days", sku))
        shortfall_units = int(gap_days * daily_burn_rate)
        total_expedite_cost = shortfall_units * unit_cost + expedite_fee
        sla_penalty = gap_days * daily_penalty
        net_savings = sla_penalty - total_expedite_cost
        vendor_can_cover_gap = lead_time_days <= days_of_supply

        if not is_critical:
            recommendation = "Monitor inbound shipment"
        elif not vendor_can_cover_gap:
            recommendation = "Review alternate supply options"
        elif net_savings > 0:
            recommendation = "Expedite backup order"
        else:
            recommendation = "Review expedite economics"

        results.append({
            "sku": str(sku),
            "part_name": str(inventory["part_name"]),
            "facility": str(inventory["facility_location"]),
            "po_number": str(shipment["po_number"]),
            "vessel_id": str(shipment["vessel_id"]),
            "port": str(shipment["destination_port"]),
            "orig_eta": str(original_eta),
            "revised_eta": str(revised_eta),
            "delay_days": (revised_eta - original_eta).days,
            "days_of_supply": days_of_supply,
            "stockout_date": str(stockout_date),
            "is_critical": is_critical,
            "gap_days": gap_days,
            "sla_penalty": sla_penalty,
            "shortfall_units": shortfall_units,
            "vendor_name": str(vendor["vendor_name"]),
            "contact_email": str(vendor["contact_email"]),
            "unit_cost": unit_cost,
            "expedite_fee": expedite_fee,
            "total_expedite_cost": total_expedite_cost,
            "net_savings": net_savings,
            "lead_time_days": lead_time_days,
            "vendor_can_cover_gap": vendor_can_cover_gap,
            "recommendation": recommendation,
        })

    results.sort(key=lambda item: (not item["is_critical"], -item["net_savings"]))
    return {
        "results": results,
        "delayed_count": len(results),
        "critical_count": sum(item["is_critical"] for item in results),
    }


def load_triage(data_dir=None):
    """Load local workbooks and return the complete triage summary."""
    base_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent / "data"
    shipments_df = pd.read_excel(base_dir / "shipments.xlsx")
    inventory_df = pd.read_excel(base_dir / "inventory.xlsx")
    vendors_df = pd.read_excel(base_dir / "backup_vendors.xlsx")
    return triage_dataframes(shipments_df, inventory_df, vendors_df)


def run_triage(data_dir=None):
    """Backward-compatible entry point for the app and CLI."""
    return load_triage(data_dir)


if __name__ == "__main__":
    result = run_triage()
    print("--- TRIAGE CALCULATION RESULTS ---")
    print(f"Delayed shipments: {result['delayed_count']}")
    for item in result["results"]:
        print(f"\n{item['po_number']} | {item['sku']} | {item['recommendation']}")
        for key, value in item.items():
            print(f"{key}: {value}")