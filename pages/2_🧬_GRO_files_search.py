"""Our program is a streamlit app for exploring molecular dynamics (MD) data.

There were extracted from unmoderated and generalized data such as Zenodo, etc.
We propose an website allowing to facilitate the user's search in these MD data.
"""

import streamlit as st
import pandas as pd
from st_keyup import st_keyup
from st_aggrid import AgGrid
from datetime import datetime
import website_management as wm


def request_search(data: pd.DataFrame, search: str) -> pd.DataFrame:
    """Search the data in the pd.DataFrame for the desired value.

    Parameters
    ----------
    data : pd.DataFrame
        contains all the information from our extracted MD data
    search : str
        contains the searched keyword

    Returns
    -------
    pd.DataFrame
        returns the filtered pd.DataFrame object.
    """
    to_keep = [
        "dataset_origin",
        "dataset_id",
        "title",
        "description",
        "file_name",
        "atom_number",
        "has_protein",
        "has_lipid",
        "has_nucleic",
        "dataset_url"
    ]
    results = data[
        data["title"].str.contains(search, case=False)
        | data["file_name"].str.contains(search, case=False)
        | data["description"].str.contains(search, case=False)
    ]
    results = results[to_keep]
    results.columns = [
        "Dataset",
        "ID",
        "Title",
        "Description",
        "File name",
        "Atom number",
        "Protein",
        "Lipid",
        "Nucleic",
        "URL",
    ]
    return results


def config_options_gro(data_filtered: pd.DataFrame, page_size: int) -> dict: 
    gridOptions = wm.config_options(data_filtered, page_size)
    # Configuration of specific column widths
    return gridOptions


def user_interaction() -> None:
    """Control the streamlit application.
    
    Allows interaction between the user and our informational data from MD data.
    """
    # Configuration of the display and the parameters of the website
    st.set_page_config(page_title="MDverse", layout="wide")
    data = wm.load_data()[1]
    st.title("MDverse")
    search = ""
    placeholder = "Enter search term (for instance: POPC, Gromacs, CHARMM36)"
    col_keyup, _, _ = st.columns([3, 1, 1])
    with col_keyup:
        search = st_keyup("GRO files search", placeholder=placeholder)
    columns = st.columns([2 if i == 0 or i == 1 else 1 for i in range(10)])
    with columns[0]:
        show_all = st.checkbox("Show all", key="gro")
        if show_all:
            search = " "
    # Start the research process
    if search:
        with columns[1]:
            add_filter = st.checkbox("Add filters")
        with columns[9]:
            page_size = st.selectbox(
                "Select rows", (10, 20, 30, 50, 100, 200, 250), index=1
            )
        results = request_search(data, search)
        if not results.empty:
            data_filtered = wm.filter_dataframe(results, add_filter)
            st.write(len(data_filtered), "elements found")
            # A dictionary containing all the configurations for our Aggrid objects
            gridOptions = config_options_gro(data_filtered, page_size)
            # Generate our Aggrid table and display it
            grid_table = AgGrid(
                data_filtered,
                gridOptions=gridOptions,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                theme="alpine"
            )
            sel_row = grid_table["selected_rows"]
            if sel_row:
                new_data = wm.convert_data(sel_row)
                today_date = datetime.now().strftime("%Y-%m-%d")
                st.download_button(
                    label="Export to tsv",
                    data=new_data.to_csv(sep="\t", index=False).encode("utf-8"),
                    file_name=f"mdverse_{today_date}.tsv",
                    mime="text/tsv",
                )
        else:
            st.write("No results found.")


if __name__ == "__main__":
    user_interaction()
