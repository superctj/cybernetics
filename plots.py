import os
import pandas as pd
import matplotlib.pyplot as plt
import json


import os
import json
from datetime import datetime

def load_json_files(directory, suffix):
    """Load all JSON files with a given suffix from a directory into a list of dictionaries, sorted by the date and time embedded in the filename."""
    
    json_files = []
    
    # List to hold filenames and their corresponding datetime objects
    files_with_dates = []

    # Iterate over files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(suffix):
            # Extract the date and time part of the filename
            try:
                base_name = filename.replace(suffix, "")  # Remove suffix
                date_str = base_name.split('_')[1] + "_" + base_name.split('_')[2]
                date_obj = datetime.strptime(date_str, '%Y-%m-%d_%H-%M-%S')
                # Append the filename and the corresponding datetime to the list
                files_with_dates.append((filename, date_obj))
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
    
    # Sort the files by the extracted datetime
    files_with_dates.sort(key=lambda x: x[1])

    # Now load the JSON data from the sorted filenames
    for filename, _ in files_with_dates:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r') as file:
            data = json.load(file)
            json_files.append((filename, data))
    
    return json_files


def extract_throughput_data( summary_files):
    """Extract average throughput and best throughput data from the DataFrames and JSON files."""
    throughput_data = []
    best_throughput = []
    current_best_throughput = 0
    throughput_text_lines = []

    for filename, data in summary_files:
        if 'Throughput (requests/second)' in data:
            throughput = data['Throughput (requests/second)']
            current_best_throughput = max(current_best_throughput, throughput)
            best_throughput.append(current_best_throughput)
            throughput_text_lines.append(f"{filename}: {throughput:.2f}")
            throughput_data.append(throughput)

    if len(best_throughput) < len(throughput_data):
        best_throughput.extend([current_best_throughput] * (len(throughput_data) - len(best_throughput)))

    print("Throughput Data: ", throughput_data)
    print("Best Throughput: ", best_throughput)

    return throughput_data, best_throughput, throughput_text_lines

def plot_throughput(throughput_data, best_throughput):
    """Plot the throughput data and the best throughput line."""
    iterations = range(len(throughput_data))

    plt.figure(figsize=(10, 6))
    plt.plot(iterations, throughput_data, label='Throughput', color='blue', marker='o')  # Added marker for visibility
    plt.plot(iterations, best_throughput[:len(iterations)], label='Best Throughput', color='red', marker='^')  # Added marker for visibility
    plt.xlabel('Iteration')
    plt.ylabel('Throughput (requests/second)')
    plt.title('Throughput vs. Iteration')
    plt.legend()
    plt.grid(True)

    # Save the plot with a timestamp
    output_dir = '/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp'
    os.makedirs(output_dir, exist_ok=True)
    current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_filename = os.path.join(output_dir, f'throughput_vs_iteration_{current_time}.png')

    plt.savefig(plot_filename)
    plt.show()

    print(f'Plot saved as {plot_filename}')

def save_throughput_to_file(throughput_text_lines):
    """Save the average throughput of each sample file to a text file."""
    output_dir = '/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp'
    os.makedirs(output_dir, exist_ok=True)
    current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    text_filename = os.path.join(output_dir, f'average_throughput_{current_time}.txt')

    with open(text_filename, 'w') as f:
        for line in throughput_text_lines:
            f.write(line + '\n')

    print(f'Average throughput saved as {text_filename}')

if __name__ == "__main__":
    csv_directory = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"

    summary_files = load_json_files(csv_directory, ".summary.json")
    throughput_data, best_throughput, throughput_text_lines = extract_throughput_data(summary_files)
    print(throughput_data)
    plot_throughput(throughput_data, best_throughput)
    save_throughput_to_file(throughput_text_lines)

