"""This test running TPC-C workload can take a while.
"""

import os

from cybernetics.db_interface.postgres import PostgresWrapper
from cybernetics.utils.util import create_dir, get_proj_dir
from cybernetics.workload.benchbase import BenchBaseWrapper


def test_evaluating_db_configuration():
    db_info = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "12345",
        "db_cluster": "/data/pgsql/data",
        "db_log_filepath": "/data/pgsql/log",
        "db_name": "benchbase_tpcc" # This database should be created beforehand
    }

    proj_dir = get_proj_dir(__file__, file_level=2)
    print("\n    Project directory:", proj_dir)
    workload = "tpcc"
    script = os.path.join(proj_dir,
                          f"scripts/benchbase_{workload}_postgres_test.sh")
    knob_to_tune = "shared_buffers"
    results_dir = os.path.join(proj_dir,
                               f"exps/benchbase_{workload}/postgres/tests")
    create_dir(results_dir, force=True)

    workload_wrapper = BenchBaseWrapper(workload, script)
    print("    Created workload wrapper.")

    postgres_wrapper = PostgresWrapper(db_info, workload_wrapper, results_dir)
    print("    Created Postgres wrapper.")

    # Get default performance
    postgres_wrapper.reset_knobs_by_restarting_db()
    print("    Reset the runtime configuration.")
    default_val = postgres_wrapper.get_knob_value(knob_to_tune)
    print(f"    Default value of {knob_to_tune}: {default_val}")
    
    workload_wrapper.run()
    default_performance = postgres_wrapper.get_benchbase_metrics()
    default_throughput = default_performance["Throughput (requests/second)"]
    print("    Default throughput: ", default_throughput)

    cur_val = postgres_wrapper.get_knob_value(knob_to_tune)
    print(f"    Value of {knob_to_tune} after running the workload: {cur_val}")

    # Apply a better configuration
    db_config = {knob_to_tune: "1GB"} # default is 128MB
    rtn_predicate = postgres_wrapper.apply_knobs(db_config)
    assert rtn_predicate == True

    cur_val = postgres_wrapper.get_knob_value(knob_to_tune)
    print(f"    Value of {knob_to_tune} after applying a new DBMS config: {cur_val}")

    workload_wrapper.run()
    performance = postgres_wrapper.get_benchbase_metrics()
    throughput = performance["Throughput (requests/second)"]
    print("    Tuned throughput: ", throughput)
    # # assert throughput > default_throughput

    cur_val = postgres_wrapper.get_knob_value(knob_to_tune)
    print(f"    Value of {knob_to_tune} after running the workload: {cur_val}")
    postgres_wrapper.reset_knobs_by_restarting_db()
    print("    Reset the runtime configuration.")
    default_val = postgres_wrapper.get_knob_value(knob_to_tune)
    print(f"    Default value of {knob_to_tune}: {default_val}")
