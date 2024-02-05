"""DBMS configuration optimizers.

Adapted from https://github.com/uw-mad-dash/llamatune/blob/main/optimizer.py
"""

from functools import partial

from ConfigSpace import ConfigurationSpace
from smac import BlackBoxFacade as BBFacade
from smac import HyperparameterOptimizationFacade as HPOFacade
from smac import Scenario

# from cybernetics.knobs.bias_sampling import LHDesignWithBiasedSampling
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


def get_bo_optimizer(config, dbms_config_space: ConfigurationSpace, target_function):
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


def get_ddpg_optimizer(config, dbms_config_space: ConfigurationSpace, target_function, state):
    pass
    # random number generator
    # rng = np.random.RandomState(seed=config.seed)

    # from smac.stats.stats import Stats
    # from smac.utils.io.traj_logging import TrajLogger
    # from smac.utils.io.output_directory import create_output_directory

    # scenario = Scenario({
    #     "run_obj": "quality",
    #     "runcount-limit": config.iters,
    #     "cs": dbms_config_space,
    #     "deterministic": "true",
    #     "always_race_default": "false",
    #     # disables pynisher, which allows for shared state
    #     "limit_resources": "false",
    #     "output_dir": state.results_path,
    # })

    # output_dir = create_output_directory(scenario, 0)
    # stats = Stats(scenario)
    # traj_logger = TrajLogger(output_dir=output_dir, stats=stats)

    # # Latin Hypercube design, with 10 iters
    # init_rand_samples = int(config["optimizer"].get("init_rand_samples", 10))
    # init_design_def_kwargs = {
    #     "cs": input_space,
    #     "rng": rng,
    #     "traj_logger": traj_logger, # required
    #     "ta_run_limit": 99999999999,
    #     "max_config_fracs": 1,
    #     "init_budget": init_rand_samples,
    # }
    # initial_design = LHDesignWithBiasedSampling(**init_design_def_kwargs)

    # Random conf chooser
    # from smac.optimizer.random_configuration_chooser import ChooserProb

    # rand_percentage = float(config["optimizer"]["rand_percentage"])
    # assert 0 <= rand_percentage <= 1, "Optimizer rand optimizer must be between 0 and 1"
    # rcc_rng = np.random.RandomState(seed=config.seed)
    # rand_conf_chooser = ChooserProb(rcc_rng, rand_percentage)

    # DDPG Model
    # from cybernetics.tuning.ddpg.model import DDPG
    # n_states = config.num_dbms_metrics
    # n_actions = len(input_space)

    # model = DDPG(n_states, n_actions, model_name="ddpg_model")

    # tae_runner = partial(tae_runner, state=state)
    # optimizer = DDPGOptimizer(state, model, tae_runner, initial_design, rand_conf_chooser, config.iters, logging_dir=state.results_path)

    # return optimizer


class DDPGOptimizer:
    def __init__(self, state, model, func, initial_design, rand_conf_chooser,
                    n_iters, logging_dir=None):
        assert state.target_metric == "throughput"

        self.state = state
        self.model = model
        self.func = func
        self.initial_design = initial_design
        self.input_space = initial_design.cs
        self.rand_conf_chooser = rand_conf_chooser
        self.n_iters = n_iters
        self.n_epochs = 2 # same value as CDBTune

        self.logging_dir = logging_dir

    def run(self):
        prev_perf = self.state.default_perf
        assert prev_perf >= 0

        results = [ ]

        # Bootstrap with random samples
        init_configurations = self.initial_design.select_configurations()
        for i, knob_data in enumerate(init_configurations):
            print(f"Iter {i} -- RANDOM")
            ### reward, metric_data = env.simulate(knob_data)
            # metrics & perf
            perf, metric_data = self.func(knob_data)
            perf = -perf # maximize
            assert perf >= 0
            # compute reward
            reward = self.get_reward(perf, prev_perf)
            # LOG
            print(f"Iter {i} -- PERF = {perf}")
            print(f"Iter {i} -- METRICS = {metric_data}")
            print(f"Iter {i} -- REWARD = {reward}")

            if i > 0:
                self.model.add_sample(prev_metric_data, prev_knob_data, prev_reward, metric_data)

            prev_metric_data = metric_data
            prev_knob_data = knob_data.get_array() # scale to [0, 1]
            prev_reward = reward
            prev_perf = perf

        # add last random sample
        self.model.add_sample(prev_metric_data, prev_knob_data, prev_reward, metric_data)

        # Start guided search
        for i in range(len(init_configurations), self.n_iters):

            if self.rand_conf_chooser.check(i):
                print(f"Iter {i} -- RANDOM SAMPLE")
                # get random sample from config space
                knob_data = self.input_space.sample_configuration()
                knob_data_vector = knob_data.get_array()
            else:
                print(f"Iter {i} -- GUIDED")
                # get next recommendation from DDPG
                knob_data_vector = self.model.choose_action(prev_metric_data)
                knob_data = self.convert_from_vector(knob_data_vector)

            # metrics & perf
            perf, metric_data = self.func(knob_data)
            perf = -perf # maximize
            assert perf >= 0
            # compute reward
            reward = self.get_reward(perf, prev_perf)
            # LOG
            print(f"Iter {i} -- PERF = {perf}")
            print(f"Iter {i} -- METRICS = {metric_data}")
            print(f"Iter {i} -- REWARD = {reward}")

            # register point to the optimizer
            self.model.add_sample(prev_metric_data, prev_knob_data, prev_reward, metric_data)

            prev_metric_data = metric_data
            prev_knob_data = knob_data_vector
            prev_reward = reward
            prev_perf = perf

            # update DDPG model
            if len(self.model.replay_memory) >= self.model.batch_size:
                for _ in range(self.n_epochs):
                    self.model.update()
            print("AFTER UPDATE")

    def get_reward(self, perf, prev_perf):
        """ Reward calculation same as CDBTune paper -- Section 4.2 """
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
