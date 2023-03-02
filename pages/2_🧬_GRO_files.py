"""Streamlit web app for exploring molecular dynamics (MD) data."""

import streamlit as st
import pandas as pd
import website_management as wm
import itables


@st.cache_data
def request_search(data: pd.DataFrame, search: str) -> pd.DataFrame:
    """Search the data in the pd.DataFrame for the desired value.

    Parameters
    ----------
    data: pd.DataFrame
        contains all the information from our extracted MD data.
    search: str
        contains the searched keyword.

    Returns
    -------
    pd.DataFrame
        returns the filtered pd.DataFrame object.
    """
    to_keep = [
        "dataset_url",
        "dataset_origin",
        "dataset_id",
        "title",
        "date_creation",
        "author",
        "description",
        "file_name",
        "atom_number",
        "has_protein",
        "has_lipid",
        "has_nucleic",
        "has_glucid",
        "has_water_ion",
    ]
    if search:
        results = data[
            data["title"].str.contains(search, case=False, regex=False)
            | data["file_name"].str.contains(search, case=False, regex=False)
            | data["description"].str.contains(search, case=False, regex=False)
            | data["dataset_id"].str.contains(search, case=False, regex=False)
        ]
    else:
        results = data
    results = results[to_keep]
    results.columns = [
        "URL",
        "Dataset",
        "ID",
        "Title",
        "Creation date",
        "Authors",
        "Description",
        "File name",
        "Atom number",
        "Protein",
        "Lipid",
        "Nucleic",
        "Glucid",
        "Water/Ion",
    ]
    return results


def user_interaction() -> None:
    """Control the streamlit application.

    Allows interaction between the user and our informational data from MD
    data.
    """
    st.set_page_config(page_title="MDverse - Gromacs GRO files", layout="wide")
    wm.load_css()
    select_data = "gro"
    data = wm.load_data()[select_data]
    search, col_filter, col_download = wm.display_search_bar(select_data)
    results = request_search(data, search)
    if not results.empty:
        results = results.reset_index()
        results["index"] = range(1, len(results) + 1)
        with col_filter:
            add_filter = st.checkbox("🔍 Add filter")
        data_filtered = wm.filter_dataframe(results, add_filter)
        st.components.v1.html(wm.display_table(data_filtered), height=850)
        with col_download:
            wm.display_export_button(data_filtered)
        wm.display_details(data_filtered, select_data)
    elif search != "":
        st.write("No result found.")


if __name__ == "__main__":
    user_interaction()
