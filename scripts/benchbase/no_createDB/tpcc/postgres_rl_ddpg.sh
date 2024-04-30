#!bin/bash
cd /home/zhenyu/MLforDB/cybernetics/benchbase/target/benchbase-postgres
java -jar benchbase.jar -b tpcc -c  /home/zhenyu/MLforDB/cybernetics/benchbase/target/benchbase-postgres/config/postgres/sample_tpcc_config.xml -d "/home/zhenyu/MLforDB/cybernetics/exps/benchbase_tpcc/postgres/rl_ddpg" --create=false --load=false --execute=true 