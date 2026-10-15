# ERP Data Quality & Integration Analytics Platform

A portfolio project inspired by common ERP data analyst responsibilities. It uses synthetic customer data only and is not affiliated with Greif.

## What it does
- Checks missing customer names, countries, and payment terms.
- Flags duplicate customer-name candidates for human review.
- Normalizes common country and payment-term values.
- Checks legacy-to-target customer mappings.
- Exports an issue register, validated mapping file, and summary KPIs.
- Displays results in a Streamlit dashboard.

## Project structure
- `data/`: synthetic source/target/mapping CSV files
- `src/run_analysis.py`: analysis and validation logic
- `src/app.py`: dashboard
- `sql/analysis_queries.sql`: SQL examples
- `results/`: generated outputs

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/run_analysis.py
streamlit run src/app.py
```

## Important limitations
- Sample records and results are illustrative.
- Matching by customer name is only a duplicate *candidate* check, not proof of identity.
- Never auto-merge real customer records based only on names. Validate tax/legal IDs and obtain data-owner approval.
- The quality score is a simple demonstration metric based on six checks per legacy record; it is not an industry-standard score.
