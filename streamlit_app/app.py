import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="LA Health Expansion Index",
    page_icon="🏥",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("la_expansion_index_v2.csv")
    df["zip_code"] = df["zip_code"].astype(str).str.zfill(5)
    return df

df = load_data()

st.title("🏥 LA Community Health Expansion Index")
st.write(
    "This dashboard helps identify LA ZIP codes where new community health centers may be most needed."
)

# Sidebar filters
st.sidebar.header("Filters")

top_n = st.sidebar.slider("Number of top ZIPs", 5, 50, 10)

poverty_range = st.sidebar.slider(
    "Poverty Rate Range",
    float(df["poverty_rate"].min()),
    float(df["poverty_rate"].max()),
    (float(df["poverty_rate"].min()), float(df["poverty_rate"].max()))
)

clinic_range = st.sidebar.slider(
    "Clinic Density Range",
    float(df["clinic_density"].min()),
    float(df["clinic_density"].max()),
    (float(df["clinic_density"].min()), float(df["clinic_density"].max()))
)

need_range = st.sidebar.slider(
    "Objective Need Score Range",
    float(df["objective_need_score"].min()),
    float(df["objective_need_score"].max()),
    (float(df["objective_need_score"].min()), float(df["objective_need_score"].max()))
)

index_range = st.sidebar.slider(
    "Expansion Index Range",
    float(df["expansion_index_v2"].min()),
    float(df["expansion_index_v2"].max()),
    (float(df["expansion_index_v2"].min()), float(df["expansion_index_v2"].max()))
)

df_filtered = df[
    (df["poverty_rate"] >= poverty_range[0]) &
    (df["poverty_rate"] <= poverty_range[1]) &
    (df["clinic_density"] >= clinic_range[0]) &
    (df["clinic_density"] <= clinic_range[1]) &
    (df["objective_need_score"] >= need_range[0]) &
    (df["objective_need_score"] <= need_range[1]) &
    (df["expansion_index_v2"] >= index_range[0]) &
    (df["expansion_index_v2"] <= index_range[1])
].copy()

top_df = df_filtered.sort_values("rank_v2").head(top_n).copy()

# User guidance
with st.expander("How to use this dashboard"):
    st.markdown("""
    **Average user:**  
    Start with the map and the top ranked ZIP codes. Higher scores mean stronger priority for health center expansion.

    **Pro user:**  
    Use the filters to test different assumptions. For example, focus only on high-poverty ZIP codes, low-clinic-density ZIP codes, or high-need ZIP codes.
    """)

# Scoring logic
with st.expander("Scoring logic and parameters"):
    st.latex(r"Expansion\ Index = f(Objective\ Need,\ Clinic\ Access,\ Poverty,\ Population)")
    st.latex(r"Access\ Gap\ Score = Objective\ Need\ Score \times (1 - Clinic\ Density)")
    st.latex(r"Higher\ Need + Lower\ Clinic\ Density = Higher\ Expansion\ Priority")

    st.markdown("""
    **Objective Need Score:** Measures healthcare demand.  
    **Clinic Density:** Measures current healthcare supply.  
    **Poverty Rate:** Helps identify communities with higher socioeconomic need.  
    **Expansion Index:** Final priority score used to rank ZIP codes.
    """)

# KPIs
col1, col2, col3, col4 = st.columns(4)

col1.metric("ZIP Codes Shown", len(df_filtered))

if len(df_filtered) > 0:
    col2.metric("Highest Priority Score", round(df_filtered["expansion_index_v2"].max(), 3))
    col3.metric("Avg Poverty Rate", f"{df_filtered['poverty_rate'].mean():.1f}%")
    col4.metric("Avg Clinic Density", round(df_filtered["clinic_density"].mean(), 2))
else:
    col2.metric("Highest Priority Score", "N/A")
    col3.metric("Avg Poverty Rate", "N/A")
    col4.metric("Avg Clinic Density", "N/A")

st.divider()

# MAP FIRST
st.subheader("LA County Expansion Priority Map")

if len(df_filtered) > 0:
    fig_map = px.choropleth(
        df_filtered,
        geojson="https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ca_california_zip_codes_geo.min.json",
        locations="zip_code",
        color="expansion_index_v2",
        featureidkey="properties.ZCTA5CE10",
        color_continuous_scale="Reds",
        scope="usa",
        labels={
            "expansion_index_v2": "Expansion Priority Score"
        },
        hover_data=[
            "zip_code",
            "population",
            "poverty_rate",
            "clinic_density",
            "objective_need_score",
            "expansion_index_v2"
        ],
        title="LA County ZIP Codes With Highest Health Expansion Priority"
    )

    fig_map.update_geos(
        fitbounds="locations",
        visible=False
    )

    fig_map.update_layout(
        height=700,
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )

    st.plotly_chart(fig_map, use_container_width=True)

    st.caption(
        "Annotation: Darker ZIP codes represent areas with stronger healthcare expansion priority."
    )
else:
    st.warning("No ZIP codes match the selected filters.")

st.divider()

# TOP TABLE
st.subheader("Top Ranked ZIP Codes")

display_cols = [
    "rank_v2",
    "zip_code",
    "population",
    "objective_need_score",
    "clinic_density",
    "nearby_clinic_count",
    "poverty_rate",
    "median_household_income",
    "expansion_index_v2"
]

if len(top_df) > 0:
    st.dataframe(
        top_df[display_cols],
        use_container_width=True,
        height=400
    )

    st.caption("Annotation: Rank 1 represents the ZIP code with the highest expansion priority.")
else:
    st.info("No ranked ZIP codes to display with the current filters.")

st.divider()

# CLEAN BAR VISUALS
colA, colB = st.columns(2)

with colA:
    st.subheader("High-Need ZIP Codes With Low Clinic Access")

    if len(df_filtered) > 0:
        access_gap_df = df_filtered.copy()
        access_gap_df["access_gap_score"] = (
            access_gap_df["objective_need_score"] * (1 - access_gap_df["clinic_density"])
        )

        access_gap_top = access_gap_df.sort_values(
            "access_gap_score", ascending=False
        ).head(10)

        fig1 = px.bar(
            access_gap_top.sort_values("access_gap_score", ascending=True),
            x="access_gap_score",
            y="zip_code",
            orientation="h",
            color="poverty_rate",
            title="ZIP Codes With High Need and Limited Clinic Access",
            labels={
                "access_gap_score": "Access Gap Score",
                "zip_code": "ZIP Code",
                "poverty_rate": "Poverty Rate (%)"
            },
            hover_data=[
                "population",
                "objective_need_score",
                "clinic_density",
                "nearby_clinic_count",
                "expansion_index_v2"
            ]
        )

        fig1.update_yaxes(type="category")
        fig1.update_layout(height=430)
        st.plotly_chart(fig1, use_container_width=True)

        st.caption(
            "Annotation: This chart highlights ZIP codes with high objective need and low clinic density."
        )
    else:
        st.info("No data available for this visual with the current filters.")

with colB:
    st.subheader("Highest Poverty ZIP Codes With Strong Expansion Need")

    if len(df_filtered) > 0:
        poverty_df = df_filtered.sort_values(
            "poverty_rate", ascending=False
        ).head(10)

        fig2 = px.bar(
            poverty_df.sort_values("poverty_rate", ascending=True),
            x="poverty_rate",
            y="zip_code",
            orientation="h",
            color="expansion_index_v2",
            title="High Poverty Areas With Strong Expansion Priority",
            labels={
                "poverty_rate": "Poverty Rate (%)",
                "zip_code": "ZIP Code",
                "expansion_index_v2": "Expansion Index"
            },
            hover_data=[
                "population",
                "clinic_density",
                "objective_need_score",
                "nearby_clinic_count"
            ]
        )

        fig2.update_yaxes(type="category")
        fig2.update_layout(height=430)
        st.plotly_chart(fig2, use_container_width=True)

        st.caption(
            "Annotation: ZIP codes with higher poverty rates and stronger expansion scores may require additional healthcare investment."
        )
    else:
        st.info("No data available for this visual with the current filters.")

st.divider()

# BAR CHART AT BOTTOM
st.subheader("Top Priority ZIP Codes Visual")

if len(top_df) > 0:
    bar_fig = px.bar(
        top_df.sort_values("expansion_index_v2", ascending=True),
        x="expansion_index_v2",
        y="zip_code",
        orientation="h",
        color="expansion_index_v2",
        title="Highest Priority ZIP Codes for Health Expansion",
        labels={
            "expansion_index_v2": "Expansion Priority Score",
            "zip_code": "ZIP Code"
        },
        hover_data=[
            "population",
            "poverty_rate",
            "clinic_density",
            "nearby_clinic_count"
        ]
    )

    bar_fig.update_yaxes(type="category")
    bar_fig.update_layout(height=500)
    st.plotly_chart(bar_fig, use_container_width=True)

    st.caption(
        "Annotation: This chart summarizes the highest-priority ZIP codes after filters are applied."
    )
else:
    st.info("No top ZIP codes to display with the current filters.")

