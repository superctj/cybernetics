from cybernetics.dbms_interface.postgres import PostgresWrapper


def test_get_dbms_stats():
    dbms_info = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "12345",
        "db_name": "benchbase_tpcc",
        "db_cluster": "/data/pgsql/data",
        "db_log_filepath": "/data/pgsql/log",
        "n_internal_stats": 25
    }

    postgres_wrapper = PostgresWrapper(dbms_info,
                                       workload_wrapper=None,
                                       results_dir=None)
    
    numeric_stats, dbms_stats = postgres_wrapper.get_dbms_stats()
    assert len(dbms_stats) == len(postgres_wrapper.DB_STATS_VIEWS) + \
                              len(postgres_wrapper.CLUSTER_STATS_VIEWS)
    assert "pg_stat_database" in dbms_stats
    assert dbms_stats["pg_stat_database"]["datname"] == dbms_info["db_name"]
    assert "blks_read" in dbms_stats["pg_stat_database"]
    assert "buffers_alloc" in dbms_stats["pg_stat_bgwriter"]
    assert numeric_stats.shape[0] == dbms_info["n_internal_stats"]
