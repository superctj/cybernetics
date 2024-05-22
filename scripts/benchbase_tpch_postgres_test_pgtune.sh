#!bin/bash
cd /home/phdonn/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpch -c /home/phdonn/benchbase/target/benchbase-postgres/config/postgres/sample_tpch_config.xml -d "/home/phdonn/cybernetics/exps/benchbase_tpch/postgres/pgtune_tests" --create=false --load=false --execute=true