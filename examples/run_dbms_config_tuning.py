import argparse

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

    # Init DBMS config space
    dbms_config_space_generator = KnobSpaceGenerator(
        config["knob_space"]["knob_spec"],
        int(config["knob_space"]["random_seed"]),
    )
    dbms_config_space = dbms_config_space_generator.generate_input_space(
        ignored_knobs=[]
    )

    # Init tuning engine
    tuning_engine = TuningEngine(
        config, postgres_wrapper, dbms_config_space, workload_wrapper
    )
    tuning_engine.run()
