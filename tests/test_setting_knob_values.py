from cybernetics.db_interface.postgres import PostgresClient, PostgresWrapper


def test_setting_knob_values():
    db_info = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "12345",
        "db_cluster": "/data/pgsql/data",
        "db_log_filepath": "/data/pgsql/log",
        "db_name": "benchbase_tpcc" # This database should be created beforehand
    }

    postgres_wrapper = PostgresWrapper(db_info, workload_wrapper=None, results_dir=None)
    print("\n    Created Postgres wrapper.")

    knob_to_set = "shared_buffers"
    db_config = {knob_to_set: "1 GB"} # default is 128 MB
    default_val = postgres_wrapper.get_knob_value(knob_to_set)
    print(f"    Default value of {knob_to_set}: {default_val}")

    rtn_predicate = postgres_wrapper.apply_knobs(db_config)
    cur_val = postgres_wrapper.get_knob_value(knob_to_set)
    print(f"    Current value of {knob_to_set}: {cur_val}")
    assert rtn_predicate == True
