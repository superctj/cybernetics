import os
import pandas as pd
import matplotlib.pyplot as plt
import json

def load_csv_files(directory, suffix):
    """Load all CSV files with a given suffix from a directory into a list of DataFrames."""
    data_frames = []
    for filename in os.listdir(directory):
        if filename.endswith(suffix):
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path)
            data_frames.append((filename, df))
    return data_frames

def load_json_files(directory, suffix):
    """Load all JSON files with a given suffix from a directory into a list of dictionaries."""
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith(suffix):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                data = json.load(file)
                json_files.append((filename, data))
    return json_files

def extract_throughput_data(sample_frames, summary_files):
    """Extract average throughput and best throughput data from the DataFrames and JSON files."""
    throughput_data = []
    throughput_noise_data = []
    best_throughput = []
    current_best_throughput = 0
    throughput_text_lines = []

    # Extract data from sample files
    for filename, df in sample_frames:
        if 'Throughput (requests/second)' in df.columns and 'Throughput with Noise (requests/second)' in df.columns:
            avg_throughput = df['Throughput (requests/second)'].mean()
            avg_throughput_noise = df['Throughput with Noise (requests/second)'].mean()
            throughput_data.append(avg_throughput)
            throughput_noise_data.append(avg_throughput_noise)
            throughput_text_lines.append(f"{filename}: {avg_throughput:.2f} (Original), {avg_throughput_noise:.2f} (Noise)")

            # Update the best throughput value dynamically
            if avg_throughput > current_best_throughput:
                current_best_throughput = avg_throughput
            best_throughput.append(current_best_throughput)

    # Extract best throughput from summary files if it exists (not used currently)
    for filename, data in summary_files:
        if 'Throughput (requests/second)' in data:
            throughput = data['Throughput (requests/second)']
            current_best_throughput = max(current_best_throughput, throughput)

    # If the number of best throughput data points is less than throughput data, fill the rest with the last known best throughput
    if len(best_throughput) < len(throughput_data):
        best_throughput.extend([current_best_throughput] * (len(throughput_data) - len(best_throughput)))

    print("Throughput Data: ", throughput_data)
    print("Throughput Noise Data: ", throughput_noise_data)
    print("Best Throughput: ", best_throughput)

    return throughput_data, throughput_noise_data, best_throughput, throughput_text_lines

def plot_throughput(throughput_data, throughput_noise_data, best_throughput):
    """Plot the throughput data and the best throughput line."""
    iterations = range(len(throughput_data))

    plt.figure(figsize=(10, 6))
    plt.plot(iterations, throughput_data, label='Throughput', color='blue', marker='o')  # Added marker for visibility
    plt.plot(iterations, throughput_noise_data, label='Throughput (Noise)', color='green', marker='x')  # Added marker for visibility
    plt.plot(iterations, best_throughput[:len(iterations)], label='Best Throughput', color='red', marker='^')  # Added marker for visibility
    plt.xlabel('Iteration')
    plt.ylabel('Throughput (requests/second)')
    plt.title('Throughput vs. Iteration')
    plt.legend()
    plt.grid(True)

    # Save the plot with a timestamp
    output_dir = '/home/phdonn/cybernetics_n/exps'
    os.makedirs(output_dir, exist_ok=True)
    current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_filename = os.path.join(output_dir, f'throughput_vs_iteration_{current_time}.png')

    plt.savefig(plot_filename)
    plt.show()

    print(f'Plot saved as {plot_filename}')

def save_throughput_to_file(throughput_text_lines):
    """Save the average throughput of each sample file to a text file."""
    output_dir = '/home/phdonn/cybernetics_n/exps'
    os.makedirs(output_dir, exist_ok=True)
    current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    text_filename = os.path.join(output_dir, f'average_throughput_{current_time}.txt')

    with open(text_filename, 'w') as f:
        for line in throughput_text_lines:
            f.write(line + '\n')

    print(f'Average throughput saved as {text_filename}')

if __name__ == "__main__":
    csv_directory = "/home/phdonn/cybernetics_n/exps/benchbase_tpcc/postgres/bo_gp"

    sample_frames = load_csv_files(csv_directory, ".samples.csv")
    summary_files = load_json_files(csv_directory, ".summary.json")

    throughput_data, throughput_noise_data, best_throughput, throughput_text_lines = extract_throughput_data(sample_frames, summary_files)

    plot_throughput(throughput_data, throughput_noise_data, best_throughput)
    save_throughput_to_file(throughput_text_lines)
