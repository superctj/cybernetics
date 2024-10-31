"""This test running TPC-C workload can take a while.
"""

import os

from ConfigSpace import ConfigurationSpace, Configuration
from cybernetics.dbms_interface.postgres import PostgresWrapper
from cybernetics.utils.util import create_dir, get_proj_dir
from cybernetics.workload.benchbase import BenchBaseWrapper


def test_evaluating_db_configuration():
    dbms_info = {
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

    postgres_wrapper = PostgresWrapper(dbms_info, workload_wrapper, results_dir)
    print("    Created Postgres wrapper.")

    # Apply a configuration sampled from the configuration space
    knob_space = ConfigurationSpace(
        seed=12345,
        space={
            knob_to_tune: (16384, 131072) # 128 MB to 1 GB
        }
    )
    dbms_config = knob_space.sample_configuration()
    assert isinstance(dbms_config, Configuration)
    print("    Sampled DBMS config: ", dbms_config)

    rtn_predicate = postgres_wrapper.apply_knobs(dbms_config)
    assert rtn_predicate == True

    cur_val = postgres_wrapper.get_knob_value(knob_to_tune)
    print(f"    Value of {knob_to_tune} after applying a new DBMS config: {cur_val}")

    workload_wrapper.run()
    performance = postgres_wrapper.get_benchbase_metrics()
    throughput = performance["Throughput (requests/second)"]
    print("    Throughput from sampled DBMS configuration: ", throughput)

    postgres_wrapper.reset_knobs_by_restarting_db()
    print("    Reset the runtime configuration.")
    default_val = postgres_wrapper.get_knob_value(knob_to_tune)
    print(f"    Default value of {knob_to_tune}: {default_val}")
