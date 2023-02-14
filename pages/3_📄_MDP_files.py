"""Streamlit web app for exploring molecular dynamics (MD) data."""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode
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
        "file_name",
        "dt",
        "nsteps",
        "temperature",
        "thermostat",
        "barostat",
        "dataset_url",
    ]
    if not is_show:
        results = data[
            data["title"].str.contains(search, case=False)
            | data["file_name"].str.contains(search, case=False)
            | data["description"].str.contains(search, case=False)
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
        "File name",
        "Step size",
        "# Steps",
        "Temperature (K)",
        "Thermostat",
        "Barostat",
        "URL",
    ]
    return results


def config_options_mdp(data_filtered: pd.DataFrame, page_size: int) -> list:
    """Configure an Aggrid object with specific options for mdp files searches.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        contains our data filtered by a search.
    page_size: int
        specifies the number of rows to display in the AgGrid table.

    Returns
    -------
    list
        return a list of dictionary containing all the information of the
        configuration for our Aggrid object.
    """
    gridOptions = wm.config_options(data_filtered, page_size)
    # Configuration of specific column widths
    col_names = [column["headerName"] for column in gridOptions["columnDefs"]]
    gridOptions["columnDefs"][col_names.index("Dataset")]["maxWidth"] = 160
    gridOptions["columnDefs"][col_names.index("ID")]["maxWidth"] = 120
    gridOptions["columnDefs"][col_names.index("Step size")]["maxWidth"] = 140
    gridOptions["columnDefs"][col_names.index("# Steps")]["maxWidth"] = 140
    gridOptions["columnDefs"][col_names.index("Temperature (K)")]["maxWidth"] = 190
    gridOptions["columnDefs"][col_names.index("Thermostat")]["maxWidth"] = 150
    gridOptions["columnDefs"][col_names.index("Creation date")]["hide"] = "true"
    gridOptions["columnDefs"][col_names.index("Authors")]["hide"] = "true"
    return gridOptions


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


def display_AgGrid(results: pd.DataFrame) -> object:
    """Configure, create and display the AgGrid object.

    Parameters
    ----------
    results: pd.DataFrame
        a pandas dataframe filtred.

    Returns
    -------
    object
        returns a AgGrid object contains our data filtered.
    """
    page_size = 20
    st.write(len(results), "elements found")
    # A dictionary containing all the configurations for our Aggrid objects
    gridOptions = config_options_mdp(results, page_size)
    # Generate our Aggrid table and display it
    grid_table = AgGrid(
        results,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        theme="alpine",
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        reload_data=False,
    )
    return grid_table


def user_interaction(select_data: int) -> None:
    """Control the streamlit application.

    Allows interaction between the user and our informational data from MD
    data.

    Parameters
    ----------
    select_data: int
        contains a number (0, 1 or 2) that will allow the selection of data.
    """
    st.set_page_config(page_title="MDverse", layout="wide")
    wm.load_css()
    data = wm.load_data()[select_data]
    search, is_show, col_download = wm.display_search_bar("mdp")
    results = search_processing(data=data, search=search, is_show=is_show)
    if not results.empty:
        grid_table = display_AgGrid(results)
        if grid_table:
            sel_row = grid_table["selected_rows"]
            with col_download:
                wm.display_export_button(sel_row)
            wm.display_details(sel_row)
    elif search != "":
        st.write("No result found.")


if __name__ == "__main__":
    user_interaction(2)
