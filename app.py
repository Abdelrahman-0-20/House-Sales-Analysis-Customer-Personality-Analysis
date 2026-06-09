import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration with custom theme
st.set_page_config(
    layout="wide",
    page_title="Advanced Analytics Dashboard",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Custom CSS for elegant styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .filter-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# CACHED DATA LOADERS WITH ERROR HANDLING
# ------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_customer():
    """Load and preprocess customer personality data"""
    try:
        df = pd.read_csv("marketing_campaign.csv", sep='\t')
        
        # Calculate total spending
        spending_cols = ['MntWines', 'MntFruits', 'MntMeatProducts', 
                        'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']
        df['TotalSpent'] = df[spending_cols].sum(axis=1)
        
        # Calculate age if DOB exists
        if 'Year_Birth' in df.columns:
            df['Age'] = datetime.now().year - df['Year_Birth']
        
        # Calculate customer lifetime value score
        df['CLV_Score'] = df['TotalSpent'] * (df['Recency'].max() - df['Recency']) / df['Recency'].max()
        
        # Create customer segments
        df['Spending_Segment'] = pd.qcut(df['TotalSpent'], q=4, labels=['Low', 'Medium', 'High', 'Premium'])
        
        # Calculate days since last purchase
        df['Last_Purchase_Days'] = df['Recency']
        
        # Calculate spending ratio (spending vs income)
        df['Spending_Ratio'] = (df['TotalSpent'] / df['Income'] * 100).clip(0, 100)
        
        return df
    except Exception as e:
        st.error(f"Error loading customer data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_houses():
    """Load and preprocess house sales data"""
    try:
        df = pd.read_csv("kc_house_data.csv")
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate additional features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        df['age'] = datetime.now().year - df['yr_built']
        df['renovated'] = df['yr_renovated'] > 0
        
        # Price per sqft
        df['price_per_sqft'] = df['price'] / df['sqft_living']
        
        # Price category
        df['price_category'] = pd.qcut(df['price'], q=5, labels=['Budget', 'Economic', 'Mid-Range', 'Premium', 'Luxury'])
        
        # Calculate total rooms
        df['total_rooms'] = df['bedrooms'] + df['bathrooms']
        
        return df
    except Exception as e:
        st.error(f"Error loading house data: {str(e)}")
        return pd.DataFrame()

# ------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------

def create_metric_card(title, value, delta=None, prefix="", suffix=""):
    """Create a styled metric card"""
    if delta:
        delta_html = f'<div style="font-size: 0.9rem; color: {"#4CAF50" if delta > 0 else "#f44336"}">{delta:+.1f}%</div>'
    else:
        delta_html = ""
    
    return f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; opacity: 0.9;">{title}</div>
            <div style="font-size: 1.8rem; font-weight: 700;">{prefix}{value:,.0f}{suffix}</div>
            {delta_html}
        </div>
    """

def create_download_button(df, filename, button_text="📥 Download Data"):
    """Create a download button for dataframe"""
    csv = df.to_csv(index=False)
    return st.download_button(
        label=button_text,
        data=csv,
        file_name=filename,
        mime='text/csv'
    )

# ------------------------------------------------------------
# CUSTOMER PERSONALITY DASHBOARD - ENHANCED
# ------------------------------------------------------------
def customer_dashboard():
    st.markdown('<h1 class="main-header">🛍️ Customer Analytics Hub</h1>', unsafe_allow_html=True)
    
    df = load_customer()
    if df.empty:
        return
    
    # Enhanced Filters
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            education = st.multiselect(
                "🎓 Education Level",
                df['Education'].unique(),
                default=df['Education'].unique()
            )
        
        with col2:
            marital = st.multiselect(
                "💑 Marital Status",
                df['Marital_Status'].unique(),
                default=df['Marital_Status'].unique()
            )
        
        with col3:
            income_range = st.slider(
                "💰 Income Range ($)",
                int(df['Income'].min()),
                int(df['Income'].max()),
                (30000, 100000),
                step=10000
            )
        
        with col4:
            spending_segment = st.multiselect(
                "📊 Spending Segment",
                df['Spending_Segment'].unique(),
                default=df['Spending_Segment'].unique()
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            age_range = st.slider(
                "👤 Age Range",
                int(df['Age'].min()) if 'Age' in df.columns else 18,
                int(df['Age'].max()) if 'Age' in df.columns else 100,
                (25, 65)
            )
        
        with col2:
            if 'Kidhome' in df.columns:
                kids = st.multiselect(
                    "👶 Kids at Home",
                    df['Kidhome'].unique(),
                    default=df['Kidhome'].unique()
                )
            else:
                kids = [0, 1, 2]
        
        with col3:
            if st.button("🔄 Reset Filters", key="reset_customer"):
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered = df[
        (df['Education'].isin(education)) &
        (df['Marital_Status'].isin(marital)) &
        (df['Income'].between(income_range[0], income_range[1])) &
        (df['Spending_Segment'].isin(spending_segment))
    ]
    
    if 'Age' in filtered.columns:
        filtered = filtered[filtered['Age'].between(age_range[0], age_range[1])]
    
    if 'Kidhome' in filtered.columns:
        filtered = filtered[filtered['Kidhome'].isin(kids)]
    
    # KPI Cards
    st.markdown("### 📈 Customer Insights")
    metric_cols = st.columns(5)
    
    with metric_cols[0]:
        avg_income = filtered['Income'].mean()
        st.markdown(create_metric_card("Average Income", avg_income, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[1]:
        avg_spending = filtered['TotalSpent'].mean()
        st.markdown(create_metric_card("Avg Total Spending", avg_spending, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[2]:
        avg_recency = filtered['Recency'].mean()
        st.markdown(create_metric_card("Avg Days Since Purchase", avg_recency, suffix=" days"), unsafe_allow_html=True)
    
    with metric_cols[3]:
        conversion_rate = (filtered['Response'] == 1).mean() * 100 if 'Response' in filtered.columns else 0
        st.markdown(create_metric_card("Campaign Response Rate", conversion_rate, suffix="%"), unsafe_allow_html=True)
    
    with metric_cols[4]:
        total_customers = len(filtered)
        st.markdown(create_metric_card("Active Customers", total_customers), unsafe_allow_html=True)
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Income vs Spending with trend line
        fig = px.scatter(
            filtered,
            x='Income',
            y='TotalSpent',
            color='Education',
            size='Recency',
            hover_data=['Age', 'Marital_Status', 'Spending_Segment'],
            title="Income vs Total Spending Analysis",
            trendline="ols",
            template="plotly_white",
            opacity=0.7
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Spending breakdown by product category
        spending_cols = ['MntWines', 'MntFruits', 'MntMeatProducts', 
                        'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']
        spending_avg = filtered[spending_cols].mean().sort_values(ascending=True)
        
        fig = px.bar(
            x=spending_avg.values,
            y=spending_avg.index,
            orientation='h',
            title="Average Spending by Product Category",
            labels={'x': 'Average Amount ($)', 'y': 'Product Category'},
            color=spending_avg.values,
            color_continuous_scale='Blues',
            template="plotly_white",
            text=spending_avg.values.round(0)
        )
        fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional Analytics Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Customer lifetime value by segment
        clv_by_segment = filtered.groupby('Spending_Segment').agg({
            'CLV_Score': ['mean', 'std'],
            'ID': 'count'
        }).round(2)
        clv_by_segment.columns = ['Avg_CLV', 'Std_CLV', 'Count']
        clv_by_segment = clv_by_segment.reset_index()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(name="Customer Count", x=clv_by_segment['Spending_Segment'], 
                   y=clv_by_segment['Count'], marker_color='lightblue',
                   text=clv_by_segment['Count'], textposition='auto'),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(name="Avg CLV Score", x=clv_by_segment['Spending_Segment'], 
                      y=clv_by_segment['Avg_CLV'], marker_color='darkblue', 
                      mode='lines+markers+text',
                      text=clv_by_segment['Avg_CLV'].round(0), textposition='top center'),
            secondary_y=True
        )
        
        fig.update_layout(
            title="Customer Lifetime Value by Segment",
            template="plotly_white",
            hovermode='x unified'
        )
        
        fig.update_yaxes(title_text="Number of Customers", secondary_y=False)
        fig.update_yaxes(title_text="CLV Score", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Income distribution by education
        if 'Age' in filtered.columns:
            fig = px.box(
                filtered,
                y='Income',
                x='Education',
                title="Income Distribution by Education Level",
                template="plotly_white",
                color='Education',
                points="outliers"
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Spending Patterns Section
    st.markdown("### 💳 Spending Patterns Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Recency vs Spending
        fig = px.scatter(
            filtered,
            x='Recency',
            y='TotalSpent',
            color='Spending_Segment',
            size='Income',
            hover_data=['Education', 'Marital_Status'],
            title="Purchase Recency vs Total Spending",
            template="plotly_white",
            opacity=0.7
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Campaign response analysis
        if 'Response' in filtered.columns:
            response_by_segment = filtered.groupby(['Spending_Segment', 'Response']).size().unstack(fill_value=0)
            response_by_segment['Response_Rate'] = (response_by_segment[1] / response_by_segment.sum(axis=1) * 100)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=response_by_segment.index,
                y=response_by_segment[0],
                name='No Response',
                marker_color='lightcoral'
            ))
            fig.add_trace(go.Bar(
                x=response_by_segment.index,
                y=response_by_segment[1],
                name='Responded',
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                title="Campaign Response by Spending Segment",
                barmode='stack',
                template="plotly_white",
                xaxis_title="Spending Segment",
                yaxis_title="Number of Customers"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Correlation Heatmap
    st.markdown("### 🔗 Feature Correlation Analysis")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    numeric_cols = filtered.select_dtypes(include=[np.number]).columns[:12]
    if len(numeric_cols) > 1:
        corr_matrix = filtered[numeric_cols].corr()
        
        # Create a more informative heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=list(corr_matrix.columns),
            y=list(corr_matrix.index),
            text=corr_matrix.round(2).values,
            texttemplate='%{text}',
            textfont={"size": 10},
            colorscale='RdBu',
            zmid=0,
            showscale=True
        ))
        
        fig.update_layout(
            title="Feature Correlation Heatmap",
            template="plotly_white",
            height=600,
            width=800
        )
        
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download option
    st.markdown("### 📥 Export Analysis")
    col1, col2 = st.columns([3, 1])
    with col1:
        create_download_button(filtered, "customer_analysis.csv", "📥 Download Filtered Data")
    with col2:
        st.metric("Filtered Records", len(filtered))

# ------------------------------------------------------------
# HOUSE SALES DASHBOARD - ENHANCED
# ------------------------------------------------------------
def house_dashboard():
    st.markdown('<h1 class="main-header">🏡 Real Estate Market Analytics</h1>', unsafe_allow_html=True)
    
    df = load_houses()
    if df.empty:
        return
    
    # Enhanced Filters
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            price_range = st.slider(
                "💰 Price Range ($)",
                int(df['price'].min()),
                int(df['price'].max()),
                (300000, 800000),
                step=50000
            )
        
        with col2:
            bedrooms = st.multiselect(
                "🛏️ Bedrooms",
                sorted(df['bedrooms'].unique()),
                default=[2, 3, 4]
            )
        
        with col3:
            bathrooms = st.slider(
                "🚿 Bathrooms Range",
                float(df['bathrooms'].min()),
                float(df['bathrooms'].max()),
                (1.0, 3.0),
                step=0.5
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sqft_range = st.slider(
                "📐 Living Area (sqft)",
                int(df['sqft_living'].min()),
                int(df['sqft_living'].max()),
                (1000, 3000),
                step=500
            )
        
        with col2:
            condition = st.multiselect(
                "⭐ Condition Rating",
                sorted(df['condition'].unique()),
                default=sorted(df['condition'].unique())
            )
        
        with col3:
            year_built = st.slider(
                "🏗️ Year Built",
                int(df['yr_built'].min()),
                int(df['yr_built'].max()),
                (1950, 2015)
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            waterfront = st.checkbox("🏖️ Waterfront Only", value=False)
        with col2:
            renovated = st.checkbox("🔧 Renovated Only", value=False)
        with col3:
            if st.button("🔄 Reset Filters", key="reset_house"):
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered = df[
        (df['price'].between(price_range[0], price_range[1])) &
        (df['bedrooms'].isin(bedrooms)) &
        (df['bathrooms'].between(bathrooms[0], bathrooms[1])) &
        (df['sqft_living'].between(sqft_range[0], sqft_range[1])) &
        (df['condition'].isin(condition)) &
        (df['yr_built'].between(year_built[0], year_built[1]))
    ]
    
    if waterfront:
        filtered = filtered[filtered['waterfront'] == 1]
    
    if renovated:
        filtered = filtered[filtered['renovated'] == True]
    
    # Market Overview KPIs
    st.markdown("### 📊 Market Overview")
    metric_cols = st.columns(6)
    
    with metric_cols[0]:
        avg_price = filtered['price'].mean()
        st.markdown(create_metric_card("Average Price", avg_price, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[1]:
        median_price = filtered['price'].median()
        st.markdown(create_metric_card("Median Price", median_price, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[2]:
        avg_price_sqft = filtered['price_per_sqft'].mean()
        st.markdown(create_metric_card("Price/Sqft", avg_price_sqft, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[3]:
        total_listings = len(filtered)
        st.markdown(create_metric_card("Active Listings", total_listings), unsafe_allow_html=True)
    
    with metric_cols[4]:
        avg_sqft = filtered['sqft_living'].mean()
        st.markdown(create_metric_card("Avg Living Area", avg_sqft, suffix=" sqft"), unsafe_allow_html=True)
    
    with metric_cols[5]:
        waterfront_count = filtered['waterfront'].sum()
        st.markdown(create_metric_card("Waterfront Properties", waterfront_count), unsafe_allow_html=True)
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Price distribution with statistics
        fig = px.histogram(
            filtered,
            x='price',
            nbins=50,
            title="Price Distribution Analysis",
            marginal='box',
            template="plotly_white",
            color_discrete_sequence=['#667eea']
        )
        
        # Add statistical lines
        median_price = filtered['price'].median()
        mean_price = filtered['price'].mean()
        
        fig.add_vline(x=median_price, line_dash="dash", line_color="red", 
                     annotation_text=f"Median: ${median_price:,.0f}")
        fig.add_vline(x=mean_price, line_dash="dash", line_color="green", 
                     annotation_text=f"Mean: ${mean_price:,.0f}")
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Price by bedroom with box plot
        fig = px.box(
            filtered,
            x='bedrooms',
            y='price',
            title="Price Distribution by Bedroom Count",
            template="plotly_white",
            color='bedrooms',
            color_continuous_scale='Viridis',
            points="outliers"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Price Trends
    st.markdown("### 📈 Market Trends")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Monthly price trends
    monthly_prices = filtered.groupby('year_month').agg({
        'price': ['mean', 'median', 'count', 'std']
    }).reset_index()
    monthly_prices.columns = ['year_month', 'avg_price', 'median_price', 'count', 'price_std']
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=monthly_prices['year_month'], y=monthly_prices['avg_price'],
                  name="Average Price", mode='lines+markers',
                  line=dict(color='#667eea', width=2)),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(x=monthly_prices['year_month'], y=monthly_prices['median_price'],
                  name="Median Price", mode='lines+markers',
                  line=dict(color='#764ba2', width=2, dash='dash')),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(x=monthly_prices['year_month'], y=monthly_prices['count'],
               name="Sales Volume", marker_color='lightblue', opacity=0.4),
        secondary_y=True
    )
    
    fig.update_layout(
        title="Price Trends and Sales Volume Over Time",
        template="plotly_white",
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Price ($)", secondary_y=False)
    fig.update_yaxes(title_text="Number of Sales", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced Analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Price vs Living Area with condition coloring
        fig = px.scatter(
            filtered,
            x='sqft_living',
            y='price',
            color='condition',
            size='sqft_lot',
            hover_data=['bedrooms', 'bathrooms', 'waterfront', 'age'],
            title="Price vs Living Area Analysis",
            template="plotly_white",
            trendline="ols",
            opacity=0.6
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Feature importance for price
        correlations = df[['price', 'sqft_living', 'sqft_lot', 'bedrooms', 'bathrooms', 
                          'floors', 'waterfront', 'view', 'condition', 'grade', 
                          'sqft_above', 'sqft_basement', 'age']].corr()['price'].sort_values()
        
        # Remove price itself
        correlations = correlations[correlations.index != 'price']
        
        fig = px.bar(
            x=correlations.values,
            y=correlations.index,
            orientation='h',
            title="Feature Correlation with House Price",
            labels={'x': 'Correlation Coefficient', 'y': 'Feature'},
            color=correlations.values,
            color_continuous_scale='RdBu',
            template="plotly_white",
            text=correlations.values.round(2)
        )
        fig.update_traces(textposition='outside')
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Property Analysis
    st.markdown("### 🏘️ Property Characteristics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Condition distribution
        condition_counts = filtered['condition'].value_counts().sort_index()
        
        fig = px.pie(
            values=condition_counts.values,
            names=condition_counts.index,
            title="Property Condition Distribution",
            template="plotly_white",
            hole=0.3
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Price per sqft by number of floors
        fig = px.box(
            filtered,
            x='floors',
            y='price_per_sqft',
            title="Price per Square Foot by Number of Floors",
            template="plotly_white",
            color='floors',
            points="outliers"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Geographic Distribution
    if 'lat' in filtered.columns and 'long' in filtered.columns:
        st.markdown("### 🗺️ Geographic Price Distribution")
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Sample data for map performance
        map_df = filtered.dropna(subset=['lat', 'long'])
        if len(map_df) > 2000:
            map_df = map_df.sample(2000)
        
        st.map(
            map_df,
            latitude='lat',
            longitude='long',
            color=None,
            size=None
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Export Section
    st.markdown("### 📥 Export Market Data")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        create_download_button(filtered, "house_market_data.csv", "📥 Download Filtered Data")
    with col2:
        st.metric("Filtered Listings", len(filtered))
    with col3:
        st.metric("Total Listings", len(df))

# ------------------------------------------------------------
# MAIN APPLICATION
# ------------------------------------------------------------
def main():
    # Main title
    st.markdown('<h1 class="main-header">📊 Advanced Analytics Dashboard Suite</h1>', unsafe_allow_html=True)
    
    # Dashboard selection with icons and descriptions
    st.markdown("### Select Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🛍️ Customer Analytics", use_container_width=True, key="btn_customer"):
            st.session_state['active_dashboard'] = 'customer'
    
    with col2:
        if st.button("🏡 Real Estate Market", use_container_width=True, key="btn_houses"):
            st.session_state['active_dashboard'] = 'houses'
    
    # Initialize session state
    if 'active_dashboard' not in st.session_state:
        st.session_state['active_dashboard'] = 'customer'
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        st.markdown("---")
        
        dashboard = st.radio(
            "Choose Dashboard",
            ["🛍️ Customer Analytics", "🏡 Real Estate Market"],
            index=0 if st.session_state['active_dashboard'] == 'customer' else 1
        )
        
        # Update session state based on radio selection
        dashboard_map = {
            "🛍️ Customer Analytics": "customer",
            "🏡 Real Estate Market": "houses"
        }
        st.session_state['active_dashboard'] = dashboard_map[dashboard]
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.info(
            "This advanced analytics dashboard provides deep insights into "
            "customer behavior patterns and real estate market trends. "
            "Use the interactive filters to explore the data and uncover valuable insights."
        )
        
        # Quick stats
        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        
        try:
            customer_df = load_customer()
            houses_df = load_houses()
            
            st.metric("Total Customers", f"{len(customer_df):,}")
            st.metric("Total Properties", f"{len(houses_df):,}")
        except:
            pass
        
        # System info
        st.markdown("---")
        st.markdown("### ⚙️ System Status")
        st.success("✅ All systems operational")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Render selected dashboard
    if st.session_state['active_dashboard'] == 'customer':
        customer_dashboard()
    elif st.session_state['active_dashboard'] == 'houses':
        house_dashboard()

if __name__ == "__main__":
    main()
