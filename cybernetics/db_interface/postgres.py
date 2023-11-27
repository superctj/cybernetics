"""This module is adapted from DBTune"s dbconnector.py and postgresqldb.py.

https://github.com/PKU-DAIR/DBTune/blob/main/autotune/dbconnector.py
https://github.com/PKU-DAIR/DBTune/blob/main/autotune/database/postgresqldb.py
"""

import logging
import os
import subprocess
import time

import paramiko
import psycopg2

from cybernetics.db_interface.db_connector import DBConnector


RESTART_WAIT_TIME = 20 # 20 minutes
TIMEOUT_CLOSE = 60

logger = logging.getLogger("paramiko")
logger.setLevel(logging.ERROR)


class PostgresqlConnector(DBConnector):
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

    def connect_db(self):
        conn = False
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
        results = None
        
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
    def __init__(self, db_config) -> None:
        self.host = db_config["host"]
        self.port = db_config["port"]
        self.user = db_config["user"]
        self.password = db_config["password"]
        self.db_name = db_config["db_name"]
        self.socket = db_config["socket"]
        self.pid = int(db_config["pid"])
        self.pg_cnf = db_config["cnf"]
        self.pg_ctl = db_config["pg_ctl"]
        self.pg_data = db_config["pgdata"]
        self.postgres = os.path.join(os.path.split(os.path.abspath(self.pg_ctl))[0], "postgres")

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
        self.NUMERIC_METRICS = [ # counter
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
    
    def _start_postgres(self):
        if self.remote_mode:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.ssh_user, pkey=self.pk,
                        disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]})

            start_cmd = "{} --config_file={} -D {}".format(self.postgres, self.pgcnf, self.pgdata)
            wrapped_cmd = "echo $$; exec " + start_cmd
            _, start_stdout, _ = ssh.exec_command(wrapped_cmd)
            self.pid = int(start_stdout.readline())

            if self.isolation_mode:
                cgroup_cmd = "sudo -S cgclassify -g memory,cpuset:server " + str(self.pid)
                ssh_stdin, ssh_stdout, _ = ssh.exec_command(cgroup_cmd)
                ssh_stdin.write(self.ssh_passwd + "\n")
                ssh_stdin.flush()
                ret_code = ssh_stdout.channel.recv_exit_status()
                ssh.close()
                if not ret_code:
                    logger.info("add {} to memory,cpuset:server".format(self.pid))
                else:
                    logger.info("Failed: add {} to memory,cpuset:server".format(self.pid))
        else:
            proc = subprocess.Popen([self.postgres, "--config_file={}".format(self.pgcnf), "-D",  self.pgdata])
            self.pid = proc.pid
            if self.isolation_mode:
                command = "sudo cgclassify -g memory,cpuset:server " + str(self.pid)
                p = os.system(command)
                if not p:
                    logger.info("add {} to memory,cpuset:server".format(self.pid))
                else:
                    logger.info("Failed: add {} to memory,cpuset:server".format(self.pid))

        count = 0
        start_sucess = True
        logger.info("wait for connection")
        while True:
            try:
                dbc = PostgresqlConnector(host=self.host,
                                          port=self.port,
                                          user=self.user,
                                          passwd=self.passwd,
                                          name=self.dbname)
                db_conn = dbc.conn
                if db_conn.closed == 0:
                    logger.info("Connected to PostgreSQL db")
                    db_conn.close()
                    break
            except:
                pass

            time.sleep(1)
            count = count + 1
            if count > 600:
                start_sucess = False
                logger.info("can not connect to DB")
                clear_cmd = """ps -ef|grep postgres|grep -v grep|cut -c 9-15|xargs kill -9"""
                subprocess.Popen(clear_cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
                                 close_fds=True)
                logger.info("kill all postgres process")
                break

        logger.info("finish {} seconds waiting for connection".format(count))
        logger.info("postgres --config_file={}".format(self.pgcnf))
        logger.info("postgres is up")
        return start_sucess
    
    def _kill_postgres(self):
        kill_cmd = "{} stop -D {}".format(self.pg_ctl, self.pg_data)
        force_kill_cmd1 = "ps aux|grep '" + self.socket + "'|awk '{print $2}'|xargs kill -9"
        force_kill_cmd2 = "ps aux|grep '" + self.pg_cnf + "|awk '{print $2}'|xargs kill -9"

        # if self.remote_mode:
        #     ssh = paramiko.SSHClient()
        #     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #     ssh.connect(self.host, username=self.ssh_user, pkey=self.pk,
        #                 disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]})
        #     ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(kill_cmd)
        #     ret_code = ssh_stdout.channel.recv_exit_status()
        #     if ret_code == 0:
        #         logger.info("Close db successfully")
        #     else:
        #         logger.info("Force close DB!")
        #         ssh.exec_command(force_kill_cmd1)
        #         ssh.exec_command(force_kill_cmd2)
        #     ssh.close()
        #     logger.info("postgresql is shut down remotely")
        # else:
        #     p_close = subprocess.Popen(kill_cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
        #                                close_fds=True)
        #     try:
        #         outs, errs = p_close.communicate(timeout=TIMEOUT_CLOSE)
        #         ret_code = p_close.poll()
        #         if ret_code == 0:
        #             logger.info("Close db successfully")
        #     except subprocess.TimeoutExpired:
        #         logger.info("Force close!")
        #         os.system(force_kill_cmd1)
        #         os.system(force_kill_cmd2)
        #     logger.info("postgresql is shut down")

        p_close = subprocess.Popen(kill_cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, close_fds=True)
        try:
            outs, errs = p_close.communicate(timeout=TIMEOUT_CLOSE)
            ret_code = p_close.poll()
            if ret_code == 0:
                logger.info("Close db successfully")
        except subprocess.TimeoutExpired:
            logger.info("Force close!")
            os.system(force_kill_cmd1)
            os.system(force_kill_cmd2)
        logger.info("postgresql is shut down")
    
    def apply_knobs_online(self, knobs) -> bool:
        # apply knobs remotely
        db_conn = PostgresqlConnector(host=self.host,
                                      port=self.port,
                                      user=self.user,
                                      password=self.password,
                                      db_name=self.db_name)

        for key in knobs.keys():
            self.set_knob_value(db_conn, key, knobs[key])

        db_conn.close_db()
        logger.info("[{}] Knobs applied online!".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        return True

    def apply_knobs_offline(self, knobs) -> bool:
        self._kill_postgres()

        if "min_wal_size" in knobs.keys():
            if "wal_segment_size" in knobs.keys():
                wal_segment_size = knobs["wal_segment_size"]
            else:
                wal_segment_size = 16
            if knobs["min_wal_size"] < 2 * wal_segment_size:
                knobs["min_wal_size"] = 2 * wal_segment_size
                logger.info(""min_wal_size" must be at least twice "wal_segment_size"")

        knobs_not_in_cnf = self._gen_config_file(knobs)
        sucess = self._start_postgres()
        try:
            logger.info("sleeping for {} seconds after restarting postgres".format(RESTART_WAIT_TIME))
            time.sleep(RESTART_WAIT_TIME)

            if len(knobs_not_in_cnf) > 0:
                tmp_rds = {}
                for knob_rds in knobs_not_in_cnf:
                    tmp_rds[knob_rds] = knobs[knob_rds]
                self.apply_knobs_online(tmp_rds)
        except:
            sucess = False

        return sucess

