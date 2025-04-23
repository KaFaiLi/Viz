import pandas as pd
import numpy as np

# Parameters
N = 500 # Number of fake records

# Possible values based on example
rmRiskIndicators = ['CREDIT DELTA', 'VAR', 'FTQ', 'BASIS DELTA']
rmRiskMetricNames = ['CredBpv', 'CredBpv10Y', 'CredBpv3Y', 'VaR', 'SOVFutureJapan', 
                     'BASISSensiByCurrencyByPillar', 'BASISSensiByCurrency']
stranaNodeNames = ['FICRATG10JGB', 'FICASIRATFLO', 'FICRATG10FUT', 'FICRATG5YJPY', 'FICASIRATG30']
dates = pd.date_range(start='2023-01-01', end='2023-03-31').to_pydatetime().tolist()

# Generate data
data = []
for _ in range(N):
    indicator = np.random.choice(rmRiskIndicators)
    metric = np.random.choice(rmRiskMetricNames)
    
    # Determine consoMreMetricName
    if 'Pillar' in metric:
        suffix = np.random.choice(['[EUR][1W]', '[JPY][1W]'])
        conso_metric = f"{metric}{suffix}"
    elif 'Currency' in metric:
        suffix = np.random.choice(['[EUR]', '[JPY]'])
        conso_metric = f"{metric}{suffix}"
    elif metric in ['CredBpv', 'CredBpv10Y', 'CredBpv3Y', 'SOVFutureJapan']:
        conso_metric = metric
    else:
        conso_metric = ''
    
    # lim values
    lim_max = np.nan if indicator != 'VAR' else np.round(np.random.uniform(5e6, 1.5e7), 2)
    lim_min = np.nan if indicator != 'VAR' else np.round(np.random.uniform(1e6, 7e6), 2)
    
    record = {
        'limId': np.random.randint(200000, 700000),
        'rmRiskIndicator': indicator,
        'rmRiskMetricName': metric,
        'stranaNodeName': np.random.choice(stranaNodeNames),
        'consoValue': np.round(np.random.uniform(-1e7, 2e7), 2),
        'Date': np.random.choice(dates).strftime('%-m/%-d/%Y'),
        'consoMreMetricName': conso_metric,
        'limMaxValue': lim_max if not np.isnan(lim_max) else '',
        'limMinValue': lim_min if not np.isnan(lim_min) else ''
    }
    data.append(record)

df = pd.DataFrame(data)
df.to_csv('fake_data.csv', index=False)