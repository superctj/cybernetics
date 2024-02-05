"""Logic for keeping track of experiment states.

This module is adapted from Llamatune's run-smac.py
"""

import os

from cybernetics.utils.util import create_dir


class ExperimentState:
    def __init__(self, dbms_info: dict, workload_info: dict, target_metric: str, results_path: str):
        self.iter = 0
        self.best_conf = None
        self.best_perf = None
        self.worse_perf = None
        self.default_perf = None
        self.default_perf_stats = None

        assert target_metric in ["throughput", "latency"], f"Unsupported target metric: {target_metric}"
        self._target_metric = target_metric
        self.minimize = (target_metric == "latency")

        self._dbms_info = dbms_info
        self._workload_info = workload_info

        create_dir(results_path, force=True)

        # if not os.path.exists(results_path):
        # create_dir(results_path, force=False)
        # else:
        #     self.results_path = os.path.join(results_path, CUSTOM_LOGGING_INSTANCE.id)

        #     create_dir(self.results_path, force=True)

    @property
    def benchmark_info(self):
        return self._benchmark_info

    @property
    def dbms_info(self):
        return self._dbms_info

    @property
    def results_path(self) -> str:
        return self._results_path

    @property
    def target_metric(self) -> str:
        return self._target_metric

    # def is_better_perf(self, perf, other):
    #     return (perf > other) if not self.minimize else (perf < other)

    def __str__(self):
        fields = ["iter", "best_conf", "best_perf", "worse_perf",
                    "default_perf_stats", "target_metric"]
        return "<ExperimentState>:\n" + \
            "\n".join([ f"{f}: \t{getattr(self, f)}" for f in fields ])
