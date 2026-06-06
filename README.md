# Loan Decision Engine Simulator

A live simulator for testing underwriting rule changes and measuring their impact on loan approval volume, default rate, and projected portfolio risk.

Built to demonstrate decision engine analytics in the context of consumer lending.

**Live App:** [Launch Simulator](https://ninja-decision-engine.streamlit.app)

---

## What It Does

This tool simulates how changes to underwriting rules affect key business outcomes — before those changes go into production.

Adjust four core decisioning rules in real time:

- **Minimum FICO Score** — credit quality floor
- **Maximum DTI (%)** — debt-to-income ceiling
- **Max Inquiries (Last 6 Months)** — recent credit-seeking behavior
- **Max Delinquencies (Last 2 Years)** — recent payment history

The simulator immediately shows the downstream impact on:

- Approval rate vs baseline
- Default rate vs baseline
- Loans approved and denied
- Projected origination volume
- Full FICO distribution across approved, denied, and pre-engine rejected populations

---

## Why This Matters

Every rule change in a lending decision engine is a business trade-off. Tighten the FICO floor and you reduce default risk — but you also turn away borrowers who would have paid. Loosen DTI limits and you grow volume — but you take on more credit risk.

This simulator makes that trade-off visible, measurable, and communicable to both technical and business stakeholders before a single line of production code changes.

---

## Data

Uses the public Lending Club loan dataset (2007–2018):
- `accepted_2007_to_2018Q4.csv` — 50,000 resolved loans (Fully Paid or Charged Off)
- `rejected_2007_to_2018Q4.csv` — 50,000 pre-engine rejections

Data files are excluded from this repo via `.gitignore`. Download from [Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club).

---

## Tech Stack

- Python, pandas
- Streamlit
- Plotly
- scikit-learn (available for future model layer)

---

## Project Structure

```text
ninja-decision-engine/
├── data/               # Local only — not in repo
├── notebooks/          # EDA and analysis
├── src/
│   └── engine.py       # Decision rules and metrics logic
├── app.py              # Streamlit application
└── README.md
```

---

## Author

Chris Ruiz — Pricing & Commercial Analytics  
[GitHub](https://github.com/chrisruiz01) | [LinkedIn](https://linkedin.com/in/chrisruiz01)
