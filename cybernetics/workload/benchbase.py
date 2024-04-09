import subprocess

from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


TIMEOUT = 36000 # 1 hour


class BenchBaseWrapper:
    def __init__(self, workload: str, first_script: str, script: str) -> None:
        self.workload = workload
        self.script = script
        self.first_script = first_script
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()
        self.is_first_run = True

    def run(self) -> None:
        
        if self.is_first_run:
            payload = ["bash", self.first_script]
            self.is_first_run = False
        else:
            # Modify self.script so that the flags are set to false
            payload = ["bash", self.script]
            
        workload_process = subprocess.Popen(payload, stderr=subprocess.PIPE, 
                                            stdout=subprocess.PIPE, close_fds=True)

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


if __name__ == "__main__":
    workload="tpcc"
    script="/home/aditk/cybernetics/scripts/benchbase_tpcc_postgres.sh"

    benchbase_wrapper = BenchBaseWrapper(workload, script)
    benchbase_wrapper.run()
