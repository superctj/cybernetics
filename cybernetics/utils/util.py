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


def get_proj_dir(filepath: str, file_level: int = 3) -> str:
    """Get the project directory.

    Args:
        filepath (str): The path of the file.
        file_level (int): The level of the file relative to the project
            directory starting at 1.

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

    return parser


def get_postgres_user_and_password() -> tuple:
    """Get Postgres user and password from the environment variables.

    Returns:
        (tuple): The DBMS user and password.
    """

    postgres_user = os.getenv("POSTGRES_USER")
    if not postgres_user:
        raise EnvironmentError("Environment variable POSTGRES_USER not set.")

    postgres_password = os.getenv("POSTGRES_PASSWORD")
    if not postgres_password:
        raise EnvironmentError(
            "Environment variable POSTGRES_PASSWORD not set."
        )

    return postgres_user, postgres_password


def get_benchbase_postgres_target_dir() -> str:
    """Get the BenchBase target directory for Postgres from the environment
      variable.

    Returns:
        (str): The target directory containing the Java executable.
    """

    benchbase_postgres_target_dir = os.getenv("BENCHBASE_POSTGRES_TARGET_DIR")
    if not benchbase_postgres_target_dir:
        raise EnvironmentError(
            "Environment variable BENCHBASE_POSTGRES_TARGET_DIR not set."
        )

    return benchbase_postgres_target_dir
