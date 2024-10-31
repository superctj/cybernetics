#!bin/bash
cd /home/aditk/workspace/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c /home/aditk/workspace/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config_200.xml -d "/home/aditk/workspace/cybernetics/exps/benchbase_tpcc/postgres/bo_gp" --create=true --load=true --execute=true 
