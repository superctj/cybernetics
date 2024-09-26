import argparse

from cybernetics.tuning.engine import TuningEngine
from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.utils.util import fix_global_random_state, parse_config, get_benchbase_postgres_target_dir, get_postgres_user_and_password

if __name__ == "__main__":
    # Parsing command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the configuration file",
    )

    parser.add_argument(
        "--projection_dim",
        type=int,
        required=False,
        help="Number of dimensions to project to (optional. Suggested value: 16)",  # noqa: E501
    )
    parser.add_argument(
        "--quantization_factor",
        type=float,
        required=False,
        help="Quantization factor (optional. Suggested value: 10000)",
    )
    parser.add_argument(
        "--bias_prob",
        type=float,
        required=False,
        help="Bias for selecting special values (optional. Suggested value: 0.2)",  # noqa: E501
    )

    args = parser.parse_args()

    # Parse configuration
    config = parse_config(args.config_path)
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

    # Init DBMS config space
    dbms_config_space_generator = KnobSpaceGenerator(
        config["knob_space"]["knob_spec"],
        int(config["knob_space"]["random_seed"]),
    )
    dbms_config_space = dbms_config_space_generator.generate_input_space(
        ignored_knobs=[]
    )

    # PROJECTING POINTS
    target_dim = args.projection_dim
    bias_prob = args.bias_prob
    quantization_factor = args.quantization_factor
    adapter = dbms_config_space_generator.get_input_space_adapter(
        dbms_config_space, target_dim, bias_prob, quantization_factor
    )
    if adapter:
        dbms_config_space = adapter.target

    # Init tuning engine
    tuning_engine = TuningEngine(
        config,
        postgres_wrapper,
        dbms_config_space,
        workload_wrapper,
        adapter=adapter,
    )
    tuning_engine.run()
