import os
import re
import matplotlib.pyplot as plt
from datetime import datetime
import math

def parse_throughputs(log_file_path):
    predicted_throughputs = []
    actual_throughputs = []
    best_throughput = []
    current_best = float('-inf')  # Initialize to negative infinity

    with open(log_file_path, 'r') as file:
        for line in file:
            # Extract predicted throughput
            predicted_match = re.search(r"\[INFO\] Predicted throughput for trial: \[\[(-?\d+\.?\d*e?[-+]?\d*)\]\]", line)
            if predicted_match:
                predicted_value = round(abs(float(predicted_match.group(1))), 2)
                predicted_throughputs.append(predicted_value)
                print(f"[DEBUG] Parsed predicted throughput: {predicted_value}")  # Debugging statement

            # Extract actual throughput
            actual_match = re.search(r"\[INFO\] Actual throughput for trial: (-?\d+\.?\d*e?[-+]?\d*)", line)
            if actual_match:
                actual_value = actual_match.group(1)
                if actual_value.lower() == 'inf':
                    actual_value = float('inf')  # Handle 'inf' properly
                else:
                    actual_value = abs(float(actual_value))  # Store as absolute value

                actual_value = round(actual_value, 3)  # Round to 3 decimal places
                actual_throughputs.append(actual_value)
                print(f"[DEBUG] Parsed actual throughput: {actual_value}")  # Debugging statement

                # Track best throughput based on actual throughput
                if actual_value > current_best:
                    current_best = actual_value
                best_throughput.append(round(current_best, 3))  # Round to 3 decimal places

    print(f"[DEBUG] Length of predicted_throughputs: {len(predicted_throughputs)}")
    print(f"[DEBUG] Length of actual_throughputs: {len(actual_throughputs)}")
    print(f"[DEBUG] Length of best_throughput: {len(best_throughput)}")

    return predicted_throughputs, actual_throughputs, best_throughput

def plot_throughputs(predicted_throughputs, actual_throughputs, best_throughput):
    # Determine the minimum length to ensure alignment
    min_length = min(len(predicted_throughputs), len(actual_throughputs), len(best_throughput))
    print(f"[DEBUG] Using minimum length: {min_length}")

    if min_length == 0:
        print("[ERROR] No data to plot.")
        return

    predicted_throughputs = predicted_throughputs[:min_length]
    actual_throughputs = actual_throughputs[:min_length]
    best_throughput = best_throughput[:min_length]

    iterations = range(min_length)

    plt.figure(figsize=(10, 6))
    plt.plot(iterations, predicted_throughputs, label='Predicted Throughput', color='green', marker='x')
    plt.plot(iterations, actual_throughputs, label='Actual Throughput', color='blue', marker='o')
    plt.plot(iterations, best_throughput, label='Best Throughput', color='red', marker='^')
    plt.xlabel('Iteration')
    plt.ylabel('Throughput (absolute value)')
    plt.title('Predicted vs Actual Throughput')
    plt.legend()
    plt.grid(True)
    plt.ylim(0, max(best_throughput) * 1.5)  # Set y-axis to be slightly above the max throughput

    # Save the plot with a timestamp
    output_dir = '/home/phdonn/cybernetics/exps'
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plot_filename = os.path.join(output_dir, f'throughput_vs_iteration_{timestamp}.png')
    plt.savefig(plot_filename)
    plt.show()

    print(f'Plot saved as {plot_filename}')

    # Log the throughput data to a text file with a timestamp
    log_filename = os.path.join(output_dir, f'throughput_data_{timestamp}.txt')
    with open(log_filename, 'w') as log_file:
        log_file.write('Iteration\tPredicted Throughput\tActual Throughput\tBest Throughput\n')
        for i in iterations:
            log_file.write(f"{i+1}\t{predicted_throughputs[i]:.3f}\t{actual_throughputs[i]:.3f}\t{best_throughput[i]:.3f}\n")

    print(f'Data logged to {log_filename}')

def main():
    log_file_path = "/home/phdonn/cybernetics/exps/Gaussian_predict_output.txt"

    predicted_throughputs, actual_throughputs, best_throughput = parse_throughputs(log_file_path)

    plot_throughputs(predicted_throughputs, actual_throughputs, best_throughput)

if __name__ == "__main__":
    main()
