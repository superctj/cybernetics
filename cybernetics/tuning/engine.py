""" Core logic for configuration tuning.

This module is adapted from DBTune's tuner.py and Llamatune's run-smac.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/tuner.py
https://github.com/uw-mad-dash/llamatune/blob/main/run-smac.py
"""

from cybernetics.tuning.dbms_config_optimizer import get_bo_optimizer
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE
from cybernetics.utils.exp_tracker import ExperimentState


logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(__name__)


class TuningEngine:
    def __init__(self, config, dbms_wrapper, dbms_config_space, workload_wrapper) -> None:
        self.config = config
        self.dbms_wrapper = dbms_wrapper
        self.dbms_config_space = dbms_config_space
        self.workload_wrapper = workload_wrapper

        self.exp_state = ExperimentState(
            config["dbms_info"],
            config["workload_info"],
            config["config_optimizer"]["target_metric"],
            config["results"]["save_path"]
        )
        self.target_metric = self.config["config_optimizer"]["target_metric"]
        self.optimizer = self.init_optimizer()
        

    def target_function(self, dbms_config, seed: int):
        """Target function for the DBMS configuration optimizer.
        """
        rtn_predicate = self.dbms_wrapper.apply_knobs(dbms_config)
        assert rtn_predicate, "Failed to apply DBMS configuration."

        self.workload_wrapper.run()
        performance = self.dbms_wrapper.get_benchbase_metrics()

        if self.target_metric == "throughput":
            throughput = performance["Throughput (requests/second)"]
            logger.info(f"Throughput (requests/second): {throughput}")
            
            if self.exp_state.best_perf is None or throughput > self.exp_state.best_perf:
                self.exp_state.best_perf = throughput
            return -throughput
        elif self.target_metric == "latency":
            latency = performance["Latency Distribution"]["95th Percentile Latency (microseconds)"]
            logger.info(f"95th Percentile Latency (microseconds): {latency}")

            if self.exp_state.best_perf is None or latency < self.exp_state.best_perf:
                self.exp_state.best_perf = latency
            return latency
    
    def init_optimizer(self):
        if self.config["config_optimizer"]["optimizer"].startswith("bo"):
            return get_bo_optimizer(self.config, self.dbms_config_space, self.target_function)

    def run(self):
        # SMAC
        if hasattr(self.optimizer, "optimize"):
            best_dbms_config = self.optimizer.optimize()
        # OpenBox
        else:
            self.optimizer.run()
        
        # Complete tuning
        logger.info(f"\nBest DBMS Configuration:\n{best_dbms_config}")
        
        if self.exp_state.target_metric == "throughput":
            logger.info(f"Best Throughput: {self.exp_state.best_perf} ops/sec")
        else:
            logger.info(f"Best 95-th Latency: {self.exp_state.best_perf} microseconds")
