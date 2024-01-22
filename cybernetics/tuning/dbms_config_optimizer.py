"""DBMS configuration optimizers.

https://github.com/uw-mad-dash/llamatune/blob/main/optimizer.py
"""

from functools import partial

from ConfigSpace import ConfigurationSpace
from smac import BlackBoxFacade as BBFacade
from smac import HyperparameterOptimizationFacade as HPOFacade
from smac import Scenario

# from cybernetics.knobs.bias_sampling import LHDesignWithBiasedSampling
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(__name__)


def get_bo_optimizer(config, dbms_config_space: ConfigurationSpace, target_function):
    logger.info("Constructing BO-based optimizer...")
    # logger.info(f"Run History: {run_history}")
    # logger.info(f"Ignored knobs: {ignored_knobs}")

    scenario = Scenario(
        configspace=dbms_config_space,
        output_directory=config["results"]["save_path"],
        deterministic=True,
        objectives="cost", # minimize the objective
        n_trials=100,
        seed=int(config["knob_space"]["random_seed"])
    )

    target_function = partial(target_function, seed=int(config["knob_space"]["random_seed"]))

    if config["config_optimizer"]["optimizer"] == "bo-gp":
        optimizer = BBFacade(
            scenario=scenario,
            target_function=target_function
        )
    elif optimizer == "bo-rf":
        optimizer = HPOFacade(
            scenario=scenario,
            target_function=target_function
        )
    else:
        raise ValueError(f"Optimizer {optimizer} not supported.")
    
    return optimizer


# def get_smac_optimizer(config, knob_space: ConfigurationSpace, tae_runner, state, ignored_knobs=None, run_history=None):
#     logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(__name__)
#     logger.info("Constructing new optimizer...")
#     logger.info(f"Run History: {run_history}")
#     logger.info(f"Ignored knobs: {ignored_knobs}")

#     # Generate input (i.e. knobs) and output (i.e. perf metric) space
#     input_space = knob_space.generate_input_space(
#         config.seed, ignore_extra_knobs=ignored_knobs)

#     logger.info(f"\ninput space:\n{input_space}")

#     scenario = Scenario({
#         "run_obj": "quality",
#         "runcount-limit": config.iters,
#         "cs": input_space,
#         "deterministic": "true",
#         "always_race_default": "false",
#         # disables pynisher, which allows for shared state
#         "limit_resources": "false",
#         "output_dir": state.results_path,
#     })

    # Latin Hypercube design, with 10 iters
    # init_rand_samples = int(config["optimizer"].get("init_rand_samples", 10))
    # initial_design = LHDesignWithBiasedSampling
    # initial_design_kwargs = {
    #     "init_budget": init_rand_samples,
    #     "max_config_fracs": 1,
    # }

    # Get RF params from config
    # rand_percentage = float(config["optimizer"]["rand_percentage"])
    # assert 0 <= rand_percentage <= 1, "Optimizer random percentage must be between 0 and 1"
    # n_estimators = int(config["optimizer"]["n_estimators"])

    # #  how often to evaluate a random sample
    # random_configuration_chooser_kwargs = {
    #     "prob": rand_percentage,
    # }

    # tae_runner = partial(tae_runner, state=state)

    # model_type = config["optimizer"].get("model_type", "rf") # default is RF-SMACHPO
    # assert model_type in ["rf", "gp", "mkbo"], "Model type %s not supported" % model_type

    # if model_type == "rf":
    #     # RF model params -- similar to MLOS ones
    #     model_kwargs = {
    #         "num_trees": n_estimators,
    #         "log_y": False,         # no log scale
    #         "ratio_features": 1,    #
    #         "min_samples_split": 2, # min number of samples to perform a split
    #         "min_samples_leaf": 3,  # min number of smaples on a leaf node
    #         "max_depth": 2**20,     # max depth of tree
    #     }
    #     optimizer = SMAC4HPO(
    #         scenario=scenario,
    #         tae_runner=tae_runner,
    #         rng=config.seed,
    #         model_kwargs=model_kwargs,
    #         initial_design=initial_design,
    #         initial_design_kwargs=initial_design_kwargs,
    #         random_configuration_chooser_kwargs=random_configuration_chooser_kwargs,
    #     )

    # elif model_type == "gp":
    #     optimizer = SMAC4BB(
    #         model_type="gp",
    #         scenario=scenario,
    #         tae_runner=tae_runner,
    #         rng=config.seed,
    #         initial_design=initial_design,
    #         initial_design_kwargs=initial_design_kwargs,
    #         random_configuration_chooser_kwargs=random_configuration_chooser_kwargs,
    #     )

    # elif model_type == "mkbo":
    #     # OpenBox
    #     import openbox
    #     # openbox.utils.limit._platform = "Windows" # Patch to avoid objective function wrapping
    #     optimizer = openbox.Optimizer(
    #         tae_runner,
    #         input_space,
    #         num_objs=1,
    #         num_constraints=0,
    #         max_runs=config.iters,
    #         surrogate_type="gp",
    #         acq_optimizer_type="local_random",
    #         initial_runs=10,
    #         init_strategy="random_explore_first",
    #         time_limit_per_trial=10**6,
    #         logging_dir=state.results_path,
    #         random_state=config.seed,
    #     )

    # logger.info(optimizer)
    # return optimizer
