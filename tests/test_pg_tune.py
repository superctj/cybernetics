from cybernetics.workload.benchbase import BenchBaseWrapper
from cybernetics.utils.util import fix_global_random_state, parse_config, get_benchbase_postgres_target_dir, get_postgres_user_and_password

if __name__ == "__main__":
    # Parsing command line arguments

    #parse_config on cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini
    # Parse configuration
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

    #apply configurations specified through PG Tune
    # DB Version: 12
    # OS Type: linux
    # DB Type: oltp
    # Total Memory (RAM): 64 GB
    # CPUs num: 32
    # Data Storage: Network SAN
    # max_connections = 300
    # shared_buffers = 16GB
    # effective_cache_size = 48GB
    # maintenance_work_mem = 2GB
    # checkpoint_completion_target = 0.9
    # wal_buffers = 16MB
    # default_statistics_target = 100
    # random_page_cost = 1.1
    # effective_io_concurrency = 300
    # work_mem = 13981kB
    # huge_pages = try
    # min_wal_size = 2GB
    # max_wal_size = 8GB
    # max_worker_processes = 32
    # max_parallel_workers_per_gather = 4
    # max_parallel_workers = 32
    # max_parallel_maintenance_workers = 4
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