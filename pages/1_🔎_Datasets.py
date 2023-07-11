"""Streamlit web app for exploring molecular dynamics (MD) data."""

import streamlit as st
import pandas as pd
import website_management as wm


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
        "file_number",
    ]
    if search:
        results = data[
            data["title"].str.contains(search, case=False, regex=False)
            | data["keywords"].str.contains(search, case=False, regex=False)
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
        "# Files",
    ]
    return results


def user_interaction() -> None:
    """Control the streamlit application.

    Allows interaction between the user and our informational data from MD
    data.
    """
    st.set_page_config(page_title="MDverse - datasets", layout="wide")
    wm.load_css()
    select_data = "datasets"
    data = wm.load_data()[select_data]
    search, col_filter, col_download = wm.display_search_bar(select_data)
    results = request_search(data, search)
    if not results.empty:
        with col_filter:
            add_filter = st.checkbox("🔍 Add filter", key="filter" + select_data)
        data_filtered = wm.filter_dataframe(results, add_filter)

        selection = [False] * len(data_filtered)
        data_filtered.insert(0, "Selection", selection)
        config = st.column_config.Column(
            disabled=True,
        )
        column_config = {
            column: config for column in data_filtered.columns if column != "Selection"
        }
        st.data_editor(
            data_filtered,
            height=850,
            width=1200,
            key="data_editor",
            hide_index=True,
            num_rows="fixed",
            column_config=column_config,
        )

        edited_rows = st.session_state["data_editor"].get("edited_rows")
        selected = []
        for key, value in edited_rows.items():
            if value["Selection"] == True:
                selected.append(key)

        st.sidebar.write("Selected datasets:", len(selected), "\n", selected)

        with col_download:
            wm.display_export_button(data_filtered)
        wm.display_details(data_filtered, select_data)
    elif search != "":
        st.write("No result found.")


if __name__ == "__main__":
    user_interaction()
