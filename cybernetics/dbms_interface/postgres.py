"""This module is adapted from DBTune's dbconnector.py and postgresqldb.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/dbconnector.py
https://github.com/PKU-DAIR/DBTune/blob/main/autotune/database/postgresqldb.py
"""

import json
import glob
import os
import subprocess
from typing import Union

import psycopg2

from ConfigSpace import Configuration
from cybernetics.dbms_interface.dbms_client import DBClient
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


RESTART_TIMEOUT = 60 # 60 seconds


class PostgresClient(DBClient):
    def __init__(self, host, port, user, password, db_name, logger=None):
        super().__init__()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.logger = logger

        self.conn, self.cursor = self.connect_db()

    def connect_db(self):
        try:
            conn = psycopg2.connect(host=self.host,
                                    port=self.port,
                                    user=self.user,
                                    password=self.password,
                                    database=self.db_name)
            conn.autocommit = True
            cursor = conn.cursor()

            if self.logger:
                self.logger.info("Connected to Postgres.")
            return conn, cursor
        except:
            if self.logger:
                self.logger.info("Unable to connect to Postgres.")

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        
        if self.logger:
            self.logger.info("Closed connection to Postgres.")

    def execute_and_fetch_results(self, sql, json=True) -> list:
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if json:
                columns = [col[0] for col in self.cursor.description]
                return [dict(zip(columns, row)) for row in results]
        
            return results
        except:
            self.close_connection()
            return []

    def execute(self, sql) -> bool:
        try:
            self.cursor.execute(sql)
            return True
        except:
            self.close_connection()
            return False


class PostgresWrapper:
    def __init__(self, dbms_info, workload_wrapper, results_dir: str) -> None:
        self.host = dbms_info["host"]
        self.port = dbms_info["port"]
        self.user = dbms_info["user"]
        self.password = dbms_info["password"]
        self.db_cluster = dbms_info["db_cluster"]
        self.db_log_filepath = dbms_info["db_log_filepath"]
        self.db_name = dbms_info["db_name"]
        self.logger = CUSTOM_LOGGING_INSTANCE.get_logger()
        
        self.workload_wrapper = workload_wrapper
        self.results_dir = results_dir
        # TODO: Add support for remote mode

        # self.num_metrics = 60
        # self.PG_STAT_VIEWS = [
        #     "pg_stat_archiver", "pg_stat_bgwriter",  # global
        #     "pg_stat_database", "pg_stat_database_conflicts",  # local
        #     "pg_stat_user_tables", "pg_statio_user_tables",  # local
        #     "pg_stat_user_indexes", "pg_statio_user_indexes"  # local
        # ]
        # self.PG_STAT_VIEWS_LOCAL_DATABASE = ["pg_stat_database", "pg_stat_database_conflicts"]
        # self.PG_STAT_VIEWS_LOCAL_TABLE = ["pg_stat_user_tables", "pg_statio_user_tables"]
        # self.PG_STAT_VIEWS_LOCAL_INDEX = ["pg_stat_user_indexes", "pg_statio_user_indexes"]
        # self.NUMERIC_METRICS = [
        #     # global
        #     "buffers_alloc", "buffers_backend", "buffers_backend_fsync", "buffers_checkpoint", "buffers_clean",
        #     "checkpoints_req", "checkpoints_timed", "checkpoint_sync_time", "checkpoint_write_time", "maxwritten_clean",
        #     "archived_count", "failed_count",
        #     # database
        #     "blk_read_time", "blks_hit", "blks_read", "blk_write_time", "conflicts", "deadlocks", "temp_bytes",
        #     "temp_files", "tup_deleted", "tup_fetched", "tup_inserted", "tup_returned", "tup_updated", "xact_commit",
        #     "xact_rollback", "confl_tablespace", "confl_lock", "confl_snapshot", "confl_bufferpin", "confl_deadlock",
        #     # table
        #     "analyze_count", "autoanalyze_count", "autovacuum_count", "heap_blks_hit", "heap_blks_read", "idx_blks_hit",
        #     "idx_blks_read", "idx_scan", "idx_tup_fetch", "n_dead_tup", "n_live_tup", "n_tup_del", "n_tup_hot_upd",
        #     "n_tup_ins", "n_tup_upd", "n_mod_since_analyze", "seq_scan", "seq_tup_read", "tidx_blks_hit",
        #     "tidx_blks_read",
        #     "toast_blks_hit", "toast_blks_read", "vacuum_count",
        #     # index
        #     "idx_blks_hit", "idx_blks_read", "idx_scan", "idx_tup_fetch", "idx_tup_read"
        # ]
    
    def _start_postgres(self) -> bool:
        # This function is only used when failing to restart Postgres due to invalid DBMS configuration (e.g., request too many resources)
        postgres_auto_config_path = os.path.join(self.db_cluster, "postgresql.auto.conf")
        with open(postgres_auto_config_path, "w") as f:
            f.write("# Overwritten invalid configuration.\n")

        payload = ["pg_ctl", "-D", self.db_cluster, "-l", self.db_log_filepath, "start"]
        p = subprocess.Popen(payload, stderr=subprocess.PIPE, 
                             stdout=subprocess.PIPE, close_fds=True)
        try:
            # communicate() will block the program until the subprocess finishes
            stdout, stderr = p.communicate(timeout=RESTART_TIMEOUT)
            if p.returncode == 0:
                self.logger.info("Overwritten invalid configuration and started Postgres with default configuration.")
                self.logger.info(f"Subprocess output: \n{stdout.decode()}")
                return True
            else:
                self.logger.info("Failed to overwrite invalid configuration and start Postgres with default configuration.")
                self.logger.info(f"Subprocess output: \n{stderr.decode()}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.info("Timeout when starting Postgres.")
            return False

    def _restart_postgres(self) -> bool:
        payload = ["pg_ctl", "-D", self.db_cluster, "-l", self.db_log_filepath, "restart"]
        p = subprocess.Popen(payload, stderr=subprocess.PIPE, 
                             stdout=subprocess.PIPE, close_fds=True)
        try:
            # communicate() will block the program until the subprocess finishes
            stdout, stderr = p.communicate(timeout=RESTART_TIMEOUT)
            if p.returncode == 0:
                self.logger.info("Restarted Postgres.")
                self.logger.info(f"Subprocess output: \n{stdout.decode()}")
                return True
            else:
                self.logger.info("Failed to restart Postgres.")
                self.logger.info(f"Subprocess output: \n{stderr.decode()}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.info("Timeout when restarting Postgres.")
            return False

    def _check_applied(self, db_conn, k, default_val):
        sql = f"SHOW {k};"
        cur_val = db_conn.execute_and_fetch_results(sql)[0][0]

        if cur_val == default_val:
            return False
        else:
            return True
    
    def get_knob_value(self, k) -> str:
        try:
            pg_client = PostgresClient(host=self.host,
                                       port=self.port,
                                       user=self.user,
                                       password=self.password,
                                       db_name=self.db_name,
                                       logger=self.logger)
            
            get_val_sql = f"SHOW {k};"
            val = pg_client.execute_and_fetch_results(get_val_sql, json=False)[0][0]
            pg_client.close_connection()

            return val
        except:
            self.logger.info(f"Failed to get value of knob {k}.")
            return None
    
    def set_knob_value(self, db_client, k, v) -> bool:
        sql = f"SHOW {k};"
        cur_val = db_client.execute_and_fetch_results(sql, json=False)[0][0]
        self.logger.info(f"Current value of knob {k}: {cur_val}")

        if cur_val == v:
            self.logger.info(f"Knob {k} has already been set to {v}.")
            return True
        else:
            if type(v) == str:
                set_sql = f"ALTER SYSTEM SET {k}='{v}';"
            else:
                set_sql = f"ALTER SYSTEM SET {k}={v};"

            try:
                # reload_sql = "SELECT pg_reload_conf();"
                _ = db_client.execute(set_sql)
                self.logger.info(f"Set knob {k} to {v}.")

                # _ = db_conn.execute(reload_sql)
                # Check if knob value v has taken effect
                # while not self._check_applied(db_conn, k, cur_val):
                #     time.sleep(1)
                return True
            except:
                self.logger.info(f"Failed to set knob {k} to {v}.")
                return False
    
    def apply_knobs(self, knobs: Union[dict, Configuration]) -> bool:
        if isinstance(knobs, Configuration):
            knobs = dict(knobs)

        try:
            pg_client = PostgresClient(host=self.host,
                                        port=self.port,
                                        user=self.user,
                                        password=self.password,
                                        db_name=self.db_name,
                                        logger=self.logger)

            for key in knobs.keys():
                self.set_knob_value(pg_client, key, knobs[key])

            pg_client.close_connection()
        except:
            self.logger.info("Failed to alter knobs.")
            return False

        restart_predicate = self._restart_postgres()
        if restart_predicate:
            self.logger.info("Restarted Postgres to make the DBMS config take effect.")
            return True
        else:
            return self._start_postgres()
    
    def reset_knobs_by_restarting_db(self) -> bool:
        try:
            pg_client = PostgresClient(host=self.host,
                                       port=self.port,
                                       user=self.user,
                                       password=self.password,
                                       db_name=self.db_name,
                                       logger=self.logger)
            
            reset_sql = "ALTER SYSTEM RESET ALL;"
            _ = pg_client.execute(reset_sql)
            pg_client.close_connection()

            self._restart_postgres()
            self.logger.info(f"Reset knobs with Postgres restarted.")
            return True
        except:
            self.logger.info("Failed to reset knobs with Postgres restarted.")
            return False

    def get_benchbase_metrics(self):
        metrics_files = glob.glob(f"{self.results_dir}/*.summary.json")
        latest_metrics_file = max(metrics_files, key=os.path.getctime)

        with open(latest_metrics_file, "r") as f:
            metrics = json.load(f)
        
        return metrics
