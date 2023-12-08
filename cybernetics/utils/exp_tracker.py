import os

from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE, create_dir, get_proj_dir


class ExperimentState:
    def __init__(self, benchmark_info, dbms_info, target_metric: str):
        self.iter = 0
        self.best_conf = None
        self.best_perf = None
        self.worse_perf = None
        self.default_perf_stats = None

        assert target_metric in ["throughput", "latency"], \
            f"Unsupported target metric: {target_metric}"
        self.minimize = target_metric != "throughput"
        self._target_metric = target_metric

        self._benchmark_info = benchmark_info
        self._dbms_info = dbms_info

        proj_dir = get_proj_dir(__file__)
        self._results_path = os.path.join(
            proj_dir, f"results/{CUSTOM_LOGGING_INSTANCE.id}")
        create_dir(self._results_path, force=False)

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

    def is_better_perf(self, perf, other):
        return (perf > other) if not self.minimize else (perf < other)

    def __str__(self):
        fields = ["iter", "best_conf", "best_perf", "worse_perf",
                    "default_perf_stats", "target_metric"]
        return "<ExperimentState>:\n" + \
            "\n".join([ f"{f}: \t{getattr(self, f)}" for f in fields ])
