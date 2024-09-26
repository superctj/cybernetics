import time
import subprocess
import json
import glob

# This test runs Cybernetics without any of the LlamaTune search space transformations and then runs with just quantization

# The transofrmations should provide a speedup to the runtime,
# but this may not always be the case due to fluctations in time it takes to query workloads on your machine's Postgres server


print("Running with no search space transformation:")
start_time = time.time()
payload = [
    "python",
    "/home/jhsueh/Desktop/cybernetics/examples/run_dbms_config_tuning.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
]
workload_process = subprocess.run(payload)
end_time = time.time()
duration_no_transform = end_time - start_time
print(
    f"Runtime for no search space transformation: {duration_no_transform} seconds"
)

# Read the summary file for no transformation

summary_files = glob.glob("/home/jhsueh/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
summary_files.sort(key=lambda x: x, reverse=True)
summary_file_no_transform = summary_files[0]

#summary_file_no_transform = "/home/jhsueh/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/no_transform.summary.json"
with open(summary_file_no_transform) as f:
    summary_no_transform = json.load(f)

print()

print(
    "Running with quantization (bucketing)"
)
start_time = time.time()
payload = [
    "python",
    "/home/jhsueh/Desktop/cybernetics/examples/run_dim_reduction.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
    "--quantization_factor",
    "10000",
]
workload_process = subprocess.run(payload)
end_time = time.time()
duration_transform = end_time - start_time
print(
    f"Runtime for quantization (bucketing): {end_time - start_time} seconds"
)

# assert duration_no_transform > duration_transform

# Read the summary file for quantization
summary_files = glob.glob("/home/jhsueh/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
summary_files.sort(key=lambda x: x, reverse=True)
summary_file_transform = summary_files[0]

with open(summary_file_transform) as f:
    summary_transform = json.load(f)

# Compare throughput
throughput_no_transform = summary_no_transform["Throughput (requests/second)"]
throughput_transform = summary_transform["Throughput (requests/second)"]
print(f"Throughput without transformation: {throughput_no_transform}")
print(f"Throughput with quantization: {throughput_transform}")

# Compare latencies
latencies_no_transform = summary_no_transform["Latency Distribution"]["95th Percentile Latency (microseconds)"]
latencies_transform = summary_transform["Latency Distribution"]["95th Percentile Latency (microseconds)"]
print(f"95th Percentile Latencies without transformation: {latencies_no_transform}")
print(f"95th Percentile Latencies with quantization: {latencies_transform}")

print(f"Duration without transformation: {duration_no_transform}")
print(f"Duration with quantization: {duration_transform}")