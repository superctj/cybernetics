#!bin/bash
cd /home/aditk/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpch -c /home/aditk/benchbase/target/benchbase-postgres/config/postgres/sample_tpch_config.xml -d "/home/aditk/cybernetics/exps/benchbase_tpch/postgres/bo_gp" --create=true --load=true --execute=true 