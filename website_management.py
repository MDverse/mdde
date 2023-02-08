"""This python file contains all the functions to help manage the site.
"""

import streamlit as st
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from st_aggrid import GridOptionsBuilder, JsCode
from datetime import datetime


@st.experimental_memo
def load_data() -> tuple:
    """Retrieve our data and loads it into the pd.DataFrame object.

    Returns
    -------
    tuple
        returns an tuple contains pd.DataFrame object containing our data.
    """
    repository = ["zenodo", "figshare", "osf"]
    dfs_merged = []
    for name_rep in repository :
        tmp_data_text = pd.read_csv(f"data/{name_rep}_datasets_text.tsv", 
                            delimiter="\t", dtype={"dataset_id": str})
        tmp_dataset = pd.read_csv(f"data/{name_rep}_datasets.tsv",
                            delimiter="\t", dtype={"dataset_id": str})
        tmp_data_merged = pd.merge(tmp_data_text, tmp_dataset, on=["dataset_id",
                                    "dataset_origin"], validate="many_to_many")
        print(f"{name_rep}: found {tmp_data_merged.shape[0]} datasets.")
        dfs_merged.append(tmp_data_merged)
    datasets = pd.concat(dfs_merged, ignore_index=True)

    gro = pd.read_csv(f"data/gromacs_gro_files_info.tsv",
                            delimiter="\t", dtype={"dataset_id": str})
    gro_data = pd.merge(gro, datasets, how="left", on=["dataset_id", 
                        "dataset_origin"], validate="many_to_one")
    gro_data.to_csv("gro_data.tsv", sep="\t")

    mdp = pd.read_csv(f"data/gromacs_mdp_files_info.tsv",
                            delimiter="\t", dtype={"dataset_id": str})
    mdp_data = pd.merge(mdp, datasets, how="left", on=["dataset_id", 
                        "dataset_origin"], validate="many_to_one")                     
    return datasets, gro_data, mdp_data


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