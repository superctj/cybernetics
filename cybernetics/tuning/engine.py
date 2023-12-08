""" Core logic for configuration tuning.

This module is adapted from DBTune's tuner.py and Llamatune's run-smac.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/tuner.py
https://github.com/uw-mad-dash/llamatune/blob/main/run-smac.py
"""

from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


class TuningEngine:
    def __init__(self, db_wrapper, db_config_space, optimizer, exp_state) -> None:
        self.db_wrapper = db_wrapper
        self.db_config_space = db_config_space
        self.optimizer = optimizer
        self.exp_state = exp_state
        self.logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(__name__)

    def _evaluate_default_db_config(self):
        """Evaluate the default DBMS configuration.
        """
        default_dbms_config = self.knob_space.get_default_configuration()
        self.logger.info("Evaluating default DBMS configuration...")
        self.logger.info(f"Default DBMS config: {default_dbms_config}")

        default_perf = self.db_wrapper.evaluate_db_config(default_dbms_config)
        default_perf = default_perf if self.exp_state.minimize else -default_perf
        assert default_perf >= 0, f"Performance should not be negative: perf={default_perf}, metric={self.exp_state.target_metric}"

        self.exp_state.worse_perf = default_perf

    def run(self):
        # SMAC
        if hasattr(self.optimizer, "optimize"):
            self.optimizer.optimize()
        # OpenBox
        else:
            self.optimizer.run()
        
        # Complete tuning
        self.logger.info(f"\nBest Configuration:\n{self.exp_state.best_conf}")
        if self.exp_state.target_metric == "throughput":
            self.logger.info(f"Throughput: {self.exp_state.best_perf} ops/sec")
        else:
            self.logger.info(f"95-th Latency: {self.exp_state.best_perf} milliseconds")
