""" Core logic for configuration tuning.

This module is adapted from DBTune's tuner.py and Llamatune's run-smac.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/tuner.py
https://github.com/uw-mad-dash/llamatune/blob/main/run-smac.py
"""

import time
import numpy as np
from cybernetics.tuning.dbms_config_optimizer import (
    get_bo_optimizer,
    get_ddpg_optimizer,
    get_liquid_ddpg_optimizer,
)
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE
from cybernetics.utils.exp_tracker import ExperimentState

class TuningEngine:
    def __init__(self, config, dbms_wrapper, dbms_config_space, workload_wrapper, adapter=None):
        self.config = config
        self.dbms_wrapper = dbms_wrapper
        self.dbms_config_space = dbms_config_space
        self.workload_wrapper = workload_wrapper
        self.adapter = adapter
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()
        self.exp_state = ExperimentState(
            config["dbms_info"],
            config["workload_info"],
            config["config_optimizer"]["target_metric"],
            config["results"]["save_path"]
        )
        self.target_metric = self.config["config_optimizer"]["target_metric"]
        self.optimizer = self.init_optimizer()
        self.logger.info("DBMS config optimizer is ready.")
        self.start_time = time.time()
        self.evaluation_time = 0

    def target_function(self, dbms_config, seed: int):
        if self.adapter:
            dbms_config = self.adapter.unproject_point(dbms_config)

        beg_time = time.time()
        rtn_predicate = self.dbms_wrapper.apply_knobs(dbms_config)
        assert rtn_predicate, "Failed to apply DBMS configuration."

        self.workload_wrapper.run()
        performance = self.dbms_wrapper.get_benchbase_metrics()

        end_time = time.time()
        self.evaluation_time += end_time - beg_time

        optimization_time = end_time - self.start_time - self.evaluation_time
        self.logger.info("TOTAL USED EVALUATION TIME: " + str(self.evaluation_time))
        self.logger.info("TOTAL USED OPTIMIZATION TIME: " + str(optimization_time))

        if self.target_metric == "throughput":
            throughput_noise = performance.get("Throughput (noise)", 0)
            self.logger.info(f"Throughput with Noise (requests/second): {throughput_noise}")

            if throughput_noise == 0 or np.isnan(throughput_noise):
                self.logger.warning("Invalid throughput noise value encountered.")
                return float('inf')

            if self.exp_state.best_perf is None or throughput_noise > self.exp_state.best_perf:
                self.exp_state.best_perf = throughput_noise
                self.exp_state.best_config = dbms_config

            if self.exp_state.worst_perf is None or throughput_noise < self.exp_state.worst_perf:
                self.exp_state.worst_perf = throughput_noise
                self.exp_state.worst_config = dbms_config

            return -throughput_noise

        elif self.target_metric == "latency":
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            self.logger.info(f"95th Percentile Latency (microseconds): {latency}")

            if self.exp_state.best_perf is None or latency < self.exp_state.best_perf:
                self.exp_state.best_perf = latency
                self.exp_state.best_config = dbms_config

            if self.exp_state.worst_perf is None or latency > self.exp_state.worst_perf:
                self.exp_state.worst_perf = latency
                self.exp_state.worst_config = dbms_config

            return latency

    def init_optimizer(self):
        if self.config["config_optimizer"]["optimizer"].startswith("bo"):
            self.logger.info("Initiating BO-based optimizer...")
            optimizer = get_bo_optimizer(self.config, self.dbms_config_space, self.target_function)
        elif self.config["config_optimizer"]["optimizer"].startswith("rl"):
            self.logger.info("Initiating RL-based optimizer...")
            optimizer = get_ddpg_optimizer(self.config, self.dbms_config_space, self.rl_target_function, self.exp_state)
        elif self.config["config_optimizer"]["optimizer"].startswith("liquid"):
            self.logger.info("Initiating Liquid-RL-based optimizer...")
            optimizer = get_liquid_ddpg_optimizer(self.config, self.dbms_config_space, self.rl_target_function, self.exp_state)
        else:
            raise ValueError(f"Optimizer {optimizer} not supported.")
        return optimizer

    def run(self):
        beg_time = time.time()
        self.dbms_wrapper.reset_knobs_by_restarting_db()
        self.workload_wrapper.run()
        performance = self.dbms_wrapper.get_benchbase_metrics()
        end_time = time.time()
        self.evaluation_time += end_time - beg_time
        optimization_time = end_time - self.start_time - self.evaluation_time
        self.logger.info("TOTAL USED EVALUATION TIME: " + str(self.evaluation_time))
        self.logger.info("TOTAL USED OPTIMIZATION TIME: " + str(optimization_time))

        if self.target_metric == "throughput":
            throughput_noise = performance.get("Throughput (noise)", 0)
            self.exp_state.default_perf = throughput_noise
            self.exp_state.best_perf = throughput_noise
            self.exp_state.worst_perf = throughput_noise
            self.logger.info(f"Default Throughput with Noise (requests/second): {throughput_noise}")

        elif self.target_metric == "latency":
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            self.exp_state.default_perf = latency
            self.exp_state.best_perf = latency
            self.exp_state.worst_perf = latency
            self.logger.info(f"Default 95th Percentile Latency (microseconds): {latency}")

        if hasattr(self.optimizer, "optimize"):
            best_dbms_config = self.optimizer.optimize()
        else:
            best_dbms_config = self.optimizer.run()

        self.logger.info("\nCompleted DBMS configuration tuning.")
        self.logger.info(f"\nBest DBMS Configuration:\n{best_dbms_config}")
        self.logger.info(f"\nWorst DBMS Configuration:\n{self.exp_state.worst_config}")

        if self.exp_state.target_metric == "throughput":
            self.logger.info(f"Best Throughput with Noise: {self.exp_state.best_perf} ops/sec")
            self.logger.info(f"Worst Throughput with Noise: {self.exp_state.worst_perf} ops/sec")
        else:
            self.logger.info(f"Best 95-th Latency: {self.exp_state.best_perf} microseconds")
            self.logger.info(f"Worst 95-th Latency: {self.exp_state.worst_perf} microseconds")
