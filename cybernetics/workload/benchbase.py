import os
import subprocess
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE

TIMEOUT = 36000  # 1 hour

class BenchBaseWrapper:
    def __init__(self, target_dir: str, dbms_name: str, workload: str, results_save_dir: str = None) -> None:
        self.target_dir = target_dir
        self.dbms_name = dbms_name
        self.workload = workload
        self.results_save_dir = results_save_dir
        self.first_run = True
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()

    def run(self) -> None:
        workload_config_path = f"/home/phdonn/benchbase/config/{self.dbms_name}/sample_{self.workload}_config.xml"

        # Load data in the first run
        if self.first_run:
            os.chdir(self.target_dir)
            payload = [
                "java",
                "-jar",
                "benchbase.jar",
                "-b",
                self.workload,
                "-c",
                workload_config_path,
                "-d",
                self.results_save_dir,
                "--create=true",
                "--load=true",
                "--execute=true",
            ] if self.results_save_dir else [
                "java",
                "-jar",
                "benchbase.jar",
                "-b",
                self.workload,
                "-c",
                workload_config_path,
                "--create=true",
                "--load=true",
                "--execute=true",
            ]
            self.first_run = False
        else:
            payload = [
                "java",
                "-jar",
                "benchbase.jar",
                "-b",
                self.workload,
                "-c",
                workload_config_path,
                "-d",
                self.results_save_dir,
                "--create=false",
                "--load=false",
                "--execute=true",
            ] if self.results_save_dir else [
                "java",
                "-jar",
                "benchbase.jar",
                "-b",
                self.workload,
                "-c",
                workload_config_path,
                "--create=false",
                "--load=false",
                "--execute=true",
            ]

        workload_process = subprocess.Popen(
            payload,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=True,
        )

        try:
            stdout, stderr = workload_process.communicate(timeout=TIMEOUT)
            self.logger.info(f"Subprocess return code: {workload_process.returncode}")
            self.logger.info(f"Subprocess stdout: \n{stdout.decode()}")
            self.logger.info(f"Subprocess stderr: \n{stderr.decode()}")

            if workload_process.returncode == 0:
                self.logger.info("Finished running workload.")
            else:
                self.logger.info("Error when running workload.")

            # Additional logging to check the contents of the results directory
            if self.results_save_dir:
                files_in_results_dir = os.listdir(self.results_save_dir)
                self.logger.info(f"Files in results directory ({self.results_save_dir}): {files_in_results_dir}")

        except subprocess.TimeoutExpired:
            self.logger.info("Timeout when running workload.")
