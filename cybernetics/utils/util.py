import os
import random

from shutil import rmtree

from configparser import ConfigParser

import numpy as np


def create_dir(dir_path: str, force: bool) -> None:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    else:
        if force:
            rmtree(dir_path)
            os.makedirs(dir_path)
        else:
            raise ValueError(f"Directory {dir_path} already exists.")


def get_proj_dir(filepath: str, file_level: int=3) -> str:
    """Get the project directory.

    Args:
        filepath (str): The path of the file.
        file_level (int): The level of the file relative to the project directory starting at 1.
    
    Returns:
        (str): The project directory.
    """

    abs_path = os.path.abspath(filepath)
    proj_dir = "/".join(abs_path.split("/")[:-file_level])
    return proj_dir


def fix_global_random_state(seed: int):
    """Fix the random state of the global random number generator.

    Args:
        seed (int): The seed to use.
    """
    
    random.seed(seed)
    np.random.seed(seed)


def parse_config(config_path: str) -> ConfigParser:
    """Parse a configuration file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        (dict): The parsed configuration.
    """
    
    parser = ConfigParser()
    parser.read(config_path)
    for key, value in config.items(section):
        # Replace variables with their values
        config.set(section, key, os.path.expandvars(value))
    return parser
