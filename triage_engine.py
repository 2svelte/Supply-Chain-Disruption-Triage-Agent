import pandas as pd
from datetime import timedelta

def run_triage():
    # Load the Excel datasets
    shipments_df = pd.read_excel("data/shipments.xlsx")
    inventory_df = pd.read_excel("data/inventory.xlsx")
    vendors_df = pd.read_excel("data/backup_vendors.xlsx")

    # Filter for delayed shipments
    delayed = shipments_df[shipments_df["status"] == "Delayed"]
    if delayed.empty:
        return None

    # Focus on the primary delayed record
    shipment = delayed.iloc[0]
    sku = shipment["sku"]

    # Match inventory and vendor records
    inv = inventory_df[inventory_df["sku"] == sku].iloc[0]
    vendor = vendors_df[vendors_df["sku"] == sku].iloc[0]

    # Timeline calculations (safe for both Excel timestamps and raw strings)
    orig_eta = pd.to_datetime(shipment["original_eta"]).date()
    rev_eta = pd.to_datetime(shipment["revised_eta"]).date()
    delay_days = (rev_eta - orig_eta).days

    # Days of supply on hand: current_stock / daily_burn_rate
    days_of_supply = int(inv["current_stock"] / inv["daily_burn_rate"])
    stockout_date = orig_eta + timedelta(days=days_of_supply)

    # Check if a stockout occurs before the delayed vessel docks
    is_critical = rev_eta > stockout_date

    # Financial and operational calculations
    gap_days = (rev_eta - stockout_date).days if is_critical else 0
    sla_penalty = gap_days * float(inv["sla_penalty_per_day"])

    # Quantity needed to cover the gap until the ship arrives
    shortfall_units = gap_days * int(inv["daily_burn_rate"])

    # Cost using domestic backup vendor
    emergency_po_cost = shortfall_units * float(vendor["unit_cost"])
    total_expedite_cost = emergency_po_cost + float(vendor["expedite_shipping_flat_fee"])
    net_savings = sla_penalty - total_expedite_cost

    return {
        "sku": sku,
        "part_name": inv["part_name"],
        "facility": inv["facility_location"],
        "po_number": shipment["po_number"],
        "vessel_id": shipment["vessel_id"],
        "port": shipment["destination_port"],
        "orig_eta": str(orig_eta),
        "revised_eta": str(rev_eta),
        "delay_days": delay_days,
        "days_of_supply": days_of_supply,
        "stockout_date": str(stockout_date),
        "is_critical": is_critical,
        "gap_days": gap_days,
        "sla_penalty": sla_penalty,
        "shortfall_units": shortfall_units,
        "vendor_name": vendor["vendor_name"],
        "contact_email": vendor["contact_email"],
        "unit_cost": float(vendor["unit_cost"]),
        "expedite_fee": float(vendor["expedite_shipping_flat_fee"]),
        "total_expedite_cost": total_expedite_cost,
        "net_savings": net_savings,
        "lead_time_days": int(vendor["lead_time_days"])
    }

if __name__ == "__main__":
    result = run_triage()
    print("--- TRIAGE CALCULATION RESULTS ---")
    for key, value in result.items():
        print(f"{key}: {value}")