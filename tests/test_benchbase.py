import os
import time

from cybernetics.workload.benchbase import BenchBaseWrapper
from cybernetics.utils.util import get_benchbase_postgres_target_dir


def test_benchbase_postgres():
    benchbase_postgres_target_dir = get_benchbase_postgres_target_dir()

    assert os.path.isdir(
        benchbase_postgres_target_dir
    ), "BenchBase target directory does not exist."

    dbms_name = "postgres"
    workload = "tpcc"

    workload_wrapper = BenchBaseWrapper(
        target_dir=benchbase_postgres_target_dir,
        dbms_name=dbms_name,
        workload=workload,
    )

    start_time = time.time()
    workload_wrapper.run()
    first_run_duration = time.time() - start_time
    print(f"First run duration: {first_run_duration:.2f} s")

    start_time = time.time()
    workload_wrapper.run()
    second_run_duration = time.time() - start_time
    print(f"Second run duration: {second_run_duration:.2f} s")

    assert (
        first_run_duration > second_run_duration
    ), "First run should take more time due to data loading."
