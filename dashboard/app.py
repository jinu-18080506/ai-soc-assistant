"""Streamlit dashboard. Start it with:  streamlit run dashboard/app.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from dashboard.data import (  # noqa: E402
    SEVERITY_ORDER,
    alert_label,
    alerts_to_rows,
    filter_alerts,
    find_report,
    severity_counts,
    severity_of,
)
from soc.alert_reader import read_alerts  # noqa: E402
from soc.mitre import technique_links  # noqa: E402

st.set_page_config(page_title="AI SOC Assistant", layout="wide")
st.title("AI SOC Assistant")
st.caption("Triage dashboard: alerts, MITRE ATT&CK mapping and AI incident reports")

# ---- sidebar: where the data lives ----
st.sidebar.header("Data")
alerts_path = st.sidebar.text_input("Alerts file", str(ROOT / "data" / "sample_alerts.jsonl"))
live_reports = ROOT / "reports"
default_reports = live_reports if any(live_reports.glob("*.md")) else ROOT / "docs" / "sample_reports"
reports_dir = st.sidebar.text_input("Reports folder", str(default_reports))

if not Path(alerts_path).is_file():
    st.error(f"Alerts file not found: {alerts_path}")
    st.stop()

alerts = read_alerts(alerts_path)
if not alerts:
    st.warning("No valid alerts in that file.")
    st.stop()

# ---- summary numbers ----
counts = severity_counts(alerts)
columns = st.columns(len(SEVERITY_ORDER) + 1)
columns[0].metric("Total alerts", len(alerts))
for column, name in zip(columns[1:], SEVERITY_ORDER):
    column.metric(name, counts[name])

# ---- filters and table ----
st.subheader("Alerts")
left, right = st.columns([2, 3])
chosen = left.multiselect("Severity", SEVERITY_ORDER, default=SEVERITY_ORDER)
search = right.text_input("Search (rule, host, MITRE ID, log text)")
shown = filter_alerts(alerts, chosen, search)
st.caption(f"Showing {len(shown)} of {len(alerts)} alerts")
if not shown:
    st.info("No alerts match these filters.")
    st.stop()
st.dataframe(alerts_to_rows(shown), hide_index=True)

# ---- one alert in detail ----
st.subheader("Alert detail")
index = st.selectbox("Pick an alert", range(len(shown)), format_func=lambda i: alert_label(shown[i]))
alert = shown[index]
details_tab, report_tab = st.tabs(["Details", "AI incident report"])

with details_tab:
    info, log = st.columns(2)
    with info:
        st.markdown(f"**Severity:** {severity_of(alert)} (rule level {alert.rule.level})")
        st.markdown(f"**Rule:** {alert.rule.id}, {alert.rule.description}")
        st.markdown(f"**Host:** {alert.agent.name} ({alert.agent.ip or 'unknown IP'})")
        st.markdown(f"**Time:** {alert.timestamp.isoformat()}")
        st.markdown("**MITRE ATT&CK:**")
        links = technique_links(alert.rule.mitre)
        if links:
            for technique_id, name, url in links:
                st.markdown(f"- [{technique_id}]({url}) {name}")
        else:
            st.write("None mapped")
    with log:
        st.markdown("**Log**")
        st.code(alert.full_log or "(no log text)", language="text")

with report_tab:
    report = find_report(alert, reports_dir)
    if report is None:
        st.info("No report for this alert yet. Create one with:  python main.py")
    else:
        st.markdown(report.read_text(encoding="utf-8"))
