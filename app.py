import streamlit as st

from agent import generate_emergency_po
from triage_engine import TriageDataError, load_triage


st.set_page_config(page_title="Supply Chain Disruption Triage", layout="wide")
st.title("Supply Chain Disruption Triage")
st.caption("Deterministic inventory risk analysis with AI-assisted PO drafting")


def money(value):
    return f"${value:,.2f}"


api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("OpenAI API key (optional)", type="password")
st.sidebar.caption("The dashboard works offline with a deterministic PO draft.")

try:
    summary = load_triage()
except (FileNotFoundError, TriageDataError, ValueError) as error:
    st.error(f"Unable to analyze the local workbooks: {error}")
    st.stop()

if not summary["results"]:
    st.success("No delayed shipments were found in the current workbooks.")
    st.stop()

st.subheader("Disruption overview")
overview_one, overview_two, overview_three = st.columns(3)
overview_one.metric("Delayed shipments", summary["delayed_count"])
overview_two.metric("Critical stockout risks", summary["critical_count"])
overview_three.metric(
    "Potential net savings",
    money(sum(item["net_savings"] for item in summary["results"] if item["is_critical"])),
)

labels = [
    f"{item['po_number']} | {item['sku']} | {item['recommendation']}"
    for item in summary["results"]
]
selected_label = st.selectbox("Shipment to investigate", labels)
data = summary["results"][labels.index(selected_label)]

st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Disruption alert")
    if data["is_critical"]:
        st.error("CRITICAL STOCKOUT RISK")
    else:
        st.success("NO STOCKOUT RISK IDENTIFIED")
    st.write(f"**Vessel:** {data['vessel_id']}")
    st.write(f"**Impacted PO:** {data['po_number']}")
    st.write(f"**SKU:** {data['sku']} ({data['part_name']})")
    st.write(f"**Facility:** {data['facility']}")
    st.write(f"**Original ETA:** {data['orig_eta']}")
    st.write(f"**Revised ETA:** {data['revised_eta']} (+{data['delay_days']} days)")
    st.write(f"**Estimated stockout:** {data['stockout_date']}")
    st.metric("Days of supply", data["days_of_supply"])

with col2:
    st.subheader("Financial evaluation")
    st.metric("Estimated SLA penalty", money(data["sla_penalty"]))
    st.metric("Emergency PO + freight", money(data["total_expedite_cost"]))
    st.metric(
        "Projected net savings",
        money(data["net_savings"]),
        delta=money(data["net_savings"]) if data["is_critical"] else None,
    )
    st.write(f"**Shortfall:** {data['shortfall_units']:,} units")
    st.write(f"**Coverage gap:** {data['gap_days']} days")
    st.write(f"**Backup lead time:** {data['lead_time_days']} days")
    st.info(f"Recommendation: {data['recommendation']}")

with col3:
    st.subheader("Actionable output")
    st.write(f"**Backup vendor:** {data['vendor_name']}")
    st.write(f"**Contact:** {data['contact_email']}")
    if data["recommendation"] == "Expedite backup order":
        if st.button("Generate draft PO", type="primary"):
            st.session_state["po_draft"] = generate_emergency_po(data, api_key=api_key)
            st.session_state["po_po_number"] = data["po_number"]
    else:
        st.info("A PO draft is available for critical cases with positive projected savings.")

    if st.session_state.get("po_po_number") == data["po_number"]:
        st.text_area("Draft emergency purchase order", st.session_state["po_draft"], height=300)
        st.download_button(
            "Download draft PO",
            data=st.session_state["po_draft"],
            file_name=f"draft_emergency_po_{data['po_number']}.txt",
            mime="text/plain",
        )
        if st.button("Approve draft for simulation"):
            st.success("Draft approved for demonstration. No external order was submitted.")