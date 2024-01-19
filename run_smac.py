import argparse

from cybernetics.tuning.engine import TuningEngine
from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE, create_dir
from cybernetics.utils.util import fix_global_random_state, parse_config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the configuration file"
    )

    args = parser.parse_args()

    # Parse configuration
    config = parse_config(args.config_path)

    # Set global random state
    fix_global_random_state(config["config_optimizer"]["random_seed"])

    # Create logger for the main module
    # main_logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(module_name=__name__)

    # Create workload wrapper
    if config["workload_info"]["benchmark"] == "benchbase":
        from cybernetics.workload.benchbase import BenchBaseWrapper
        workload_wrapper = BenchBaseWrapper(
            config["benchmark_info"]["workload"],
            config["benchmark_info"]["script"])
    
    # Create DBMS executor
    if config["dbms_info"]["dbms_name"] == "postgres":
        from cybernetics.db_interface.postgres import PostgresWrapper
        postgres_wrapper = PostgresWrapper(config["dbms_info"], 
                                           workload_wrapper)

    # Init DBMS config space
    dbms_config_space_generator = KnobSpaceGenerator(
        config["knob_space"]["knob_spec"], args.random_seed)
    dbms_config_space = dbms_config_space_generator.generate_input_space(
        ignored_knobs=[])
    
    # Init tuning engine
    tuning_engine = TuningEngine(
        config, postgres_wrapper, dbms_config_space, workload_wrapper
    )
    tuning_engine.run()
