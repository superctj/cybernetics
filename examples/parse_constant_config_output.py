import re
import csv
import sys

input_file = sys.argv[1]
output_csv = sys.argv[1][:-3] + 'csv'


throughput_pattern = r'Throughput\s+\(requests/second\):\s+([\d\.]+)'

# Lists to hold the extracted data
data = []

# Open the input file for reading
with open(input_file, 'r') as file:
    content = file.read()
    
    # Find all matches for iterations, throughput, and latency
    # iterations = re.findall(iteration_pattern, content)
    throughputs = re.findall(throughput_pattern, content)
    # latencies = re.findall(latency_pattern, content)
    
    # Ensure all lists have the same length (should match if the file format is consistent)
    for i in range(len(throughputs)):
        # Append each row of data (iteration, throughput, latency)
        data.append([i, throughputs[i]])

# Write the data into a CSV file
with open(output_csv, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Write the header
    csvwriter.writerow(['Iteration', 'Throughput (requests/second)'])
    # Write the data rows
    csvwriter.writerows(data)

print(f"CSV file '{output_csv}' has been generated.")