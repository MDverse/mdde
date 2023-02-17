"""Streamlit web app for exploring molecular dynamics (MD) data."""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
import website_management as wm
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models import DataTable, TableColumn, HTMLTemplateFormatter
from streamlit_bokeh_events import streamlit_bokeh_events


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


def display_AgGrid(data_filtered: pd.DataFrame) -> object:
    """Configure, create and display the AgGrid object.

    Parameters
    ----------
    data_filtered: pd.DataFrame
        a pandas dataframe filtred.

    Returns
    -------
    object
        returns a AgGrid object contains our data filtered and some options.
    """
    page_size = 20
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


def display_bokeh(data_filtered: pd.DataFrame) -> list:
    st.write(len(data_filtered), "elements found")
    if "data" not in st.session_state:
        st.session_state["changed"] = False
        st.session_state["data"] = data_filtered
    
    source = ColumnDataSource(data_filtered)
    
    if (not data_filtered.equals(st.session_state["data"])) :
        st.session_state["changed"] = True
        st.session_state["data"] = data_filtered
    else : 
        st.session_state["changed"] = False
    
    template = """
        <span href="#" data-toggle="tooltip" title="<%= value %>"><%= value %></span>
        <span style='word-break: break-all;'></span>
    """
    
    #wrap_fmt = HTMLTemplateFormatter(template="""<span style='word-break: break-all;'> <%=value %></span>""")
    wrap_fmt = HTMLTemplateFormatter(template=template)
    
    columns = []
    for col_name in data_filtered.columns:
        columns.append(TableColumn(field=col_name, title=col_name, formatter=wrap_fmt))
    columns.pop()
    
    source.selected.js_on_change(
        "indices",
        CustomJS(
                args=dict(source=source),
                code="""
                document.dispatchEvent(
                    new CustomEvent("INDEX_SELECT", {detail: source.selected.indices})
                )
                """
        )
    )
    
    viewport_height = max(550, len(data_filtered)//10)
    
    datatable = DataTable(
        source=source, 
        columns=columns,
        height=viewport_height,
        selectable="checkbox",
        index_position=None,
        sizing_mode="stretch_both",
        row_height=45
    )
    
    bokeh_table = streamlit_bokeh_events(
        bokeh_plot=datatable,
        events="INDEX_SELECT",
        key="bokeh_table",
        refresh_on_update=st.session_state["changed"],
        debounce_time=0,
        override_height=viewport_height+5,
    )
    
    return bokeh_table


def user_interaction() -> None:
    """Control the streamlit application.

    Allows interaction between the user and our informational data from MD
    data.
    """
    st.set_page_config(page_title="MDverse", layout="wide")
    wm.load_css()
    select_data = "datasets"
    data = wm.load_data()[select_data]
    search, is_show, col_filter, col_download = wm.display_search_bar(select_data)
    results = search_processing(data=data, search=search, is_show=is_show)
    if not results.empty:
        with col_filter:
            add_filter = st.checkbox("Add filter")
        data_filtered = wm.filter_dataframe(results, add_filter)
        bokeh_table = display_bokeh(data_filtered)
        if bokeh_table:
            sel_row = bokeh_table.get("INDEX_SELECT")
            with col_download:
                wm.display_export_button(sel_row, data_filtered)
            wm.display_details(sel_row, data_filtered, select_data)
    elif search != "":
        st.write("No result found.")


if __name__ == "__main__":
    user_interaction()
