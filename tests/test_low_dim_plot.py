import time
import subprocess
import json
import glob
import shutil
import os

# This test runs Cybernetics without any of the LlamaTune search space transformations and then runs with only the linear projection transformation

# The transofrmations should provide a speedup to the runtime,
# but this may not always be the case due to fluctations in time it takes to query workloads on your machine's Postgres server

save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
for file_name in os.listdir(save_dir):
    print("deleting file: ", file_name)
    file_path = os.path.join(save_dir, file_name)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")

print(
    "Running with only linear projection transformation:"
)
start_time = time.time()
payload = [
    "python",
    "/home/samika/cybernetics/examples/run_dim_reduction.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
    "--projection_dim",
    "16",
]
workload_process = subprocess.run(payload)
end_time = time.time()
duration_transform = end_time - start_time
print(
    f"Runtime for just linear projection transformation: {end_time - start_time} seconds"
)

#assert duration_no_transform > duration_transform

# Read the summary file for quantization
summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
throughput_values = []
for summary_file in summary_files:
    with open(summary_file) as f:
        summary = json.load(f)
        if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
            best_summary_file = summary_file
        throughput_values.append(summary["Throughput (requests/second)"])

#plot throughput values on y-axis and iteration number on x-axis
import matplotlib.pyplot as plt
plt.plot(throughput_values)
plt.xlabel("Iteration Number")
plt.ylabel("Throughput (requests/second)")
plt.title("Throughput vs Iteration Number")
plt.show()


#Document what hyperparameters and configs
#Change 1 to 10 for scale factor in ~/benchbase/target/benchbase-postgress/config/postgres/sample_tpcc_config.xml
#Also compare no transformation vs transformation vs PG Tune (Heuristic) (End to End). 
#End to end run time as well as plots of best throughput over time for no transformation vs transformation
# for 1 and 10
