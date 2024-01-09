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
                          f"scripts/benchbase_{workload}_postgres_test_pgtune.sh")
    results_dir = os.path.join(proj_dir,
                               f"exps/benchbase_{workload}/postgres/pgtune_tests")

    if not os.path.exists(results_dir):
        create_dir(results_dir, force=False)

    workload_wrapper = BenchBaseWrapper(workload, script)
    print("    Created workload wrapper.")

    postgres_wrapper = PostgresWrapper(db_info, workload_wrapper, results_dir)
    print("    Created Postgres wrapper.")

    # Get default performance
    postgres_wrapper.reset_knobs_by_restarting_db()
    print("    Reset the runtime configuration.")
    
    workload_wrapper.run()
    default_performance = postgres_wrapper.get_benchbase_metrics()
    default_throughput = default_performance["Throughput (requests/second)"]
    print("    Default throughput: ", default_throughput)

    # Apply PGTune configuration
    db_config = {
        "max_connections": 300,
        "shared_buffers": "32GB",
        "effective_cache_size": "96GB",
        "maintenance_work_mem": "2GB",
        # "checkpoint_completion_target": 0.9,
        "wal_buffers": "16MB",
        "default_statistics_target": 100,
        # "random_page_cost": 1.1,
        "effective_io_concurrency": 200,
        "work_mem": "27962kB",
        "huge_pages": "try",
        "min_wal_size": "2GB",
        "max_wal_size": "8GB",
        "max_worker_processes": 32,
        "max_parallel_workers_per_gather": 4,
        "max_parallel_workers": 32,
        "max_parallel_maintenance_workers": 4
    }
    rtn_predicate = postgres_wrapper.apply_knobs(db_config)
    assert rtn_predicate == True

    workload_wrapper.run()
    performance = postgres_wrapper.get_benchbase_metrics()
    throughput = performance["Throughput (requests/second)"]
    print("    Tuned throughput: ", throughput)

    postgres_wrapper.reset_knobs_by_restarting_db()
    print("    Reset the runtime configuration.")
    
    # assert throughput > default_throughput
