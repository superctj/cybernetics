""" Core logic for configuration tuning.

This module is adapted from DBTune's tuner.py and Llamatune's run-smac.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/tuner.py
https://github.com/uw-mad-dash/llamatune/blob/main/run-smac.py
"""


class TuningEngine:
    def __init__(self, optimizer) -> None:
        self.optimizer = optimizer

    def run(self):
        # SMAC
        if hasattr(self.optimizer, "optimize"):
            self.optimizer.optimize()
        # OpenBox
        else:
            self.optimizer.run()
       