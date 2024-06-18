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
    """Extract average throughput and best throughput data from the DataFrames."""
    throughput_data = []
    throughput_noise_data = []
    best_throughput = []
    current_best_throughput = 0
    throughput_text_lines = []

    for filename, df in data_frames:
        # Assuming the throughput data is in a column named 'Throughput (requests/second)'
        if 'Throughput (requests/second)' in df.columns and 'Throughput (noise)' in df.columns:
            avg_throughput = df['Throughput (requests/second)'].mean()
            avg_throughput_noise = df['Throughput (noise)'].mean()
            throughput_data.append(avg_throughput)
            throughput_noise_data.append(avg_throughput_noise)
            current_best_throughput = max(current_best_throughput, avg_throughput)
            best_throughput.append(current_best_throughput)
            throughput_text_lines.append(f"{filename}: {avg_throughput:.2f} (Original), {avg_throughput_noise:.2f} (Noise)")

    return throughput_data, throughput_noise_data, best_throughput, throughput_text_lines

def plot_throughput(throughput_data, throughput_noise_data, best_throughput):
    """Plot the throughput data and the best throughput line."""
    iterations = range(len(throughput_data))

    plt.figure(figsize=(10, 6))
    plt.plot(iterations, throughput_data, label='Throughput', color='blue')
    plt.plot(iterations, throughput_noise_data, label='Throughput (Noise)', color='green')
    plt.plot(iterations, best_throughput, label='Best Throughput', color='red')
    plt.xlabel('Iteration')
    plt.ylabel('Throughput (requests/second)')
    plt.title('Throughput vs. Iteration')
    plt.legend()
    plt.grid(True)

    # Save the plot with a timestamp
    output_dir = '/home/phdonn/cybernetics/exps'
    os.makedirs(output_dir, exist_ok=True)
    current_time = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_filename = os.path.join(output_dir, f'throughput_vs_iteration_{current_time}.png')

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

if __name__ == "__main__":
    csv_directory = "/home/phdonn/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
    data_frames = load_csv_files(csv_directory)
    throughput_data, throughput_noise_data, best_throughput, throughput_text_lines = extract_throughput_data(data_frames)
    plot_throughput(throughput_data, throughput_noise_data, best_throughput)
    save_throughput_to_file(throughput_text_lines)
