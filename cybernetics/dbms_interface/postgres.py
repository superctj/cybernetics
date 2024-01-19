"""This module is adapted from DBTune's dbconnector.py and postgresqldb.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/dbconnector.py
https://github.com/PKU-DAIR/DBTune/blob/main/autotune/database/postgresqldb.py
"""

import json
import glob
import os
import subprocess
import time

import psycopg2

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
    def __init__(self, db_info, workload_wrapper=None, results_dir=None) -> None:
        self.host = db_info["host"]
        self.port = db_info["port"]
        self.user = db_info["user"]
        self.password = db_info["password"]
        self.db_cluster = db_info["db_cluster"]
        self.db_log_filepath = db_info["db_log_filepath"]
        self.db_name = db_info["db_name"]
        
        self.workload_wrapper = workload_wrapper
        self.results_dir = results_dir
        self.logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(__name__)
        # TODO: Add support for remote mode

        self.num_metrics = 60
        self.PG_STAT_VIEWS = [
            "pg_stat_archiver", "pg_stat_bgwriter",  # global
            "pg_stat_database", "pg_stat_database_conflicts",  # local
            "pg_stat_user_tables", "pg_statio_user_tables",  # local
            "pg_stat_user_indexes", "pg_statio_user_indexes"  # local
        ]
        self.PG_STAT_VIEWS_LOCAL_DATABASE = ["pg_stat_database", "pg_stat_database_conflicts"]
        self.PG_STAT_VIEWS_LOCAL_TABLE = ["pg_stat_user_tables", "pg_statio_user_tables"]
        self.PG_STAT_VIEWS_LOCAL_INDEX = ["pg_stat_user_indexes", "pg_statio_user_indexes"]
        self.NUMERIC_METRICS = [
            # global
            "buffers_alloc", "buffers_backend", "buffers_backend_fsync", "buffers_checkpoint", "buffers_clean",
            "checkpoints_req", "checkpoints_timed", "checkpoint_sync_time", "checkpoint_write_time", "maxwritten_clean",
            "archived_count", "failed_count",
            # database
            "blk_read_time", "blks_hit", "blks_read", "blk_write_time", "conflicts", "deadlocks", "temp_bytes",
            "temp_files", "tup_deleted", "tup_fetched", "tup_inserted", "tup_returned", "tup_updated", "xact_commit",
            "xact_rollback", "confl_tablespace", "confl_lock", "confl_snapshot", "confl_bufferpin", "confl_deadlock",
            # table
            "analyze_count", "autoanalyze_count", "autovacuum_count", "heap_blks_hit", "heap_blks_read", "idx_blks_hit",
            "idx_blks_read", "idx_scan", "idx_tup_fetch", "n_dead_tup", "n_live_tup", "n_tup_del", "n_tup_hot_upd",
            "n_tup_ins", "n_tup_upd", "n_mod_since_analyze", "seq_scan", "seq_tup_read", "tidx_blks_hit",
            "tidx_blks_read",
            "toast_blks_hit", "toast_blks_read", "vacuum_count",
            # index
            "idx_blks_hit", "idx_blks_read", "idx_scan", "idx_tup_fetch", "idx_tup_read"
        ]
    
    # def _start_postgres(self) -> bool:
    #     proc = subprocess.Popen([self.postgres, f"--config_file={self.pg_cnf}", "-D",  self.pg_data])
    #     self.pid = proc.pid

    #     count = 0
    #     start_success = True
    #     self.logger.info("Wait for Postgres connection...")

    #     while True:
    #         try:
    #             pg_client = PostgresClient(host=self.host,
    #                                        port=self.port,
    #                                        user=self.user,
    #                                        password=self.password,
    #                                        db_name=self.db_name)
    #             if pg_client.conn.closed == 0:
    #                 self.logger.info("Connected to Postgres.")
    #                 pg_client.close_connection()
    #                 break
    #         except:
    #             pass

    #         time.sleep(1)
    #         count += 1
    #         if count > 600:
    #             start_success = False
    #             self.logger.info("Can not connect to Postgres.")
    #             clear_cmd = """ps -ef|grep postgres|grep -v grep|cut -c 9-15|xargs kill -9"""
    #             subprocess.Popen(clear_cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, close_fds=True)
    #             self.logger.info("Kill all Postgres processes.")
    #             break

    #     self.logger.info(f"Postgres is up! Waited {count} seconds for connection.")
    #     return start_success
    
    # def _kill_postgres(self) -> None:
    #     kill_cmd = f"{self.pg_ctl} stop -D {self.pg_data}"
    #     force_kill_cmd1 = "ps aux|grep '" + self.socket + "'|awk '{print $2}'|xargs kill -9"
    #     force_kill_cmd2 = "ps aux|grep '" + self.pg_cnf + "'|awk '{print $2}'|xargs kill -9"

    #     p_close = subprocess.Popen(kill_cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, close_fds=True)
        
    #     try:
    #         _, _ = p_close.communicate(timeout=TIMEOUT_CLOSE)
    #         ret_code = p_close.poll()
    #         if ret_code == 0:
    #             self.logger.info("Close Postgres successfully.")
    #     except subprocess.TimeoutExpired:
    #         self.logger.info("Force close Postgres.")
    #         os.system(force_kill_cmd1)
    #         os.system(force_kill_cmd2)
    #         self.logger.info("Postgres is shut down")

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
                # set_sql = f"SET {k} = '{v}';"
                set_sql = f"ALTER SYSTEM SET {k}='{v}';"
            else:
                assert type(v) == int
                # set_sql = f"SET {k} = {v};"
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
    
    def reset_knob_value(self, k) -> bool:
        """Restore the value of a run-time knob to the default value
        """
        try:
            pg_client = PostgresClient(host=self.host,
                                       port=self.port,
                                       user=self.user,
                                       password=self.password,
                                       db_name=self.db_name,
                                       logger=self.logger)
            reset_sql = f"ALTER SYSTEM RESET {k};"
            reload_sql = "SELECT pg_reload_conf();"
            _ = pg_client.execute(reset_sql)
            _ = pg_client.execute(reload_sql)
            
            pg_client.close_connection()
            return True
        except:
            self.logger.info(f"Failed to reset knob {k} to the default value.")
            return False

    # def reset_knobs_online(self, knobs: list) -> bool:
    #     try:
    #         pg_client = PostgresClient(host=self.host,
    #                                    port=self.port,
    #                                    user=self.user,
    #                                    password=self.password,
    #                                    db_name=self.db_name)
    #         for k in knobs:
    #             self.reset_knob_value(pg_client, k)

    #         pg_client.close_connection()
    #         self.logger.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] Knobs applied online.")

    #         return True
    #     except:
    #         return False
    
    def apply_knobs(self, knobs: dict) -> bool:
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
            self._restart_postgres()
            self.logger.info("Knobs applied.")
            return True
        except:
            self.logger.info("Failed to apply knobs.")
            return False
    
    def reset_runtime_knobs(self) -> bool:
        try:
            pg_client = PostgresClient(host=self.host,
                                       port=self.port,
                                       user=self.user,
                                       password=self.password,
                                       db_name=self.db_name,
                                       logger=self.logger)
            
            reset_sql = "RESET ALL;"
            _ = pg_client.execute(reset_sql)
            pg_client.close_connection()

            self.logger.info(f"Reset runtime knobs.")
            return True
        except:
            self.logger.info("Failed to reset runtime knobs.")
            return False
    
    def reset_knobs_by_reloading_config(self) -> bool:
        try:
            pg_client = PostgresClient(host=self.host,
                                       port=self.port,
                                       user=self.user,
                                       password=self.password,
                                       db_name=self.db_name,
                                       logger=self.logger)
            
            reset_sql = "ALTER SYSTEM RESET ALL;"
            reload_sql = "SELECT pg_reload_conf();"

            _ = pg_client.execute(reset_sql)
            _ = pg_client.execute(reload_sql)
            pg_client.close_connection()

            self.logger.info(f"Reset runtime knobs.")
            return True
        except:
            self.logger.info("Failed to reset runtime knobs.")
            return False
    
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

    def apply_knobs_offline(self, knobs: dict) -> bool:
        self._kill_postgres()

        if "min_wal_size" in knobs.keys():
            if "wal_segment_size" in knobs.keys():
                wal_segment_size = knobs["wal_segment_size"]
            else:
                wal_segment_size = 16
            
            if knobs["min_wal_size"] < 2 * wal_segment_size:
                knobs["min_wal_size"] = 2 * wal_segment_size
                self.logger.info("min_wal_size must be at least twice wal_segment_size")

        # knobs_not_in_cnf = self._gen_config_file(knobs)
        
        success = self._start_postgres()
        try:
            self.logger.info(f"Sleep for {RESTART_TIMEOUT} seconds after restarting Postgres...")
            time.sleep(RESTART_TIMEOUT)

            self.apply_knobs_online(knobs)

            # if len(knobs_not_in_cnf) > 0:
            #     tmp_rds = {}
            #     for knob_rds in knobs_not_in_cnf:
            #         tmp_rds[knob_rds] = knobs[knob_rds]
            #     self.apply_knobs_online(tmp_rds)
        except:
            success = False

        return success

    def get_benchbase_metrics(self):
        metrics_files = glob.glob(f"{self.results_dir}/*.summary.json")
        latest_metrics_file = max(metrics_files, key=os.path.getctime)

        with open(latest_metrics_file, "r") as f:
            metrics = json.load(f)
        
        return metrics

    def evaluate_db_info(self, knobs: dict) -> dict:
        success = self.apply_knobs_offline(knobs)
        if not success:
            self.logger.info("Failed to apply the given DBMS configuration.")
            return {}
        
        # Execute the workload
        self.workload_wrapper.run()

        # Collect metrics
        metrics = self._get_benchbase_metrics()

        return metrics
