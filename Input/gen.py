import pandas as pd
import numpy as np

# Define all risk metrics and their indicators
risk_metrics = [
    ('CREDIT DELTA', 'CredBpv'),
    ('CREDIT DELTA', 'CredBpv10Y'),
    ('CREDIT DELTA', 'CredBpv3Y'),
    ('VAR', 'VaR'),
    ('FTQ', 'SOVFutureJapan'),
    ('BASIS DELTA', 'BASISSensiByCurrencyByPillar[EUR][1W]'),
    ('BASIS DELTA', 'BASISSensiByCurrencyByPillar[JPY][1W]'),
    ('BASIS DELTA', 'BASISSensiByCurrency[EUR]'),
    ('BASIS DELTA', 'BASISSensiByCurrency[JPY]'),
    # FTQ additional metrics
    ('FTQ', 'FTQ'),
    ('FTQ', 'FTQ1M'),
    ('FTQ', 'FTQ5Y'),
    ('FTQ', 'FTQ10Y'),
    ('FTQ', 'FTQglobJapan'),
    ('FTQ', 'FTQglobJapan1M'),
    ('FTQ', 'FTQglobJapan3Y'),
    ('FTQ', 'FTQglobJapan5Y'),
    ('FTQ', 'FTQJapan'),
    ('FTQ', 'FTQJapan2W'),
    ('FTQ', 'FTQJapan3Y'),
    # FX additional metrics
    ('FX', 'FX'),
    ('FX', 'FXUSD'),
    ('FX', 'FXEUR'),
    ('FX', 'FXJPY'),
    ('FX', 'FXOther')
]

# Define all nodes
nodes = ['FICRATG10JGB', 'FICASIRATFLO']

# Create date range for Q1 2023
dates = pd.date_range(start='2023-01-01', end='2023-03-31')

# Generate the data
data = []
for date in dates:
    for indicator, metric in risk_metrics:
        for node in nodes:
            # Random limit values only for VAR
            lim_max = np.nan
            lim_min = np.nan
            if indicator == 'VAR':
                lim_max = round(np.random.uniform(5e6, 1.5e7), 2)
                lim_min = round(np.random.uniform(1e6, 7e6), 2)
            
            record = {
                'limId': np.random.randint(200000, 700000),
                'rmRiskIndicator': indicator,
                'rmRiskMetricName': metric,
                'stranaNodeName': node,
                'consoValue': round(np.random.uniform(-1e7, 2e7), 2),
                'Date': date.strftime('%#m/%#d/%Y'),  # Use '%#m/%#d/%Y' on Windows
                'consoMreMetricName': metric,
                'limMaxValue': lim_max if not np.isnan(lim_max) else '',
                'limMinValue': lim_min if not np.isnan(lim_min) else ''
            }
            data.append(record)

# Convert to DataFrame
df = pd.DataFrame(data)

df.to_csv("Input/fake_data.csv", index=False)

print("Generated")