"""Our program is a streamlit app for exploring molecular dynamics (MD) data.

There were extracted from unmoderated and generalized data such as Zenodo, etc.
We propose an website allowing to facilitate the user's search in these MD
data.
"""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
import website_management as wm


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
            data["title"].str.contains(search, case=False)
            | data["keywords"].str.contains(search, case=False)
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
        "# Files",
        "URL",
    ]
    return results


def config_options_keywords(data_filtered: pd.DataFrame, page_size: int) -> list:
    """Configure the Aggrid object with specific options for keyword searches.

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
    gridOptions["columnDefs"][col_names.index("# Files")]["maxWidth"] = 100
    gridOptions["columnDefs"][col_names.index("ID")]["maxWidth"] = 100
    gridOptions["columnDefs"][col_names.index("Creation date")]["maxWidth"] = 140
    gridOptions["columnDefs"][col_names.index("Dataset")]["maxWidth"] = 140
    gridOptions["columnDefs"][col_names.index("Authors")]["maxWidth"] = 140
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


def display_AgGrid(results: pd.DataFrame, columns: list, select_data: int) -> object:
    """Configure, create and display the AgGrid object.

    Parameters
    ----------
    results: pd.DataFrame
        a pandas dataframe filtred.
    select_data: int
        contains a number (0, 1 or 2) that will allow the selection of data.
    columns: list
        a list for the layout of the site.

    Returns
    -------
    object
        returns a AgGrid object contains our data filtered.
    """
    with columns[1]:
        # Add a key to make the checkbox unique from other checkboxes
        add_filter = st.checkbox("Add filters", key=select_data + 10)
    with columns[9]:
        page_size = st.selectbox(
            "Select rows", (10, 20, 30, 50, 100, 200, 250), index=1
        )
    data_filtered = wm.filter_dataframe(results, add_filter)
    st.write(len(data_filtered), "elements found")
    # A dictionary containing all the configurations for our Aggrid objects
    gridOptions = config_options_keywords(data_filtered, page_size)
    # Generate our Aggrid table and display it
    grid_table = AgGrid(
        data_filtered,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        theme="alpine",
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
    #st.set_page_config(page_title="MDverse", layout="wide")
    data = wm.load_data()[select_data]
    search, is_show, columns = wm.display_search_bar(select_data)
    results = search_processing(data=data, search=search, is_show=is_show)
    if not results.empty:
        grid_table = display_AgGrid(
            results=results, columns=columns, select_data=select_data
        )
        if grid_table:
            wm.display_export_button(grid_table)
    elif search != "":
        st.write("No result found.")


if __name__ == "__main__":
    user_interaction(0)
