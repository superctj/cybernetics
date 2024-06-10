#!bin/bash
cd /home/phdonn/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c /home/phdonn/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml -d "/home/tianji/cybernetics/exps/benchbase_tpcc/postgres/bo_rf" --create=true --load=true --execute=true 