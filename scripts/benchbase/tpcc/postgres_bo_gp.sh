#!bin/bash
cd /home/mingo/Desktop/cybernetics/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c /home//mingo/Desktop/cybernetics/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml -d "/home/mingo/Desktop/cybernetics/exps/benchbase_tpcc/postgres/bo_gp" --create=true --load=true --execute=true 