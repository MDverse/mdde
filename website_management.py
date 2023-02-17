"""Helper functions to manage the Streamlit application."""

import streamlit as st
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from st_keyup import st_keyup
from st_aggrid import GridOptionsBuilder, JsCode
from datetime import datetime


@st.cache_data
def load_data() -> tuple:
    """Retrieve our data and loads it into the pd.DataFrame object.

    Returns
    -------
    tuple
        returns an tuple contains pd.DataFrame object containing our datasets.
    """
    repository = ["zenodo", "figshare", "osf"]
    dfs_merged = []
    for name_rep in repository:
        tmp_data_text = pd.read_csv(
            f"data/{name_rep}_datasets_text.tsv",
            delimiter="\t",
            dtype={"dataset_id": str},
        )
        tmp_dataset = pd.read_csv(
            f"data/{name_rep}_datasets.tsv", delimiter="\t", dtype={"dataset_id": str}
        )
        tmp_data_merged = pd.merge(
            tmp_data_text,
            tmp_dataset,
            on=["dataset_id", "dataset_origin"],
            validate="many_to_one",
        )
        print(f"{name_rep}: found {tmp_data_merged.shape[0]} datasets.")
        dfs_merged.append(tmp_data_merged)
    datasets = pd.concat(dfs_merged, ignore_index=True)
    gro = pd.read_csv(
        f"data/gromacs_gro_files_info.tsv", delimiter="\t", dtype={"dataset_id": str}
    )
    gro_data = pd.merge(
        gro,
        datasets,
        how="left",
        on=["dataset_id", "dataset_origin"],
        validate="many_to_one",
    )
    mdp = pd.read_csv(
        f"data/gromacs_mdp_files_info.tsv", delimiter="\t", dtype={"dataset_id": str}
    )
    mdp_data = pd.merge(
        mdp,
        datasets,
        how="left",
        on=["dataset_id", "dataset_origin"],
        validate="many_to_one",
    )
    return datasets, gro_data, mdp_data


@st.cache_data
def load_data() -> dict:
    """Retrieve our data and loads it into the pd.DataFrame object.

    Returns
    -------
    dict
        returns a dict contains pd.DataFrame object containing our datasets.
    """
    dfs = {}
    datasets = pd.read_parquet(
        "https://github.com/MDverse/data/blob/master/datasets.parquet?raw=true"
    )
    gro = pd.read_parquet(
        "https://github.com/MDverse/data/blob/master/gromacs_gro_files.parquet?raw=true"
    )
    gro_data = pd.merge(
        gro,
        datasets,
        how="left",
        on=["dataset_id", "dataset_origin"],
        validate="many_to_one",
    )
    mdp = pd.read_parquet(
        "https://github.com/MDverse/data/blob/master/gromacs_mdp_files.parquet?raw=true"
    )
    mdp_data = pd.merge(
        mdp,
        datasets,
        how="left",
        on=["dataset_id", "dataset_origin"],
        validate="many_to_one",
    )
    dfs["datasets"] = datasets
    dfs["gro"] = gro_data
    dfs["mdp"] = mdp_data
    return dfs


def is_isoformat(dates: object) -> bool:
    """Check that all dates are in iso 8601 format.

    Parameters
    ----------
    dates: object
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
    """Add a UI on top of a dataframe to let user filter columns.
    This function is based on the code from the following repository:
    https://github.com/tylerjrichards/st-filter-dataframe

    Parameters
    ----------
    df : pd.DataFrame
        original dataframe.
    add_filter : bool
        tells if the user wants to apply filter.

    Returns
    -------
    pd.DataFrame
            Filtered dataframe
    """
    if not add_filter:
        return df

    df = df.copy()
    tmp_col = {}
    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                tmp_col[col] = pd.to_datetime(df[col].copy())
                df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    modification_container = st.expander(label="Filter dataframe on:", expanded=True)
    with modification_container:
        to_filter_columns = st.multiselect(label="Filter dataframe on", options=df.columns[:-1], label_visibility="collapsed")
        for column in to_filter_columns:
            left, right, _ = st.columns((1, 20, 5))
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
                    df = df[
                        df[column].str.contains(user_text_input, case=False, na=False)
                    ]
    return df


def content_cell_func() -> str:
    """Return a Java script function as a string to display a tooltip.

    The Java script code will be configured in the config_options function.

    Returns
    -------
    str
        return the JS code as a string.
    """
    return """
            function(params) {
                return '<span title="' + params.value + '">'+params.value+'</span>';
            };
            """


def link_cell_func(col_name: str) -> str:
    """Return a Java script function as a string to create a hyperlink.

    The Java script code will be configured in the config_options function.

    Parameters
    ----------
    col_name: str
        name of column contains a hyperlink.

    Returns
    -------
    str
        return the JS code as a string.
    """
    contents = f"params.node.data.{col_name}"
    return f"""
            function(params) {{
                return '<a href="' + {contents} + '" target="_blank">'+ params.value+'</a>';
            }};
            """


def config_options(results: pd.DataFrame, page_size: int) -> list:
    """Configure the Aggrid object with dedicated functions for our data.

    Parameters
    ----------
    results: pd.DataFrame
        contains our data filtered by a search.
    page_size: int
        number of rows to display

    Returns
    -------
    list
        return a list of dictionary containing all the information of the
        configuration for our Aggrid object.
    """
    # Convert our dataframe into a GridOptionBuilder object
    gb = GridOptionsBuilder.from_dataframe(results)
    # Add a checkbox for each row
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_pagination(
        enabled=True, paginationAutoPageSize=False, paginationPageSize=page_size
    )
    # Add a checkbox in the first column to select all columns
    gb.configure_column("Dataset", headerCheckboxSelection=True)
    # Remove filters included in Aggrid
    gb.configure_default_column(filterable=False, sortable=False, suppressMenu=True)
    # Add a JsCode that will display the content when hovering with the mouse
    gb.configure_columns(results.columns, cellRenderer=JsCode(content_cell_func()))
    # Add a JsCode that will add a hyperlink to the URL column
    gb.configure_column("ID", cellRenderer=JsCode(link_cell_func("URL")))
    gb.configure_column("URL", hide=True)
    # Build the dictionary that will contain all the configurations
    gridOptions = gb.build()
    return gridOptions


def convert_data(sel_row: list) -> pd.DataFrame:
    """Convert a list of dictionary into a pd.DataFrame object.

    Parameters
    ----------
    sel_row: list
        contains the selected rows of our Aggrid array as a list of dictionary.

    Returns
    -------
    pd.DataFrame
        returns an pd.DataFrame object containing the selected rows of our
        data.
    """
    to_export: pd.DataFrame = pd.DataFrame.from_records(sel_row)
    if "_selectedRowNodeInfo" in to_export.columns:
        to_export.pop("_selectedRowNodeInfo")
    return to_export


def display_search_bar(select_data: str = "datasets") -> tuple:
    """Configure the display and the parameters of the website.

    Parameters
    ----------
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro","mdp"]
        Default: "datasets"

    Returns
    -------
    tuple
        contains search word, a bool for checkbox and a list for the layout of
        the site.
    """
    st.title("MDverse")
    placeholder = "Enter search term (for instance: Covid, POPC, Gromacs, CHARMM36)"
    label_search = ""
    if select_data == "datasets":
        label_search = "Datasets search"
    elif select_data == "gro":
        label_search = ".gro files search"
    elif select_data == "mdp":
        label_search = ".mdp files search"
    col_keyup, col_show, col_filter, col_download = st.columns([3, 1, 1, 1])
    with col_keyup:
        search = st_keyup(label_search, placeholder=placeholder)
    with col_show:
        is_show = st.checkbox("Show all", key=select_data)
    return search, is_show, col_filter, col_download


def display_export_button(sel_row: list, data_filtered) -> None:
    """Add a download button to export the selected data from the AgGrid table.

    Parameters
    ----------
    sel_row: list
        contains the selected rows of our Aggrid array as a list of dictionary.
    """
    if sel_row:
        new_data = data_filtered
        date_now = f"{datetime.now():%Y-%m-%d_%H-%M-%S}"
        st.download_button(
            label="Export selection to tsv",
            data=new_data.to_csv(sep="\t", index=False).encode("utf-8"),
            file_name=f"mdverse_{date_now}.tsv",
            mime="text/tsv",
        )


def update_contents(sel_row: list, data_filtered: pd.DataFrame, select_data: str) -> None:
    """Change the content display according to the cursor position.

    Parameters
    ----------
    sel_row: list
        contains the selected rows of our Aggrid array as a list of dictionary.
    data_filtered: pd.DataFrame
        filtered dataframe.
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro","mdp"]
    """
    selected_row = sel_row[st.session_state["cursor" + select_data]]
    data = data_filtered.iloc[selected_row]
    contents = f"""
        **{data["Dataset"]}**:
        [{data["ID"]}]({data["URL"]})\n
        {data["Creation date"]}\n
        ### **{data["Title"]}**\n
        ##### {data["Authors"]}\n
        {data["Description"]}
    """
    st.session_state["contents"] = contents


def update_cursor(is_previous: bool, select_data: str) -> None:
    """Change the value of the cursor by incrementing or decrementing.

    Parameters
    ----------
    is_previous: bool
        determine if it should increment the cursor or decrement.
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro","mdp"]
    """
    if is_previous:
        st.session_state["cursor" + select_data] -= 1
    else:
        st.session_state["cursor" + select_data] += 1


def fix_cursor(size_selected: int, select_data: str) -> None:
    """Correct the cursor position according to the number of selected rows.

    Parameters
    ----------
    size_selected: int
        total number of selected rows.
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro","mdp"]
    """
    while st.session_state["cursor" + select_data] >= size_selected:
        st.session_state["cursor" + select_data] -= 1


def display_details(sel_row: list, data_filtered, select_data: str) -> None:
    """Show the details of the selected rows in the sidebar.

    Parameters
    ----------
    sel_row: list
        contains the selected rows of our Aggrid array as a list of dictionary.
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro","mdp"]
    """
    if "cursor" + select_data not in st.session_state:
        st.session_state["cursor" + select_data] = 0

    size_selected = len(sel_row)
    if size_selected != 0:
        fix_cursor(size_selected, select_data)
        update_contents(sel_row, data_filtered, select_data)
        cursor = st.session_state["cursor" + select_data]

        col_select, col_previous, col_next = st.sidebar.columns([2, 1, 1])
        disabled_previous, disabled_next = False, False
        with col_select:
            st.write(cursor + 1, "/", size_selected, "selected")
        with col_previous:
            disabled_previous = False if cursor - 1 >= 0 else True
            st.button(
                "⬅",
                on_click=update_cursor,
                args=(True, select_data,),
                key="previous",
                disabled=disabled_previous,
                use_container_width=True,
            )
        with col_next:
            disabled_next = False if cursor + 1 < size_selected else True
            st.button(
                "➡",
                on_click=update_cursor,
                args=(False, select_data,),
                key="next",
                disabled=disabled_next,
                use_container_width=True,
            )
        st.sidebar.markdown(st.session_state["contents"], unsafe_allow_html=True)
    else:
        st.session_state["cursor" + select_data] = 0


def load_css() -> None:
    """Load a css style."""
    st.markdown(
        """
        <style>
            .stCheckbox {
                position: absolute;
                top: 40px;
            }

            .stDownloadButton {
                position: absolute;
                top: 33px;
            }

            .stDownloadButton > button {
                width: 100%;
            }

            .block-container:first-of-type {
                padding-top: 20px;
                padding-left: 20px;
                padding-right: 20px;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )
