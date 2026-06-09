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
        
        return df
    except Exception as e:
        st.error(f"Error loading house data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_olympics():
    """Load and preprocess olympics data"""
    try:
        df = pd.read_csv("athlete_events.csv")
        
        # Calculate additional metrics
        df['Total_Medals'] = df['Medal'].notna().astype(int)
        df['Gold'] = (df['Medal'] == 'Gold').astype(int)
        df['Silver'] = (df['Medal'] == 'Silver').astype(int)
        df['Bronze'] = (df['Medal'] == 'Bronze').astype(int)
        
        # Calculate BMI if Height and Weight are available
        df['BMI'] = df['Weight'] / ((df['Height'] / 100) ** 2)
        
        return df
    except Exception as e:
        st.error(f"Error loading olympics data: {str(e)}")
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
# OLYMPICS DASHBOARD - ENHANCED
# ------------------------------------------------------------
def olympics_dashboard():
    st.markdown('<h1 class="main-header">🏅 Olympic Games Analytics</h1>', unsafe_allow_html=True)
    
    df = load_olympics()
    if df.empty:
        return
    
    # Advanced Filters in a container
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            seasons = st.multiselect(
                "🌍 Season",
                df['Season'].unique(),
                default=df['Season'].unique()
            )
        
        with col2:
            years = st.slider(
                "📅 Year Range",
                int(df['Year'].min()),
                int(df['Year'].max()),
                (1960, 2016)
            )
        
        with col3:
            sports = st.multiselect(
                "🏃 Sport",
                df['Sport'].unique(),
                default=df['Sport'].unique()[:5]
            )
        
        with col4:
            medal_types = st.multiselect(
                "🥇 Medal Type",
                ['Gold', 'Silver', 'Bronze'],
                default=['Gold', 'Silver', 'Bronze']
            )
        
        # Advanced filters row 2
        col1, col2, col3 = st.columns(3)
        with col1:
            countries = st.multiselect(
                "🏳️ Countries (Top N)",
                df['NOC'].unique(),
                default=df['NOC'].value_counts().head(10).index.tolist()
            )
        
        with col2:
            sex_filter = st.multiselect(
                "⚥ Gender",
                df['Sex'].unique(),
                default=df['Sex'].unique()
            )
        
        with col3:
            if st.button("🔄 Reset Filters", key="reset_olympics"):
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered = df[
        (df['Season'].isin(seasons)) &
        (df['Year'].between(years[0], years[1])) &
        (df['Sport'].isin(sports)) &
        (df['Sex'].isin(sex_filter)) &
        (df['NOC'].isin(countries))
    ]
    
    if medal_types:
        filtered = filtered[filtered['Medal'].isin(medal_types) | filtered['Medal'].isna()]
    
    # Key Metrics Row
    st.markdown("### 📈 Key Performance Indicators")
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        total_athletes = filtered['ID'].nunique()
        st.markdown(create_metric_card("Total Athletes", total_athletes, suffix="+"), unsafe_allow_html=True)
    
    with metric_cols[1]:
        total_medals = filtered['Medal'].notna().sum()
        st.markdown(create_metric_card("Total Medals", total_medals), unsafe_allow_html=True)
    
    with metric_cols[2]:
        total_countries = filtered['NOC'].nunique()
        st.markdown(create_metric_card("Countries", total_countries), unsafe_allow_html=True)
    
    with metric_cols[3]:
        avg_age = filtered['Age'].mean()
        st.markdown(create_metric_card("Avg Age", avg_age, suffix=" yrs"), unsafe_allow_html=True)
    
    # Charts Section
    st.markdown("### 📊 Analytics & Insights")
    
    # Row 1: Top Countries and Athletes
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Enhanced medal chart with medal types
            medals_by_country = filtered[filtered['Medal'].notna()].groupby(['NOC', 'Medal']).size().unstack(fill_value=0)
            medals_by_country['Total'] = medals_by_country.sum(axis=1)
            top_countries = medals_by_country.nlargest(10, 'Total')
            
            fig = go.Figure(data=[
                go.Bar(name='Gold', x=top_countries.index, y=top_countries.get('Gold', 0), marker_color='#FFD700'),
                go.Bar(name='Silver', x=top_countries.index, y=top_countries.get('Silver', 0), marker_color='#C0C0C0'),
                go.Bar(name='Bronze', x=top_countries.index, y=top_countries.get('Bronze', 0), marker_color='#CD7F32')
            ])
            
            fig.update_layout(
                title="Top 10 Countries - Medal Distribution",
                barmode='stack',
                xaxis_title="Country",
                yaxis_title="Number of Medals",
                template="plotly_white",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Top athletes with horizontal bar
            top_athletes = filtered[filtered['Medal'].notna()].groupby('Name')['Medal'].count().nlargest(10)
            
            fig = px.bar(
                top_athletes,
                orientation='h',
                title="Top 10 Athletes by Medal Count",
                labels={'value': 'Medals', 'Name': 'Athlete'},
                color=top_athletes.values,
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(showlegend=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Row 2: Trends and Correlations
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Athletes trend with gender breakdown
            athletes_trend = filtered.groupby(['Year', 'Sex'])['ID'].nunique().reset_index()
            
            fig = px.area(
                athletes_trend,
                x='Year',
                y='ID',
                color='Sex',
                title="Athlete Participation Over Time by Gender",
                labels={'ID': 'Number of Athletes', 'Year': 'Year'},
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # BMI distribution by sport
            bmi_data = filtered.dropna(subset=['BMI'])
            if not bmi_data.empty:
                top_sports = bmi_data['Sport'].value_counts().head(5).index
                bmi_sport = bmi_data[bmi_data['Sport'].isin(top_sports)]
                
                fig = px.box(
                    bmi_sport,
                    x='Sport',
                    y='BMI',
                    title="BMI Distribution by Top Sports",
                    template="plotly_white",
                    color='Sport'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No BMI data available")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Row 3: Additional Analytics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Age distribution
        fig = px.histogram(
            filtered.dropna(subset=['Age']),
            x='Age',
            nbins=30,
            title="Age Distribution of Athletes",
            template="plotly_white",
            marginal='box'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Height distribution
        fig = px.histogram(
            filtered.dropna(subset=['Height']),
            x='Height',
            nbins=30,
            title="Height Distribution",
            template="plotly_white",
            color='Sex'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Weight distribution
        fig = px.histogram(
            filtered.dropna(subset=['Weight']),
            x='Weight',
            nbins=30,
            title="Weight Distribution",
            template="plotly_white",
            color='Sex'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Download Section
    st.markdown("### 📥 Export Data")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        create_download_button(filtered, "olympics_data.csv")
    with col2:
        st.metric("Filtered Records", len(filtered))
    with col3:
        st.metric("Total Records", len(df))

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
    
    # KPI Cards
    st.markdown("### 📈 Customer Insights")
    metric_cols = st.columns(4)
    
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
            hover_data=['Age', 'Marital_Status'],
            title="Income vs Total Spending Analysis",
            trendline="ols",
            template="plotly_white"
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
            labels={'x': 'Average Amount ($)', 'y': 'Product'},
            color=spending_avg.values,
            color_continuous_scale='Blues',
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional Analytics Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Customer lifetime value by segment
        clv_by_segment = filtered.groupby('Spending_Segment')['CLV_Score'].agg(['mean', 'count']).reset_index()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(name="Customer Count", x=clv_by_segment['Spending_Segment'], 
                   y=clv_by_segment['count'], marker_color='lightblue'),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(name="Avg CLV Score", x=clv_by_segment['Spending_Segment'], 
                      y=clv_by_segment['mean'], marker_color='darkblue', mode='lines+markers'),
            secondary_y=True
        )
        
        fig.update_layout(
            title="Customer Lifetime Value by Segment",
            template="plotly_white",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Age distribution by education
        if 'Age' in filtered.columns:
            fig = px.violin(
                filtered.dropna(subset=['Age']),
                y='Age',
                x='Education',
                box=True,
                title="Age Distribution by Education Level",
                template="plotly_white",
                color='Education'
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Correlation Heatmap
    st.markdown("### 🔗 Correlation Analysis")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    numeric_cols = filtered.select_dtypes(include=[np.number]).columns[:10]
    if len(numeric_cols) > 1:
        corr_matrix = filtered[numeric_cols].corr()
        
        fig = ff.create_annotated_heatmap(
            z=corr_matrix.values,
            x=list(corr_matrix.columns),
            y=list(corr_matrix.index),
            annotation_text=corr_matrix.round(2).values,
            colorscale='RdBu',
            showscale=True
        )
        
        fig.update_layout(
            title="Feature Correlation Heatmap",
            template="plotly_white",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download option
    st.markdown("### 📥 Export Analysis")
    create_download_button(filtered, "customer_analysis.csv")

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
                "⭐ Condition",
                sorted(df['condition'].unique()),
                default=sorted(df['condition'].unique())
            )
        
        with col3:
            waterfront = st.checkbox("🏖️ Waterfront Only", value=False)
        
        if st.button("🔄 Reset Filters", key="reset_house"):
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered = df[
        (df['price'].between(price_range[0], price_range[1])) &
        (df['bedrooms'].isin(bedrooms)) &
        (df['bathrooms'].between(bathrooms[0], bathrooms[1])) &
        (df['sqft_living'].between(sqft_range[0], sqft_range[1])) &
        (df['condition'].isin(condition))
    ]
    
    if waterfront:
        filtered = filtered[filtered['waterfront'] == 1]
    
    # Market Overview KPIs
    st.markdown("### 📊 Market Overview")
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        avg_price = filtered['price'].mean()
        st.markdown(create_metric_card("Average Price", avg_price, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[1]:
        median_price = filtered['price'].median()
        st.markdown(create_metric_card("Median Price", median_price, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[2]:
        avg_price_sqft = filtered['price_per_sqft'].mean()
        st.markdown(create_metric_card("Price per Sqft", avg_price_sqft, prefix="$"), unsafe_allow_html=True)
    
    with metric_cols[3]:
        total_listings = len(filtered)
        st.markdown(create_metric_card("Active Listings", total_listings), unsafe_allow_html=True)
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Price distribution with KDE
        fig = px.histogram(
            filtered,
            x='price',
            nbins=50,
            title="Price Distribution Analysis",
            marginal='box',
            template="plotly_white",
            color_discrete_sequence=['#667eea']
        )
        
        # Add median line
        median_price = filtered['price'].median()
        fig.add_vline(x=median_price, line_dash="dash", line_color="red", 
                     annotation_text=f"Median: ${median_price:,.0f}")
        
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
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Price Trends
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Monthly price trends
    monthly_prices = filtered.groupby('year_month').agg({
        'price': ['mean', 'median', 'count']
    }).reset_index()
    monthly_prices.columns = ['year_month', 'avg_price', 'median_price', 'count']
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=monthly_prices['year_month'], y=monthly_prices['avg_price'],
                  name="Average Price", mode='lines+markers',
                  line=dict(color='#667eea', width=2)),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(x=monthly_prices['year_month'], y=monthly_prices['count'],
               name="Number of Sales", marker_color='lightblue', opacity=0.5),
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
            hover_data=['bedrooms', 'bathrooms', 'waterfront'],
            title="Price vs Living Area Analysis",
            template="plotly_white",
            trendline="ols"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Feature importance for price (simple correlation)
        correlations = df[['price', 'sqft_living', 'bedrooms', 'bathrooms', 'sqft_lot', 
                          'floors', 'waterfront', 'view', 'condition', 'grade']].corr()['price'].sort_values()
        
        fig = px.bar(
            x=correlations[1:].values,
            y=correlations[1:].index,
            orientation='h',
            title="Feature Correlation with Price",
            labels={'x': 'Correlation Coefficient', 'y': 'Feature'},
            color=correlations[1:].values,
            color_continuous_scale='RdBu',
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Geographic Distribution
    if 'lat' in filtered.columns and 'long' in filtered.columns:
        st.markdown("### 🗺️ Geographic Distribution")
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Sample data for map performance
        map_df = filtered.dropna(subset=['lat', 'long']).sample(min(2000, len(filtered)))
        
        # Color by price
        st.map(
            map_df,
            latitude='lat',
            longitude='long',
            color='price',
            size='sqft_living'
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Export Section
    st.markdown("### 📥 Export Market Data")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        create_download_button(filtered, "house_market_data.csv")
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏅 Olympics History", use_container_width=True):
            st.session_state['active_dashboard'] = 'olympics'
    
    with col2:
        if st.button("🛍️ Customer Analytics", use_container_width=True):
            st.session_state['active_dashboard'] = 'customer'
    
    with col3:
        if st.button("🏡 Real Estate Market", use_container_width=True):
            st.session_state['active_dashboard'] = 'houses'
    
    # Initialize session state
    if 'active_dashboard' not in st.session_state:
        st.session_state['active_dashboard'] = 'olympics'
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        st.markdown("---")
        
        dashboard = st.radio(
            "Choose Dashboard",
            ["🏅 Olympics History", "🛍️ Customer Analytics", "🏡 Real Estate Market"],
            index=["olympics", "customer", "houses"].index(st.session_state['active_dashboard'])
        )
        
        # Update session state based on radio selection
        dashboard_map = {
            "🏅 Olympics History": "olympics",
            "🛍️ Customer Analytics": "customer",
            "🏡 Real Estate Market": "houses"
        }
        st.session_state['active_dashboard'] = dashboard_map[dashboard]
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.info(
            "This advanced analytics dashboard provides deep insights into "
            "Olympic history, customer behavior, and real estate markets. "
            "Use the filters to explore the data and uncover patterns."
        )
        
        # System info
        st.markdown("---")
        st.markdown("### ⚙️ System Status")
        st.success("✅ All systems operational")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Render selected dashboard
    if st.session_state['active_dashboard'] == 'olympics':
        olympics_dashboard()
    elif st.session_state['active_dashboard'] == 'customer':
        customer_dashboard()
    elif st.session_state['active_dashboard'] == 'houses':
        house_dashboard()

if __name__ == "__main__":
    main()
