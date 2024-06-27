import os
import subprocess
import pandas as pd
import json
import numpy as np
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE

TIMEOUT = 36000  # 1 hour

class BenchBaseWrapper:
    def __init__(self, target_dir: str, dbms_name: str, workload: str, results_save_dir: str = None, noise_level: float = 5.0):
        self.target_dir = target_dir
        self.dbms_name = dbms_name
        self.workload = workload
        self.results_save_dir = results_save_dir
        self.noise_level = noise_level  # Increased noise level
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
            summary_json_path = os.path.join(self.results_save_dir, "summary.json")
            if os.path.exists(summary_json_path):
                self._add_noise_to_json(summary_json_path)

    def _add_noise_to_csv(self, file_path):
        df = pd.read_csv(file_path)
        if 'Throughput (requests/second)' in df.columns:
            noise = np.random.normal(0, self.noise_level, size=len(df))
            df['Throughput with Noise (requests/second)'] = df['Throughput (requests/second)'] + noise
            df.to_csv(file_path, index=False)
            self.logger.info(f"Added Gaussian noise to {file_path}")

    def _add_noise_to_json(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        if "Throughput (requests/second)" in data:
            data["Throughput with Noise (requests/second)"] = data["Throughput (requests/second)"] + np.random.normal(0, self.noise_level)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        self.logger.info(f"Added Gaussian noise to {file_path}")

# Ensure that this method is correctly called within your engine.py to get the noise values for the model
def get_benchbase_metrics(self) -> dict:
    output_dir = "/home/phdonn/cybernetics_n/exps/benchbase_tpcc/postgres/bo_gp"
    performance = {"Throughput (requests/second)": 0, "Throughput (noise)": 0}

    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file_name)
        if file_name.endswith('.samples.csv'):
            df = pd.read_csv(file_path)
            if 'Throughput with Noise (requests/second)' in df.columns:
                throughput_noise = df["Throughput with Noise (requests/second)"].mean()
                performance["Throughput (requests/second)"] = df["Throughput (requests/second)"].mean()
                performance["Throughput (noise)"] = throughput_noise
        elif file_name.endswith('.summary.json'):
            with open(file_path, 'r') as file:
                data = json.load(file)
                if 'Throughput with Noise (requests/second)' in data:
                    performance["Throughput (noise)"] = data['Throughput with Noise (requests/second)']
                if 'Throughput (requests/second)' in data:
                    performance["Throughput (requests/second)"] = data['Throughput (requests/second)']

    # Ensure no NaN values are returned
    performance = {k: float(np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)) for k, v in performance.items()}

    return performance
