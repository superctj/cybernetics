import logging
import os

from datetime import datetime

from cybernetics.utils.util import create_dir, get_proj_dir


class CustomLoggingInstance:
    def __init__(self) -> None:
        proj_dir = get_proj_dir(__file__)
        self.id = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        
        self.log_dir = os.path.join(proj_dir, f"logs/{self.id}")
        create_dir(self.log_dir, force=True)

        self.logger = self.setup_logger()

    def setup_logger(self, module_name: str="cybernetics", logging_level: int=logging.INFO):
        logger = logging.getLogger(module_name)
        logger.setLevel(logging_level)

        # Configure the formatter and handler
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        log_filepath = os.path.join(self.log_dir, f"{module_name}.log")
        handler = logging.FileHandler(log_filepath, mode="w")

        # Add formatter to handler
        handler.setFormatter(formatter)
        # Add handler to logger
        logger.addHandler(handler)

        logger.info(f"Init the custom logger for module {module_name}...")
        return logger
    
    def get_logger(self):
        return self.logger


CUSTOM_LOGGING_INSTANCE = CustomLoggingInstance()
