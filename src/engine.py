import pandas as pd

def apply_rules(df, min_fico, max_dti, max_inq, max_delinq):
    """
    Apply underwriting rules to a loan dataframe.
    Returns the dataframe with an 'approved' column.
    """
    approved = (
        (df['fico_range_low'] >= min_fico) &
        (df['dti'] <= max_dti) &
        (df['inq_last_6mths'] <= max_inq) &
        (df['delinq_2yrs'] <= max_delinq)
    )
    
    df = df.copy()
    df['approved'] = approved.astype(int)
    return df


def get_metrics(df):
    """
    Given a dataframe with 'approved' and 'default' columns,
    return key decision engine performance metrics.
    """
    approved = df[df['approved'] == 1]
    total = len(df)
    n_approved = len(approved)
    
    approval_rate = n_approved / total if total > 0 else 0
    default_rate = approved['default'].mean() if n_approved > 0 else 0
    avg_loan = approved['loan_amnt'].mean() if n_approved > 0 else 0
    projected_volume = approved['loan_amnt'].sum() if n_approved > 0 else 0

    return {
        'total_applications': total,
        'approved': n_approved,
        'denied': total - n_approved,
        'approval_rate': round(approval_rate * 100, 1),
        'default_rate': round(default_rate * 100, 1),
        'avg_loan_amount': round(avg_loan, 0),
        'projected_volume': round(projected_volume, 0)
    }


def load_rejected(filepath, nrows=50000):
    """
    Load and clean the rejected loans file.
    Returns a dataframe with normalized column names
    matching the accepted loans schema.
    """
    df = pd.read_csv(filepath, nrows=nrows, low_memory=False)
    
    df = df.rename(columns={
        'Amount Requested': 'loan_amnt',
        'Risk_Score': 'fico_range_low',
        'Debt-To-Income Ratio': 'dti',
        'Employment Length': 'emp_length'
    })
    
    # Clean DTI — remove % sign and convert to float
    df['dti'] = df['dti'].astype(str).str.replace('%', '').str.strip()
    df['dti'] = pd.to_numeric(df['dti'], errors='coerce')
    
    df['Decision'] = 'Rejected (Pre-Engine)'
    
    return df[['loan_amnt', 'fico_range_low', 'dti', 'emp_length', 'Decision']].dropna(subset=['fico_range_low'])