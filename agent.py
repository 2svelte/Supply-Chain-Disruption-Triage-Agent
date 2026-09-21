import os

from openai import OpenAI


def _draft_template(data):
    return f"""Subject: DRAFT - Emergency backup order for {data['sku']}

To: {data['contact_email']}

Hello {data['vendor_name']} Order Fulfillment,

Please confirm availability for the following emergency backup order. This is a draft for internal approval and has not been submitted.

SKU: {data['sku']} - {data['part_name']}
Quantity: {data['shortfall_units']:,} units
Unit price: ${data['unit_cost']:,.2f}
Expedited freight: ${data['expedite_fee']:,.2f}
Estimated total: ${data['total_expedite_cost']:,.2f}
Ship to: {data['facility']}
Required delivery: On or before {data['stockout_date']}

Internal financial justification: Avoids an estimated ${data['sla_penalty']:,.2f} in downtime penalties. Projected net savings are ${data['net_savings']:,.2f}.

Please provide confirmation and earliest delivery availability for approval.

Regards,
Supply Chain Operations
"""


def generate_emergency_po(triage_data: dict, api_key: str = None) -> str:
    """Generate a draft PO with an offline template fallback."""
    required_fields = {
        "vendor_name", "contact_email", "sku", "part_name", "facility",
        "shortfall_units", "unit_cost", "expedite_fee", "total_expedite_cost",
        "stockout_date", "sla_penalty", "net_savings",
    }
    missing = required_fields - set(triage_data)
    if missing:
        raise ValueError(f"Cannot draft PO; missing fields: {', '.join(sorted(missing))}")

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        return _draft_template(triage_data)

    prompt = f"""Draft a concise emergency purchase order email using only these calculated facts:
Supplier: {triage_data['vendor_name']} ({triage_data['contact_email']})
SKU: {triage_data['sku']} - {triage_data['part_name']}
Quantity: {triage_data['shortfall_units']} units
Unit cost: ${triage_data['unit_cost']:.2f}
Expedited freight: ${triage_data['expedite_fee']:.2f}
Total estimated cost: ${triage_data['total_expedite_cost']:.2f}
Destination: {triage_data['facility']}
Required delivery date: {triage_data['stockout_date']}
Avoided SLA penalty: ${triage_data['sla_penalty']:.2f}
Projected net savings: ${triage_data['net_savings']:.2f}

Label it clearly as a DRAFT FOR INTERNAL APPROVAL. Do not claim that it was submitted, paid, or dispatched. Do not change any quantity, date, or financial value."""

    try:
        client = OpenAI(api_key=key, timeout=30.0)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional logistics and procurement operations specialist."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content.strip() if content else _draft_template(triage_data)
    except Exception:
        return _draft_template(triage_data)