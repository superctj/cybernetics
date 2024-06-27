import os
import pandas as pd
import matplotlib.pyplot as plt

def load_csv_files(directory):
    """Load all .samples.csv files from a given directory into a list of DataFrames."""
    data_frames = []
    for filename in os.listdir(directory):
        if filename.endswith(".samples.csv"):
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path)
            data_frames.append((filename, df))
    return data_frames

def extract_throughput_data(data_frames):
    """Extract average throughput data from the DataFrames."""
    throughput_data = []
    throughput_text_lines = []

    for filename, df in data_frames:
        # Assuming the throughput data is in a column named 'Throughput (requests/second)'
        if 'Throughput (requests/second)' in df.columns:
            avg_throughput = df['Throughput (requests/second)'].mean()
            throughput_data.append(avg_throughput)
            throughput_text_lines.append(f"{filename}: {avg_throughput:.2f}")

    return throughput_data, throughput_text_lines

def plot_average_throughput(avg_throughput_data):
    """Plot the average throughput data for every 5 iterations."""
    avg_iterations = range(len(avg_throughput_data))

    plt.figure(figsize=(10, 6))
    plt.plot(avg_iterations, avg_throughput_data, label='Avg Throughput (every 5 iter)', color='green')
    plt.xlabel('Iteration (grouped by 5)')
    plt.ylabel('Throughput (requests/second)')
    plt.title('Average Throughput vs. Iteration (every 5 iterations)')
    plt.legend()
    plt.grid(True)

    # Save the plot with a timestamp
    output_dir = '/home/phdonn/cybernetics/exps'
    os.makedirs(output_dir, exist_ok=True)
    current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_filename = os.path.join(output_dir, f'avg_throughput_vs_iteration_{current_time}.png')

    plt.savefig(plot_filename)
    plt.show()

    print(f'Plot saved as {plot_filename}')

def save_throughput_to_file(throughput_text_lines):
    """Save the average throughput of each sample file to a text file."""
    output_dir = '/home/phdonn/cybernetics/exps'
    os.makedirs(output_dir, exist_ok=True)
    current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    text_filename = os.path.join(output_dir, f'average_throughput_{current_time}.txt')

    with open(text_filename, 'w') as f:
        for line in throughput_text_lines:
            f.write(line + '\n')

    print(f'Average throughput saved as {text_filename}')

def calculate_average_every_n_iterations(data, n):
    """Calculate the average throughput for every n iterations."""
    avg_data = []
    for i in range(0, len(data), n):
        avg_data.append(sum(data[i:i+n]) / n)
    return avg_data

if __name__ == "__main__":
    csv_directory = "/home/phdonn/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
    data_frames = load_csv_files(csv_directory)
    throughput_data, throughput_text_lines = extract_throughput_data(data_frames)

    # Calculate average throughput for every 5 iterations
    avg_throughput_data = calculate_average_every_n_iterations(throughput_data, 5)

    plot_average_throughput(avg_throughput_data)
    save_throughput_to_file(throughput_text_lines)
