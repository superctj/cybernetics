#!bin/bash
cd /home/aditk/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c /home/aditk/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config_200.xml -d "/home/aditk/cybernetics/exps/benchbase_tpcc/postgres/bo_gp" --execute=true 