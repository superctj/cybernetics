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

    ```git clone <Cybernetics repo url>```

    ```cd cybernetics```

2. Create and activate the development environment:

    ```conda env create -f environment.yml ```

    ```conda activate cybernetics```

3. Import Cybernetics as editable packages to the conda environment:

    ```conda develop <path to Cybernetics>```

    e.g., ```conda develop /home/tianji/cybernetics```


## Quick Start
Follow the steps below to run the default configuration and the PGTune configuration on the TPC-C benchmark.

1. Change DBMS connection configuration in ```./tests/test_evaluating_pgtune_tpcc.py``` to your own .

2. Change Benchbase-related paths in ```./scripts/benchbase_tpcc_postgres_test_pgtune.sh``` to your own.

3. Evaluate the default configuration and the PGTune configuration:

   pytest -s ./tests/test_evaluating_pgtune_tpcc.py

## Wish List
Cybernetics is under active development by [Tianji Cong](https://superctj.github.io). Please use GitHub's issue tracker for all issues and feature requests.

### Configuration optimizers
- [ ] BO - Gaussian Process
- [ ] BO - SMAC
- [ ] RL - DDPG

### Parameter Space Reduction
- [ ] Knob Selection - Lasso
- [ ] Knob Selection - Gini Index
- [ ] Knob Selection - fANOVA
- [ ] Knob Selection - SHAP Value
- [ ] Subspace - Randomized Low-Dimensional Projection
- [ ] Subspace - Biased Sampling for Hybrid Knobs
- [ ] Subspace - Knob Value Bucketization

### Knowledge Transfer
- [ ] Workload Mapping
