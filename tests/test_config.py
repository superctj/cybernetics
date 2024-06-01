import os

from cybernetics.utils.util import get_proj_dir, parse_config


def test_config():
    proj_dir = get_proj_dir(__file__, file_level=2)
    config_path = os.path.join(
        proj_dir, "cybernetics/configs/benchbase/tpcc/postgres_bo_gp.ini"
    )

    parser = parse_config(config_path)
    assert "dbms_info" in parser.sections()
    assert parser["dbms_info"]["dbms_name"] in ["postgres", "mysql"]
