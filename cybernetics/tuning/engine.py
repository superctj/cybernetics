import time
import json
import os
import logging
from functools import partial
import numpy as np
from ConfigSpace import Configuration
from cybernetics.dbms_config_optimizer import (
    get_bo_optimizer,
    get_ddpg_optimizer,
    get_liquid_ddpg_optimizer,
)
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE
from cybernetics.utils.exp_tracker import ExperimentState

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TuningEngine:
    def __init__(self, config, dbms_wrapper, dbms_config_space, workload_wrapper, adapter=None) -> None:
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
            config["results"]["save_path"],
        )
        self.target_metric = self.config["config_optimizer"]["target_metric"]
        self.optimizer = self.init_optimizer()

        self.logger.info("DBMS config optimizer is ready.")
        self.start_time = time.time()
        self.evaluation_time = 0

    def target_function(self, dbms_config, seed: int):
        """Target function for BO-based optimizer."""
        
        # Unproject the configuration if an adapter is provided
        if self.adapter:
            dbms_config = self.adapter.unproject_point(dbms_config)

        beg_time = time.time()

        # Apply the DBMS configuration and ensure it succeeds
        rtn_predicate = self.dbms_wrapper.apply_knobs(dbms_config)
        assert rtn_predicate, "Failed to apply DBMS configuration."

        # Run the workload and get performance metrics
        self.workload_wrapper.run()
        performance = self.dbms_wrapper.get_benchbase_metrics()

        end_time = time.time()
        self.evaluation_time += end_time - beg_time

        optimization_time = end_time - self.start_time - self.evaluation_time
        self.logger.info(f"TOTAL USED EVALUATION TIME: {self.evaluation_time}")
        self.logger.info(f"TOTAL USED OPTIMIZATION TIME: {optimization_time}")

        # Handle throughput as the target metric
        if self.target_metric == "throughput":
            throughput = performance.get("Throughput (requests/second)", float('nan'))
            self.logger.info(f"Throughput (requests/second): {throughput}")

            # Handle invalid throughput (NaN or Inf)
            if not np.isfinite(throughput):
                self.logger.error("Throughput value is invalid (NaN or Inf). Setting throughput to fallback value.")
                return float('inf')  # Treat invalid throughput as failure

            # Update the best configuration
            if self.exp_state.best_perf is None or throughput > self.exp_state.best_perf:
                self.exp_state.best_perf = throughput
                self.exp_state.best_config = dbms_config
                self.logger.info(f"New best configuration with throughput: {throughput}")
                self.logger.info(f"Best configuration: {dbms_config}")

            # Update the worst configuration
            if self.exp_state.worst_perf is None or throughput < self.exp_state.worst_perf:
                self.exp_state.worst_perf = throughput
                self.exp_state.worst_config = dbms_config
                self.logger.info(f"New worst configuration with throughput: {throughput}")
                self.logger.info(f"Worst configuration: {dbms_config}")

            return -throughput  # Minimize negative throughput to maximize actual throughput

        # Handle latency as the target metric
        elif self.target_metric == "latency":
            latency = performance.get("Latency Distribution", {}).get("95th Percentile Latency (microseconds)", float('nan'))
            self.logger.info(f"95th Percentile Latency (microseconds): {latency}")

            # Handle NaN latency
            if np.isnan(latency):
                self.logger.error("Latency value is NaN. Setting latency to fallback value.")
                return float('inf')  # Treat NaN as a crash/failure

            # Update the best configuration
            if self.exp_state.best_perf is None or latency < self.exp_state.best_perf:
                self.exp_state.best_perf = latency
                self.exp_state.best_config = dbms_config
                self.logger.info(f"New best configuration with latency: {latency}")
                self.logger.info(f"Best configuration: {dbms_config}")

            # Update the worst configuration
            if self.exp_state.worst_perf is None or latency > self.exp_state.worst_perf:
                self.exp_state.worst_perf = latency
                self.exp_state.worst_config = dbms_config  # Fixed typo from worst_confg to worst_config
                self.logger.info(f"New worst configuration with latency: {latency}")
                self.logger.info(f"Worst configuration: {dbms_config}")

            return latency  # Minimize latency




    def rl_target_function(self, dbms_config, seed: int):
        """Target function for RL-based optimizer."""

        rtn_predicate = self.dbms_wrapper.apply_knobs(dbms_config)
        assert rtn_predicate, "Failed to apply DBMS configuration."

        reset_predicate = self.dbms_wrapper.reset_cumulative_stats()
        assert reset_predicate, "Failed to reset DBMS cumulative statistics."

        self.workload_wrapper.run()
        performance = self.dbms_wrapper.get_benchbase_metrics()
        numeric_stats, _ = self.dbms_wrapper.get_dbms_stats()

        if self.target_metric == "throughput":
            throughput = performance["Throughput (requests/second)"]
            self.logger.info(f"Throughput (requests/second): {throughput}")

            if (
                self.exp_state.best_perf is None
                or throughput > self.exp_state.best_perf
            ):
                self.exp_state.best_perf = throughput
                self.exp_state.best_config = dbms_config

            if (
                self.exp_state.worst_perf is None
                or throughput < self.exp_state.worst_perf
            ):
                self.exp_state.worst_perf = throughput
                self.exp_state.worst_confg = dbms_config

            return throughput, numeric_stats

        elif self.target_metric == "latency":
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            self.logger.info(f"95th Percentile Latency (microseconds): {latency}")

            if (
                self.exp_state.best_perf is None
                or latency < self.exp_state.best_perf
            ):
                self.exp_state.best_perf = latency
                self.exp_state.best_config = dbms_config
            if (
                self.exp_state.worst_perf is None
                or latency > self.exp_state.worst_perf
            ):
                self.exp_state.worst_perf = latency
                self.exp_state.worst_confg = dbms_config

            return latency, numeric_stats

    def init_optimizer(self):
        if self.config["config_optimizer"]["optimizer"].startswith("bo"):
            self.logger.info("Initiating BO-based optimizer...")
            optimizer = get_bo_optimizer(
                self.config, self.dbms_config_space, self.target_function
            )
            self.logger.info(f"BO optimizer initialized with {optimizer.scenario.n_trials} trials.")
            print(f"BO optimizer initialized with {optimizer.scenario.n_trials} trials.")  # Additional print for debugging
        elif self.config["config_optimizer"]["optimizer"].startswith("rl"):
            self.logger.info("Initiating RL-based optimizer...")

            optimizer = get_ddpg_optimizer(
                self.config,
                self.dbms_config_space,
                self.rl_target_function,
                self.exp_state,
            )
        elif self.config["config_optimizer"]["optimizer"].startswith("liquid"):
            self.logger.info("Initiating Liquid-RL-based optimizer...")

            optimizer = get_liquid_ddpg_optimizer(
                self.config,
                self.dbms_config_space,
                self.rl_target_function,
                self.exp_state,
            )
        else:
            raise ValueError(f"Optimizer {self.config['config_optimizer']['optimizer']} not supported.")

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
            throughput = performance["Throughput (requests/second)"]
            self.exp_state.default_perf = throughput
            self.exp_state.best_perf = throughput
            self.exp_state.worst_perf = throughput

            self.logger.info(f"Default Throughput (requests/second): {throughput}")
        elif self.target_metric == "latency":
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            self.exp_state.default_perf = latency
            self.exp_state.best_perf = latency
            self.exp_state.worst_perf = latency

            self.logger.info(f"Default 95th Percentile Latency (microseconds): {latency}")

        if hasattr(self.optimizer, "optimize"):
            self.logger.info("Starting optimization...")
            best_dbms_config = self.optimizer.optimize()
            self.logger.info(f"Optimization completed. Best configuration: {best_dbms_config}")

            if hasattr(self.optimizer, "runhistory"):
                self.logger.info(f"Optimizer ran for {len(self.optimizer.runhistory._data)} trials.")
                print(f"Optimizer ran for {len(self.optimizer.runhistory._data)} trials.")  # Additional print for debugging
        else:
            self.logger.info("Starting RL-based optimization...")
            best_dbms_config = self.optimizer.run()
            self.logger.info(f"RL-based optimization completed. Best configuration: {best_dbms_config}")

        # Complete tuning
        self.logger.info("\nCompleted DBMS configuration tuning.")
        self.logger.info(f"\nBest DBMS Configuration:\n{self.exp_state.best_config}")
        self.logger.info(
            f"\nWorst DBMS Configuration:\n{self.exp_state.worst_confg}"
        )

        if self.exp_state.target_metric == "throughput":
            self.logger.info(
                f"Best Throughput: {self.exp_state.best_perf} ops/sec"
            )
            self.logger.info(
                f"Worst Throughput: {self.exp_state.worst_perf} ops/sec"
            )
        else:
            self.logger.info(
                f"Best 95th Percentile Latency: {self.exp_state.best_perf} microseconds"
            )
            self.logger.info(
                f"Worst 95th Percentile Latency: {self.exp_state.worst_perf} microseconds"
            )
