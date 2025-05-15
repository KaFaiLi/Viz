import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import platform

# Configurations
products = ["bond", "future", "irdswap"]
pillars = ["100Y", "10Y", "15Y", "1M", "1W", "1Y", "20Y", "25Y", "2Y", "30Y", "3M", "40Y", "50Y"]
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)

# Choose correct date format depending on OS
date_format = "%#m/%#d/%Y" if platform.system() == "Windows" else "%-m/%-d/%Y"

# Create unique product-pillar combinations
combinations = [(p, pi) for p in products for pi in pillars]
max_entries = len(combinations)

# Generate unique pricing dates
def generate_unique_dates(n):
    date_range = (end_date - start_date).days
    selected_days = random.sample(range(date_range), n)
    return [start_date + timedelta(days=day) for day in selected_days]

# Generate dataset
rows = []
unique_dates = generate_unique_dates(max_entries)

for i, (product, pillar) in enumerate(combinations):
    pricingdate = unique_dates[i].strftime(date_format)
    validated_value = round(np.random.uniform(0.0, 100.0), 4)

    # Determine Outlier
    outlier = None
    if product != "irdswap":
        outlier = np.random.choice([0, 1], p=[0.9, 0.1])  # 10% chance of being an outlier

    # Determine is Auction Date
    is_auction = np.random.choice([0, 1], p=[0.5, 0.5])  # 50% chance

    rows.append({
        "Product": product,
        "Projected Pillar": pillar,
        "pricingdate": pricingdate,
        "Validated Value Projected CV": validated_value,
        "Outlier": outlier,
        "Is Auction Date": is_auction
    })

# Create DataFrame
df = pd.DataFrame(rows)

# Shuffle rows
df = df.sample(frac=1).reset_index(drop=True)

# Display head
print(df.head())

# Optional: Export to CSV
df.to_csv("Updated_IR_Delta.csv", index=False)
