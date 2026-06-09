import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(layout="wide", page_title="Advanced Analytics Dashboard", page_icon="📊", initial_sidebar_state="expanded")

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
# CACHED DATA LOADERS
# ------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_customer():
    try:
        df = pd.read_csv("marketing_campaign.csv", sep='\t')
        spending_cols = ['MntWines', 'MntFruits', 'MntMeatProducts',
                        'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']
        df['TotalSpent'] = df[spending_cols].sum(axis=1)
        if 'Year_Birth' in df.columns:
            df['Age'] = datetime.now().year - df['Year_Birth']
        # Customer Lifetime Value (simple proxy)
        df['CLV_Score'] = df['TotalSpent'] * (df['Recency'].max() - df['Recency']) / df['Recency'].max()
        df['Spending_Segment'] = pd.qcut(df['TotalSpent'], q=4, labels=['Low', 'Medium', 'High', 'Premium'])
        df['Last_Purchase_Days'] = df['Recency']
        df['Spending_Ratio'] = (df['TotalSpent'] / df['Income'] * 100).clip(0, 100)
        # Age groups for line chart
        df['Age_Group'] = pd.cut(df['Age'], bins=[18,30,40,50,60,100], labels=['18-30','31-40','41-50','51-60','60+'])
        return df
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_houses():
    try:
        df = pd.read_csv("kc_house_data.csv")
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        df['age'] = datetime.now().year - df['yr_built']
        df['renovated'] = df['yr_renovated'] > 0
        df['price_per_sqft'] = df['price'] / df['sqft_living']
        df['price_category'] = pd.qcut(df['price'], q=5, labels=['Budget', 'Economic', 'Mid-Range', 'Premium', 'Luxury'])
        df['total_rooms'] = df['bedrooms'] + df['bathrooms']
        return df
    except Exception as e:
        st.error(f"Error loading house data: {e}")
        return pd.DataFrame()

# ------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------
def create_metric_card(title, value, prefix="", suffix=""):
    return f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; opacity: 0.9;">{title}</div>
            <div style="font-size: 1.8rem; font-weight: 700;">{prefix}{value:,.0f}{suffix}</div>
        </div>
    """

def create_download_button(df, filename, button_text="📥 Download Data"):
    csv = df.to_csv(index=False)
    return st.download_button(label=button_text, data=csv, file_name=filename, mime='text/csv')

# ------------------------------------------------------------
# CUSTOMER PERSONALITY DASHBOARD (7+ charts)
# ------------------------------------------------------------
def customer_dashboard():
    st.markdown('<h1 class="main-header">🛍️ Customer Analytics Hub</h1>', unsafe_allow_html=True)
    df = load_customer()
    if df.empty:
        return

    # Filters
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            education = st.multiselect("🎓 Education", df['Education'].unique(), default=df['Education'].unique())
        with col2:
            marital = st.multiselect("💑 Marital Status", df['Marital_Status'].unique(), default=df['Marital_Status'].unique())
        with col3:
            income_range = st.slider("💰 Income Range ($)", int(df['Income'].min()), int(df['Income'].max()), (30000, 100000), step=10000)
        with col4:
            spending_segment = st.multiselect("📊 Spending Segment", df['Spending_Segment'].unique(), default=df['Spending_Segment'].unique())
        col1, col2, col3 = st.columns(3)
        with col1:
            age_range = st.slider("👤 Age Range", int(df['Age'].min()), int(df['Age'].max()), (25, 65))
        with col2:
            if 'Kidhome' in df.columns:
                kids = st.multiselect("👶 Kids at Home", df['Kidhome'].unique(), default=df['Kidhome'].unique())
            else:
                kids = [0,1,2]
        with col3:
            if st.button("🔄 Reset Filters", key="reset_customer"): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    filtered = df[(df['Education'].isin(education)) & (df['Marital_Status'].isin(marital)) &
                  (df['Income'].between(income_range[0], income_range[1])) & (df['Spending_Segment'].isin(spending_segment))]
    if 'Age' in filtered.columns:
        filtered = filtered[filtered['Age'].between(age_range[0], age_range[1])]
    if 'Kidhome' in filtered.columns:
        filtered = filtered[filtered['Kidhome'].isin(kids)]

    # KPI Cards
    st.markdown("### 📈 Customer Insights")
    mc = st.columns(5)
    mc[0].markdown(create_metric_card("Avg Income", filtered['Income'].mean(), prefix="$"), unsafe_allow_html=True)
    mc[1].markdown(create_metric_card("Avg Total Spending", filtered['TotalSpent'].mean(), prefix="$"), unsafe_allow_html=True)
    mc[2].markdown(create_metric_card("Avg Days Since Purchase", filtered['Recency'].mean(), suffix=" days"), unsafe_allow_html=True)
    mc[3].markdown(create_metric_card("Response Rate", (filtered['Response']==1).mean()*100 if 'Response' in filtered.columns else 0, suffix="%"), unsafe_allow_html=True)
    mc[4].markdown(create_metric_card("Active Customers", len(filtered)), unsafe_allow_html=True)

    # Chart 1: Income vs Spending (scatter, no trendline)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig1 = px.scatter(filtered, x='Income', y='TotalSpent', color='Education',
                      size='Recency', hover_data=['Age','Marital_Status'],
                      title="Income vs Total Spending", opacity=0.7)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 2 & 3: Side by side
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        spending_cols = ['MntWines','MntFruits','MntMeatProducts','MntFishProducts','MntSweetProducts','MntGoldProds']
        spend_avg = filtered[spending_cols].mean().sort_values()
        fig2 = px.bar(x=spend_avg.values, y=spend_avg.index, orientation='h',
                      title="Avg Spending by Category", labels={'x':'Amount ($)','y':'Category'},
                      color=spend_avg.values, color_continuous_scale='Blues',
                      text=spend_avg.values.round(0))
        fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        # Chart 3: Donut – Marital Status distribution
        marital_counts = filtered['Marital_Status'].value_counts()
        fig3 = px.pie(values=marital_counts.values, names=marital_counts.index,
                      title="Marital Status Distribution", hole=0.4)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Chart 4: CLV by Segment (dual axis)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    clv_seg = filtered.groupby('Spending_Segment').agg(CLV=('CLV_Score','mean'), Count=('ID','count')).reset_index()
    fig4 = make_subplots(specs=[[{"secondary_y": True}]])
    fig4.add_trace(go.Bar(name="Count", x=clv_seg['Spending_Segment'], y=clv_seg['Count'], marker_color='lightblue'), secondary_y=False)
    fig4.add_trace(go.Scatter(name="Avg CLV", x=clv_seg['Spending_Segment'], y=clv_seg['CLV'],
                              marker_color='darkblue', mode='lines+markers+text',
                              text=clv_seg['CLV'].round(0), textposition='top center'), secondary_y=True)
    fig4.update_layout(title="CLV by Spending Segment", template="plotly_white")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 5: Income box plot by Education
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig5 = px.box(filtered, y='Income', x='Education', title="Income Distribution by Education",
                  color='Education', points="outliers")
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 6: Line chart – Average spending by Age Group
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    age_spend = filtered.groupby('Age_Group')['TotalSpent'].mean().reset_index()
    fig6 = px.line(age_spend, x='Age_Group', y='TotalSpent', markers=True,
                   title="Average Spending by Age Group", line_shape='spline')
    st.plotly_chart(fig6, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 7: Recency vs Spending colored by Response
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    if 'Response' in filtered.columns:
        fig7 = px.scatter(filtered, x='Recency', y='TotalSpent', color='Response',
                          title="Recency vs Total Spending (Response)", opacity=0.6,
                          color_discrete_map={0:'lightcoral',1:'lightgreen'})
        st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("No response column found.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 8: Stacked bar – Campaign response by spending segment
    if 'Response' in filtered.columns:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        resp_seg = filtered.groupby(['Spending_Segment','Response']).size().unstack(fill_value=0)
        fig8 = go.Figure(data=[
            go.Bar(name='No Response', x=resp_seg.index, y=resp_seg.get(0,0), marker_color='lightcoral'),
            go.Bar(name='Responded', x=resp_seg.index, y=resp_seg.get(1,0), marker_color='lightgreen')
        ])
        fig8.update_layout(barmode='stack', title="Campaign Response by Segment", template="plotly_white")
        st.plotly_chart(fig8, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Correlation Heatmap
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    num_cols = filtered.select_dtypes(include=[np.number]).columns[:10]
    if len(num_cols)>1:
        corr = filtered[num_cols].corr()
        fig_corr = go.Figure(data=go.Heatmap(z=corr.values, x=list(corr.columns), y=list(corr.index),
                                             text=corr.round(2).values, texttemplate='%{text}',
                                             colorscale='RdBu', zmid=0))
        fig_corr.update_layout(title="Correlation Heatmap", height=600)
        st.plotly_chart(fig_corr, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Download
    st.markdown("### 📥 Export")
    create_download_button(filtered, "customer_analysis.csv")

# ------------------------------------------------------------
# HOUSE SALES DASHBOARD (7+ charts + map)
# ------------------------------------------------------------
def house_dashboard():
    st.markdown('<h1 class="main-header">🏡 Real Estate Market Analytics</h1>', unsafe_allow_html=True)
    df = load_houses()
    if df.empty: return

    # Filters
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1:
            price_range = st.slider("💰 Price Range ($)", int(df['price'].min()), int(df['price'].max()), (300000,800000), step=50000)
        with c2:
            bedrooms = st.multiselect("🛏️ Bedrooms", sorted(df['bedrooms'].unique()), default=[2,3,4])
        with c3:
            bathrooms = st.slider("🚿 Bathrooms", float(df['bathrooms'].min()), float(df['bathrooms'].max()), (1.0,3.0), 0.5)
        c1,c2,c3 = st.columns(3)
        with c1:
            sqft_range = st.slider("📐 Living Area (sqft)", int(df['sqft_living'].min()), int(df['sqft_living'].max()), (1000,3000), 500)
        with c2:
            condition = st.multiselect("⭐ Condition", sorted(df['condition'].unique()), default=sorted(df['condition'].unique()))
        with c3:
            year_built = st.slider("🏗️ Year Built", int(df['yr_built'].min()), int(df['yr_built'].max()), (1950,2015))
        c1,c2,c3 = st.columns(3)
        with c1:
            waterfront = st.checkbox("🏖️ Waterfront Only")
        with c2:
            renovated = st.checkbox("🔧 Renovated Only")
        with c3:
            if st.button("🔄 Reset Filters", key="reset_house"): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    filtered = df[(df['price'].between(*price_range)) & (df['bedrooms'].isin(bedrooms)) &
                  (df['bathrooms'].between(*bathrooms)) & (df['sqft_living'].between(*sqft_range)) &
                  (df['condition'].isin(condition)) & (df['yr_built'].between(*year_built))]
    if waterfront: filtered = filtered[filtered['waterfront']==1]
    if renovated: filtered = filtered[filtered['renovated']==True]

    # KPI Cards
    st.markdown("### 📊 Market Overview")
    mc = st.columns(6)
    mc[0].markdown(create_metric_card("Avg Price", filtered['price'].mean(), prefix="$"), unsafe_allow_html=True)
    mc[1].markdown(create_metric_card("Median Price", filtered['price'].median(), prefix="$"), unsafe_allow_html=True)
    mc[2].markdown(create_metric_card("Price/Sqft", filtered['price_per_sqft'].mean(), prefix="$"), unsafe_allow_html=True)
    mc[3].markdown(create_metric_card("Listings", len(filtered)), unsafe_allow_html=True)
    mc[4].markdown(create_metric_card("Avg Living Area", filtered['sqft_living'].mean(), suffix=" sqft"), unsafe_allow_html=True)
    mc[5].markdown(create_metric_card("Waterfront", filtered['waterfront'].sum()), unsafe_allow_html=True)

    # Chart 1: Price histogram
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig1 = px.histogram(filtered, x='price', nbins=50, title="Price Distribution", marginal='box', color_discrete_sequence=['#667eea'])
    median = filtered['price'].median()
    fig1.add_vline(x=median, line_dash="dash", line_color="red", annotation_text=f"Median: ${median:,.0f}")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 2: Price by bedrooms (box)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig2 = px.box(filtered, x='bedrooms', y='price', title="Price by Bedroom Count", color='bedrooms', points="outliers")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 3: Price trends over time (line + bar)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    monthly = filtered.groupby('year_month').agg(avg_price=('price','mean'), count=('price','count')).reset_index()
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Scatter(x=monthly['year_month'], y=monthly['avg_price'], name="Avg Price", line=dict(color='#667eea',width=2)), secondary_y=False)
    fig3.add_trace(go.Bar(x=monthly['year_month'], y=monthly['count'], name="Sales Volume", marker_color='lightblue', opacity=0.5), secondary_y=True)
    fig3.update_layout(title="Price Trends & Sales Volume", template="plotly_white", hovermode='x unified')
    fig3.update_xaxes(title="Month")
    fig3.update_yaxes(title="Price ($)", secondary_y=False)
    fig3.update_yaxes(title="Sales Count", secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 4: Price vs Living Area (scatter, no trendline)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig4 = px.scatter(filtered, x='sqft_living', y='price', color='condition', size='sqft_lot',
                      hover_data=['bedrooms','bathrooms','waterfront'], title="Price vs Living Area", opacity=0.6)
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 5: Feature correlation bar
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    corr_data = df[['price','sqft_living','sqft_lot','bedrooms','bathrooms','floors','waterfront','view','condition','grade','sqft_above','sqft_basement','age']].corr()['price'].drop('price').sort_values()
    fig5 = px.bar(x=corr_data.values, y=corr_data.index, orientation='h', title="Feature Correlation with Price",
                  color=corr_data.values, color_continuous_scale='RdBu', text=corr_data.values.round(2))
    fig5.update_traces(textposition='outside')
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 6: Donut – Condition distribution
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    cond = filtered['condition'].value_counts().sort_index()
    fig6 = px.pie(values=cond.values, names=cond.index, title="Condition Distribution", hole=0.4)
    st.plotly_chart(fig6, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 7: Donut – Grade distribution
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    grade = filtered['grade'].value_counts().sort_index()
    fig7 = px.pie(values=grade.values, names=grade.index, title="Grade Distribution", hole=0.4)
    st.plotly_chart(fig7, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 8: Line – Average price by year built
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    year_price = filtered.groupby('yr_built')['price'].mean().reset_index()
    fig8 = px.line(year_price, x='yr_built', y='price', title="Average Price by Year Built", markers=True)
    st.plotly_chart(fig8, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 9: Price per sqft by number of floors (box)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig9 = px.box(filtered, x='floors', y='price_per_sqft', title="Price per Sqft by Floors", color='floors', points="outliers")
    st.plotly_chart(fig9, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Map (Geographic Distribution)
    if 'lat' in filtered.columns and 'long' in filtered.columns:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("🗺️ Geographic Distribution")
        map_df = filtered.dropna(subset=['lat','long']).sample(min(2000, len(filtered)))
        st.map(map_df, latitude='lat', longitude='long')
        st.markdown('</div>', unsafe_allow_html=True)

    # Export
    st.markdown("### 📥 Export")
    col1, col2, _ = st.columns([2,1,1])
    with col1: create_download_button(filtered, "house_market_data.csv")
    with col2: st.metric("Filtered", len(filtered))

# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
def main():
    st.markdown('<h1 class="main-header">📊 Advanced Analytics Dashboard Suite</h1>', unsafe_allow_html=True)
    st.markdown("### Select Dashboard")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🛍️ Customer Analytics", use_container_width=True, key="btn_cust"): st.session_state['active'] = 'customer'
    with c2:
        if st.button("🏡 Real Estate Market", use_container_width=True, key="btn_house"): st.session_state['active'] = 'houses'

    if 'active' not in st.session_state: st.session_state['active'] = 'customer'

    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        dash = st.radio("Choose", ["🛍️ Customer Analytics", "🏡 Real Estate Market"],
                        index=0 if st.session_state['active']=='customer' else 1)
        st.session_state['active'] = 'customer' if dash.startswith("🛍️") else 'houses'
        st.markdown("---")
        st.info("Deep insights into customer behavior and real estate trends.")
        st.markdown("---")
        st.success("✅ System operational")
        st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if st.session_state['active'] == 'customer':
        customer_dashboard()
    else:
        house_dashboard()

if __name__ == "__main__":
    main()
