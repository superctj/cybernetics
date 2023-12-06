import argparse

from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE
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
    
    # # Set global random state
    # fix_global_random_state(args.random_seed)

    # # Parse configuration
    # config_parser = parse_config(args.config_path)

    # Create logger for the main module
    main_logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(module_name=__name__)
    
    # if config_parser["dbms_info"]["name"] == "postgres":
    #     from cybernetics.db_interface.postgres import PostgresWrapper
