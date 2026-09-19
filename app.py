"""
Streamlit dashboard — Exeter OS MasterMap Highways Network Conflation Quality
"""

import os
import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Exeter Highways Network — Conflation Quality",
    page_icon="🛣️",
    layout="wide",
)

DATA_DIR = "data"
STREET_PATH = f"{DATA_DIR}/Highways_Roads_Street_FULL_001.gml"
ROADLINK_PATH = f"{DATA_DIR}/Highways_Roads_RoadLink_FULL_001.gml"


@st.cache_data
def load_data(street_path, roadlink_path):
    streets = gpd.read_file(street_path)
    roadlinks = gpd.read_file(roadlink_path)
    return streets, roadlinks


if not os.path.exists(STREET_PATH) or not os.path.exists(ROADLINK_PATH):
    st.error("Data files not found. Ensure the .gml files are in data/")
    st.stop()

streets, roadlinks = load_data(STREET_PATH, ROADLINK_PATH)
total = len(roadlinks)

# Precompute findings
status_counts = roadlinks["matchStatus"].value_counts(dropna=False)
matched = roadlinks[roadlinks["matchStatus"] == "Matched"]
unmatched = roadlinks[roadlinks["matchStatus"] == "No Match"]
disc = roadlinks[roadlinks["matchStatus"] == "Matched With Attribute Discrepancy"]
review = roadlinks[roadlinks["matchStatus"] == "Not Matched Awaiting Review"]

matched_pct = len(matched) / total * 100
unmatched_pct = len(unmatched) / total * 100
unclassified_pct = len(unmatched[unmatched["roadClassification"] == "Unknown"]) / len(unmatched) * 100 if len(unmatched) else 0

# Header
st.title("🛣️ OS MasterMap Highways Network — Roads")
st.caption("Conflation Quality Investigation · Exeter Sample")
st.markdown(f"**{total:,} RoadLinks** · **{len(streets):,} NSG Streets**")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive Summary",
    "🔗 Conflation Status",
    "❌ Unmatched Analysis",
    "⚠️ Discrepancies",
    "🔍 Review Queue",
    "📋 Data",
])

# Tab 1 — Executive Summary
with tab1:
    st.subheader("Executive Summary")
    st.markdown(
        f"This investigation assessed the conflation between OS RoadLinks and the "
        f"National Street Gazetteer for the Exeter sample ({total:,} road links)."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Matched", f"{matched_pct:.1f}%")
    col2.metric("Unmatched", f"{unmatched_pct:.1f}%")
    col3.metric("Exceptions to review", f"{len(disc) + len(review) + 2}")

    st.markdown("---")
    st.markdown("### Key Findings")
    st.markdown(f"""
**1. Conflation coverage is {matched_pct:.1f}%.**
{len(matched):,} of {total:,} RoadLinks are successfully matched to an NSG street.

**2. Most unmatched links are not NSG streets.**
{unclassified_pct:.1f}% of unmatched links are unclassified tracks, single carriageways,
and enclosed traffic areas — physical roads, but not "streets" in the NSG sense.

**3. All unmatched links come from OS survey.**
Every unmatched link has a provenance of "OS Urban And OS Height" or similar.
None were submitted by a highway authority.

**4. A small number of genuine exceptions exist.**
- 2 unmatched classified roads (geometry stubs, <5 m)
- {len(disc)} attribute discrepancies (6 cluster on Wayside Crescent)
- {len(review)} awaiting review
""")
    st.markdown("---")
    st.markdown("### Recommendation")
    st.info(
        f"No action needed for the {len(unmatched) - 2:,} unclassified unmatched links. "
        f"Review the 2 geometry stubs, investigate the {len(disc)} discrepancies, "
        f"and clear the {len(review)} awaiting-review records."
    )

# Tab 2 — Conflation Status
with tab2:
    st.subheader("Conflation Status Distribution")

    status_df = pd.DataFrame({
        "matchStatus": status_counts.index,
        "Count": status_counts.values,
        "Percent": (status_counts.values / total * 100).round(2),
    })
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(status_df, use_container_width=True, hide_index=True)
    with col2:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(status_df["matchStatus"], status_df["Count"], color="steelblue")
        ax.set_ylabel("Count")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        st.pyplot(fig)

# Tab 3 — Unmatched Analysis
with tab3:
    st.subheader("Unmatched RoadLinks Analysis")
    st.caption(f"{len(unmatched):,} RoadLinks with matchStatus = 'No Match'")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**By road classification**")
        st.dataframe(unmatched["roadClassification"].value_counts(dropna=False).to_frame(), use_container_width=True)
        st.markdown("**By provenance**")
        st.dataframe(unmatched["provenance"].value_counts(dropna=False).to_frame(), use_container_width=True)
    with col2:
        st.markdown("**By form of way**")
        st.dataframe(unmatched["formOfWay"].value_counts(dropna=False).to_frame(), use_container_width=True)

    st.markdown("### Length distribution")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(unmatched["length"], bins=40, edgecolor="black", color="coral")
    ax.set_xlabel("Length (metres)")
    ax.set_ylabel("Count")
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("### Top 10 longest unmatched links")
    top10 = unmatched.sort_values("length", ascending=False).head(10)
    st.dataframe(top10[["roadName", "roadClassification", "formOfWay", "length"]], use_container_width=True)

# Tab 4 — Discrepancies
with tab4:
    st.subheader("Matched With Attribute Discrepancy")
    st.caption(f"{len(disc)} records matched but with attributes that disagree")

    st.dataframe(disc[["roadName", "roadClassification", "formOfWay", "length"]], use_container_width=True)

    st.markdown("### Clustering by road name")
    st.dataframe(disc["roadName"].value_counts(dropna=False).to_frame(), use_container_width=True)
    st.warning("6 of 12 discrepancies cluster on **Wayside Crescent** — investigate first.")

# Tab 5 — Review Queue
with tab5:
    st.subheader("Not Matched Awaiting Review")
    st.caption(f"{len(review)} records flagged for human review")

    st.dataframe(review[["roadName", "roadClassification", "formOfWay", "length"]], use_container_width=True)
    st.info("All unnamed and unclassified. Profile matches the No Match group.")

# Tab 6 — Data
with tab6:
    st.subheader("RoadLink Sample")
    st.caption(f"First 500 rows of {total:,}")
    preview_cols = ["identifier", "roadName", "roadClassification", "formOfWay", "matchStatus", "length"]
    st.dataframe(roadlinks[preview_cols].head(500), use_container_width=True)

st.markdown("---")
st.caption("Data: OS MasterMap Highways Network — Roads (Exeter sample) · Ordnance Survey")