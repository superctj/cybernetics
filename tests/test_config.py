import os

from cybernetics.utils.util import parse_config


def test_config():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root_dir, "cybernetics/configs/benchbase/tpcc/postgres.ini")
    
    parser = parse_config(config_path)
    assert "dbms_info" in parser.sections()
    assert parser["dbms_info"]["name"] in ["postgres", "mysql"]
