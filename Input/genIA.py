import pandas as pd
import numpy as np

# Generate two years of daily dates from 2023-04-26 to 2025-04-25
start = pd.Timestamp('2023-04-26')
end = pd.Timestamp('2025-04-25')
dates = pd.date_range(start, end, freq='D')
n = len(dates)

# Create the DataFrame with constant ProfitCenter and dates
df = pd.DataFrame({
    'AnalyticalStructure.ProfitCenter': ['FICRATG10JGB'] * n,
    'Context.AsOfDate': dates,
})

# Set random seed for reproducibility
np.random.seed(42)

# Define mother level effect variables
mother_vars = [
    'Theta/FIN.DtD',
    'NnM Effect.DtD',
    'Market Effect.DtD'
]

# Define L1 effect variables (existing + two new ones)
l1_vars = [
    'Commo Effect_L1.DtD',
    'Credit Effect_L1.DtD',
    'Eqty Effect_L1.DtD',
    'Forex Effect_L1.DtD',
    'Rates Effect_L1.DtD',
    'CreditSpread Effect_L1.DtD'
]

# Generate L1 effect columns
for var in l1_vars:
    df[var] = np.random.normal(loc=0, scale=1000, size=n)

# Generate mother level effect columns
for var in mother_vars:
    df[var] = np.random.normal(loc=0, scale=1000, size=n) # Using same scale as L1 for mother level

# Define L2 effect variables (sub-components)
l2_vars = [
    'Energy Effect_L2.DtD',
    'Metals Effect_L2.DtD',
    'IG Credit Effect_L2.DtD',
    'HY Credit Effect_L2.DtD',
    'Spot FX Effect_L2.DtD',
    'Forward FX Effect_L2.DtD'
]

# Generate L2 effect columns (smaller scale)
for var in l2_vars:
    df[var] = np.random.normal(loc=0, scale=500, size=n)

# Compute total of all effects
sum_effects = df[mother_vars + l1_vars + l2_vars].sum(axis=1)

# Generate delta based on sum direction
delta_positive = np.random.uniform(0, 50, size=n)
delta_negative = np.random.uniform(50, 150, size=n)
deltas = np.where(sum_effects >= 0, delta_positive, delta_negative)

# Final result, biased to be more often positive
df['PnL Explanation.DTD'] = sum_effects - deltas

# Save full dataset to CSV
csv_path = 'Input/fake_pnl_IA.csv'
df.to_csv(csv_path, index=False)
