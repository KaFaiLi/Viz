import pandas as pd
import random
from datetime import datetime, timedelta
import os
import platform

# Set seed for reproducibility
random.seed(42)

# Define parameters
num_rows = 300
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 3, 31)
date_range = pd.date_range(start=start_date, end=end_date, freq='3D')

global_product_names = [
    "xone_bond", "bondfuture", "slbond", "xone_irdswap", "repo", 
    "bond", "xone_bondfuture", "irdswap"
]

projected_pillars = ["2Y", "6M", "1Y", "3M", "100Y", "50Y"]

# Choose date format depending on OS
if os.name == "nt":  # Windows
    date_format = "%#m/%#d/%Y"
else:  # Unix/Linux/Mac
    date_format = "%-m/%-d/%Y"

# Generate the dataset
data = {
    "Global Product Name": [random.choice(global_product_names) for _ in range(num_rows)],
    "Projected Pillar": [random.choice(projected_pillars) for _ in range(num_rows)],
    "pricingdate": [random.choice(date_range).strftime(date_format) for _ in range(num_rows)],
    "Validated Value Projected CV": [round(random.uniform(0.001, 5.0), 9) for _ in range(num_rows)],
}

df = pd.DataFrame(data)

# Ensure the output directory exists
output_dir = "Input"
os.makedirs(output_dir, exist_ok=True)

# Save to CSV
csv_path = os.path.join(output_dir, "IR Delta 2023-20250314.csv")
df.to_csv(csv_path, index=False)

print(f"CSV file saved to: {csv_path}")


import pandas as pd
import random
from datetime import datetime, timedelta
import os
import platform

# Set seed for reproducibility
random.seed(42)

# Define parameters
num_rows = 300
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 3, 31)
date_range = pd.date_range(start=start_date, end=end_date, freq='3D')

global_product_names = [
    "xone_bond", "bondfuture", "bondfuture",
    "bond", "xone_bondfuture"
]

projected_pillars = ["2Y", "6M", "1Y", "3M", "100Y", "50Y"]

# Choose date format depending on OS
if os.name == "nt":  # Windows
    date_format = "%#m/%#d/%Y"
else:  # Unix/Linux/Mac
    date_format = "%-m/%-d/%Y"

# Generate the dataset
data = {
    "Global Product Name": [random.choice(global_product_names) for _ in range(num_rows)],
    "Projected Pillar": [random.choice(projected_pillars) for _ in range(num_rows)],
    "pricingdate": [random.choice(date_range).strftime(date_format) for _ in range(num_rows)],
    "Validated Value Projected CV": [round(random.uniform(0.001, 5.0), 9) for _ in range(num_rows)],
}

df = pd.DataFrame(data)

# Ensure the output directory exists
output_dir = "Input"
os.makedirs(output_dir, exist_ok=True)

# Save to CSV
csv_path = os.path.join(output_dir, "FTQ 2023-20250314.csv")
df.to_csv(csv_path, index=False)

print(f"CSV file saved to: {csv_path}")
