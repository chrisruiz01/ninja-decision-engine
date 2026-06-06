import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(__file__))
from src.engine import apply_rules, get_metrics

st.set_page_config(page_title="Loan Decision Engine Simulator", layout="wide")
st.title("Loan Decision Engine Simulator")
st.markdown("Adjust underwriting rules to see the impact on approval volume and default rate.")

# --- Default baseline rules ---
BASELINE = {
    'min_fico': 660,
    'max_dti': 30,
    'max_inq': 3,
    'max_delinq': 1
}

@st.cache_data
def load_data():
    COLS = [
        'loan_amnt', 'term', 'purpose', 'annual_inc', 'dti',
        'fico_range_low', 'fico_range_high', 'emp_length',
        'home_ownership', 'inq_last_6mths', 'pub_rec',
        'delinq_2yrs', 'int_rate', 'grade', 'loan_status'
    ]
    df = pd.read_csv(
        'data/accepted_2007_to_2018Q4.csv',
        usecols=COLS,
        nrows=50000,
        low_memory=False
    )
    df = df[df['loan_status'].isin(['Fully Paid', 'Charged Off'])]
    df['default'] = (df['loan_status'] == 'Charged Off').astype(int)
    df = df.dropna(subset=['dti'])
    return df

@st.cache_data
def load_rejected_data():
    from src.engine import load_rejected
    return load_rejected('data/rejected_2007_to_2018Q4.csv', nrows=50000)


df = load_data()

# --- Sidebar: Rule Controls ---
st.sidebar.header("Underwriting Rules")
st.sidebar.markdown("*Baseline values shown as defaults*")

min_fico = st.sidebar.slider(
    "Minimum FICO Score",
    min_value=600, max_value=800,
    value=BASELINE['min_fico'], step=5
)
max_dti = st.sidebar.slider(
    "Maximum DTI (%)",
    min_value=5, max_value=50,
    value=BASELINE['max_dti'], step=1
)
max_inq = st.sidebar.slider(
    "Max Inquiries (Last 6 Months)",
    min_value=0, max_value=10,
    value=BASELINE['max_inq'], step=1
)
max_delinq = st.sidebar.slider(
    "Max Delinquencies (Last 2 Years)",
    min_value=0, max_value=5,
    value=BASELINE['max_delinq'], step=1
)

# --- Apply Rules ---
baseline_result = apply_rules(
    df,
    BASELINE['min_fico'],
    BASELINE['max_dti'],
    BASELINE['max_inq'],
    BASELINE['max_delinq']
)
current_result = apply_rules(df, min_fico, max_dti, max_inq, max_delinq)
current_result['Decision'] = current_result['approved'].map({1: 'Approved', 0: 'Denied'})

baseline_metrics = get_metrics(baseline_result)
current_metrics = get_metrics(current_result)

# --- Delta calculations ---
def delta(current, baseline):
    diff = current - baseline
    return f"+{diff}" if diff > 0 else str(diff)

def delta_pct(current, baseline):
    diff = round(current - baseline, 1)
    return f"+{diff}%" if diff > 0 else f"{diff}%"

# --- Metrics Row ---
st.subheader("Decision Engine Output")
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Approval Rate",
    f"{current_metrics['approval_rate']}%",
    delta_pct(current_metrics['approval_rate'], baseline_metrics['approval_rate'])
)
col2.metric(
    "Default Rate",
    f"{current_metrics['default_rate']}%",
    delta_pct(current_metrics['default_rate'], baseline_metrics['default_rate']),
    delta_color="inverse"
)
col3.metric(
    "Loans Approved",
    f"{current_metrics['approved']:,}",
    delta(current_metrics['approved'], baseline_metrics['approved'])
)
col4.metric(
    "Projected Volume",
    f"${current_metrics['projected_volume']:,.0f}",
    delta(current_metrics['projected_volume'], baseline_metrics['projected_volume'])
)

# --- Plain English Recommendation ---
st.subheader("Rule Change Analysis")

approval_delta = current_metrics['approval_rate'] - baseline_metrics['approval_rate']
default_delta = current_metrics['default_rate'] - baseline_metrics['default_rate']

if approval_delta == 0 and default_delta == 0:
    st.info("Rules match baseline. Adjust sliders to simulate a rule change.")
elif approval_delta < 0 and default_delta < 0:
    st.success(
        f"Tightening rules reduced approval rate by {abs(approval_delta):.1f}% "
        f"and cut default rate by {abs(default_delta):.1f}%. "
        f"Trade-off: fewer loans originated, lower credit risk."
    )
elif approval_delta > 0 and default_delta > 0:
    st.warning(
        f"Loosening rules increased approval rate by {approval_delta:.1f}% "
        f"but raised default rate by {default_delta:.1f}%. "
        f"Trade-off: more volume, higher credit risk."
    )
else:
    st.info(
        f"Approval rate changed by {approval_delta:+.1f}%, "
        f"default rate changed by {default_delta:+.1f}%."
    )

# --- Charts ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Approved vs Denied")
    fig1 = px.bar(
        x=["Approved", "Denied"],
        y=[current_metrics['approved'], current_metrics['denied']],
        color=["Approved", "Denied"],
        color_discrete_map={"Approved": "#2ecc71", "Denied": "#e74c3c"}
    )
    st.plotly_chart(fig1, width='stretch')

with col_right:
    st.subheader("Default Rate by Loan Grade (Approved Loans)")
    approved_df = current_result[current_result['approved'] == 1]
    grade_default = approved_df.groupby('grade')['default'].mean().reset_index()
    grade_default.columns = ['grade', 'default_rate']
    grade_default['default_rate'] = (grade_default['default_rate'] * 100).round(1)
    grade_default = grade_default.sort_values('grade')

    fig2 = px.bar(
        grade_default, x='grade', y='default_rate',
        color='default_rate',
        color_continuous_scale='Reds',
        labels={'default_rate': 'Default Rate (%)'}
    )
    st.plotly_chart(fig2, width='stretch')

# --- FICO Distribution: Full Population ---
st.subheader("FICO Score Distribution: Full Application Population")

rejected_df = load_rejected_data()

# Build accepted population with Decision label
accepted_fico = current_result[['fico_range_low', 'Decision']].copy()

# Combine accepted (approved + denied by our rules) with pre-engine rejected
fico_combined = pd.concat([
    accepted_fico,
    rejected_df[['fico_range_low', 'Decision']]
], ignore_index=True)

fig3 = px.histogram(
    fico_combined,
    x='fico_range_low',
    color='Decision',
    barmode='overlay',
    opacity=0.7,
    color_discrete_map={
        'Approved': '#2ecc71',
        'Denied': '#e74c3c',
        'Rejected (Pre-Engine)': '#f39c12'
    },
    labels={'fico_range_low': 'FICO Score'}
)
fig3.update_xaxes(range=[min_fico - 40, fico_combined['fico_range_low'].max() + 10])
st.plotly_chart(fig3, width='stretch')


# --- Scenario Comparison Table ---
st.subheader("Scenario Comparison: Baseline vs Current Rules")

comparison = pd.DataFrame({
    'Metric': [
        'Approval Rate (%)',
        'Default Rate (%)',
        'Loans Approved',
        'Loans Denied',
        'Projected Volume ($)'
    ],
    'Baseline': [
        baseline_metrics['approval_rate'],
        baseline_metrics['default_rate'],
        baseline_metrics['approved'],
        baseline_metrics['denied'],
        baseline_metrics['projected_volume']
    ],
    'Current Rules': [
        current_metrics['approval_rate'],
        current_metrics['default_rate'],
        current_metrics['approved'],
        current_metrics['denied'],
        current_metrics['projected_volume']
    ]
})

comparison['Delta'] = comparison['Current Rules'] - comparison['Baseline']
comparison['Delta'] = comparison['Delta'].apply(
    lambda x: f"+{x:,.1f}" if x > 0 else f"{x:,.1f}"
)
comparison['Baseline'] = comparison['Baseline'].apply(lambda x: f"{x:,.1f}")
comparison['Current Rules'] = comparison['Current Rules'].apply(lambda x: f"{x:,.1f}")

st.dataframe(comparison, width='stretch', hide_index=True)