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

    args = parser.parse_args()

    # Parse configuration
    config = parse_config(args.config_path)

    # Set global random state
    print(config["knob_space"])
    fix_global_random_state(int(config["knob_space"]["random_seed"]))

    # Create workload wrapper
    if config["workload_info"]["framework"] == "benchbase":
        from cybernetics.workload.benchbase import BenchBaseWrapper
        

        workload_wrapper = BenchBaseWrapper(
            config["workload_info"]["workload"],
            config["workload_info"]["first_script"],
            config["workload_info"]["script"],
        )
        
        
    
    # Create DBMS executor
    if config["dbms_info"]["dbms_name"] == "postgres":
        from cybernetics.dbms_interface.postgres import PostgresWrapper


        postgres_wrapper = PostgresWrapper(
            config["dbms_info"], 
            workload_wrapper,
            config["results"]["save_path"]
        )
    
    # executes same loads ============================
    sample_times = 50
    # import json
    # with open(config["knob_space"]["knob_spec"], 'r') as f:
    #     data = json.load(f)
    # knobs_list = list(data)
    #print(knobs_list)

    
    postgres_wrapper.reset_knobs_by_restarting_db()
    for i in range(sample_times):
        postgres_wrapper.workload_wrapper.run()
        
    # import glob

    # directory = f"/home/zhenyu/MLforDB/cybernetics/exps/benchbase_tpcc/postgres/bo_gp/*.summary.json"
    # metrics_files = glob.glob(directory)
    # metrics_files = sorted(metrics_files)

    # for file_name in metrics_files:
    #     with open(file_name,'r') as f:
    #         json_data = f.read()
    #     data_dict = json.loads(json_data)
    #     y.append(data_dict["Latency Distribution"]["Median Latency (microseconds)"])
    
    # print(X)
    # print(y)

    # file_path1 = "knobSelection_X.json"
    # file_path2 = "knobSelection_Y.json"

    # with open(file_path1, 'w') as file:
    #     json.dump(X, file)
    # with open(file_path2, 'w') as file:
    #     json.dump(y, file)

    # from KnobSelection import LassoFeatureSelector as LFS
    # selector = LFS(X,y,10)
    # print(selector.get_feature())
    # keepIndices = selector.get_feature()
    # tobeIgnoreKnobs = []
    # for i in range(len(knobs_list)):
    #     if i not in keepIndices:
    #         tobeIgnoreKnobs.append(knobs_list[i]["name"])
    # print(tobeIgnoreKnobs)
    # executes workload ends ===============================

    # Init DBMS config space
