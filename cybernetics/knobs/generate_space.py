"""This module is adapted from LlamaTune's config space generator.

https://github.com/uw-mad-dash/llamatune/blob/main/space.py
"""
import json

import ConfigSpace.hyperparameters as CSH
from ConfigSpace import ConfigurationSpace


class KnobSpaceGenerator:
    def __init__(self, knob_config: str, random_seed: int):
        """Initialize the knob space generator.
        """
        
        # self.knob_types = ["enum", "integer", "real"]
        self.all_knobs = self.read_db_knobs(knob_config)
        self.random_seed = random_seed

    def read_db_knobs(self, knob_config) -> dict:
        """Read a file containing DBMS knobs.
        
        Args:
            knob_filepath (str): The path to the file containing the knobs.

        Returns:
            (dict): Dictionary with knob name as key and knob specification as value.
        """

        with open(knob_config, "r") as f:
            knobs = json.load(f)

        return knobs

    def generate_input_space(self, ignored_knobs: list) -> ConfigurationSpace:
        """
        Generate an input space of knobs to tune.

        Args:
            ignored_knobs (list): The knobs to ignore.

        Returns:
            (ConfigurationSpace): The knob configuration space.
        """

        input_knobs = []
        for knob_spec in self.all_knobs:
            knob_name, knob_type = knob_spec["name"], knob_spec["type"]
            
            if knob_name in ignored_knobs:
                continue

            # Categorical
            if knob_type == "enum":
                knob = CSH.CategoricalHyperparameter(
                    name=knob_name,
                    choices=knob_spec["choices"],
                    default_value=knob_spec["default"])
            # Numerical
            elif knob_type == "integer":
                knob = CSH.UniformIntegerHyperparameter(
                    name=knob_name,
                    lower=knob_spec["min"],
                    upper=knob_spec["max"],
                    default_value=knob_spec["default"])
            elif knob_type == "real":
                knob = CSH.UniformFloatHyperparameter(
                    name=knob_name,
                    lower=knob_spec["min"],
                    upper=knob_spec["max"],
                    default_value=knob_spec["default"])
            else:
                raise ValueError(f"Unknown knob type: {knob_type}")

            input_knobs.append(knob)

        knob_space = ConfigurationSpace(seed=self.random_seed)
        knob_space.add_hyperparameters(input_knobs)
        
        return knob_space
