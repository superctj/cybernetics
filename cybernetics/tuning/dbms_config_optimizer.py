"""DBMS configuration optimizers.

Adapted from https://github.com/uw-mad-dash/llamatune/blob/main/optimizer.py
"""

from functools import partial

import ConfigSpace.hyperparameters as CSH
import numpy as np
import smac.initial_design as smac_init_design

from ConfigSpace import ConfigurationSpace
from smac import BlackBoxFacade as BBFacade
from smac import HyperparameterOptimizationFacade as HPOFacade
from smac import Scenario

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

    target_function = partial(target_function,
                              seed=int(config["knob_space"]["random_seed"]))

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
                       target_function, exp_state):
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
            n_configs=int(config["config_optimizer"]["n_initial_configs"]),
            seed=int(config["knob_space"]["random_seed"])
        )

    # DDPG Model
    from cybernetics.tuning.ddpg.model import DDPG
    
    n_states = int(config["dbms_info"]["n_numeric_stats"])
    n_actions = len(dbms_config_space)
    model = DDPG(n_states, n_actions, model_name="ddpg_model")

    target_function = partial(target_function,
                              seed=int(config["knob_space"]["random_seed"]))
    optimizer = DDPGOptimizer(
        model,
        target_function,
        initial_design,
        int(config["config_optimizer"]["n_total_configs"]),
        int(config["config_optimizer"]["n_epochs"]),
        exp_state,
        is_liquid= False
    )

    return optimizer

def get_liquid_ddpg_optimizer(config, dbms_config_space: ConfigurationSpace,
                       target_function, exp_state):
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
            n_configs=int(config["config_optimizer"]["n_initial_configs"]),
            seed=int(config["knob_space"]["random_seed"])
        )

    # DDPG Model
    from cybernetics.tuning.ddpg.liquid_model import DDPG
    
    n_states = int(config["dbms_info"]["n_numeric_stats"])
    n_actions = len(dbms_config_space)
    model = DDPG(n_states, n_actions, model_name="ddpg_model")

    target_function = partial(target_function,
                              seed=int(config["knob_space"]["random_seed"]))
    optimizer = DDPGOptimizer(
        model,
        target_function,
        initial_design,
        int(config["config_optimizer"]["n_total_configs"]),
        int(config["config_optimizer"]["n_epochs"]),
        exp_state,
        True
    )

    return optimizer



class DDPGOptimizer:
    def __init__(self, model, target_function, initial_design, n_iters: int,
                 n_epochs: int, exp_state, is_liquid):
        # assert exp_state.target_metric == "throughput" # TODO: Check why this is necessary

        self.exp_state = exp_state
        self.model = model
        self.target_function = target_function
        self.initial_design = initial_design
        self.input_space = initial_design._configspace
        self.n_iters = n_iters
        self.n_epochs = n_epochs # CDBTune uses 2
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()
        self.is_liquid = is_liquid

    def run(self):
        # If using liquid model, initialized the hidden state
        if self.is_liquid:
            hidden = None

        prev_perf = self.exp_state.default_perf
        assert prev_perf >= 0 # TODO: Check why this is necessary

        # Bootstrap with random samples
        init_configurations = self.initial_design.select_configurations()

        for i, dbms_config in enumerate(init_configurations):
            self.logger.info(f"Iter {i} -- Sample from Initial Design:")

            perf, numeric_stats = self.target_function(dbms_config)
            assert perf >= 0
            
            # Compute reward
            reward = self.get_reward(perf, prev_perf)

            self.logger.info(f"Performance: {perf}")
            self.logger.info(f"DBMS numeric stats: {numeric_stats}")
            self.logger.info(f"Reward: {reward}")

            if i > 0:
                self.model.add_sample(prev_numeric_stats, prev_dbms_config,
                                      prev_reward, numeric_stats)

            prev_numeric_stats = numeric_stats
            prev_dbms_config = dbms_config.get_array() # scale to [0, 1]
            prev_reward = reward
            prev_perf = perf

        # Add last random sample
        self.model.add_sample(prev_numeric_stats, prev_dbms_config,
                              prev_reward, numeric_stats)
        
        # To count the number of update, delete later
        # numUpdate = 0

        # Start guided search
        for i in range(len(init_configurations), self.n_iters):
            self.logger.info(f"Iter {i} -- Sample from DDPG:")
            
            # Get next recommendation from DDPG
            if self.is_liquid:
                ddpg_action, hidden = self.model.choose_action(prev_numeric_stats, hidden)
            else:
                ddpg_action = self.model.choose_action(prev_numeric_stats)

            dbms_config = self.convert_ddpg_action_to_dbms_config(ddpg_action)

            perf, numeric_stats = self.target_function(dbms_config)
            assert perf >= 0
            
            # Compute reward
            reward = self.get_reward(perf, prev_perf)

            self.logger.info(f"Performance: {perf}")
            self.logger.info(f"DBMS numeric stats: {numeric_stats}")
            self.logger.info(f"Reward: {reward}")

            # register point to the optimizer
            self.model.add_sample(prev_numeric_stats, prev_dbms_config,
                                  prev_reward, numeric_stats)

            prev_numeric_stats = numeric_stats
            prev_dbms_config = ddpg_action
            prev_reward = reward
            prev_perf = perf

            # update DDPG model
            if len(self.model.replay_memory) >= self.model.batch_size:
                for _ in range(self.n_epochs):
                    self.model.update()
                    # For debugging, delete later
                    # numUpdate += 1
                    # print(f'Number of Update done: {numUpdate}.')
        
        return self.exp_state.best_config

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

        if perf == self.exp_state.worst_perf:
            return 0

        # perf diff from default / prev evaluation
        delta_default = (perf - self.exp_state.default_perf) / self.exp_state.default_perf
        delta_prev = (perf - prev_perf) / prev_perf

        return calculate_reward(delta_default, delta_prev)

    def convert_ddpg_action_to_dbms_config(self, ddpg_action) -> dict:
        dbms_config = {}

        # TODO: Need to double check if model_outputs matches the input space
        for hp, ddpg_value in zip(self.input_space.get_hyperparameters(), ddpg_action):
            if isinstance(hp, CSH.CategoricalHyperparameter):
                choice_idx = int(round(ddpg_value * (hp.num_choices - 1)))
                dbms_config[hp.name] = hp.choices[choice_idx]
            elif isinstance(hp, CSH.UniformIntegerHyperparameter) or isinstance(hp, CSH.UniformFloatHyperparameter):
                dbms_config[hp.name] = hp._transform(ddpg_value)
            else:
                raise NotImplementedError()

        return dbms_config
