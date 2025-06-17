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

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

Create the virtual environment:

```bash
uv sync
```

## Get data

Data files are directly downloaded from [Zenodo](https://doi.org/10.5281/zenodo.7856523).


## Run the web application

```bash
uv run streamlit run MDverse_data_explorer.py
```