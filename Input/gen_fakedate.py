import csv
import random
from datetime import datetime, timedelta

# Define parameters
num_entries = 180
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
maturities = [
    "2-year JGB", "5-year JGB", "10-year JGB",
    "20-year JGB", "30-year JGB", "40-year JGB"
]

# Generate random dates and random maturities
data = []
for _ in range(num_entries):
    random_date = start_date + timedelta(
        days=random.randint(0, (end_date - start_date).days)
    )
    random_maturity = random.choice(maturities)
    data.append([random_date.strftime('%Y-%m-%d'), random_maturity])

# Write to CSV
csv_filename = "Auction Date.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["EventDate", "Bond Maturity"])
    writer.writerows(data)

print(f"{num_entries} entries written to {csv_filename}")
