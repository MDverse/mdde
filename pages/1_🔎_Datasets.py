"""Streamlit web app for exploring molecular dynamics (MD) data."""

import streamlit as st
import pandas as pd
import website_management as wm


@st.cache_data
def request_search(data: pd.DataFrame, search: str, is_show: bool) -> pd.DataFrame:
    """Search the data in the pd.DataFrame for the desired value.

    Parameters
    ----------
    data: pd.DataFrame
        contains all the information from our extracted MD data.
    search: str
        contains the searched keyword.
    is_show: bool
        determines whether all data should be shown.

    Returns
    -------
    pd.DataFrame
        returns the filtered pd.DataFrame object.
    """
    to_keep = [
        "dataset_origin",
        "dataset_id",
        "title",
        "date_creation",
        "author",
        "description",
        "file_number",
        "dataset_url",
    ]
    if not is_show:
        results = data[
            data["title"].str.contains(search, case=False, regex=False)
            | data["keywords"].str.contains(search, case=False, regex=False)
            | data["description"].str.contains(search, case=False, regex=False)
        ]
    else:
        results = data
    results = results[to_keep]
    results.columns = [
        "Dataset",
        "ID",
        "Title",
        "Creation date",
        "Authors",
        "Description",
        "# Files",
        "URL",
    ]
    return results


def search_processing(data: pd.DataFrame, search: str, is_show: bool) -> tuple:
    """Search the table for the word the user is looking for.

    Parameters
    ----------
    data: pd.DataFrame
        a pandas dataframe contains our datasets.
    search: str
        search word.
    is_show: bool
        determines whether all data should be shown.

    Returns
    -------
    object
        returns a AgGrid object or None if our data is empty.
    """
    # Start the research process
    if search or is_show:
        results = request_search(data, search, is_show)
        return results
    else:
        return pd.DataFrame()


def user_interaction() -> None:
    """Control the streamlit application.

    Allows interaction between the user and our informational data from MD
    data.
    """
    st.set_page_config(page_title="MDverse", layout="wide")
    wm.load_css()
    select_data = "datasets"
    data = wm.load_data()[select_data]
    search, is_show, col_filter, col_download = wm.display_search_bar(
        select_data)
    results = search_processing(data=data, search=search, is_show=is_show)
    if not results.empty:
        with col_filter:
            add_filter = st.checkbox("Add filter")
        data_filtered = wm.filter_dataframe(results, add_filter)
        bokeh_table = wm.display_bokeh(data_filtered)
        sel_row = None
        if bokeh_table:
            sel_row = bokeh_table.get("INDEX_SELECT")
            with col_download:
                wm.display_export_button(sel_row, data_filtered)
            wm.display_details(sel_row, data_filtered, select_data)
    elif search != "":
        st.write("No result found.")


if __name__ == "__main__":
    user_interaction()
