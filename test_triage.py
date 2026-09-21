import unittest

import pandas as pd

from agent import generate_emergency_po
from triage_engine import TriageDataError, triage_dataframes


SHIPMENT_COLUMNS = [
    "status", "sku", "original_eta", "revised_eta", "po_number",
    "vessel_id", "destination_port",
]
INVENTORY_COLUMNS = [
    "sku", "part_name", "facility_location", "current_stock",
    "daily_burn_rate", "sla_penalty_per_day",
]
VENDOR_COLUMNS = [
    "sku", "vendor_name", "contact_email", "unit_cost",
    "expedite_shipping_flat_fee", "lead_time_days",
]


def frames(revised_eta="2026-10-09", current_stock=150, burn=50, penalty=12000):
    shipments = pd.DataFrame([[
        "Delayed", "SKU-1", "2026-10-05", revised_eta, "PO-1", "VESSEL-1", "Port A"
    ]], columns=SHIPMENT_COLUMNS)
    inventory = pd.DataFrame([[
        "SKU-1", "Test Part", "Plant A", current_stock, burn, penalty
    ]], columns=INVENTORY_COLUMNS)
    vendors = pd.DataFrame([[
        "SKU-1", "Test Vendor", "orders@test.example", 65, 500, 1
    ]], columns=VENDOR_COLUMNS)
    return shipments, inventory, vendors


class TriageTests(unittest.TestCase):
    def test_critical_case_calculates_savings(self):
        result = triage_dataframes(*frames())["results"][0]
        self.assertTrue(result["is_critical"])
        self.assertEqual(result["gap_days"], 1)
        self.assertEqual(result["shortfall_units"], 50)
        self.assertEqual(result["net_savings"], 8250)

    def test_same_day_arrival_is_not_critical(self):
        result = triage_dataframes(*frames(revised_eta="2026-10-08"))["results"][0]
        self.assertFalse(result["is_critical"])
        self.assertEqual(result["gap_days"], 0)
        self.assertEqual(result["recommendation"], "Monitor inbound shipment")

    def test_no_delays_returns_empty_summary(self):
        shipments, inventory, vendors = frames()
        shipments["status"] = "On Time"
        result = triage_dataframes(shipments, inventory, vendors)
        self.assertEqual(result["results"], [])
        self.assertEqual(result["delayed_count"], 0)

    def test_zero_burn_rate_is_rejected(self):
        with self.assertRaises(TriageDataError):
            triage_dataframes(*frames(burn=0))

    def test_missing_vendor_is_rejected(self):
        shipments, inventory, vendors = frames()
        vendors = vendors.iloc[0:0]
        with self.assertRaises(TriageDataError):
            triage_dataframes(shipments, inventory, vendors)

    def test_offline_po_draft_uses_calculated_values(self):
        result = triage_dataframes(*frames())["results"][0]
        draft = generate_emergency_po(result, api_key="")
        self.assertIn("DRAFT", draft)
        self.assertIn("50 units", draft)
        self.assertIn("$8,250.00", draft)


if __name__ == "__main__":
    unittest.main()
