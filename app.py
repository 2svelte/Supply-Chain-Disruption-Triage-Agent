import streamlit as st
from triage_engine import run_triage
from agent import generate_emergency_po

st.set_page_config(page_title="Supply Chain Disruption Triage", layout="wide")

st.title("Supply Chain Disruption Triage Agent")
st.caption("Operational Impact Analysis & Automated Mitigation")

# API Key handling (reads from .streamlit/secrets.toml or UI input)
api_key = st.secrets.get("OPENAI_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

# Run calculation
data = run_triage()

if not data:
    st.info("No active delayed shipments requiring intervention.")
else:
    col1, col2, col3 = st.columns(3)

    # Column 1: Alert & Risk
    with col1:
        st.subheader("⚠️ Disruption Alert")
        st.error("CRITICAL STOCKOUT RISK")
        st.write(f"**Vessel:** {data['vessel_id']}")
        st.write(f"**Impacted PO:** {data['po_number']}")
        st.write(f"**SKU:** {data['sku']} ({data['part_name']})")
        st.write(f"**Destination:** {data['facility']}")
        st.write(f"**Original ETA:** {data['orig_eta']}")
        st.write(f"**Revised ETA:** {data['revised_eta']} (+{data['delay_days']} days)")
        st.write(f"**Estimated Stockout:** {data['stockout_date']}")

    # Column 2: Financial Trade-off
    with col2:
        st.subheader("💵 Financial Evaluation")
        st.metric(label="Cost of Inaction (SLA Downtime)", value=f"${data['sla_penalty']:,.2f}")
        st.metric(label="Emergency PO + Freight Cost", value=f"${data['total_expedite_cost']:,.2f}")
        st.metric(label="Projected Net Savings", value=f"${data['net_savings']:,.2f}", delta=f"+${data['net_savings']:,.2f}")
        st.info("Recommendation: Expedite partial order with domestic supplier.")

    # Column 3: AI Generated Output
    with col3:
        st.subheader("📄 Actionable Output")
        if st.button("Generate Mitigation Plan & PO", type="primary"):
            if not api_key:
                st.warning("Please provide an OpenAI API key in the sidebar or secrets.")
            else:
                with st.spinner("Agent drafting purchase order..."):
                    po_text = generate_emergency_po(data, api_key=api_key)
                    st.text_area("Draft Emergency Purchase Order", po_text, height=320)
                    if st.button("Execute Mitigation Plan"):
                        st.success("Purchase order dispatched to vendor and logged to ERP.")