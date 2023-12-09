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
        "db_name": "benchbase_tpcc" # This database should be created beforehand
    }

    proj_dir = get_proj_dir(__file__, file_level=2)
    print("\n    Project directory:", proj_dir)
    workload = "tpcc"
    script = os.path.join(proj_dir,
                          f"scripts/benchbase_{workload}_postgres_test.sh")
    
    workload_wrapper = BenchBaseWrapper(workload, script)
    print("    Created workload wrapper.")

    results_dir = os.path.join(proj_dir,
                               f"exps/benchbase_{workload}/postgres/tests")
    create_dir(results_dir, force=True)

    postgres_wrapper = PostgresWrapper(db_info, workload_wrapper, results_dir)
    print("    Created Postgres wrapper.")

    # Get default performance
    workload_wrapper.run()
    default_performance = postgres_wrapper.get_benchbase_metrics()
    default_throughput = default_performance["Throughput (requests/second)"]
    print("    Default throughput: ", default_throughput)

    # Apply a better configuration
    db_config = {"work_mem": "1GB"} # default is 4096 kB
    rtn_predicate = postgres_wrapper.apply_knobs_online(db_config)
    assert rtn_predicate == True

    workload_wrapper.run()
    performance = postgres_wrapper.get_benchbase_metrics()
    throughput = performance["Throughput (requests/second)"]
    print("Tuned throughput: ", throughput)
    assert throughput > default_throughput
