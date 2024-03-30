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
    fix_global_random_state(int(config["knob_space"]["random_seed"]))

    # Create workload wrapper
    if config["workload_info"]["framework"] == "benchbase":
        from cybernetics.workload.benchbase import BenchBaseWrapper
        
        #Initialize the knob selection workload
        # sample_workload_wrapper = BenchBaseWrapper(
        #    config["workload_info"]["workload"],
        #    config["workload_info"]["sample_script"]
        # )

        workload_wrapper = BenchBaseWrapper(
            config["workload_info"]["workload"],
            config["workload_info"]["first_script"],
            config["workload_info"]["script"],
        )
        
        
    
    # Create DBMS executor
    if config["dbms_info"]["dbms_name"] == "postgres":
        from cybernetics.dbms_interface.postgres import PostgresWrapper

        # sample_postgres_wrapper = PostgresWrapper(
        #    config["dbms_info"], 
        #    workload_wrapper,
        #    config["results"]["sample_save_path"]
        #)

        postgres_wrapper = PostgresWrapper(
            config["dbms_info"], 
            workload_wrapper,
            config["results"]["save_path"]
        )
    
    # knobSelection starts ============================
    #execute to start knob selection
    # sample_times = 20
    # import json
    # with open(config["knob_space"]["knob_spec"], 'r') as f:
    #     data = json.load(f)
    # knobs_list = list(data)
    # #print(knobs_list)

    
    # import random

    # def sample_knob_val():
    #     knobs_dict = {}
    #     x_point = []
    #     for knob in knobs_list:
    #         try:
    #             knobs_dict[knob["name"]] = random.randint(int(knob["min_val"]),int(knob["max_val"]))
    #             x_point.append(knobs_dict[knob["name"]])
    #         except:
    #             knobs_dict[knob["name"]] = random.choice(knob["enumvals"])
    #             x_point.append(knob["enumvals"].index(knobs_dict[knob["name"]])) # TODO 
    #     return knobs_dict,x_point

    # X = []
    # y = []  
    # for i in range(sample_times):
    #     knobs_dict,x_point = sample_knob_val()
    #     X.append(x_point)
    #     sample_postgres_wrapper.apply_knobs(knobs_dict)
    #     print("knobs changed")
    #     sample_postgres_wrapper.workload_wrapper.run()
        
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
    # knobSelection ends ===============================

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
