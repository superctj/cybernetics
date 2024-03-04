import argparse

from cybernetics.tuning.engine import TuningEngine
from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.utils.util import fix_global_random_state, parse_config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    parser.add_argument(
        "--db_cluster_path",
        type=str,
        required=False,
        help="Absolute path to data cluster for Postgres (for example: /home/bob/data/pgsql/data) (optional)"
    )
    parser.add_argument(
        "--db_log_filepath",
        type=str,
        required=False,
        help="Absolute path to log file for Postgres (for example: /home/bob/data/pgsql/log) (optional)"
    )
    parser.add_argument(
        "--db_username",
        type=str,
        required=True,
        help="Postgres username that you want to use"
    )
    parser.add_argument(
        "--db_password",
        type=str,
        required=True,
        help="Password for that Postgres user"
    )

    args = parser.parse_args()

    # Parse configuration
    config = parse_config(args.config_path)
    db_cluster_path = args.db_cluster_path
    db_log_path = args.db_log_filepath
    db_usr = args.db_username
    db_pwd = args.db_password
    # Set global random state
    fix_global_random_state(int(config["knob_space"]["random_seed"]))

    # Create workload wrapper
    if config["workload_info"]["framework"] == "benchbase":
        from cybernetics.workload.benchbase import BenchBaseWrapper
        
        workload_wrapper = BenchBaseWrapper(
            config["workload_info"]["workload"],
            config["workload_info"]["script"]
        )
    
    # Create DBMS executor
    if db_cluster_path is not None:
        config.set("dbms_info", "db_cluster", db_cluster_path)
    if db_log_path is not None:
        config.set("dbms_info", "db_log_filepath", db_log_path)
    config.set("dbms_info", "user", db_usr)
    config.set("dbms_info", "password", db_pwd)
    if config["dbms_info"]["dbms_name"] == "postgres":
        from cybernetics.dbms_interface.postgres import PostgresWrapper

        postgres_wrapper = PostgresWrapper(
            config["dbms_info"], 
            workload_wrapper,
            config["results"]["save_path"]
        )

    # Init DBMS config space
    dbms_config_space_generator = KnobSpaceGenerator(
        config["knob_space"]["knob_spec"],
        int(config["knob_space"]["random_seed"])
    )
    dbms_config_space = dbms_config_space_generator.generate_input_space(
        ignored_knobs=[]
    )
    
    # Init tuning engine
    tuning_engine = TuningEngine(
        config, postgres_wrapper, dbms_config_space, workload_wrapper
    )
    tuning_engine.run()
