import time
import subprocess

# This test runs Cybernetics without any of the LlamaTune search space transformations and then runs with the search space transformations

# The transofrmations should provide a speedup to the runtime,
# but this may not always be the case due to fluctations in time it takes to query workloads on your machine's Postgres server


print("Running with no search space transformation:")
start_time = time.time()
payload = [
    "python",
    "/home/tianji/cybernetics/run_dbms_optimization.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.ini",
]
workload_process = subprocess.run(payload)
end_time = time.time()
duration_no_transform = end_time - start_time
print(
    f"Runtime for no search space transformation: {duration_no_transform} seconds"
)

print()

print(
    "Running with all search space transformations (biased sampling, quantization (bucketing), and linear projection):"
)
start_time = time.time()
payload = [
    "python",
    "/home/tianji/cybernetics/run_dbms_optimization.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.ini",
    "--projection_dim",
    "16",
    "--quantization_factor",
    "10000",
    "--bias_prob",
    "0.2",
]
workload_process = subprocess.run(payload)
end_time = time.time()
duration_transform = end_time - start_time
print(
    f"Runtime for all search space transformations: {end_time - start_time} seconds"
)

assert duration_no_transform > duration_transform
