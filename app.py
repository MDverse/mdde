import streamlit as st
import pandas as pd
import numpy as np


def load_data(loader_str):
    df = pd.DataFrame()
    for repository in ["zenodo", "figshare", "osf"]:
        datasets = pd.read_csv(
            f"data/{repository}_datasets.tsv",
            sep="\t",
            dtype={"dataset_id": str}
        )
        loader_str.write(f"{repository}: found {datasets.shape[0]} datasets.")
        files = pd.read_csv(
            f"data/{repository}_files.tsv",
            sep="\t",
            dtype={"dataset_id": str, "file_type": str,
                "file_md5": str, "file_url": str}
        )
        loader_str.text(f"{repository}: found {files.shape[0]} files.")
        tab = pd.merge(files, datasets, how="left", on=["dataset_id", "dataset_origin"], validate="many_to_one")
        loader_str.text(f"{repository}: merged dataframe has {tab.shape[0]} entries.")
        df = pd.concat([df, tab], ignore_index=True)

    loader_str.text(f"Dimensions of the final dataframe: {df.shape[0]} lines (files) x {df.shape[1]} columns")

st.title("MDverse data explorer")

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')

data = load_data(data_load_state)

# Notify the reader that the data was successfully loaded.
data_load_state.text('Loading data...done!')