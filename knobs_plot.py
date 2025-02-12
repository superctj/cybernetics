import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Directories
json_dir = "/home/boyuann/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
output_dir = "/home/boyuann/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/plots"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# List of knobs to track
target_knobs = ["shared_buffers", "effective_cache_size", "max_connections","work_mem"]

# Regex pattern to extract timestamp from filenames
pattern = re.compile(r"ycsb_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.params\.json")

# Function to convert memory values (e.g., "128MB", "4GB") to MB
def convert_to_mb(value):
    if isinstance(value, (int, float)):  # Already numeric
        return value  
    if isinstance(value, str):
        match = re.match(r"(\d+(?:\.\d+)?)([KMG]B)?", value, re.IGNORECASE)
        if match:
            num, unit = match.groups()
            num = float(num)
            unit = unit.upper() if unit else ""
            if unit == "KB":
                return num / 1024  # Convert KB to MB
            elif unit == "MB":
                return num  # Already in MB
            elif unit == "GB":
                return num * 1024  # Convert GB to MB
            else:
                return np.nan  # Unrecognized format
    return np.nan  # Conversion failed

# Collect and sort JSON files by timestamp
json_files = []
for f in os.listdir(json_dir):
    match = pattern.match(f)
    if match:
        timestamp = match.group(1)  # Extract timestamp from filename
        json_files.append((timestamp, f))

# Sort files by extracted timestamp
json_files.sort()

# Print file names in sorted order
print("Processing files in order:")
for idx, (timestamp, filename) in enumerate(json_files, start=1):
    print(f"Iteration {idx}: {filename}")

# Collect numeric knob data
data = []
iteration_numbers = list(range(1, len(json_files) + 1))  # Replace timestamps with iteration numbers

for _, file in json_files:
    file_path = os.path.join(json_dir, file)
    with open(file_path, "r") as f:
        config = json.load(f)
        numeric_config = {}

        for key in target_knobs:
            if key in config:
                try:
                    if key in ["shared_buffers", "effective_cache_size", "work_mem"]:
                        numeric_config[key] = convert_to_mb(config[key])  # Convert memory values to MB
                    else:
                        numeric_config[key] = int(config[key])  # Convert max_connections to integer
                except (ValueError, TypeError):
                    numeric_config[key] = np.nan  # Ignore non-numeric values

        data.append(numeric_config)

# Convert to DataFrame
df = pd.DataFrame(data, index=iteration_numbers)

# Remove columns that have all NaN values
df = df.dropna(axis=1, how="all")

# Print extracted values for debugging
print("\nExtracted Numeric Values:")
print(df)

# Plot and save each selected knob separately
for column in df.columns:
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df[column], marker='o', linestyle='-', label=column, alpha=0.8)
    plt.xticks(df.index)  # Set x-axis to iteration numbers
    plt.xlabel("Iteration")
    plt.ylabel("Value (MB for Memory Knobs, Count for max_connections)")
    plt.title(f"Changes in {column} Over Iterations")
    plt.legend()
    plt.grid(True)

    # Save the figure
    plot_path = os.path.join(output_dir, f"{column}.png")
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()  # Close the plot to save memory

    print(f"Saved plot: {plot_path}")

print("All selected knob plots saved successfully.")