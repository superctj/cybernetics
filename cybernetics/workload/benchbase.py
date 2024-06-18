import subprocess
import numpy as np
import os
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE

TIMEOUT = 36000  # 10 hours

class BenchBaseWrapper:
    def __init__(self, workload: str, script: str) -> None:
        self.workload = workload
        self.script = script
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()
        self.noise_level = 0.5 

    def add_noise_to_csv(self, file_path: str) -> None:
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            self.logger.info(f"First few lines of data from {file_path}: \n{lines[:10]}")
            csv_start_index = next((i for i, line in enumerate(lines) if "Time (seconds)" in line), None)
            
            if csv_start_index is None:
                self.logger.error(f"CSV header not found in {file_path}.")
                return

            csv_lines = lines[csv_start_index:]
            headers = csv_lines[0].strip() + ",Throughput (noise)\n"
            values = []

            for line in csv_lines[1:]:
                split_line = line.strip().split(',')
                if len(split_line) == len(csv_lines[0].strip().split(',')):
                    try:
                        values.append(list(map(float, split_line)))
                    except ValueError:
                        self.logger.warning(f"Skipping line due to conversion error: {line}")
                else:
                    self.logger.warning(f"Skipping malformed line: {line}")

            values = np.array(values)

            if values.ndim == 1:  # Handle the case where we get a 1D array
                values = values.reshape(-1, len(csv_lines[0].strip().split(',')))

            if values.shape[1] > 2:
                noise = np.random.normal(0, self.noise_level * values[:, 2])
                noisy_values = np.column_stack((values, values[:, 2] + noise))
            else:
                self.logger.warning(f"Not enough columns in {file_path} to add noise")
                return

            # Reconstructing the noisy data
            noisy_data = headers + "\n".join([",".join(map(str, line)) for line in noisy_values])
            
            # Write noisy data back to file
            with open(file_path, 'w') as file:
                file.write(noisy_data)

            self.logger.info(f"Added noise to {file_path}")
        except ValueError as e:
            self.logger.error(f"Failed to convert data to float for adding noise in {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error when adding noise to {file_path}: {e}")

    def save_data(self, original_data: str) -> None:
        output_dir = "/home/phdonn/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
        os.makedirs(output_dir, exist_ok=True)

        original_file_path = os.path.join(output_dir, "original_data.txt")
        with open(original_file_path, "w") as original_file:
            original_file.write(original_data)

    def run(self) -> None:
        payload = ["bash", self.script]
        self.logger.info(payload)
        workload_process = subprocess.Popen(payload, stderr=subprocess.PIPE,
                                            stdout=subprocess.PIPE, close_fds=True)

        try:
            stdout, stderr = workload_process.communicate(timeout=TIMEOUT)
            if workload_process.returncode == 0:
                original_data = stdout.decode()
                self.logger.info("Finish running workload.")
                self.logger.info(f"Subprocess output: \n{original_data}")
                
                self.save_data(original_data)

                output_dir = "/home/phdonn/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
                for file_name in os.listdir(output_dir):
                    if file_name.endswith('.csv') and not file_name.endswith('raw.csv'):
                        self.add_noise_to_csv(os.path.join(output_dir, file_name))

            else:
                self.logger.info("Error when running workload.")
                self.logger.info(f"Subprocess output: \n{stderr.decode()}")
        except subprocess.TimeoutExpired:
            self.logger.info("Timeout when running workload.")

    def get_noisy_throughput_data(self, directory: str):
        """Extract throughput (noise) from .samples.csv files."""
        noisy_throughput_data = []
        for filename in os.listdir(directory):
            if filename.endswith(".samples.csv"):
                file_path = os.path.join(directory, filename)
                df = pd.read_csv(file_path)
                if 'Throughput (noise)' in df.columns:
                    noisy_throughput_data.append(df['Throughput (noise)'].mean())
        return noisy_throughput_data


from cybernetics.tuning.engine import TuningEngine

class NoisyTuningEngine(TuningEngine):
    def run(self):

        # Get noisy throughput data
        output_dir = "/home/phdonn/cybernetics/exps/benchbase_tpcc/postgres/bo_gp"
        noisy_throughput_data = self.workload_wrapper.get_noisy_throughput_data(output_dir)

        # Use noisy throughput data in your tuning process
        for throughput in noisy_throughput_data:
            # Your tuning logic here...
            pass

