"""
Streamlit app for visualising the South East London population projections using Plotly.

This app reads the Excel workbook `population_projection_se_london_icb.xlsx`
(which contains one worksheet per borough and for the combined South East London ICB)
and allows the user to interactively explore population counts and percent change
across different age groups.

Usage:

    streamlit run streamlit_app.py

Ensure that `population_projection_se_london_icb.xlsx` is in the same directory
as this script when running locally. On the Streamlit sidebar, you can choose
which area to display and whether to view population counts or percent change.

Requirements:

    streamlit >= 1.20
    pandas
    plotly

"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Set the page configuration
st.set_page_config(page_title="South East London Population Projections", layout="centered")

st.title("South East London Population Projections (2025‑2035)")

@st.cache_data
def load_data(excel_file: str):
    """Load data from the Excel workbook into a dictionary of DataFrames.

    Parameters
    ----------
    excel_file : str
        Path to the Excel workbook.

    Returns
    -------
    dict
        A dictionary where keys are sheet names and values are DataFrames.
    """
    xls = pd.ExcelFile(excel_file)
    data = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name)
        # Only load sheets that contain the expected 'Year' column
        if not df.empty and 'Year' in df.columns:
            data[sheet_name] = df
    return data

# Determine the path to the default Excel file
DEFAULT_EXCEL_FILE = Path(__file__).resolve().parent / "population_projection_se_london_icb.xlsx"

# Allow user to specify an alternative Excel file path
excel_file_path = st.sidebar.text_input(
    "Excel file path",
    value=str(DEFAULT_EXCEL_FILE),
    help="Path to the Excel workbook. Must contain the same structure as the default file."
)

# Load data
try:
    data_dict = load_data(excel_file_path)
except Exception as e:
    st.error(f"Failed to load data from {excel_file_path}: {e}")
    st.stop()

if not data_dict:
    st.error("No valid worksheets were found in the provided Excel file.")
    st.stop()

# Sidebar: select area
area_names = list(data_dict.keys())
selected_area = st.sidebar.selectbox("Select area", area_names)
selected_df = data_dict[selected_area]

# Sidebar: select view type
view_type = st.sidebar.radio(
    "View",
    options=["Percent change", "Counts"],
    help="Select whether to view percentage change relative to 2025 or raw population counts."
)

# Determine which columns to plot based on view_type
if view_type == "Percent change":
    plot_columns = [col for col in selected_df.columns if col.endswith("_pct")]
    y_label = "Percent change (%)"
    title_suffix = " – Percent Change"
    zero_line = True
else:
    plot_columns = [col for col in ['0-24', '25-64', '65-79', '80+', 'All ages'] if col in selected_df.columns]
    y_label = "Population (persons)"
    title_suffix = " – Population Counts"
    zero_line = False

# Prepare long-form dataframe for Plotly when multiple columns are selected
plot_df = selected_df[['Year'] + plot_columns]

# Define a custom colour scheme with distinct colours for each series.
#
# To ensure each line is clearly distinguishable, avoid using similar hues.  The
# palette below assigns orange for under‑25s, blue for the working age group,
# green for the 65‑79 cohort, red for the 80+ cohort, and a dark neutral
# colour for the aggregated “All ages” series.  Percent‑change variants use
# the same colours as their corresponding count series.
color_map = {
    '0-24': '#F5B041',       # orange (0‑24)
    '25-64': '#5DADE2',      # blue (25‑64)
    '65-79': '#58D68D',      # green (65‑79)
    '80+': '#E74C3C',        # red (80+)
    'All ages': '#34495E',   # dark slate grey (All ages)
    '0-24_pct': '#F5B041',
    '25-64_pct': '#5DADE2',
    '65-79_pct': '#58D68D',
    '80+_pct': '#E74C3C',
    'All ages_pct': '#34495E'
}

# Create Plotly line chart with custom colours and thicker lines
fig = px.line(
    plot_df,
    x='Year',
    y=plot_columns,
    labels={'value': y_label, 'variable': 'Age group'},
    title=f"{selected_area}{title_suffix}",
    color_discrete_map=color_map
)

# Make lines thicker
fig.update_traces(line=dict(width=3))

# Ensure the x-axis includes all years up to the maximum (2035)
fig.update_xaxes(range=[plot_df['Year'].min(), plot_df['Year'].max()])

# Add baseline line at zero for percent change view
if zero_line:
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

# Display the plot using Streamlit
st.plotly_chart(fig, use_container_width=True)

st.write(
    """
    **Instructions:**
    - Use the sidebar to select a borough or the combined South East London ICB.
    - Choose whether to display raw counts or percent change relative to 2025.
    - The data is sourced from the GLA 2022‑based population projections for the housing‑led central fertility variant.
    - Lines have been thickened and colours are now clearly distinct for each series.
    """
)
