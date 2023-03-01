"""Streamlit web app for exploring molecular dynamics (MD) data."""

import streamlit as st

import website_management as wm

st.set_page_config(page_title="MDverse", page_icon="🔎", layout="wide")

st.write("# Welcome to MDverse data explorer 🔎")

st.sidebar.success("⬆️ Select the item you want to search for.")

datasets_df = wm.load_data()["datasets"]

dataset_agg = (datasets_df
 .groupby("dataset_origin")
 .agg(
     number_of_datasets=("dataset_id", "nunique"),
     date_first_dataset=("date_creation", "min"),
     date_last_dataset=("date_creation", "max"),
 )
 .rename(columns={"number_of_datasets": "Number of datasets",
                  "date_first_dataset":"First dataset",
                  "date_last_dataset":"Last dataset"})
)
dataset_agg.loc["total"] = dataset_agg.sum(numeric_only=True)
dataset_agg.index.name = "Dataset origin"
st.write("Amount of data available:")
st.dataframe(dataset_agg.style.format(thousands=",", precision=0))

