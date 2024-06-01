import os
import subprocess

from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


TIMEOUT = 36000  # 1 hour


class BenchBaseWrapper:
    def __init__(
        self,
        target_dir: str,
        dbms_name: str,
        workload: str,
        results_save_dir: str = None,
    ) -> None:
        self.target_dir = target_dir
        self.dbms_name = dbms_name
        self.workload = workload
        self.results_save_dir = results_save_dir

        self.first_run = True
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()

    def run(self) -> None:
        workload_config_path = (
            f"./config/{self.dbms_name}/sample_{self.workload}_config.xml"
        )

        # Load data in the first run
        if self.first_run:
            # Changing the current working directory may have a side effect
            os.chdir(self.target_dir)

            # Save the results to a specified directory
            if self.results_save_dir:
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
                ]
            # Save the results to the BenchBase default directory
            else:
                payload = [
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
        # Skip loading data in the subsequent runs
        else:
            if self.results_save_dir:
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
                ]
            else:
                payload = [
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
            # communicate() will block the program until the subprocess finishes
            stdout, stderr = workload_process.communicate(timeout=TIMEOUT)

            if workload_process.returncode == 0:
                self.logger.info("Finish running workload.")
                self.logger.info(f"Subprocess output: \n{stdout.decode()}")
            else:
                self.logger.info("Error when running workload.")
                self.logger.info(f"Subprocess output: \n{stderr.decode()}")
        except subprocess.TimeoutExpired:
            self.logger.info("Timeout when running workload.")
