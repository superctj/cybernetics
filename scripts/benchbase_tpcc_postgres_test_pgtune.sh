#!bin/bash
cd /home/phdonn/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c /home/phdonn/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml -d "/home/phdonn/cybernetics/exps/benchbase_tpcc/postgres/pgtune_tests" --create=true --load=true --execute=true 