import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="USDA Rural Development Analytics",
    page_icon="🌾",
    layout="wide"
)

# --- 2. Data Loading & Cleaning ---
# We use st.cache_data so the app doesn't reload the CSV every time you click a button
@st.cache_data
def load_data(file_path):
    # Load skipping the first 6 metadata rows
    df = pd.read_csv(file_path, skiprows=6)
    
    # Fix the multi-header issue (Device Category + Metric Name)
    device_categories = df.columns
    metrics = df.iloc[0]
    new_columns = []
    
    for i in range(len(device_categories)):
        dev_cat = str(device_categories[i])
        metric = str(metrics[i])
        
        if dev_cat.startswith("Unnamed"):
            new_columns.append(metric)
        else:
            dev_cat_clean = dev_cat.split('.')[0]
            new_columns.append(f"{dev_cat_clean}_{metric}")
            
    df.columns = new_columns
    
    # Drop the metric name row and Grand Total row
    df = df.iloc[2:].reset_index(drop=True)
    
    # Convert necessary metrics to numeric
    numeric_cols = ['Totals_Active users', 'Totals_Sessions', 'Totals_Bounce rate']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# Load the dataset (Make sure the file name matches exactly)
try:
    df = load_data("Datasets-IC-purdue-01222026.csv")
except FileNotFoundError:
    st.error("Dataset not found. Please ensure 'Datasets-IC-purdue-01222026.csv' is in the same directory as this script.")
    st.stop()

# --- 3. Dashboard Header ---
st.title("🌾 USDA Rural Development: Executive Web Analytics")
st.markdown("""
This dashboard evaluates digital effectiveness and global reach across USDA Rural Development public-facing websites. 
Navigate between the tabs below to view insights regarding **Navigational Friction** and **International Interest**.
""")

# Create Tabs
tab1, tab2 = st.tabs(["RQ2: Friction Matrix", "RQ1: Global Reach"])

# --- 4. Tab 1: Friction Matrix (RQ2) ---
with tab1:
    st.header("Navigational Friction Analysis")
    st.markdown("Identifying critical program pathways with severe indicators of user friction (High Traffic + High Bounce Rate).")
    
    # Data Prep for Friction
    url_metrics = df.groupby(['Page title', 'Device category_Page path and screen class']).agg(
        Total_Sessions=('Totals_Sessions', 'sum'),
        Avg_Bounce_Rate=('Totals_Bounce rate', 'mean')
    ).reset_index()
    
    # Filter for high traffic pages (e.g., > 50,000 sessions) to remove noise
    high_traffic_urls = url_metrics[url_metrics['Total_Sessions'] > 50000].copy()
    
    # Convert Bounce Rate to Percentage for better tooltips
    high_traffic_urls['Avg_Bounce_Rate_%'] = high_traffic_urls['Avg_Bounce_Rate'] * 100
    
    # Plotly Scatter Plot
    fig_friction = px.scatter(
        high_traffic_urls,
        x='Total_Sessions',
        y='Avg_Bounce_Rate_%',
        hover_data=['Page title', 'Device category_Page path and screen class'],
        size='Total_Sessions',
        color='Avg_Bounce_Rate_%',
        color_continuous_scale='Reds',
        labels={
            'Total_Sessions': 'Total Sessions',
            'Avg_Bounce_Rate_%': 'Average Bounce Rate (%)'
        },
        title="Friction Matrix: Sessions vs. Bounce Rate (Pages > 50k Sessions)"
    )
    
    # Add a visual "Danger Zone" rectangle
    fig_friction.add_shape(
        type="rect",
        x0=200000, y0=30, x1=max(high_traffic_urls['Total_Sessions']) * 1.1, y1=max(high_traffic_urls['Avg_Bounce_Rate_%']) * 1.1,
        fillcolor="red", opacity=0.1, line_width=0, layer="below"
    )
    fig_friction.add_annotation(x=400000, y=36, text="High Traffic / High Friction", showarrow=False, font=dict(color="red", size=14))
    
    st.plotly_chart(fig_friction, use_container_width=True)
    
    # Show the raw data table below the chart
    st.subheader("Top Friction Pages (Data Table)")
    st.dataframe(
        high_traffic_urls.sort_values('Avg_Bounce_Rate_%', ascending=False).head(10)[['Page title', 'Total_Sessions', 'Avg_Bounce_Rate_%']]
        .style.format({'Total_Sessions': '{:,.0f}', 'Avg_Bounce_Rate_%': '{:.1f}%'})
    )


# --- 5. Tab 2: Global Reach (RQ1) ---
with tab2:
    st.header("Global Interest & Policy Reach")
    st.markdown("Analyzing non-U.S. traffic to understand global interest in U.S. rural development models.")
    
    # Data Prep for International
    us_territories = ['United States', 'Puerto Rico', 'Guam', 'U.S. Virgin Islands', 'Northern Mariana Islands', 'American Samoa', '(not set)']
    df_intl = df[~df['Country'].isin(us_territories)].copy()
    
    # 1. Top Countries Bar Chart
    top_countries = df_intl.groupby('Country')['Totals_Active users'].sum().reset_index()
    top_countries = top_countries.sort_values(by='Totals_Active users', ascending=False).head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 International Origins")
        fig_countries = px.bar(
            top_countries,
            x='Totals_Active users',
            y='Country',
            orientation='h',
            title="Active Users by Country (Excl. US & Territories)",
            color='Totals_Active users',
            color_continuous_scale='Teal'
        )
        fig_countries.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_countries, use_container_width=True)
        
    with col2:
        st.subheader("Most Accessed Content Internationally")
        top_pages_intl = df_intl.groupby('Page title')['Totals_Active users'].sum().reset_index()
        top_pages_intl = top_pages_intl.sort_values(by='Totals_Active users', ascending=False).head(10)
        
        st.dataframe(
            top_pages_intl.style.format({'Totals_Active users': '{:,.0f}'}),
            hide_index=True,
            use_container_width=True
        )

# --- 6. Executive Summary Footer ---
st.divider()
st.markdown("""
**Key Takeaways for Decision Makers:**
* **Chatbot/AI Candidate:** The LINC Training & Resource Library exhibits a severe bounce rate relative to its traffic volume, indicating users are struggling to self-serve.
* **Global Intent:** International traffic heavily indexes toward Single Family Housing programs, suggesting expatriate or immigration-driven real estate interest rather than policy research.
""")
