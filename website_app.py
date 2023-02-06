"""Our program is a streamlit app for exploring molecular dynamics (MD) data.

There were extracted from unmoderated and generalized data such as Zenodo, etc.
We propose an website allowing to facilitate the user's search in these MD data.
"""

import streamlit as st
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from st_keyup import st_keyup
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from datetime import datetime


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
        "date_creation",
        "author",
        "description",
        "file_number",
        "dataset_url",
    ]
    results = data[
        data["title"].str.contains(search, case=False)
        | data["keywords"].str.contains(search, case=False)
        | data["description"].str.contains(search, case=False)
    ]
    results = results[to_keep]
    results.columns = [
        "Dataset",
        "ID",
        "Title",
        "Creation date",
        "Authors",
        "Description",
        "#Files",
        "URL",
    ]
    return results


@st.cache
def load_data() -> pd.DataFrame:
    """Retrieve our data and loads it into the pd.DataFrame object.

    Returns
    -------
    pd.DataFrame
        returns an pd.DataFrame object containing our data.
    """
    paths = ["../data/zenodo_datasets_text.tsv", "../data/zenodo_datasets.tsv"]
    data1 = pd.read_csv(paths[0], delimiter="\t")
    data2 = pd.read_csv(paths[1], delimiter="\t")
    data = pd.merge(data1, data2)
    return data


def is_isoformat(dates: object) -> bool:
    """Check that all dates are in iso 8601 format.

    Parameters
    ----------
    dates : object
        contains all dates from a pandas dataframe.

    Returns
    -------
    bool
        returns false if at least one element does not respect the format
        otherwise returns true.
    """
    for date_str in dates:
        # Try to convert a string into an iso datatime format
        try:
            datetime.fromisoformat(date_str)
        except Exception:
            return False
    return True


def filter_dataframe(df: pd.DataFrame, add_filter) -> pd.DataFrame:
    """Add a UI on top of a dataframe to let viewers filter columns.

    This slightly modified function was extracted from the following git. 
    https://github.com/tylerjrichards/st-filter-dataframe

    Parameters
    ----------
    df : pd.DataFrame
        original dataframe.
    add_filter : bool
        allows to know if the user wants to do a filter.

    Returns
    -------
    pd.DataFrame
            Filtered dataframe
    """
    if not add_filter:
        return df

    df: pd.DataFrame = df.copy()
    tmp_col = {}
    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                tmp_col[col] = pd.to_datetime(df[col].copy())
                df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    modification_container = st.container()
    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_isoformat(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        tmp_col[column].min(),
                        tmp_col[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[tmp_col[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input, case=False)]
    return df


def content_cell_func() -> str:
    """Return a Java script function as a string to display a tooltip.

    The Java script code will be configured in the config_options function.

    Returns
    -------
    str
        return the JS code as a string
    """
    return """
            function(params) { 
                return '<span title="' + params.value + '">'+params.value+'</span>';  
            }; 
            """


def link_cell_func() -> str:
    """Return a Java script function as a string to create a hyperlink.

    The Java script code will be configured in the config_options function.

    Returns
    -------
    str
        return the JS code as a string
    """
    return """
            function(params) {
                return '<a href="' + params.value + '" target="_blank">'+ params.value+'</a>'; 
            };
            """


def clicked_cell_func(col_name: list) -> str:
    """Return a Java script function as a string to display a popup.

    The popup contains the title and description of the data. 
    The Java script code will be configured in the config_options function.

    Parameters
    ----------
    col_names : list
        contains the list of column names of interest, namely the Title
        and Description column.

    Returns
    -------
    str
        return the JS code as a string
    """
    contents: str = (
        f"params.node.data.{col_name[0]} + '<br/>' + params.node.data.{col_name[1]}"
    )
    return f"""
            function(params){{ 
                confirm({contents});
                return '<a href="' + params.value + '" target="_blank">'+ params.value+'</a>';  
            }};
            """


def config_options(data_filtered: pd.DataFrame, page_size: int) -> dict:
    """Configure the Aggrid object with dedicated functions for our data.

    Parameters
    ----------
    data_filtered : pd.DataFrame
        contains our data filtered by a search

    Returns
    -------
    dict
        return a dictionary containing all the information of the configuration
        for our Aggrid object.
    """
    # Convert our dataframe into a GridOptionBuilder object
    gb = GridOptionsBuilder.from_dataframe(data_filtered)
    # Add a checkbox for each row
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_pagination(
        enabled=True, paginationAutoPageSize=False, paginationPageSize=page_size
    )
    # Add a checkbox in the first column to select all columns
    gb.configure_column("Dataset", headerCheckboxSelection=True)
    # Add a JsCode that will display the content when hovering with the mouse
    gb.configure_columns(
        data_filtered.columns, cellRenderer=JsCode(content_cell_func())
    )
    # Add a JsCode that will add a hyperlink to the URL column
    gb.configure_column("URL", cellRenderer=JsCode(link_cell_func()))
    # Add a JsCode that will display the full content in a popup
    gb.configure_columns(
        ["Title", "Description"],
        onCellDoubleClicked=JsCode(clicked_cell_func(["Title", "Description"])),
    )
    # Build the dictionary that will contain all the configurations
    gridOptions = gb.build()

    # Configuration of specific column widths
    for column_parameters in gridOptions["columnDefs"]:
        if (
            column_parameters["headerName"] == "#Files"
            or column_parameters["headerName"] == "ID"
        ):
            column_parameters["maxWidth"] = 100
        elif (
            column_parameters["headerName"] == "Creation date"
            or column_parameters["headerName"] == "Dataset"
            or column_parameters["headerName"] == "Authors"
        ):
            column_parameters["maxWidth"] = 140
    return gridOptions


@st.cache
def convert_data(sel_row: dict) -> pd.DataFrame:
    """Convert a dictionary into a pd.DataFrame object.

    Parameters
    ----------
    sel_row : dict
        contains the selected rows of our Aggrid array as a dictionary.

    Returns
    -------
    pd.DataFrame
        returns an pd.DataFrame object containing the selected rows of our data.
    """
    to_export: pd.DataFrame = pd.DataFrame.from_records(sel_row)
    if "_selectedRowNodeInfo" in to_export.columns:
        to_export.pop("_selectedRowNodeInfo")
    return to_export


def user_interaction() -> None:
    """Control the streamlit application.
    
    Allows interaction between the user and our informational data from MD data.
    """
    # Configuration of the display and the parameters of the website
    st.set_page_config(layout="wide")
    data = load_data()
    st.title("MDverse")
    placeholder = "Enter search term (for instance: POPC, Gromacs, CHARMM36)"
    col_keyup, _, _ = st.columns([3, 1, 1])
    with col_keyup:
        search = st_keyup("", placeholder=placeholder)
    columns = st.columns([1 for i in range(10)])
    with columns[0]:
        show_all = st.checkbox("Show all")
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
            data_filtered = filter_dataframe(results, add_filter)
            st.write(len(data_filtered), "elements found")
            # A dictionary containing all the configurations for our Aggrid objects
            gridOptions = config_options(data_filtered, page_size)
            grid_table = AgGrid(
                data_filtered,
                gridOptions=gridOptions,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                theme="alpine",
            )
            sel_row = grid_table["selected_rows"]
            if sel_row:
                new_data = convert_data(sel_row)
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
