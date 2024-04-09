""" Core logic for configuration tuning.

This module is adapted from DBTune's tuner.py and Llamatune's run-smac.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/tuner.py
https://github.com/uw-mad-dash/llamatune/blob/main/run-smac.py
"""

from cybernetics.tuning.dbms_config_optimizer import get_bo_optimizer, get_ddpg_optimizer
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE
from cybernetics.utils.exp_tracker import ExperimentState
import time


class TuningEngine:
    def __init__(self, config, dbms_wrapper, dbms_config_space, workload_wrapper) -> None:
        self.config = config
        self.dbms_wrapper = dbms_wrapper
        self.dbms_config_space = dbms_config_space
        self.workload_wrapper = workload_wrapper
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

    def target_function(self, dbms_config, seed: int):
        """Target function for BO-based optimizer.
        """
        rtn_predicate = self.dbms_wrapper.apply_knobs(dbms_config)
        assert rtn_predicate, "Failed to apply DBMS configuration."

        self.workload_wrapper.run()
        performance = self.dbms_wrapper.get_benchbase_metrics()

        if self.target_metric == "throughput":
            throughput = performance["Throughput (requests/second)"]
            self.logger.info(f"Throughput (requests/second): {throughput}")
            
            if self.exp_state.best_perf is None or throughput > self.exp_state.best_perf:
                self.exp_state.best_perf = throughput
            return -throughput
        elif self.target_metric == "latency":
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            self.logger.info(f"95th Percentile Latency (microseconds): {latency}")

            if self.exp_state.best_perf is None or latency < self.exp_state.best_perf:
                self.exp_state.best_perf = latency
            return latency
    
    def rl_target_function(self, dbms_config, seed: int):
        """Target function for RL-based optimizer.
        """
        # Apply DBMS configuration
        rtn_predicate = self.dbms_wrapper.apply_knobs(dbms_config)
        assert rtn_predicate, "Failed to apply DBMS configuration."

        # Reset DBMS statistics which are needed for DDPG-based tuning
        # reset_predicate = self.dbms_wrapper.reset_cumulative_stats()
        # assert reset_predicate, "Failed to reset DBMS cumulative statistics."

        # Run the workload
        self.workload_wrapper.run()
        performance = self.dbms_wrapper.get_benchbase_metrics()
        numeric_stats, _ = self.dbms_wrapper.get_dbms_stats()

        if self.target_metric == "throughput":
            throughput = performance["Throughput (requests/second)"]
            self.logger.info(f"Throughput (requests/second): {throughput}")
            
            if self.exp_state.best_perf is None or throughput > self.exp_state.best_perf:
                self.exp_state.best_perf = throughput

            if self.exp_state.worst_perf is None or throughput < self.exp_state.worst_perf:
                self.exp_state.worst_perf = throughput

            return throughput, numeric_stats
        
        elif self.target_metric == "latency":
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            self.logger.info(f"95th Percentile Latency (microseconds): {latency}")

            if self.exp_state.best_perf is None or latency < self.exp_state.best_perf:
                self.exp_state.best_perf = latency
            
            if self.exp_state.worst_perf is None or latency > self.exp_state.worst_perf:
                self.exp_state.worst_perf = latency

            return latency, numeric_stats
    
    def init_optimizer(self):
        if self.config["config_optimizer"]["optimizer"].startswith("bo"):
            self.logger.info("Initiating BO-based optimizer...")
            
            optimizer = get_bo_optimizer(
                self.config,
                self.dbms_config_space,
                self.target_function
            )
        elif self.config["config_optimizer"]["optimizer"].startswith("rl"):
            self.logger.info("Initiating RL-based optimizer...")
            
            optimizer = get_ddpg_optimizer(
                self.config,
                self.dbms_config_space,
                self.rl_target_function,
                self.exp_state
            )
        
        else:
            raise ValueError(f"Optimizer {optimizer} not supported.")

        return optimizer

    def run(self):
        # Restart DBMS with default configuration
        self.dbms_wrapper.reset_knobs_by_restarting_db()

        # Run default configuration 100 times to see if throughout and latency change significantly
        
        for _ in range(100):
            start_time = time.time()
            self.workload_wrapper.run()
            end_time = time.time()
            self.logger.info(f"Executing Time: {end_time - start_time}")
            
            performance = self.dbms_wrapper.get_benchbase_metrics()

           
            throughput = performance["Throughput (requests/second)"]
            self.exp_state.default_perf = throughput
            self.exp_state.best_perf = throughput
            self.exp_state.worst_perf = throughput
            
            self.logger.info(f"Default Throughput (requests/second): {throughput}")
            
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            self.exp_state.default_perf = latency
            self.exp_state.best_perf = latency
            self.exp_state.worst_perf = latency

            self.logger.info(f"Default 95th Percentile Latency (microseconds): {latency}")
        return

        # SMAC
        if hasattr(self.optimizer, "optimize"):
            opt_start_time = time.time()
            best_dbms_config = self.optimizer.optimize()
            opt_end_time = time.time()
            self.logger.info(f"Optimization Time:{opt_end_time - opt_start_time}")
        # RL-DDPG
        else:
            best_dbms_config = self.optimizer.run()
        
        # Complete tuning
        self.logger.info(f"\nBest DBMS Configuration:\n{best_dbms_config}")
        
        if self.exp_state.target_metric == "throughput":
            self.logger.info(f"Best Throughput: {self.exp_state.best_perf} ops/sec")
        else:
            self.dbms_config_spacelogger.info(f"Best 95-th Latency: {self.exp_state.best_perf} microseconds")
