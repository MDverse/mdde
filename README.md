# Molecular dynamics data explorer

## Setup your environment

Clone the repository:

```bash
git clone https://github.com/MDverse/mdde.git
```

Move to the new directory:

```bash
cd mdde
```

Install [miniconda](https://docs.conda.io/en/latest/miniconda.html).

Install [mamba](https://github.com/mamba-org/mamba):

```bash
conda install mamba -n base -c conda-forge
```

Create the `mdde` conda environment:
```
mamba env create -f binder/environment.yml
```

Load the `mdde` conda environment:
```
conda activate mdde
```

Note: you can also update the conda environment with:

```bash
mamba env update -f binder/environment.yml
```

To deactivate an active environment, use

```
conda deactivate
```

## Get data

Data files should be located in the `data` directory and comply with the [data model](https://github.com/MDverse/mdws/blob/main/docs/data_model.md).


## Run the web application

```bash
streamlit run app.py
```