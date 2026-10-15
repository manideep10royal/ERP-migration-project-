from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
st.set_page_config(page_title="ERP Data Quality Dashboard", layout="wide")
st.title("ERP Data Quality & Integration Analytics")
st.caption("Portfolio demo using synthetic data; not actual Greif data.")

summary_path = RESULTS / "summary_metrics.csv"
issues_path = RESULTS / "issue_register.csv"
mapping_path = RESULTS / "validated_mapping.csv"

if not summary_path.exists() or not issues_path.exists() or not mapping_path.exists():
    st.warning("Results not found. Run `python src/run_analysis.py` first.")
    st.stop()

summary = pd.read_csv(summary_path)
issues = pd.read_csv(issues_path)
mapping = pd.read_csv(mapping_path)

metrics = dict(zip(summary["metric"], summary["value"]))
c1, c2, c3, c4 = st.columns(4)
c1.metric("Legacy records", int(metrics["Legacy records reviewed"]))
c2.metric("Target records", int(metrics["Target records available"]))
c3.metric("Records requiring review", int(metrics["Records requiring review"]))
c4.metric("Data quality score", f'{metrics["Data quality score (%)"]:.1f}%')

st.subheader("Summary metrics")
st.dataframe(summary, use_container_width=True, hide_index=True)

st.subheader("Issues by category")
if len(issues):
    chart_data = issues.groupby(["issue", "severity"]).size().reset_index(name="issue_count")
    st.bar_chart(chart_data.set_index("issue")["issue_count"])
    severity = st.selectbox("Filter severity", ["All", "High", "Medium", "Low"])
    filtered = issues if severity == "All" else issues[issues["severity"] == severity]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
else:
    st.success("No issues detected in the current sample.")

st.subheader("Validated mapping review")
cols = [c for c in [
    "legacy_customer_id", "customer_name_legacy", "target_customer_id",
    "mapping_status", "review_required", "missing_customer_name",
    "missing_country", "missing_payment_terms", "duplicate_name_candidate"
] if c in mapping.columns]
st.dataframe(mapping[cols], use_container_width=True, hide_index=True)

st.download_button("Download issue register CSV", issues.to_csv(index=False), "issue_register.csv", "text/csv")
