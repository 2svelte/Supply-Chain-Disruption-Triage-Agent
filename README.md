# Supply-Chain-Disruption-Triage-Agent
Automated supply chain disruption triage agent that calculates stockout risks, models SLA penalty trade-offs, and generates emergency purchase orders.

# 🚢 Supply Chain Disruption Triage Agent
**Automating Decision Latency in Inbound Freight Disruption & Mitigation**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_STREAMLIT_APP_URL_HERE)

## The Problem
When inbound container freight is delayed, supply chain planners spend hours manually cross-referencing shipping ETAs, warehouse burn rates, and supplier lead times. This manual analysis latency frequently results in assembly line shutdowns and costly contractual SLA breach penalties before backup parts can be secured.

## The Solution
This tool automates the entire disruption-to-resolution loop in under 30 seconds:
1. **Deterministic Risk Scoring:** Monitors inbound shipment delays against real-time facility inventory burn rates to pinpoint the exact stockout date ($Runout < ETA$).
2. **Cost-to-Resolve Modeling:** Evaluates the trade-off between the cost of inaction (contractual SLA downtime penalties) and the cost of resolution (emergency backup vendor unit premiums and expedited freight fees).
3. **Automated PO Generation:** Utilizes an LLM agent to instantly draft a binding, audit-ready Emergency Purchase Order with pre-calculated shortfall quantities and hard-stop delivery dates.

## Tech Stack
- **Interface:** Streamlit
- **Analytics & Logic:** Python (Pandas, Datetime)
- **Agent Orchestration:** OpenAI API (`gpt-4o-mini`)
- **Data Engine:** Relational tracking schemas (Inbound Freight, Inventory Status, Backup Suppliers)
