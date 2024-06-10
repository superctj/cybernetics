import argparse

from cybernetics.tuning.engine import TuningEngine
from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.utils.util import fix_global_random_state, parse_config
from cybernetics.dbms_interface.postgres import PostgresWrapper

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
    
    # Debugging: Print the sections and keys in the configuration file
    print("Parsed Configuration:")
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config.items(section):
            print(f"{key} = {value}")

    # Set global random state
    try:
        fix_global_random_state(int(config["knob_space"]["random_seed"]))
    except KeyError as e:
        print(f"KeyError: {e} not found in the configuration file.")
        raise

    # Create workload wrapper
    if config["workload_info"]["framework"] == "benchbase":
        from cybernetics.workload.benchbase import BenchBaseWrapper
        
        workload_wrapper = BenchBaseWrapper(
            config["workload_info"]["workload"],
            config["workload_info"]["script"]
        )
    
    # Create DBMS executor
    if config["dbms_info"]["dbms_name"] == "postgres":

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
