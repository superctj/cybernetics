import time
import subprocess

# This test runs Cybernetics without any of the LlamaTune search space transformations and then runs with biased sampling

# The transofrmations should provide a speedup to the runtime,
# but this may not always be the case due to fluctations in time it takes to query workloads on your machine's Postgres server


print("Running with no search space transformation:")
start_time = time.time()
payload = [
    "python",
    "/home/jhsueh/Desktop/cybernetics/examples/run_dbms_config_tuning.py",
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
    "Running with biased sampling:"
)
start_time = time.time()
payload = [
    "python",
    "/home/jhsueh/Desktop/cybernetics/examples/run_dim_reduction.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.ini",
    "--bias_prob",
    "0.2",
]
workload_process = subprocess.run(payload)
end_time = time.time()
duration_transform = end_time - start_time
print(
    f"Runtime for biased sampling: {end_time - start_time} seconds"
)

assert duration_no_transform > duration_transform
