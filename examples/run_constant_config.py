"""
*******************USAGE*******************
After running tuning, copy over the best config json. It's at the end of the output, should look something like:

Configuration(values={
  'checkpoint_completion_target': 0.11183177959173918,
  'default_statistics_target': 104,
  'effective_cache_size': 8207566,
  'effective_io_concurrency': 4,
  'huge_pages': 'try',
  'maintenance_work_mem': 2018584,
  'max_connections': 454,
  'max_parallel_maintenance_workers': 2,
  'max_parallel_workers': 46,
  'max_parallel_workers_per_gather': 5,
  'max_wal_size': 7661,
  'max_worker_processes': 13,
  'min_wal_size': 2666,
  'random_page_cost': 5.847389217466116,
  'shared_buffers': 2062043,
  'wal_buffers': 1941,
  'work_mem': 12585,
})

Remove the "Configuration(values= " at the start of the output to make it JSON format, and save as knobs.json in the examples folder

Then run the following in terminal:

python ./examples/run_constant_config.py --config_path ./cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini --knob_config_path ./examples/knobs.json

"""
import argparse
import json
from cybernetics.tuning.engine import TuningEngine
from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.utils.util import (
    fix_global_random_state,
    get_benchbase_postgres_target_dir,
    get_postgres_user_and_password,
    parse_config,
)


if __name__ == "__main__":
    # Parsing command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--knob_config_path",
        type=str,
        required=True,
        help="Path to the knob results",
    )

    args = parser.parse_args()

    # Parse configuration
    config = parse_config(args.config_path)
    
    # Set global random state
    fix_global_random_state(int(config["knob_space"]["random_seed"]))

    # Create DBMS executor
    if config["dbms_info"]["dbms_name"] == "postgres":
        from cybernetics.dbms_interface.postgres import PostgresWrapper

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

        postgres_wrapper = PostgresWrapper(
            config["dbms_info"],
            workload_wrapper,
            config["results"]["save_path"],
        )

        with open (args.knob_config_path, 'r') as f:
            knob_values = json.load(f)


        for i in range(20):
            print("ITERATION ", i)
            postgres_wrapper.apply_knobs(knob_values)
            print("Finished applying knobs")
            workload_wrapper.run()
            performance = postgres_wrapper.get_benchbase_metrics()

            throughput = performance["Throughput (requests/second)"]
            print(f"Throughput (requests/second): {throughput}")
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            print(f"95th Percentile Latency (microseconds): {latency}")
