from cybernetics.db_interface.postgres import PostgresWrapper


def test_restarting_postgres():
    db_info = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "12345",
        "db_cluster": "/data/pgsql/data",
        "db_log_filepath": "/data/pgsql/log",
        "db_name": "benchbase_tpcc" # This database should be created beforehand
    }

    postgres_wrapper = PostgresWrapper(db_info)
    rtn_predicate = postgres_wrapper._restart_postgres()
    assert(rtn_predicate == True)

    # import subprocess
    # RESTART_WAIT_TIME = 60

    # payload = ["pg_ctl", "-D", db_info["db_cluster"], "-l", db_info["db_log_filepath"], "restart"]
    # p = subprocess.Popen(payload, stderr=subprocess.PIPE, 
    #                         stdout=subprocess.PIPE, close_fds=True)
    # try:
    #     # communicate() will block the program until the subprocess finishes
    #     stdout, stderr = p.communicate(timeout=RESTART_WAIT_TIME)
    #     if p.returncode == 0:
    #         print("Restarted Postgres.")
    #         print((f"Subprocess output: \n{stdout.decode()}"))
    #     else:
    #         print("Failed to restart Postgres.")
    #         print(f"Subprocess output: \n{stderr.decode()}")
    # except subprocess.TimeoutExpired:
    #     print("Timeout when restarting Postgres.")
    #     assert False
