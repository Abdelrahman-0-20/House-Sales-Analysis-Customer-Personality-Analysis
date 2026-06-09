import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ─── Page Config ───
st.set_page_config(
    page_title="Interactive Power BI → Streamlit Dashboards",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Interactive Power BI → Streamlit Dashboards")

# ─── Data Loaders with Error Handling ───

@st.cache_data
def load_olympics():
    """Load Olympics history data."""
    file_path = Path("athlete_events.csv")
    if not file_path.exists():
        return None
    try:
        df = pd.read_csv(file_path)
        df["Year"] = df["Year"].astype(int)
        df["Season"] = df["Season"].astype(str)
        df["Medal"] = df["Medal"].fillna("No Medal")
        return df
    except Exception as e:
        st.error(f"Error loading Olympics data: {e}")
        return None


@st.cache_data
def load_customer():
    """Load customer personality data."""
    file_path = Path("marketing_campaign.csv")
    if not file_path.exists():
        return None
    try:
        df = pd.read_csv(file_path, sep="\t")
        df["Age"] = 2024 - df["Year_Birth"]
        df["Spending"] = df[
            ["MntWines", "MntFruits", "MntMeatProducts",
             "MntFishProducts", "MntSweetProducts", "MntGoldProds"]
        ].sum(axis=1)
        return df
    except Exception as e:
        st.error(f"Error loading Customer data: {e}")
        return None


@st.cache_data
def load_houses():
    """Load house sales data."""
    file_path = Path("kc_house_data.csv")
    if not file_path.exists():
        return None
    try:
        df = pd.read_csv(file_path)
        df["date"] = pd.to_datetime(df["date"])
        df["price_per_sqft"] = df["price"] / df["sqft_living"]
        return df
    except Exception as e:
        st.error(f"Error loading House Sales data: {e}")
        return None


# ─── Tab Layout ───

tab1, tab2, tab3 = st.tabs([
    "🏅 Olympics History",
    "👥 Customer Personality",
    "🏠 House Sales"
])

# ──────────────────────────────────────────
# Tab 1: Olympics History
# ──────────────────────────────────────────
with tab1:
    df_olympics = load_olympics()
    if df_olympics is None:
        st.warning(
            "⚠️ `athlete_events.csv` not found. "
            "Please upload it to your repository root.",
            icon="⚠️"
        )
        st.info(
            "Download from Kaggle: "
            "[120 Years of Olympic History](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results)"
        )
    else:
        st.subheader("🏅 Olympics History Dashboard")
        st.dataframe(df_olympics.head())

        # Medal counts by year
        medal_counts = (
            df_olympics[df_olympics["Medal"] != "No Medal"]
            .groupby(["Year", "Medal"])
            .size()
            .reset_index(name="Count")
        )
        fig = px.bar(
            medal_counts,
            x="Year", y="Count", color="Medal",
            title="Medal Counts Over Years",
            color_discrete_map={
                "Gold": "gold", "Silver": "silver", "Bronze": "#cd7f32"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────
# Tab 2: Customer Personality
# ──────────────────────────────────────────
with tab2:
    df_customer = load_customer()
    if df_customer is None:
        st.warning(
            "⚠️ `marketing_campaign.csv` not found. "
            "Please upload it to your repository root.",
            icon="⚠️"
        )
        st.info(
            "Download from Kaggle: "
            "[Customer Personality Analysis](https://www.kaggle.com/datasets/imakash3011/customer-personality-analysis)"
        )
    else:
        st.subheader("👥 Customer Personality Dashboard")
        st.dataframe(df_customer.head())

        fig = px.scatter(
            df_customer, x="Income", y="Spending",
            color="Education", title="Income vs Spending",
            hover_data=["Age"]
        )
        st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────
# Tab 3: House Sales
# ──────────────────────────────────────────
with tab3:
    df_houses = load_houses()
    if df_houses is None:
        st.warning(
            "⚠️ `kc_house_data.csv` not found. "
            "Please upload it to your repository root.",
            icon="⚠️"
        )
        st.info(
            "Download from Kaggle: "
            "[House Sales in King County](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction)"
        )
    else:
        st.subheader("🏠 House Sales Dashboard")
        st.dataframe(df_houses.head())

        fig = px.scatter_mapbox(
            df_houses,
            lat="lat", lon="long",
            color="price", size="sqft_living",
            mapbox_style="open-street-map",
            title="House Prices Map",
            zoom=8
        )
        st.plotly_chart(fig, use_container_width=True)
