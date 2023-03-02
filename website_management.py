"""Helper functions to manage the Streamlit application."""

import streamlit as st
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from datetime import datetime
import itables
from itables import JavascriptFunction


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

    modification_container = st.expander(label="Filter dataframe on:", expanded=True)
    with modification_container:
        to_filter_columns = st.multiselect(
            label="Filter dataframe on",
            options=df.columns[:-1].drop(["URL", "ID"], errors="ignore"),
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


def link_content_func() -> str:
    """Return a JavaScript template as a string to display a tooltip and href.

    The template create a hyperlink to a specifi column and display a tooltip
    for each cells of the table. The template will be configured in the
    display_table function.

    Returns
    -------
    str
        return the JS code as a string.
    """
    return """
            function (td, cellData, rowData, row, col) {
                if (col == 3) {
                    td.innerHTML = "<a href="+rowData[1]+" target='_blank'>"+cellData+"</a>";
                }
                td.setAttribute('title', cellData);
            }
            """


@st.cache_data
def display_table(data_filtered: pd.DataFrame) -> object:
    """Display a table of the query data.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        filtered dataframe.

    Returns
    -------
    str
        return a HTML object contains all information about the datatable.
    """
    st.write(f"{len(data_filtered)} elements found")
    table = itables.to_html_datatable(
        data_filtered,
        classes="display nowrap cell-border",
        dom="ltpr",
        lengthMenu=[20, 50, 100, 250],
        style="width:100%",
        columnDefs=[
            {
                "targets": "_all",
                "createdCell": JavascriptFunction(link_content_func()),
            }
        ],
        scrollX=True,
        scrollY=650,
        maxBytes=0,
    )
    return table


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
    st.title("MDverse data explorer")
    placeholder = (
        "Enter search term. For instance: Covid, POPC, Gromacs, CHARMM36, 1402417"
    )
    label_search = ""
    if select_data == "datasets":
        label_search = "Datasets quick search"
    elif select_data == "gro":
        label_search = ".gro files quick search"
    elif select_data == "mdp":
        label_search = ".mdp files quick search"
    col_keyup, col_filter, col_download, _ = st.columns([4, 1.2, 1, 1])
    with col_keyup:
        # search = st_keyup(label_search, placeholder=placeholder)
        search = st.text_input(label_search, placeholder=placeholder)
    return search, col_filter, col_download


def display_export_button(data_filtered: pd.DataFrame) -> None:
    """Add a download button to export the selected data from the bokeh table.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        filtered dataframe.
    """
    date_now = f"{datetime.now():%Y-%m-%d_%H-%M-%S}"
    data_filtered = data_filtered.drop("index", axis=1)
    temp_cols = list(data_filtered.columns)
    new_cols = temp_cols[1:] + temp_cols[0:1]
    data_filtered = data_filtered[new_cols]
    st.download_button(
        label="📦 Export to tsv",
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


def display_slider(select_data: str, size_selected: int) -> None:
    cursor = st.sidebar.slider("Selected row:", 1, size_selected, 1)
    st.session_state["cursor" + select_data] = cursor - 1


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
    if (
        "cursor" + select_data not in st.session_state
        or "content" not in st.session_state
    ):
        st.session_state["cursor" + select_data] = 0
        st.session_state["content"] = ""

    size_selected = len(data_filtered)
    if size_selected:
        if size_selected > 1:
            display_slider(select_data, size_selected)
        update_contents(data_filtered, select_data)
        st.sidebar.markdown(st.session_state["content"], unsafe_allow_html=True)
    else:
        st.session_state["cursor" + select_data] = 0


def load_css() -> None:
    """Load a css style."""
    st.markdown(
        """
        <style>
            /* Centre the add filter checkbox and the download button */
            .stCheckbox {
                position: absolute;
                top: 40px;
            }

            .stDownloadButton {
                position: absolute;
                top: 33px;
            }
            
            /* Responsive display */
            @media (max-width:640px) { 
                .stCheckbox {
                    position: static;;    
                }
                
                .stDownloadButton {
                    position: static;
                }
            }
            
            /* Maximize thedusplay of the data explorer search */
            .block-container:first-of-type {
                padding-top: 20px;
                padding-left: 20px;
                padding-right: 20px;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )
    itables.options.css = """
            /* Change the display of the table */
            .itables {
                font-family: 'sans-serif';
                font-size: 0.8rem;
                background: white;
                padding: 10px;
            }
            
            /* Specific column titles */
            .itables table th { 
                word-wrap: break-word;
                font-size: 11px;
            }

            /* Cells specific */
            .itables table td { 
                word-wrap: break-word;
                min-width: 50px;
                max-width: 50px;
                overflow: hidden;
                text-overflow: ellipsis;
                font-size: 12px;
            }

            /* Set the width of the id column */
            .itables table td:nth-child(4) {
                min-width: 80px;
                max-width: 80px;
            }

            /* Set the width of the title and description columns */
            .itables table td:nth-child(5), .itables table td:nth-child(8) {
                max-width: 300px;
            }

            /* Hide the URL column */
            .itables table th:nth-child(2), .itables table td:nth-child(2){
                display:none;
            }

            /* Apply colour to links */
            a:link, a:visited {
                color: rgb(51, 125, 255);
            }
    """
