"""DBMS configuration optimizers.

Adapted from https://github.com/uw-mad-dash/llamatune/blob/main/optimizer.py
"""

from functools import partial

import numpy as np
import smac.initial_design as smac_init_design

from ConfigSpace import ConfigurationSpace
from smac import BlackBoxFacade as BBFacade
from smac import HyperparameterOptimizationFacade as HPOFacade
from smac import Scenario

# from cybernetics.knobs.bias_sampling import LHDesignWithBiasedSampling
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


def get_bo_optimizer(config, dbms_config_space: ConfigurationSpace,
                     target_function):
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
    elif config["config_optimizer"]["optimizer"] == "bo-rf":
        optimizer = HPOFacade(
            scenario=scenario,
            target_function=target_function
        )
    else:
        raise ValueError(f"Optimizer {optimizer} not supported.")
    
    return optimizer


def get_ddpg_optimizer(config, dbms_config_space: ConfigurationSpace,
                       target_function, state):
    scenario = Scenario(
        configspace=dbms_config_space,
        output_directory=config["results"]["save_path"],
        deterministic=True,
        objectives="cost", # minimize the objective
        n_trials=100, # 100 is the default value
        seed=int(config["knob_space"]["random_seed"])
    )

    if config["config_optimizer"]["initial_design"] == "random":
        initial_design = smac_init_design.RandomInitialDesign(
            scenario=scenario,
            n_configs=config["config_optimizer"]["n_initial_configs"],
            seed=config["knob_space"]["random_seed"]
        )

    # Random conf chooser
    # from smac.optimizer.random_configuration_chooser import ChooserProb
    # rand_percentage = float(config["optimizer"]["rand_percentage"])
    # assert 0 <= rand_percentage <= 1, "Optimizer rand optimizer must be between 0 and 1"
    # rcc_rng = np.random.RandomState(seed=config.seed)
    # rand_conf_chooser = ChooserProb(rcc_rng, rand_percentage)

    # DDPG Model
    from cybernetics.tuning.ddpg.model import DDPG
    
    n_states = config["dbms_info"]["n_internal_metrics"]
    n_actions = len(dbms_config_space)
    model = DDPG(n_states, n_actions, model_name="ddpg_model")

    target_function = partial(target_function,
                              seed=int(config["knob_space"]["random_seed"]))
    optimizer = DDPGOptimizer(state, model, target_function, initial_design,
                              rand_conf_chooser,
                              config["config_optimizer"]["n_total_configs"])

    return optimizer


class DDPGOptimizer:
    def __init__(self, exp_state, model, target_function, initial_design, 
                 rand_conf_chooser, n_iters: int, n_epochs: int=2):
        assert exp_state._target_metric == "throughput"

        self.exp_state = exp_state
        self.model = model
        self.target_function = target_function
        self.initial_design = initial_design
        self.input_space = initial_design.cs
        self.rand_conf_chooser = rand_conf_chooser
        self.n_iters = n_iters
        self.n_epochs = n_epochs # CDBTune uses 2
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()

    def run(self):
        prev_perf = self.state.default_perf
        assert prev_perf >= 0 # TODO: Check why this is necessary

        # Bootstrap with random samples
        init_configurations = self.initial_design.select_configurations()

        for i, dbms_config in enumerate(init_configurations):
            self.logger.info(f"Initial Design -- Iter {i}:")

            perf, internal_metrics = self.target_function(dbms_config)
            perf = -perf # maximize
            assert perf >= 0 # TODO: Need to double check this assertion
            # compute reward
            reward = self.get_reward(perf, prev_perf)

            self.logger.info(f"Performance: {perf}")
            self.logger.info(f"Internal Metrics: {internal_metrics}")
            self.logger.info(f"Reward: {reward}")

            if i > 0:
                self.model.add_sample(prev_internal_metrics, prev_dbms_config,
                                      prev_reward, internal_metrics)

            prev_internal_metrics = internal_metrics
            prev_dbms_config = dbms_config.get_array() # scale to [0, 1]
            prev_reward = reward
            prev_perf = perf

        # Add last random sample
        self.model.add_sample(prev_internal_metrics, prev_dbms_config,
                              prev_reward, internal_metrics)

        # Start guided search
        for i in range(len(init_configurations), self.n_iters):
            if self.rand_conf_chooser.check(i):
                self.logger.info(f"Guided Search -- Iter {i} -- RANDOM:")
                # get random sample from config space
                dbms_config = self.input_space.sample_configuration()
            else:
                self.logger.info(f"Guided Search -- Iter {i} -- DDPG:")
                # get next recommendation from DDPG
                dbms_config = self.model.choose_action(prev_internal_metrics)

            # metrics & perf
            perf, metric_data = self.target_function(dbms_config)
            perf = -perf # maximize
            assert perf >= 0
            # compute reward
            reward = self.get_reward(perf, prev_perf)

            self.logger.info(f"Performance: {perf}")
            self.logger.info(f"Internal Metrics: {internal_metrics}")
            self.logger.info(f"Reward: {reward}")

            # register point to the optimizer
            self.model.add_sample(prev_internal_metrics, prev_dbms_config,
                                  prev_reward, internal_metrics)

            prev_internal_metrics = internal_metrics
            prev_dbms_config = dbms_config
            prev_reward = reward
            prev_perf = perf

            # update DDPG model
            if len(self.model.replay_memory) >= self.model.batch_size:
                for _ in range(self.n_epochs):
                    self.model.update()

    def get_reward(self, perf, prev_perf):
        """Reward calculation same as CDBTune paper -- Section 4.2
        """
        def calculate_reward(delta_default, delta_prev):
            if delta_default > 0:
                reward =   ((1 + delta_default) ** 2 - 1) * np.abs(1 + delta_prev)
            else:
                reward = - ((1 - delta_default) ** 2 - 1) * np.abs(1 - delta_prev)

            # no improvement over last evaluation -- 0 reward
            if reward > 0 and delta_prev < 0:
                reward = 0

            return reward

        if perf == self.state.worse_perf:
            return 0

        # perf diff from default / prev evaluation
        delta_default = (perf - self.state.default_perf) / self.state.default_perf
        delta_prev = (perf - prev_perf) / prev_perf

        return calculate_reward(delta_default, delta_prev)

    # def convert_from_vector(self, vector):
    #     from adapters.bias_sampling import special_value_scaler, UniformIntegerHyperparameterWithSpecialValue

    #     values = { }
    #     for hp, value in zip(self.input_space.get_hyperparameters(), vector):
    #         if isinstance(hp, CSH.NumericalHyperparameter):
    #             if isinstance(hp, UniformIntegerHyperparameterWithSpecialValue):
    #                 value = special_value_scaler(hp, value)
    #             else:
    #                 value = hp._transform(value)
    #         elif isinstance(hp, CSH.CategoricalHyperparameter):
    #             assert hp.num_choices == 2
    #             value = hp.choices[0] if value <= 0.5 else hp.choices[1]
    #         else:
    #             raise NotImplementedError()

    #         values[hp.name] = value

    #     conf = CS.Configuration(self.input_space, values=values)
    #     self.input_space.check_configuration(conf)
    #     return conf
