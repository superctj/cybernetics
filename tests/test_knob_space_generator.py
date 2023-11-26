import os

import ConfigSpace.hyperparameters as CSH

from cybernetics.knobs.generate_space import KnobSpaceGenerator


def test_knob_space_generator():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    knob_config = os.path.join(root_dir, "cybernetics/knobs/postgres_9.6.json")
    random_seed = 12345
    ignored_knobs = []

    knob_space_generator = KnobSpaceGenerator(knob_config, random_seed)
    knob_space = knob_space_generator.generate_input_space(ignored_knobs)
    
    assert "work_mem" in knob_space
    work_mem_hp = knob_space.get_hyperparameter("work_mem")
    assert work_mem_hp.default_value == 4096
