"""This module is adapted from DBTune's dbconnector.py and postgresqldb.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/dbconnector.py
https://github.com/PKU-DAIR/DBTune/blob/main/autotune/database/postgresqldb.py
"""

import glob
import os
import subprocess
import time

import paramiko
import psycopg2

from cybernetics.db_interface.db_client import DBClient
from cybernetics.utils.custom_logging import CUSTOM_LOGGING_INSTANCE


RESTART_WAIT_TIME = 20 # 20 seconds
TIMEOUT_CLOSE = 60 # 60 seconds


class PostgresClient(DBClient):
    def __init__(self, host, port, user, password, db_name, socket=None):
        super().__init__()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.socket = socket
        self.conn = self.connect_db()
        if self.conn:
            self.cursor = self.conn.cursor()
        
        self.logger = CUSTOM_LOGGING_INSTANCE.get_module_logger(__name__)

    def connect_db(self):
        if self.socket:
            conn = psycopg2.connect(host=self.host,
                                    port=self.port,
                                    user=self.user,
                                    password=self.password,
                                    database=self.db_name,
                                    unix_socket=self.socket)
        else:
            conn = psycopg2.connect(host=self.host,
                                    port=self.port,
                                    user=self.user,
                                    password=self.password,
                                    database=self.db_name)
        return conn

    def close_db(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def fetch_results(self, sql, json=True):    
        if self.conn:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if json:
                columns = [col[0] for col in self.cursor.description]
                return [dict(zip(columns, row)) for row in results]
        
        return results

    def execute(self, sql):
        results = None
        if self.conn:
            self.cursor.execute(sql)


class PostgresWrapper:
    def __init__(self, db_config, workload_wrapper, results_dir) -> None:
        self.host = db_config["host"]
        self.port = db_config["port"]
        self.user = db_config["user"]
        self.password = db_config["password"]
        self.db_name = db_config["db_name"]
        # self.socket = db_config["socket"]
        # self.pid = int(db_config["pid"])
        # self.pg_cnf = db_config["pg_cnf"]
        # self.pg_ctl = db_config["pg_ctl"]
        # self.pg_data = db_config["pg_data"]
        # self.postgres = os.path.join(os.path.split(os.path.abspath(self.pg_ctl))[0], "postgres")
        self.workload_wrapper = workload_wrapper
        self.results_dir = results_dir

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
    
    def _start_postgres(self) -> bool:
        proc = subprocess.Popen([self.postgres, f"--config_file={self.pg_cnf}", "-D",  self.pg_data])
        self.pid = proc.pid

        count = 0
        start_success = True
        self.logger.info("Wait for Postgres connection...")

        while True:
            try:
                pg_client = PostgresClient(host=self.host,
                                           port=self.port,
                                           user=self.user,
                                           password=self.password,
                                           db_name=self.db_name)
                pg_conn = pg_client.conn
                if pg_conn.closed == 0:
                    self.logger.info("Connected to Postgres.")
                    pg_conn.close()
                    break
            except:
                pass

            time.sleep(1)
            count += 1
            if count > 600:
                start_success = False
                self.logger.info("Can not connect to Postgres.")
                clear_cmd = """ps -ef|grep postgres|grep -v grep|cut -c 9-15|xargs kill -9"""
                subprocess.Popen(clear_cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, close_fds=True)
                self.logger.info("Kill all Postgres processes.")
                break

        self.logger.info(f"Postgres is up! Waited {count} seconds for connection.")
        return start_success
    
    def _kill_postgres(self) -> None:
        kill_cmd = f"{self.pg_ctl} stop -D {self.pg_data}"
        force_kill_cmd1 = "ps aux|grep '" + self.socket + "'|awk '{print $2}'|xargs kill -9"
        force_kill_cmd2 = "ps aux|grep '" + self.pg_cnf + "'|awk '{print $2}'|xargs kill -9"

        p_close = subprocess.Popen(kill_cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, close_fds=True)
        
        try:
            _, _ = p_close.communicate(timeout=TIMEOUT_CLOSE)
            ret_code = p_close.poll()
            if ret_code == 0:
                self.logger.info("Close Postgres successfully.")
        except subprocess.TimeoutExpired:
            self.logger.info("Force close Postgres.")
            os.system(force_kill_cmd1)
            os.system(force_kill_cmd2)
            self.logger.info("Postgres is shut down")
    
    def _check_apply(self, db_conn, k, v0):
        sql = f"SHOW {k};"
        r = db_conn.fetch_results(sql)

        if r[0]["Value"] == "ON":
            vv = 1
        elif r[0]["Value"] == "OFF":
            vv = 0
        else:
            vv = r[0]["Value"].strip()

        if vv == v0: # Knob value v has not taken effect yet
            return False
        else:
            return True
    
    def set_knob_value(self, db_conn, k, v) -> bool:
        sql = f"SHOW {k};"
        r = db_conn.fetch_results(sql)

        # Compare the value in the database with the value to be set
        if r[0]["Value"] == "ON":
            v0 = 1
        elif r[0]["Value"] == "OFF":
            v0 = 0
        else:
            try:
                v0 = eval(r[0]["Value"])
            except:
                v0 = r[0]["Value"].strip()
        
        if v == "ON" or v == "on":
            v = 1
        elif v == "OFF" or v == "off":
            v = 0
        
        if v0 == v:
            return True

        if str(v).isdigit():
            sql = f"SET {k}={v};"
        else:
            sql = f"SET {k}='{v}';"
        
        try:
            db_conn.execute(sql)
        except:
            self.logger.info(f"Failed to execute {sql}")

        # Check if knob value v has taken effect
        while not self._check_apply(db_conn, k, v0):
            time.sleep(1)
        
        return True
    
    def apply_knobs_online(self, knobs):
        pg_client = PostgresClient(host=self.host,
                                   port=self.port,
                                   user=self.user,
                                   password=self.password,
                                   db_name=self.db_name)

        for key in knobs.keys():
            self.set_knob_value(pg_client, key, knobs[key])

        pg_client.close_db()
        self.logger.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] Knobs applied online!")

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
            self.logger.info(f"Sleep for {RESTART_WAIT_TIME} seconds after restarting Postgres...")
            time.sleep(RESTART_WAIT_TIME)

            self.apply_knobs_online(knobs)

            # if len(knobs_not_in_cnf) > 0:
            #     tmp_rds = {}
            #     for knob_rds in knobs_not_in_cnf:
            #         tmp_rds[knob_rds] = knobs[knob_rds]
            #     self.apply_knobs_online(tmp_rds)
        except:
            success = False

        return success

    def _get_benchbase_metrics(self):
        metrics_files = glob.glob(f"{self.results_dir}/*.summary.json")
        latest_metrics_file = max(metrics_files, key=os.path.getctime)
        pass

    def evaluate_db_config(self, knobs: dict) -> dict:
        success = self.apply_knobs_offline(knobs)
        if not success:
            self.logger.info("Failed to apply the given DBMS configuration.")
            return {}
        
        # Execute the workload
        self.workload_wrapper.run()

        # Collect metrics
        metrics = self._get_benchbase_metrics()

        return metrics
