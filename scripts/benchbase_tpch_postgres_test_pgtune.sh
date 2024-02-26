#!bin/bash
cd $HOME/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpch -c $HOME/benchbase/target/benchbase-postgres/config/postgres/sample_tpch_config.xml -d "$HOME/cybernetics/exps/benchbase_tpch/postgres/pgtune_tests" --create=false --load=false --execute=true