import logging
import os

from datetime import datetime

from cybernetics.utils.util import create_dir, get_proj_dir


class CustomLoggingInstance:
    def __init__(self, force: bool) -> None:
        proj_dir = get_proj_dir(__file__)
        self.id = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        self.log_dir = os.path.join(proj_dir, f"logs/{self.id}")
        create_dir(self.log_dir, force)

    def get_module_logger(self, module_name: str, logging_level: int = logging.INFO):
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


CUSTOM_LOGGING_INSTANCE = CustomLoggingInstance(force=False) # do not overwrite existing logs


if __name__ == "__main__":
    abs_path = os.path.abspath(__file__)
    print(abs_path)
    proj_dir = "/".join(abs_path.split("/")[:-3])
    print(proj_dir)
    logging_dir = os.path.join(proj_dir, "logs")
