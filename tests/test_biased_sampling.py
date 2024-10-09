import time
import subprocess
import json
import glob
import os
import shutil

# This test runs Cybernetics without any of the LlamaTune search space transformations and then runs with biased sampling

# The transofrmations should provide a speedup to the runtime,
# but this may not always be the case due to fluctations in time it takes to query workloads on your machine's Postgres server


# print("Running with no search space transformation:")
# start_time = time.time()
# payload = [
#     "python",
#     "/home/samika/cybernetics/examples/run_dbms_config_tuning.py",
#     "--config_path",
#     "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
# ]
# workload_process = subprocess.run(payload)
# end_time = time.time()
# duration_no_transform = end_time - start_time
# print(
#     f"Runtime for no search space transformation: {duration_no_transform} seconds"
# )

# # Read the summary file for no transformation

# summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
# best_summary_file = summary_files[0]
# for summary_file in summary_files:
#     with open(summary_file) as f:
#         summary = json.load(f)
#         if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
#             best_summary_file = summary_file

# with open(best_summary_file) as f:
#     summary_no_transform = json.load(f)

# throughput_no_transform = summary_no_transform["Throughput (requests/second)"]
# latencies_no_transform = summary_no_transform["Latency Distribution"]["95th Percentile Latency (microseconds)"]

#Clear the summary files directory
save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
for file_name in os.listdir(save_dir):
    file_path = os.path.join(save_dir, file_name)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")


print()

print(
    "Running with biased sampling:"
)
start_time = time.time()
payload = [
    "python",
    "/home/samika/cybernetics/examples/run_dim_reduction.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
    "--bias_prob",
    "0.2",
]
workload_process = subprocess.run(payload)
end_time = time.time()
duration_transform = end_time - start_time
print(
    f"Runtime for biased sampling: {end_time - start_time} seconds"
)

# assert duration_no_transform > duration_transform

# assert duration_no_transform > duration_transform

# Read the summary file for quantization
summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
best_summary_file = summary_files[0]
for summary_file in summary_files:
    with open(summary_file) as f:
        summary = json.load(f)
        if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
            best_summary_file = summary_file

with open(best_summary_file) as f:
    summary_transform = json.load(f)

# Compare throughput
throughput_transform = summary_transform["Throughput (requests/second)"]
print(f"Throughput without transformation: {throughput_no_transform}")
print(f"Throughput with biased sampling: {throughput_transform}")

# Compare latencies
latencies_transform = summary_transform["Latency Distribution"]["95th Percentile Latency (microseconds)"]
print(f"95th Percentile Latencies without transformation: {latencies_no_transform}")
print(f"95th Percentile Latencies with quantization: {latencies_transform}")

print(f"Duration without transformation: {duration_no_transform}")
print(f"Duration with quantization: {duration_transform}")

save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
for file_name in os.listdir(save_dir):
    file_path = os.path.join(save_dir, file_name)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")