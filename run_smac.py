import argparse

from cybernetics.tuning.engine import TuningEngine
from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.tuning.db_config_optimizer import get_smac_optimizer
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE, create_dir
from cybernetics.utils.exp_tracker import ExperimentState
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
        "--random_seed",
        type=int,
        default=12345,
        required=True,
        help="Random seed for deterministic experiments"
    )

    args = parser.parse_args()
    
    # Set global random state
    fix_global_random_state(args.random_seed)

    # Parse configuration
    config_parser = parse_config(args.config_path)

    # Create logger for the main module
    # main_logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(module_name=__name__)

    # Create output directory to store DBMS execution results
    create_dir(config_parser["results"]["save_path"], force=False)

    # Create workload wrapper
    if config_parser["workload_info"]["benchmark"] == "benchbase":
        from cybernetics.workload.benchbase import BenchBaseWrapper
        workload_wrapper = BenchBaseWrapper(
            config_parser["benchmark_info"]["workload"],
            config_parser["benchmark_info"]["script"])
    
    # Create DBMS executor
    if config_parser["dbms_info"]["dbms_name"] == "postgres":
        from cybernetics.db_interface.postgres import PostgresWrapper
        postgres_wrapper = PostgresWrapper(config_parser["dbms_info"], 
                                           workload_wrapper)

    # Init DBMS config space
    db_config_space_generator = KnobSpaceGenerator(
        config_parser["knob_space"]["knob_spec"], args.random_seed)
    db_config_space = db_config_space_generator.generate_input_space(
        ignored_knobs=[])

    # Keep track of experiment state
    exp_state = ExperimentState(config_parser["benchmark_info"], config_parser["dbms_info"], config_parser["optimizer"]["target_metric"])

    # Init optimizer
    optimizer = get_smac_optimizer(
        config_parser, db_config_space, postgres_wrapper, exp_state)
    
    # Run tuning
    tuning_engine = TuningEngine(
        postgres_wrapper, db_config_space, optimizer, exp_state)
    tuning_engine.run()
