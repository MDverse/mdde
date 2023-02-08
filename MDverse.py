import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="MDverse",
    page_icon="🔎"
)

st.write("# Welcome to MDverse! 🔎")

st.sidebar.success("Select the type of MD search.")

st.markdown(
    """
    Streamlit is an open-source app framework built specifically for
    Machine Learning and Data Science projects.
    **👈 Select a demo from the sidebar** to see some examples
    of what Streamlit can do!
    ### Want to learn more?
    - Check out [streamlit.io](https://streamlit.io)
    - Jump into our [documentation](https://docs.streamlit.io)
    - Ask a question in our [community
        forums](https://discuss.streamlit.io)
    ### See more complex demos
    - Use a neural net to [analyze the Udacity Self-driving Car Image
        Dataset](https://github.com/streamlit/demo-self-driving)
    - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
"""
)

@st.cache
def load_data() -> pd.DataFrame:
    """Retrieve our data and loads it into the pd.DataFrame object.

    Returns
    -------
    pd.DataFrame
        returns an pd.DataFrame object containing our data.
    """
    repository = ["zenodo", "figshare", "osf"]
    dfs_merged = []
    for name_rep in repository :
        tmp_data_text = pd.read_csv(f"data/{name_rep}_datasets_text.tsv", 
                            delimiter="\t")
        tmp_dataset = pd.read_csv(f"data/{name_rep}_datasets.tsv",
                            delimiter="\t")
        tmp_data_merged = pd.merge(tmp_data_text, tmp_dataset, on=["dataset_id",
                                    "dataset_origin"], validate="many_to_many")
        print(f"{name_rep}: found {tmp_data_merged.shape[0]} datasets.")
        dfs_merged.append(tmp_data_merged)
    datasets = pd.concat(dfs_merged, ignore_index=True)

    gro = pd.read_csv(f"data/gromacs_gro_files_info.tsv",
                            delimiter="\t", dtype={"dataset_id": str})
    gro_data = pd.merge(gro, datasets, how="left", on=["dataset_id", 
                        "dataset_origin"], validate="many_to_one")
    gro_data.to_csv("test.tsv", sep="\t")

    mdp = pd.read_csv(f"data/gromacs_mdp_files_info.tsv",
                            delimiter="\t", dtype={"dataset_id": str})
    mdp_data = pd.merge(mdp, datasets, how="left", on=["dataset_id", 
                        "dataset_origin"], validate="many_to_one")                     
    return datasets, gro_data, mdp_data  

if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

if 'show' not in st.session_state:
    st.session_state['show'] = False
