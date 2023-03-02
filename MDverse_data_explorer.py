"""Streamlit web app for exploring molecular dynamics (MD) data."""

import streamlit as st
from wordcloud import WordCloud, STOPWORDS

import website_management as wm


st.set_page_config(page_title="MDverse", page_icon="🔎", layout="wide")

st.write("# Welcome to MDverse data explorer 🔎")

st.sidebar.success("⬆️ Select the item you want to search for.")

datasets_df = wm.load_data()["datasets"]

dataset_agg = (
    datasets_df.groupby("dataset_origin")
    .agg(
        number_of_datasets=("dataset_id", "nunique"),
        date_first_dataset=("date_creation", "min"),
        date_last_dataset=("date_creation", "max"),
    )
    .rename(
        columns={
            "number_of_datasets": "Number of datasets",
            "date_first_dataset": "First dataset",
            "date_last_dataset": "Last dataset",
        }
    )
)
dataset_agg.loc["total"] = dataset_agg.sum(numeric_only=True)
dataset_agg.index.name = "Dataset origin"
st.write("Amount of data available:")
st.dataframe(dataset_agg.style.format(thousands=",", precision=0))

gro_df = wm.load_data()["gro"]
st.write(f"{len(gro_df)} Gromacs GRO files")

mdp_df = wm.load_data()["mdp"]
st.write(f"{len(mdp_df)} Gromacs MDP files")


# Build word list for the wordcloud.
titles = " ".join(datasets_df["title"].values)
titles = titles.replace(",", " ").replace(".", " ")
words = [word.lower().strip() for word in titles.split()]
# Build and display the wordcloud.
wordcloud = WordCloud(
    width=1000,
    height=500,
    background_color="white",
    stopwords=set(STOPWORDS),
    min_font_size=12,
).generate(" ".join(words))
st.image(wordcloud.to_array())
