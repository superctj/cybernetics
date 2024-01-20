import os

from cybernetics.knobs.generate_space import KnobSpaceGenerator
from cybernetics.utils.util import get_proj_dir


def test_dbms_config_generator():
    proj_dir = get_proj_dir(__file__, file_level=2)
    knob_spec_path = os.path.join(proj_dir,
                                  "cybernetics/knobs/postgres_12.17_selected_knobs.json")
    assert os.path.exists(knob_spec_path)
    random_seed = 12345

    dbms_config_space_generator = KnobSpaceGenerator(knob_spec_path, random_seed)
    dbms_config_space = dbms_config_space_generator.generate_input_space(ignored_knobs=[])

    if "work_mem" in dbms_config_space:
        work_mem = dbms_config_space["work_mem"]
        min_val, max_val = work_mem.lower, work_mem.upper
        print(f"\nType of dbms_config_space: {type(dbms_config_space)}")

        dbms_config_sample = dbms_config_space.sample_configuration()
        assert dbms_config_sample["work_mem"] >= min_val and dbms_config_sample["work_mem"] <= max_val
        print(f"Type of dbms_config_sample: {type(dbms_config_sample)}")

        print(f"\nwork_mem value range: {min_val} - {max_val}")
        print(f"Sampled work_mem value: {dbms_config_sample['work_mem']}")
