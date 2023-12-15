# Cybernetics: Open Source DBMS Configuration Tuning

Codebase of a working open source DBMS configuration tuning framework for Postgres.

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

    e.g.,
    
    ```conda develop /home/tianji/cybernetics```

## Quick Start
Run the default configuration and the PGTune configuration on the TPC-C benchmark (you need to change the paths in the program to your own paths):

    ```pytest -s ./tests/test_evaluating_pgtune_tpcc.py```
