import time
import subprocess
import json
import glob
import shutil
import os
import matplotlib.pyplot as plt
from cybernetics.utils.util import fix_global_random_state, parse_config, get_benchbase_postgres_target_dir, get_postgres_user_and_password

# This test runs Cybernetics without any of the LlamaTune search space transformations and then runs with only the linear projection transformation

# The transofrmations should provide a speedup to the runtime,
# but this may not always be the case due to fluctations in time it takes to query workloads on your machine's Postgres server

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

start_time = time.time()
payload = [
    "python",
    "/home/samika/cybernetics/examples/run_dim_reduction.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
    "--projection_dim",
    "16",
    "--quantization_factor",
    "10000",
    "--bias_prob",
    "0.2",
]
workload_process = subprocess.run(payload)
end_time = time.time()
all_duration_transform = end_time - start_time

save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"

# Read the summary file for quantization
summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
all_throughput_values = []
best_summary_file = summary_files[0]
for summary_file in summary_files:
    with open(summary_file) as f:
        summary = json.load(f)
        if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
            best_summary_file = summary_file
        best_summary = json.load(open(best_summary_file))
        all_throughput_values.append(best_summary["Throughput (requests/second)"])
        
all_best_throughtput = json.load(open(best_summary_file))["Throughput (requests/second)"]

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
linear_duration_transform = end_time - start_time

save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"

# Read the summary file for quantization
summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
linear_throughput_values = []
best_summary_file = summary_files[0]
for summary_file in summary_files:
    with open(summary_file) as f:
        summary = json.load(f)
        if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
            best_summary_file = summary_file
        best_summary = json.load(open(best_summary_file))
        linear_throughput_values.append(best_summary["Throughput (requests/second)"])
        
linear_best_throughtput = json.load(open(best_summary_file))["Throughput (requests/second)"]

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

start_time = time.time()
payload = [
    "python",
    "/home/samika/cybernetics/examples/run_dim_reduction.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
    "--quantization_factor",
    "10000"
]
workload_process = subprocess.run(payload)
end_time = time.time()
quantization_duration_transform = end_time - start_time

save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"

# Read the summary file for quantization
summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
quantization_throughput_values = []
best_summary_file = summary_files[0]
for summary_file in summary_files:
    with open(summary_file) as f:
        summary = json.load(f)
        if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
            best_summary_file = summary_file
        best_summary = json.load(open(best_summary_file))
        quantization_throughput_values.append(best_summary["Throughput (requests/second)"])
        
quantization_best_throughtput = json.load(open(best_summary_file))["Throughput (requests/second)"]

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

start_time = time.time()
payload = [
    "python",
    "/home/samika/cybernetics/examples/run_dim_reduction.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
    "--bias_prob",
    "0.2"
]
workload_process = subprocess.run(payload)
end_time = time.time()
bias_duration_transform = end_time - start_time

save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"

# Read the summary file for quantization
summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
bias_throughput_values = []
best_summary_file = summary_files[0]
for summary_file in summary_files:
    with open(summary_file) as f:
        summary = json.load(f)
        if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
            best_summary_file = summary_file
        best_summary = json.load(open(best_summary_file))
        bias_throughput_values.append(best_summary["Throughput (requests/second)"])
        
bias_best_throughtput = json.load(open(best_summary_file))["Throughput (requests/second)"]

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

start_time = time.time()
payload = [
    "python",
    "/home/samika/cybernetics/examples/run_dbms_config_tuning.py",
    "--config_path",
    "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini",
]
workload_process = subprocess.run(payload)
end_time = time.time()
none_duration_transform = end_time - start_time

save_dir = "/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"

# Read the summary file for quantization
summary_files = glob.glob("/home/samika/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/tpcc_*.summary.json")
none_throughput_values = []
best_summary_file = summary_files[0]
for summary_file in summary_files:
    with open(summary_file) as f:
        summary = json.load(f)
        if summary["Throughput (requests/second)"] > json.load(open(best_summary_file))["Throughput (requests/second)"]:
            best_summary_file = summary_file
        best_summary = json.load(open(best_summary_file))
        none_throughput_values.append(best_summary["Throughput (requests/second)"])
        
none_best_throughtput = json.load(open(best_summary_file))["Throughput (requests/second)"]

config = parse_config("cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini")
# Set global random state
fix_global_random_state(int(config["knob_space"]["random_seed"]))

# Create workload wrapper
postgres_user, postgres_password = get_postgres_user_and_password()
benchbase_postgres_target_dir = get_benchbase_postgres_target_dir()

config["dbms_info"]["user"] = postgres_user
config["dbms_info"]["password"] = postgres_password

if config["workload_info"]["framework"] == "benchbase":
    from cybernetics.workload.benchbase import BenchBaseWrapper

    workload_wrapper = BenchBaseWrapper(
            target_dir=benchbase_postgres_target_dir,
            dbms_name=config["dbms_info"]["dbms_name"],
            workload=config["workload_info"]["workload"],
            results_save_dir=config["results"]["save_path"],
        )

# Create DBMS executor
if config["dbms_info"]["dbms_name"] == "postgres":
    from cybernetics.dbms_interface.postgres import PostgresWrapper

    postgres_wrapper = PostgresWrapper(
        config["dbms_info"],
        workload_wrapper,
        config["results"]["save_path"],
    )

# Get default performance
postgres_wrapper.reset_knobs_by_restarting_db()
print("    Reset the runtime configuration.")

workload_wrapper.run()
default_performance = postgres_wrapper.get_benchbase_metrics()
default_throughput = default_performance["Throughput (requests/second)"]
print("    Default throughput: ", default_throughput)
default_throughputs = [default_throughput for i in range(100)]

db_config = {
    "max_connections": 300,
    "shared_buffers": "16GB",
    "effective_cache_size": "48GB",
    "maintenance_work_mem": "2GB",
    "checkpoint_completion_target": 0.9,
    "wal_buffers": "16MB",
    "default_statistics_target": 100,
    "random_page_cost": 1.1,
    "effective_io_concurrency": 300,
    "work_mem": "13981kB",
    "huge_pages": "try",
    "min_wal_size": "2GB",
    "max_wal_size": "8GB",
    "max_worker_processes": 32,
    "max_parallel_workers_per_gather": 4,
    "max_parallel_workers": 32,
    "max_parallel_maintenance_workers": 4
}
postgres_wrapper.apply_knobs(db_config)
workload_wrapper.run()
performance = postgres_wrapper.get_benchbase_metrics()
throughput = performance["Throughput (requests/second)"]
print("    Throughput after applying configurations: ", throughput)
pg_tune_throughputs = [throughput for i in range(100)]

print("Best throughput with all transformations: ", all_best_throughtput)
print("Time taken with all transformations: ", all_duration_transform)
print("Best throughput with linear projection transformation: ", linear_best_throughtput)
print("Time taken with linear projection transformation: ", linear_duration_transform)
print("Best throughput with quantization transformation: ", quantization_best_throughtput)
print("Time taken with quantization transformation: ", quantization_duration_transform)
print("Best throughput with bias transformation: ", bias_best_throughtput)
print("Time taken with bias transformation: ", bias_duration_transform)
print("Best throughput with no transformation: ", none_best_throughtput)
print("Time taken with no transformation: ", none_duration_transform)
print("Best throughput with default configuration: ", default_throughput)
print("Best throughput with PG Tune configuration: ", throughput)

print("Throughput values with all transformations: ", all_throughput_values)
print("Throughput values with linear projection transformation: ", linear_throughput_values)
print("Throughput values with quantization transformation: ", quantization_throughput_values)
print("Throughput values with bias transformation: ", bias_throughput_values)
print("Throughput values with no transformation: ", none_throughput_values)
print("Throughput values with default configuration: ", default_throughputs)
print("Throughput values with PG Tune configuration: ", pg_tune_throughputs)

#plot throughput values on y-axis and iteration number on x-axis. Fill line by which transformation was used
plt.figure(figsize=(10, 5))
plt.plot(all_throughput_values, label="All Transformations")
plt.plot(linear_throughput_values, label="Linear Projection")
plt.plot(quantization_throughput_values, label="Quantization")
plt.plot(bias_throughput_values, label="Bias")
plt.plot(none_throughput_values, label="None")
plt.plot(default_throughputs, label="Default Configuration")
plt.plot(pg_tune_throughputs, label="PG Tune Configuration")
plt.xlabel("Iteration")
plt.ylabel("Throughput (requests/second)")

plt.legend()
plt.title("Throughput vs Iteration by Transformation")
plt.savefig("throughput_iteration_plot_1.png")

