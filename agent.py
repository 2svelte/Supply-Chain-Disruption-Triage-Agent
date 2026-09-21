import os
from openai import OpenAI

def generate_emergency_po(triage_data: dict, api_key: str = None) -> str:
    # Fall back to environment variable if no key passed directly
    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    prompt = f"""
    You are an enterprise Supply Chain Disruption Triage Agent.
    Generate a concise, professional, and binding Emergency Purchase Order email based on these exact operational metrics:

    - Target Supplier: {triage_data['vendor_name']} (Contact: {triage_data['contact_email']})
    - Impacted SKU: {triage_data['sku']} - {triage_data['part_name']}
    - Destination Facility: {triage_data['facility']}
    - Units Required: {triage_data['shortfall_units']} units
    - Contracted Unit Cost: ${triage_data['unit_cost']:.2f}
    - Expedited Freight Surcharge: ${triage_data['expedite_fee']:.2f}
    - Total Order Cost: ${triage_data['total_expedite_cost']:.2f}
    - Required Delivery Date: On or before {triage_data['stockout_date']}

    Guidelines:
    1. Address the email directly to {triage_data['vendor_name']} Order Fulfillment.
    2. Clearly list the line items, agreed unit price, expediting surcharge, and total cost.
    3. Specify that delivery must occur on or before {triage_data['stockout_date']} to prevent factory downtime.
    4. Conclude with an internal audit note:
       "Internal Financial Justification: Avoids estimated ${triage_data['sla_penalty']:,.2f} in downtime penalties with projected net savings of ${triage_data['net_savings']:,.2f}."
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional logistics and procurement operations specialist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content