#!bin/bash
cd $HOME/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c $HOME/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml -d "$HOME/cybernetics/exps/benchbase_tpcc/postgres/bo_gp" --create=true --load=true --execute=true 