# MDverse data explorer

Live app available at <https://mdverse.streamlit.app/>

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

Data files are directly downloaded from Zenodo.


## Run the web application

```bash
streamlit run MDverse_data_explorer.py
```