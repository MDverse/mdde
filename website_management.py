"""Helper functions to manage the Streamlit application."""

import streamlit as st
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from st_keyup import st_keyup
from datetime import datetime
import itables


@st.cache_data
def load_data() -> dict:
    """Retrieve our data and loads it into the pd.DataFrame object.

    Returns
    -------
    dict
        returns a dict containing the pd.DataFrame objects of our datasets.
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

    modification_container = st.expander(
        label="Filter dataframe on:", expanded=True)
    with modification_container:
        to_filter_columns = st.multiselect(
            label="Filter dataframe on",
            options=df.columns[:-1],
            label_visibility="collapsed",
        )
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
                    user_date_input = tuple(
                        map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[tmp_col[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[
                        df[column].str.contains(
                            user_text_input, case=False, na=False)
                    ]
    return df


def content_cell_func() -> str:
    """Return a JavaScript template as a string to display a tooltip.

    The template will be configured in the display_bokeh function.
    The model used is the Underscore model : http://underscorejs.org/#template

    Returns
    -------
    str
        return the JS code as a string.
    """
    return """
            <span href="#" data-toggle="tooltip" title="<%= value %>"><%= value %></span>
            <span style='word-break: break-all;'></span>
            """


def link_cell_func() -> str:
    """Return a JavaScript template as a string to create a hyperlink.

    The template will be configured in the display_bokeh function.
    The model used is the Underscore model : http://underscorejs.org/#template

    Returns
    -------
    str
        return the JS code as a string.
    """
    return """
            <a href="<%= URL %>" target="_blank" data-toggle="tooltip" title="<%= URL %>">
                <%= value %>
            </a>
            """


def display_table(data_filtered: pd.DataFrame) -> None:
    st.write(len(data_filtered), "elements found")
    data_filtered = data_filtered.reset_index(drop=True)
    # th = header
    # td = cell
    itables.options.css = """
    .itables table td { 
        word-wrap: break-word;
        max-width: 50px;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .itables table td:nth-child(3), .itables table td:nth-child(6) {
        max-width: 280px;
    }
    .itables table th { word-wrap: break-word; max-width: 150px;}
    """
    st.components.v1.html(itables.to_html_datatable(
        data_filtered.iloc[:, :-1],
        classes="display nowrap cell-border",
        dom="tpr",
    ), height=450)
    itables.init_notebook_mode(all_interactive=True)
    # st.experimental_data_editor(
    #     data_filtered, num_rows="dynamic", disabled=False, key="data", on_change=write_hello)
    # st.write(st.session_state["data"])
    # st.write(data_filtered.to_html(index=False))
    # st.dataframe(data_filtered, height=600, use_container_width=True)


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
        contains search word, a bool for checkbox and a layout of
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


def display_export_button(data_filtered: pd.DataFrame) -> None:
    """Add a download button to export the selected data from the bokeh table.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        filtered dataframe.
    """
    date_now = f"{datetime.now():%Y-%m-%d_%H-%M-%S}"
    st.download_button(
        label="Export selection to tsv",
        data=data_filtered.to_csv(sep="\t", index=False).encode("utf-8"),
        file_name=f"mdverse_{date_now}.tsv",
        mime="text/tsv",
    )


def update_contents(data_filtered: pd.DataFrame, select_data: str) -> None:
    """Change the content display according to the cursor position.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        filtered dataframe.
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro","mdp"]
    """
    selected_row = st.session_state["cursor" + select_data]
    data = data_filtered.iloc[selected_row]
    contents = f"""
        **Dataset:**
        [{data["Dataset"]} {data["ID"]}]({data["URL"]})<br />
        **Creation date:** {data["Creation date"]}<br />
        **Author(s):** {data["Authors"]}<br />
        **Title:** *{data["Title"]}*<br />
        **Description:**<br /> {data["Description"]}
    """
    st.session_state["content"] = contents


def update_cursor(select_cursor: str, select_data: str, size_selected: int) -> None:
    """Change the value of the cursor by applying a specific value to it.

    Parameters
    ----------
    select_cursor: str
        Type of increment or decrement for the cursor.
        Values: ["backward", "previous", "next", "forward"]
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro", "mdp"]
    size_selected: int
        total number of selected rows.
    """
    if select_cursor == "backward":
        st.session_state["cursor" + select_data] = 0
    elif select_cursor == "previous":
        st.session_state["cursor" + select_data] -= 1
    elif select_cursor == "next":
        st.session_state["cursor" + select_data] += 1
    else:
        st.session_state["cursor" + select_data] = size_selected - 1


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


def display_buttons_details(
    columns: list, select_data: str, size_selected: int
) -> None:
    """Display the buttons in a structured way.

    Parameters
    ----------
    columns: list
        List used for the layout of the sidebar.
        Values: ["backward", "previous", "next", "forward"]
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro", "mdp"]
    size_selected: int
        total number of selected rows.
    """
    cursor = st.session_state["cursor" + select_data]
    disabled_previous = False if cursor - 1 >= 0 else True
    disabled_next = False if cursor + 1 < size_selected else True
    with columns[2]:
        st.button(
            "«",
            on_click=update_cursor,
            args=(
                "backward",
                select_data,
                size_selected,
            ),
            key="backward",
            disabled=disabled_previous,
            use_container_width=True,
        )
        with columns[3]:
            st.button(
                "⬅",
                on_click=update_cursor,
                args=(
                    "previous",
                    select_data,
                    size_selected,
                ),
                key="previous",
                disabled=disabled_previous,
                use_container_width=True,
            )
        with columns[4]:
            st.button(
                "➡",
                on_click=update_cursor,
                args=(
                    "next",
                    select_data,
                    size_selected,
                ),
                key="next",
                disabled=disabled_next,
                use_container_width=True,
            )
        with columns[5]:
            st.button(
                "»",
                on_click=update_cursor,
                args=(
                    "forward",
                    select_data,
                    size_selected,
                ),
                key="forward",
                disabled=disabled_next,
                use_container_width=True,
            )


def display_details(data_filtered: pd.DataFrame, select_data: str) -> None:
    """Show the details of the selected rows in the sidebar.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        filtered dataframe.
    select_data: str
        Type of data to search for.
        Values: ["datasets", "gro","mdp"]
    """
    if "cursor" + select_data not in st.session_state or "content" not in st.session_state:
        st.session_state["cursor" + select_data] = 0
        st.session_state["content"] = ""

    size_selected = len(data_filtered)
    if size_selected != 0:
        fix_cursor(size_selected, select_data)
        update_contents(data_filtered, select_data)
        cursor = st.session_state["cursor" + select_data]
        columns = st.sidebar.columns([4, 1, 2, 2, 2, 2])
        with columns[0]:
            st.write(cursor + 1, "/", size_selected, "selected")
        display_buttons_details(columns, select_data, size_selected)
        st.sidebar.markdown(
            st.session_state["content"], unsafe_allow_html=True)
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
