import ConfigSpace.hyperparameters as CSH
import numpy as np
import smac.initial_design as smac_init_design

from smac import Scenario

from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.tuning.dbms_config_optimizer import DDPGOptimizer


def test_convert_ddpg_action_to_dbms_config():
    dbms_param_spec = "/home/aditk/cybernetics/cybernetics/knobs/postgres_12.17_pgtune_knobs.json"
    n_initial_configs = 10
    random_seed = 12345
    results_save_path = "/home/aditk/cybernetics/exps/benchbase_tpcc/postgres/rl_ddpg"
    
    # Consider shared_buffers (integer), checkpoint_completion_target (float), and huge_pages (enum) for testing
    ignored_knobs = [
        "max_connections", "effective_cache_size", "maintenance_work_mem",
        "wal_buffers", "default_statistics_target", "random_page_cost",
        "effective_io_concurrency", "work_mem", "min_wal_size", "max_wal_size",
        "max_worker_processes", "max_parallel_workers_per_gather",
        "max_parallel_workers", "max_parallel_maintenance_workers"
    ]

    dbms_config_space_generator = KnobSpaceGenerator(
        dbms_param_spec,
        random_seed
    )

    dbms_config_space = dbms_config_space_generator.generate_input_space(
        ignored_knobs
    )

    scenario = Scenario(
        configspace=dbms_config_space,
        output_directory=results_save_path,
        deterministic=True,
        objectives="cost", # minimize the objective
        n_trials=100, # 100 is the default value
        seed=random_seed
    )

    initial_design = smac_init_design.RandomInitialDesign(
            scenario=scenario,
            n_configs=n_initial_configs,
            seed=random_seed
        )

    ddpg_optimizer = DDPGOptimizer(None, None, initial_design, None, None, None)

    ddpg_action = np.array([0.1, 0.5, 0.9])
    dbms_config = ddpg_optimizer.convert_ddpg_action_to_dbms_config(ddpg_action)

    for dbms_param_name, dbms_param_value in dbms_config.items():
        hp = dbms_config_space[dbms_param_name]
        if isinstance(hp, CSH.CategoricalHyperparameter):
            assert dbms_param_value in hp.choices
        elif isinstance(hp, CSH.UniformIntegerHyperparameter) or isinstance(hp, CSH.UniformFloatHyperparameter):
            assert hp.lower <= dbms_param_value <= hp.upper
