from cybernetics.db_interface.postgres import PostgresClient, PostgresWrapper


def test_setting_knob_values():
    db_info = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "12345",
        "db_name": "benchbase_tpcc" # This database should be created beforehand
    }

    postgres_wrapper = PostgresWrapper(db_info, workload_wrapper=None, results_dir=None)
    print("\n    Created Postgres wrapper.")

    postgres_client = PostgresClient(db_info["host"], db_info["port"], db_info["user"], db_info["password"], db_info["db_name"])

    db_config = {"work_mem": "1GB"} # default is 4MB
    for key in db_config:
        knob_val_sql = f"SHOW {key};"
        default_val = postgres_client.execute_and_fetch_results(
            knob_val_sql, json=False)[0][0]
        # print(f"    {key} default value:", default_val)
        
        # Apply the knob value
        # set_knob_sql = f"SET {key} = '{db_config[key]}';"
        # predicate = postgres_client.execute(set_knob_sql)
        # assert(predicate == True)

        # cur_val = postgres_client.execute_and_fetch_results(
        #     knob_val_sql, json=False)[0][0]
        # assert(cur_val == db_config[key])
        predicate = postgres_wrapper.set_knob_value(postgres_client, key, db_config[key])
        assert(predicate == True)

        # Set the knob value back to default
        set_knob_sql = f"SET {key} = '{default_val}';"
        predicate = postgres_client.execute(set_knob_sql)
        assert(predicate == True)
