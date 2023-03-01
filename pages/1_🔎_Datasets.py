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


def load_css_table() -> None:
    """Load a css style."""
    itables.options.css = """
    .itables {
        font-family: 'sans-serif';
        font-size: 0.8rem;
    }

    .itables table td { 
        word-wrap: break-word;
        min-width: 50px;
        max-width: 50px;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 12px;
    }
    
    .itables table td:nth-child(3) {
        min-width: 80px;
        max-width: 80px;
    }
    
    .itables table td:nth-child(4), .itables table td:nth-child(7) {
        max-width: 300px;
    }
    
    .itables table th { 
        word-wrap: break-word;
        font-size: 12px;
    }
    
    .itables table th:nth-child(1), .itables table td:nth-child(1){
        display:none;
    }
    
    a:link, a:visited {
        color: rgb(51, 125, 255);
    }
    
    .itables {
        background: white;
        padding: 10px;
    }
    """


def user_interaction() -> None:
    """Control the streamlit application.

    Allows interaction between the user and our informational data from MD
    data.
    """
    st.set_page_config(page_title="MDverse", layout="wide")
    wm.load_css()
    select_data = "datasets"
    data = wm.load_data()[select_data]
    search, col_filter, col_download = wm.display_search_bar(select_data)
    results = request_search(data, search)
    if not results.empty:
        with col_filter:
            add_filter = st.checkbox("🔍 Add filter")
        data_filtered = wm.filter_dataframe(results, add_filter)
        load_css_table()
        wm.display_table(data_filtered)
        with col_download:
            wm.display_export_button(data_filtered)
        wm.display_details(data_filtered, select_data)
    elif search != "":
        st.write("No result found.")


if __name__ == "__main__":
    user_interaction()
