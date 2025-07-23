import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from koboextractor import KoboExtractor
import ast
from datetime import datetime

# Set up KoboToolbox connection
my_token = "de1a94cd21dd10771c7a8809a499edd209c45295"
form_id = "aksx8BXj3Zq9N6eJBpczG4"
kobo_base_url = "https://kf.kobotoolbox.org//api/v2"

# Get data from KoboToolbox
Kobo = KoboExtractor(my_token, kobo_base_url)
data = Kobo.get_data(form_id)
df=pd.json_normalize(data['results'])

# Set page config
st.set_page_config(layout="wide", page_title="Community Emergency Response System")

# Function to split the geolocation field
def split_geolocation(_geolocation):
    if isinstance(_geolocation, list) and len(_geolocation) == 2:
        try:
            lat, long = float(_geolocation[0]), float(_geolocation[1])
            return lat, long
        except ValueError:
            return None, None  # Handle potential conversion errors
    return None, None  # Handle missing or incorrect values

# Apply the function to the dataframe
df[['latitude', 'longitude']] = df['_geolocation'].apply(lambda x: pd.Series(split_geolocation(x)))

# Drop the original geolocation column as it is not needed
df = df.drop(columns=['_geolocation'])

# Title
st.title("Community Emergency Response System")
st.markdown("---")

# Create metrics for top summary
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Reports", len(df))
with col2:
    st.metric("Total Victims", pd.to_numeric(df['Number_of_Victims'], errors='coerce').fillna(0).sum())
with col3:
    st.metric("Total Deaths", pd.to_numeric(df['Number_of_Deaths'], errors='coerce').fillna(0).sum())
with col4:
    st.metric("Unique Locations", df['Location_of_Resource'].nunique())

# Create two columns for the main charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Emergency Type Distribution")
    emergency_counts = df['Emergency_Type'].fillna('Not Specified').value_counts().reset_index()
    emergency_counts.columns = ['Emergency Type', 'Count']
    fig1 = px.pie(emergency_counts, 
                  values='Count',
                  names='Emergency Type',
                  title='Distribution of Emergency Types')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Reporter Status Distribution")
    status_counts = df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status Type', 'Count']
    fig2 = px.bar(status_counts, 
                  x='Status Type',
                  y='Count',
                  title='Distribution of Reporter Status')
    st.plotly_chart(fig2, use_container_width=True)

# Map of Incidents
st.subheader("Map of Incidents and Resources")

# Calculate map center
center_lat = df['latitude'].mean() if not df['latitude'].isna().all() else 7.719421
center_lon = df['longitude'].mean() if not df['longitude'].isna().all() else 8.580176

m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

from folium.plugins import MarkerCluster

# Create a marker cluster to avoid overlapping markers
marker_cluster = MarkerCluster().add_to(m)

# Add markers to map
for idx, row in df.iterrows():
    if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
        popup_text = f"Type: {row['Emergency_Type'] if pd.notnull(row['Emergency_Type']) else row['Resource_Type']}<br>"
        popup_text += f"Area: {row['Location_of_Resource']}"
        
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=popup_text,
            icon=folium.Icon(color='red' if pd.notnull(row['Emergency_Type']) else 'blue')
        ).add_to(m)

st_folium(m, width=2000, height=500)

# Display the map
st_folium(m, width=2000, height=500)
# Victims by Emergency Type
st.subheader("Number of Victims by Emergency Type")
victims_data = df[df['Emergency_Type'].notna() & df['Number_of_Victims'].notna()]
fig3 = px.bar(victims_data,
              x='Emergency_Type',
              y='Number_of_Victims',
              title='Number of Victims per Emergency Type')
st.plotly_chart(fig3, use_container_width=True)

# Detailed Data Analysis
st.subheader("Detailed Data Analysis")

# Filter options
emergency_types = ['All'] + list(df['Emergency_Type'].dropna().unique())
selected_emergency = st.selectbox("Select Emergency Type", emergency_types)

# Filter data based on selection
filtered_df = df[df['Emergency_Type'] == selected_emergency] if selected_emergency != 'All' else df

# Show filtered data
st.dataframe(filtered_df)

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="Download Data",
    data=csv,
    file_name="emergency_data.csv",
    mime="text/csv"
)

# Date range filter
date_col1, date_col2 = st.columns(2)
with date_col1:
    start_date = st.date_input("Start Date", pd.to_datetime(df['Date']).min())
with date_col2:
    end_date = st.date_input("End Date", pd.to_datetime(df['Date']).max())