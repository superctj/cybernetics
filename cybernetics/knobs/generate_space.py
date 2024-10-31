"""This module is adapted from LlamaTune's config space generator.

https://github.com/uw-mad-dash/llamatune/blob/main/space.py
"""

import json

import ConfigSpace.hyperparameters as CSH
import ConfigSpace as CS

from ConfigSpace import ConfigurationSpace

from cybernetics.adapters import (
    Quantization,
    PostgresBiasSampling,
    LinearEmbeddingConfigSpace,
)


class KnobSpaceGenerator:
    def __init__(self, knob_spec: str, random_seed: int):
        """Initialize the knob space generator."""

        # self.knob_types = ["enum", "integer", "real"]
        self.all_knobs = self.read_db_knobs(knob_spec)
        self.random_seed = random_seed

    def read_db_knobs(self, knob_config) -> dict:
        """Read a file containing DBMS knobs.

        Args:
            knob_filepath (str): The path to the file containing the knobs.

        Returns:
            (dict): Dictionary with knob name as key and knob specification as
            value.
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
            knob_name, knob_type = knob_spec["name"], knob_spec["vartype"]

            if knob_name in ignored_knobs:
                continue

            # Categorical
            if knob_type == "enum":
                knob = CSH.CategoricalHyperparameter(
                    name=knob_name,
                    choices=knob_spec["enumvals"],
                    default_value=knob_spec["reset_val"],
                )
            # Numerical
            elif knob_type == "integer":
                knob = CSH.UniformIntegerHyperparameter(
                    name=knob_name,
                    lower=int(knob_spec["min_val"]),
                    upper=int(knob_spec["max_val"]),
                    default_value=int(knob_spec["reset_val"]),
                )
            elif knob_type == "real":
                knob = CSH.UniformFloatHyperparameter(
                    name=knob_name,
                    lower=float(knob_spec["min_val"]),
                    upper=float(knob_spec["max_val"]),
                    default_value=float(knob_spec["reset_val"]),
                )
            elif knob_type == "bool":
                knob = CSH.CategoricalHyperparameter(
                    name=knob_name,
                    choices=["on", "off"],
                    default_value=knob_spec["reset_val"],
                )
            else:
                raise ValueError(f"Unknown knob type: {knob_type}")

            input_knobs.append(knob)

        knob_space = ConfigurationSpace(seed=self.random_seed)
        knob_space.add_hyperparameters(input_knobs)

        return knob_space

    def get_input_space_adapter(
        self,
        knob_space: CS.ConfigurationSpace,
        target_dim=None,
        bias_prob=None,
        quantization_factor=None,
    ):
        """
        Do transformations on search space as described in LlamaTune

        Args:
            target_dim: Number of dimensions to project to
            bias_prob: Amount of bias given to special knob values
            quantization_factor: Makes configuration space discrete rather than
                continuous
        Returns:
            (Adapter): Adapter object that contains altered configuation space
                and can be used to unproject points during evaluation
        """
        adapter = None
        if bias_prob:
            adapter = PostgresBiasSampling(
                knob_space, 1, bias_prob_sv=bias_prob
            )
            knob_space = adapter.target
        if target_dim:
            return LinearEmbeddingConfigSpace.create(
                knob_space,
                1,
                target_dim=target_dim,
                bias_prob_sv=bias_prob,
                max_num_values=quantization_factor,
            )
        if quantization_factor:
            adapter = Quantization(knob_space, 1, quantization_factor)
        return adapter
