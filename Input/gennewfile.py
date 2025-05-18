import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configuration
products = ["bond", "future", "irdswap", "repo"]
pillars = ["100Y", "10Y", "15Y", "1M", "1W", "1Y", "20Y", "25Y", "2Y", "30Y", "3M", "40Y", "50Y"]
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
n_samples = 2000  # total number of rows to generate

# Helper to generate a random date string in MM/DD/YYYY format
def random_date(start, end):
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime("%m/%d/%Y")

# Generate base rows, one per pillar to ensure coverage
rows = []

for pillar in pillars:
    if pillar == "100Y":
        product = "bond"
    elif pillar == "10Y":
        product = "future"
    else:
        product = random.choice(products)

    pricingdate = random_date(start_date, end_date)
    cv_value = round(random.uniform(0, 1), 4)
    outlier = None if product == "irdswap" else (1 if random.random() < 0.1 else 0)
    auction_date = 1 if random.random() < 0.5 else 0

    rows.append({
        "Product": product,
        "Projected Pillar": pillar,
        "pricingdate": pricingdate,
        "Validated Value Projected CV": cv_value,
        "Outlier": outlier,
        "is Auction Date": auction_date
    })

# Fill remaining rows to reach n_samples
while len(rows) < n_samples:
    pillar = random.choice(pillars)

    if pillar == "100Y":
        product = "bond"
    elif pillar == "10Y":
        product = "future"
    else:
        product = random.choice(products)

    pricingdate = random_date(start_date, end_date)
    cv_value = round(random.uniform(0, 1), 4)
    outlier = None if product == "irdswap" else (1 if random.random() < 0.1 else 0)
    auction_date = 1 if random.random() < 0.5 else 0

    rows.append({
        "Product": product,
        "Projected Pillar": pillar,
        "pricingdate": pricingdate,
        "Validated Value Projected CV": cv_value,
        "Outlier": outlier,
        "Is Auction Date": auction_date
    })

# Build and shuffle DataFrame
df = pd.DataFrame(rows)
df = df.sample(frac=1).reset_index(drop=True)

# Optional: Validate rules
assert all(df[df["Projected Pillar"] == "100Y"]["Product"] == "bond")
assert all(df[df["Projected Pillar"] == "10Y"]["Product"] == "future")

# Preview
print(df.head(20))

# Optional: Save to CSV
# df.to_csv("synthetic_dataset.csv", index=False)


df.to_csv("input/Updated_IR_Delta.csv", index=False)
