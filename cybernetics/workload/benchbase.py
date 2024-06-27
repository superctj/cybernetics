import os
import subprocess
import pandas as pd
import json
import numpy as np
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE

TIMEOUT = 36000  # 1 hour

class BenchBaseWrapper:
    def __init__(self, target_dir: str, dbms_name: str, workload: str, results_save_dir: str = None, noise_level: float = 50.0):
        self.target_dir = target_dir
        self.dbms_name = dbms_name
        self.workload = workload
        self.results_save_dir = results_save_dir
        self.noise_level = noise_level  # Configurable noise level
        self.first_run = True
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()

    def run(self):
        workload_config_path = f"./config/{self.dbms_name}/sample_{self.workload}_config.xml"
        payload = self._build_payload(workload_config_path)
        self._execute_payload(payload)

    def _build_payload(self, workload_config_path):
        os.chdir(self.target_dir)
        base_payload = [
            "java", "-jar", "benchbase.jar",
            "-b", self.workload,
            "-c", workload_config_path,
            "-d", self.results_save_dir if self.results_save_dir else "",
            "--create=true" if self.first_run else "--create=false",
            "--load=true" if self.first_run else "--load=false",
            "--execute=true"
        ]
        self.first_run = False
        return base_payload

    def _execute_payload(self, payload):
        workload_process = subprocess.Popen(
            payload, stderr=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True
        )
        try:
            stdout, stderr = workload_process.communicate(timeout=TIMEOUT)
            if workload_process.returncode == 0:
                self.logger.info("Finish running workload.")
                self.logger.info(f"Subprocess output: \n{stdout.decode()}")
                self._add_gaussian_noise_to_results()
            else:
                self.logger.error("Error when running workload.")
                self.logger.error(f"Subprocess output: \n{stderr.decode()}")
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout when running workload.")

    def _add_gaussian_noise_to_results(self):
        if self.results_save_dir:
            for file_name in os.listdir(self.results_save_dir):
                if file_name.endswith(".csv"):
                    self._add_noise_to_csv(os.path.join(self.results_save_dir, file_name))
                elif file_name.endswith(".summary.json"):
                    self._add_noise_to_json(os.path.join(self.results_save_dir, file_name))

    def _add_noise_to_csv(self, file_path):
        df = pd.read_csv(file_path)
        if 'Throughput (requests/second)' in df.columns:
            noise = np.random.normal(0, self.noise_level, size=len(df))
            df['Throughput with Noise (requests/second)'] = df['Throughput (requests/second)'] + noise
            df['Throughput with Noise (requests/second)'] = df['Throughput with Noise (requests/second)'].clip(lower=0)
            self.logger.info(f"Adding noise to CSV: {noise}")
            df.to_csv(file_path, index=False)
            self.logger.info(f"Added Gaussian noise to {file_path}")


    def _add_noise_to_json(self, file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            if 'Throughput (requests/second)' in data:
                current_throughput = data['Throughput (requests/second)']
                noise = np.random.normal(0, self.noise_level)
                throughput_noise = current_throughput + noise
                self.logger.info(f"Adding noise to JSON: {noise}")
                data['Throughput (noise)'] = float(np.nan_to_num(throughput_noise, nan=0.0, posinf=0.0, neginf=0.0))

                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)

                self.logger.info(f"Added noise to {file_path}")
            else:
                self.logger.warning(f"'Throughput (requests/second)' key not found in {file_path}")

        except Exception as e:
            self.logger.error(f"Error when adding noise to {file_path}: {e}")