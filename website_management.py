"""This python file contains all the functions to help manage the site."""

import streamlit as st
import pandas as pd
from st_keyup import st_keyup
from st_aggrid import GridOptionsBuilder, JsCode
from datetime import datetime
import streamlit_toggle as tog


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
def load_data() -> tuple:
    """Retrieve our data and loads it into the pd.DataFrame object.

    Returns
    -------
    tuple
        returns an tuple contains pd.DataFrame object containing our datasets.
    """
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
    return datasets, gro_data, mdp_data


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


def config_options(data_filtered: pd.DataFrame, page_size: int) -> list:
    """Configure the Aggrid object with dedicated functions for our data.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        contains our data filtered by a search.
    page_size: int


    Returns
    -------
    list
        return a list of dictionary containing all the information of the
        configuration for our Aggrid object.
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


def display_search_bar(select_data: int) -> tuple:
    """Configure the display and the parameters of the website.

    Parameters
    ----------
    select_data: int
        contains a number (0, 1 or 2) that will allow the selection of data.

    Returns
    -------
    tuple
        contains search word, a bool for checkbox and a list for the layout of
        the site.
    """
    st.title("MDverse")
    placeholder = "Enter search term (for instance: POPC, Gromacs, CHARMM36)"
    if select_data == 0:
        label_search = "Keywords search"
    elif select_data == 1:
        label_search = "GRO files search"
    else:
        label_search = "MDP files search"
    col_keyup, col_show, _ = st.columns([3, 1, 1])
    with col_keyup:
        search = st_keyup(label_search, placeholder=placeholder)
    with col_show:
        is_show = st.checkbox("Show all", key=10 + select_data)
    columns = st.columns([3 if i == 9 else 2 if i == 0 else 1 for i in range(10)])
    return search, is_show, columns


def display_export_button(sel_row: list) -> None:
    """Add a download button to export the selected data from the AgGrid table.

    Parameters
    ----------
    sel_row: list
        contains the selected rows of our Aggrid array as a list of dictionary.
    """
    if sel_row:
        new_data = convert_data(sel_row)
        today_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        st.download_button(
            label="Export selection to tsv",
            data=new_data.to_csv(sep="\t", index=False).encode("utf-8"),
            file_name=f"mdverse_{today_date}.tsv",
            mime="text/tsv",
        )


def update_contents(sel_row: list) -> None:
    """Change the content display according to the cursor position.

    Parameters
    ----------
    sel_row: list
        contains the selected rows of our Aggrid array as a list of dictionary.
    """
    selected_row = sel_row[st.session_state["cursor"]]
    nb_files = ""
    if "# Files" in selected_row:
        nb_files = "\# Files : " + str(selected_row["# Files"])
    contents = f"""
        **{selected_row["Dataset"]}**:
        [{selected_row["ID"]}]({selected_row["URL"]})\n
        {selected_row["Creation date"]}\n
        ### **{selected_row["Title"]}**\n
        ##### {selected_row["Authors"]}\n
        {selected_row["Description"]}\n
        {nb_files}
    """
    st.session_state["contents"] = contents


def update_cursor(is_previous: bool) -> None:
    """Change the value of the cursor by incrementing or decrementing.

    Parameters
    ----------
    is_previous: bool
        determine if it should increment the cursor or decrement.
    """
    if is_previous:
        st.session_state["cursor"] -= 1
    else:
        st.session_state["cursor"] += 1


def fix_cursor(size_selected: int) -> None:
    """Correct the cursor position according to the number of selected rows.

    Parameters
    ----------
    size_selected: int
        total number of selected rows.
    """
    while st.session_state["cursor"] >= size_selected:
        st.session_state["cursor"] -= 1


def display_details(sel_row: list) -> None:
    """Show the details of the selected rows in the sidebar.

    Parameters
    ----------
    sel_row: list
        contains the selected rows of our Aggrid array as a list of dictionary.
    """
    if "cursor" not in st.session_state:
        st.session_state["cursor"] = 0

    size_selected = len(sel_row)
    if size_selected != 0:
        fix_cursor(size_selected)
        update_contents(sel_row)
        cursor = st.session_state["cursor"]

        col_select, col_previous, col_next = st.sidebar.columns([2, 1, 1])
        disabled_previous, disabled_next = False, False
        with col_select:
            st.write(cursor + 1, "/", size_selected, "selected")
        with col_previous:
            disabled_previous = False if cursor - 1 >= 0 else True
            st.button(
                "⬅",
                on_click=update_cursor,
                args=(True,),
                key="previous",
                disabled=disabled_previous,
                use_container_width=True,
            )
        with col_next:
            disabled_next = False if cursor + 1 < size_selected else True
            st.button(
                "➡",
                on_click=update_cursor,
                args=(False,),
                key="next",
                disabled=disabled_next,
                use_container_width=True,
            )
        st.sidebar.markdown(st.session_state["contents"], unsafe_allow_html=True)
    else:
        st.session_state["cursor"] = 0


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
                    position : absolute;
                    top: 30px;
                }

                .stDownloadButton > button {
                    width: 100%;
                }

                div.block-container.css-k1ih3n.egzxvld4 {
                    padding-top : 20px;
                }
            </style>
    """,
        unsafe_allow_html=True,
    )
