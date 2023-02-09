"""Our program is a streamlit app for exploring molecular dynamics (MD) data.

There were extracted from unmoderated and generalized data such as Zenodo, etc.
We propose an website allowing to facilitate the user's search in these MD
data.
"""

import streamlit as st

st.set_page_config(page_title="MDverse", page_icon="🔎", layout="wide")

st.write("# Welcome to MDverse! 🔎")

st.sidebar.success("Select the type of MD search.")

st.markdown(
    """
    Streamlit is an open-source app framework built specifically for
    Machine Learning and Data Science projects.
    **👈 Select a demo from the sidebar** to see some examples
    of what Streamlit can do!
    ### Want to learn more?
    - Check out [streamlit.io](https://streamlit.io)
    - Jump into our [documentation](https://docs.streamlit.io)
    - Ask a question in our [community
        forums](https://discuss.streamlit.io)
    ### See more complex demos
    - Use a neural net to [analyze the Udacity Self-driving Car Image
        Dataset](https://github.com/streamlit/demo-self-driving)
    - Explore a [New York City rideshare dataset]
        (https://github.com/streamlit/demo-uber-nyc-pickups)
"""
)
