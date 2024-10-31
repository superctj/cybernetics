import os
import pandas as pd
import matplotlib.pyplot as plt

def load_throughput_from_txt(file_path):
    """Load throughput data from a text file into a list."""
    throughput_data = []
    throughput_text_lines = []

    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            filename, avg_throughput = line.strip().split(': ')
            avg_throughput = float(avg_throughput)
            throughput_data.append(avg_throughput)
            throughput_text_lines.append(f"{filename}: {avg_throughput:.2f}")

    return throughput_data, throughput_text_lines

def plot_throughput(throughput_data):
    """Plot the throughput data."""
    sampled_throughput_data = throughput_data[::3]  # Sample every third iteration
    iterations = range(0, len(throughput_data), 3)

    plt.figure(figsize=(10, 6))
    plt.plot(iterations, sampled_throughput_data, label='Throughput (transactions/second)', color='blue', marker='o')  # Added marker for visibility
    plt.xlabel('Iteration')
    plt.ylabel('Throughput (transactions/second)')
    plt.ylim(500, 800)  # Setting the y-axis range
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
    txt_file_path = "/home/phdonn/cybernetics_n/exps/average_throughput_20240720_111718.txt"

    throughput_data, throughput_text_lines = load_throughput_from_txt(txt_file_path)

    plot_throughput(throughput_data)
    save_throughput_to_file(throughput_text_lines)
