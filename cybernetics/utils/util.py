import random

from configparser import ConfigParser

import numpy as np


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

    return parser
