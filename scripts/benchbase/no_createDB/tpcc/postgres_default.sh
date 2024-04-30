#!bin/bash
cd /home/tianji/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c /home/tianji/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml -d /home/tianji/cybernetics/exps/benchbase_tpcc/postgres --create=false --load=false --execute=true 