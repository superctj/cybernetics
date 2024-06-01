# Cybernetics: Open Source DBMS Configuration Tuning
Codebase of a working open source DBMS configuration tuning framework.


## Prerequisites

**DBMS**
- [PostgreSQL](https://www.postgresql.org) (We currently support Postgres and provide a step-by-step [reference](https://docs.google.com/document/d/1iv6B1bXawyx3K6kLBbUva91FEXKE1wns_kPd-UoUumM/edit?usp=sharing) for installing Postgres 12.17 on Ubuntu 20.04.)

**Workload Generator**
- [Benchbase](https://github.com/cmu-db/benchbase) (We currently use Benchbase as the workload generator and provide a step-by-step [reference](https://docs.google.com/document/d/1EbcwEMBdeWTmHDuWXW3lC8Pggbj3A8e-EJBlwN2VEzY/edit?usp=sharing) for running Benchbase.)


## Environment Setup
Assume using [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/) for Python package management on Linux machines.

1. Clone this repo in your working directory:

    ```
    git clone <Cybernetics repo url>
    cd cybernetics
    ```

2. Create and activate the development environment:

    ```
    conda env create -f environment.yml
    conda activate cybernetics
    ```

3. Import Cybernetics as editable packages to the conda environment:

    ```
    conda develop <path to Cybernetics>
    ```
    e.g.,
    ```
    conda develop /home/tianji/cybernetics
    ```


## Quick Start
Follow the steps below to run vanilla Bayesian optimization (i.e., BO-Gaussian Process) for Postgres over the TPC-C workload.

1. (a) Set your Postgres username, password and BenchBase target directory as environment variables in e.g., ```~/.bashrc```:

    ```
    export POSTGRES_USER=<your username>
    export POSTGRES_PASSWORD=<your password>
    export BENCHBASE_POSTGRES_TARGET_DIR=<path to directory containing BenchBase executable jar>
    ```

    E.g., If `benchbase.jar` is under `~/benchbase/target/benchbase-postgres`, then set ```export BENCHBASE_POSTGRES_TARGET_DIR=~/benchbase/target/benchbase-postgres```

   (b) Apply the changes: ```source ~/.bashrc```

2. Specify local paths in ```cybernetics/configs/benchbase/tpcc/postgres_bo_gp.ini``` including

    ```dbms_info.db_cluster```: where Postgres stores all data
    
    ```dbms_info.db_log_filepath```: where Postgres saves logs

    ```results.save_path```: where you want to save the experiment results

3. Start DBMS config tuning:

   ```
   python ./examples/run_dbms_config_tuning.py --config_path ./cybernetics/configs/benchbase/tpcc/postgres_bo_gp.ini
   ```

4. Once tuning is complete, check ```./logs/<latest run>/cybernetics.log``` for logs and see BenchBase and tuning optimizer outputs in ```results.save_path```.

## Wish List
Cybernetics is under active development by [Tianji Cong](https://superctj.github.io). Please use GitHub's issue tracker for all issues and feature requests.

### Configuration optimizers
- [x] BO - Gaussian Process (Vanilla BO)
- [x] BO - Random Forest (SMAC)
- [x] RL - DDPG

### Parameter Space Reduction
- [ ] Knob Selection - Lasso
- [ ] Knob Selection - Gini Index
- [ ] Knob Selection - fANOVA
- [ ] Knob Selection - SHAP Value
- [ ] Space Transformation - Random Linear Projection
- [ ] Space Transformation - Biased Sampling for Hybrid Knobs
- [ ] Space Transformation - Knob Value Bucketization

### Knowledge Transfer
- [ ] Workload Mapping
