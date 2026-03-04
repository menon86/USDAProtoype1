import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="USDA Rural Development Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Data Loading & Cleaning ---
@st.cache_data
def load_data(file_path):
    # Pandas will automatically unzip and read the file
    df = pd.read_csv(file_path, skiprows=6, compression='zip')
    
    # Fix the multi-header issue
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
    df = df.iloc[2:].reset_index(drop=True)
    
    # Convert numeric columns safely
    numeric_cols = ['Totals_Active users', 'Totals_Sessions', 'Totals_Bounce rate', 'Totals_Exits']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

try:
    df = load_data("dataset.csv.zip")
except FileNotFoundError:
    st.error("Dataset not found. Please ensure 'dataset.csv.zip' is in the same directory.")
    st.stop()

# --- 3. Sidebar Configuration ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/United_States_Department_of_Agriculture_logo.svg/1200px-United_States_Department_of_Agriculture_logo.svg.png", width=150)
    st.title("Project Scope")
    st.markdown("""
    **Client:** USDA Rural Development  
    **Objective:** Evaluate digital effectiveness, user friction, and global reach.  
    **Deliverable:** Final Executive Web Analytics Dashboard  
    """)
    st.divider()
    st.markdown("**Team Analytics Parameters:**")
    traffic_threshold = st.slider("Min. Sessions Filter (Friction Matrix)", min_value=10000, max_value=100000, value=50000, step=10000)

# --- 4. Main Dashboard Header ---
st.title("Digital Effectiveness & User Journey Analysis")
st.markdown("A data-driven evaluation of the USDA Rural Development web ecosystem to identify underserved users and self-service friction points.")

# Create Tabs
tab1, tab2, tab3 = st.tabs(["⚠️ Navigational Friction (RQ2)", "🌍 Global Reach (RQ1)", "💡 Strategic Recommendations"])

# --- 5. Tab 1: Friction Matrix (RQ2) ---
with tab1:
    st.subheader("Identifying Friction Points in High-Value Pathways")
    
    # Data Prep
    url_metrics = df.groupby(['Page title', 'Device category_Page path and screen class']).agg(
        Total_Sessions=('Totals_Sessions', 'sum'),
        Avg_Bounce_Rate=('Totals_Bounce rate', 'mean')
    ).reset_index()
    
    high_traffic_urls = url_metrics[url_metrics['Total_Sessions'] >= traffic_threshold].copy()
    high_traffic_urls['Avg_Bounce_Rate_%'] = high_traffic_urls['Avg_Bounce_Rate'] * 100
    
    # Top Level Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Pages Analyzed (Above Threshold)", f"{len(high_traffic_urls)}")
    col2.metric("Highest System Bounce Rate", f"{high_traffic_urls['Avg_Bounce_Rate_%'].max():.1f}%")
    col3.metric("Total Sessions in Danger Zone", f"{high_traffic_urls[high_traffic_urls['Avg_Bounce_Rate_%'] > 30]['Total_Sessions'].sum():,.0f}")
    
    st.divider()

    # Plotly Scatter Plot
    fig_friction = px.scatter(
        high_traffic_urls,
        x='Total_Sessions',
        y='Avg_Bounce_Rate_%',
        hover_data=['Page title', 'Device category_Page path and screen class'],
        size='Total_Sessions',
        color='Avg_Bounce_Rate_%',
        color_continuous_scale='Reds',
        template='plotly_white',
        labels={'Total_Sessions': 'Total Sessions', 'Avg_Bounce_Rate_%': 'Average Bounce Rate (%)'}
    )
    
    # Danger Zone Annotation
    fig_friction.add_shape(
        type="rect",
        x0=max(high_traffic_urls['Total_Sessions']) * 0.2, y0=30, 
        x1=max(high_traffic_urls['Total_Sessions']) * 1.1, y1=max(high_traffic_urls['Avg_Bounce_Rate_%']) * 1.05,
        fillcolor="red", opacity=0.1, line_width=0, layer="below"
    )
    fig_friction.add_annotation(
        x=max(high_traffic_urls['Total_Sessions']) * 0.5, y=35, 
        text="High Traffic / High Friction (Danger Zone)", showarrow=False, font=dict(color="red", size=14)
    )
    
    st.plotly_chart(fig_friction, use_container_width=True)


# --- 6. Tab 2: Global Reach (RQ1) ---
with tab2:
    st.subheader("International Interest in U.S. Rural Development Models")
    
    # Data Prep
    us_territories = ['United States', 'Puerto Rico', 'Guam', 'U.S. Virgin Islands', 'Northern Mariana Islands', 'American Samoa', '(not set)']
    df_intl = df[~df['Country'].isin(us_territories)].copy()
    
    total_intl_users = df_intl['Totals_Active users'].sum()
    top_country = df_intl.groupby('Country')['Totals_Active users'].sum().idxmax()
    
    col1, col2 = st.columns(2)
    col1.metric("Total True International Users", f"{total_intl_users:,.0f}")
    col2.metric("Top International Origin", top_country)
    
    st.divider()
    
    col3, col4 = st.columns(2)
    with col3:
        top_countries = df_intl.groupby('Country')['Totals_Active users'].sum().reset_index().sort_values('Totals_Active users', ascending=False).head(10)
        fig_countries = px.bar(
            top_countries, x='Totals_Active users', y='Country', orientation='h',
            title="Active Users by Country (Excl. US & Territories)",
            color='Totals_Active users', color_continuous_scale='Teal', template='plotly_white'
        )
        fig_countries.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_countries, use_container_width=True)
        
    with col4:
        st.markdown("**Most Accessed Content Internationally**")
        top_pages_intl = df_intl.groupby(['Page title', 'Device category_Page path and screen class'])['Totals_Active users'].sum().reset_index()
        top_pages_intl = top_pages_intl.sort_values(by='Totals_Active users', ascending=False).head(8)
        st.dataframe(top_pages_intl[['Page title', 'Totals_Active users']].style.format({'Totals_Active users': '{:,.0f}'}), hide_index=True, use_container_width=True)


# --- 7. Tab 3: Recommendations ---
with tab3:
    st.subheader("Data-Driven Recommendations & Next Steps")
    
    st.info("**Finding 1: The 'LINC Training Library' is failing its users.** \nData shows this critical portal has a bounce rate exceeding 33% despite high traffic volume. Users are arriving but immediately abandoning the self-service flow.")
    st.success("**Recommendation 1: Deploy an AI-Enabled Guided Navigation Chatbot.** \nInstead of a static directory of PDFs, implement a conversational interface on the LINC hub that asks lenders what specific form or policy they are looking for and routes them directly to it.")
    
    st.info("**Finding 2: International traffic is driven by housing, not policy.** \nOur geographic segmentation reveals that users in Asia and Canada are predominantly accessing the 'Single Family Housing' portals rather than agricultural business grants.")
    st.success("**Recommendation 2: Content Localization.** \nWe recommend translating the top 3 Housing Program landing pages into Tagalog, Hindi, and Indonesian, or providing clear digital pathways for prospective immigrants to understand rural housing eligibility.")
