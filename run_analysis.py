"""
Greif-style ERP Data Quality & Integration Analytics Platform
Portfolio demo using synthetic data only. Not affiliated with or using Greif data.
Run from project root:
    pip install -r requirements.txt
    python src/run_analysis.py
    streamlit run src/app.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

COUNTRY_MAP = {
    "india": "IN", "in": "IN",
    "usa": "US", "united states": "US", "us": "US",
    "uk": "GB", "united kingdom": "GB", "gb": "GB",
}
PAYMENT_MAP = {
    "30 days": "Net 30", "net 30": "Net 30",
    "45 days": "Net 45", "net 45": "Net 45",
    "60 days": "Net 60", "net 60": "Net 60",
}

def clean_text(series):
    return series.astype("string").str.strip()

def main():
    legacy = pd.read_csv(DATA / "legacy_customers.csv")
    target = pd.read_csv(DATA / "target_customers.csv")
    mapping = pd.read_csv(DATA / "customer_mapping.csv")

    # Normalize text and codes
    for col in ["customer_name", "country", "payment_terms", "status"]:
        legacy[col] = clean_text(legacy[col])
        target[col] = clean_text(target[col])
    legacy["country_normalized"] = legacy["country"].str.lower().map(COUNTRY_MAP)
    target["country_normalized"] = target["country"].str.lower().map(COUNTRY_MAP)
    legacy["payment_terms_normalized"] = legacy["payment_terms"].str.lower().map(PAYMENT_MAP)
    target["payment_terms_normalized"] = target["payment_terms"].str.lower().map(PAYMENT_MAP)

    # Data quality checks
    legacy["missing_customer_name"] = legacy["customer_name"].isna() | legacy["customer_name"].eq("")
    legacy["missing_country"] = legacy["country"].isna() | legacy["country"].eq("")
    legacy["missing_payment_terms"] = legacy["payment_terms"].isna() | legacy["payment_terms"].eq("")
    legacy["duplicate_name_candidate"] = (
        legacy["customer_name"].fillna("").str.lower().duplicated(keep=False)
        & legacy["customer_name"].notna()
    )
    legacy["invalid_country_code"] = legacy["country_normalized"].isna() & legacy["country"].notna()
    legacy["invalid_payment_terms"] = legacy["payment_terms_normalized"].isna() & legacy["payment_terms"].notna()

    # Mapping validation
    merged = legacy.merge(mapping, on="legacy_customer_id", how="left")
    merged = merged.merge(
        target[["target_customer_id", "customer_name", "country_normalized", "payment_terms_normalized"]],
        on="target_customer_id", how="left", suffixes=("_legacy", "_target")
    )
    merged["mapping_missing"] = merged["target_customer_id"].isna()
    merged["mapping_to_unknown_target"] = (
        merged["target_customer_id"].notna()
        & merged["customer_name_target"].isna()
    )
    merged["review_required"] = (
        merged["missing_customer_name"]
        | merged["missing_country"]
        | merged["missing_payment_terms"]
        | merged["duplicate_name_candidate"]
        | merged["invalid_country_code"]
        | merged["invalid_payment_terms"]
        | merged["mapping_missing"]
        | merged["mapping_to_unknown_target"]
        | merged["mapping_status"].astype("string").str.contains("review|validate|unmapped", case=False, na=False)
    )

    # Issue register with one row per issue
    issue_rows = []
    checks = [
        ("Missing customer name", "missing_customer_name", "High", "Obtain verified legal/customer name before migration."),
        ("Missing country", "missing_country", "Medium", "Confirm country with source business owner."),
        ("Missing payment terms", "missing_payment_terms", "Medium", "Confirm payment terms against approved contract/master data."),
        ("Duplicate customer candidate", "duplicate_name_candidate", "High", "Compare tax/legal identifiers and obtain approval before consolidation."),
        ("Unrecognized country", "invalid_country_code", "Medium", "Map source country value to approved ISO-style code."),
        ("Unrecognized payment terms", "invalid_payment_terms", "Medium", "Map to approved payment terms after business validation."),
        ("Missing target mapping", "mapping_missing", "High", "Assign target customer or formally exclude from migration."),
        ("Target ID not found", "mapping_to_unknown_target", "High", "Check target ID against target master data."),
    ]
    for label, col, severity, action in checks:
        for _, row in merged[merged[col]].iterrows():
            issue_rows.append({
                "legacy_customer_id": row["legacy_customer_id"],
                "customer_name": row["customer_name_legacy"],
                "issue": label,
                "severity": severity,
                "recommended_action": action
            })
    issues = pd.DataFrame(issue_rows, columns=[
        "legacy_customer_id", "customer_name", "issue", "severity", "recommended_action"
    ])

    # Simple, transparent score: percentage of checks passed across 6 checks per source record.
    quality_checks = [
        ~merged["missing_customer_name"],
        ~merged["missing_country"],
        ~merged["missing_payment_terms"],
        ~merged["duplicate_name_candidate"],
        ~merged["invalid_country_code"],
        ~merged["invalid_payment_terms"],
    ]
    total_checks = len(merged) * len(quality_checks)
    passed_checks = sum(int(x.sum()) for x in quality_checks)
    quality_score = round(100 * passed_checks / total_checks, 1) if total_checks else 0

    summary = pd.DataFrame([
        ["Legacy records reviewed", len(legacy)],
        ["Target records available", len(target)],
        ["Records with missing customer name", int(merged["missing_customer_name"].sum())],
        ["Records with missing country", int(merged["missing_country"].sum())],
        ["Records with missing payment terms", int(merged["missing_payment_terms"].sum())],
        ["Duplicate customer candidates (records)", int(merged["duplicate_name_candidate"].sum())],
        ["Records with unrecognized country", int(merged["invalid_country_code"].sum())],
        ["Records with unrecognized payment terms", int(merged["invalid_payment_terms"].sum())],
        ["Records without target mapping", int(merged["mapping_missing"].sum())],
        ["Records requiring review", int(merged["review_required"].sum())],
        ["Open issue instances", len(issues)],
        ["Data quality score (%)", quality_score],
    ], columns=["metric", "value"])

    # Export results
    merged.to_csv(RESULTS / "validated_mapping.csv", index=False)
    issues.to_csv(RESULTS / "issue_register.csv", index=False)
    summary.to_csv(RESULTS / "summary_metrics.csv", index=False)

    print("\n=== ERP DATA QUALITY SUMMARY ===")
    print(summary.to_string(index=False))
    print("\n=== ISSUE REGISTER (first 20 rows) ===")
    print(issues.head(20).to_string(index=False))
    print(f"\nSaved results to: {RESULTS}")

if __name__ == "__main__":
    main()
