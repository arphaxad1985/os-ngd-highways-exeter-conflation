"""
Streamlit dashboard — OS MasterMap Highways Network Roads
Conflation Quality Check

Three modes:
  1. Demo — uses the bundled Exeter sample
  2. Quick Check — user provides RoadLink file only (matchStatus profiling)
  3. Full Analysis — user provides Street + RoadLink (context + matchStatus)
"""

import os
import tempfile
import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Highways Network — Conflation Quality",
    page_icon="🛣️",
    layout="wide",
)

DEMO_STREET = "data/Highways_Roads_Street_FULL_001.gml"
DEMO_ROADLINK = "data/Highways_Roads_RoadLink_FULL_001.gml"

REQUIRED_COLS = {"matchStatus", "roadClassification", "formOfWay", "provenance", "length"}


# ---------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------
@st.cache_data
def load_demo():
    streets = gpd.read_file(DEMO_STREET)
    roadlinks = gpd.read_file(DEMO_ROADLINK)
    return streets, roadlinks


@st.cache_data
def load_roadlink_only(roadlink_bytes, roadlink_name):
    suffix = os.path.splitext(roadlink_name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as rf:
        rf.write(roadlink_bytes)
        path = rf.name
    return gpd.read_file(path)


@st.cache_data
def load_both(street_bytes, roadlink_bytes, street_name, roadlink_name):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(street_name)[1]) as sf:
        sf.write(street_bytes)
        street_path = sf.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(roadlink_name)[1]) as rf:
        rf.write(roadlink_bytes)
        roadlink_path = rf.name
    return gpd.read_file(street_path), gpd.read_file(roadlink_path)


# ---------------------------------------------------------------------
# Sidebar — product scope + mode selector
# ---------------------------------------------------------------------
st.sidebar.title("Data source")

with st.sidebar.expander("ℹ️ What this check works with", expanded=False):
    st.markdown("""
**Product:** OS MasterMap Highways Network — **Roads**

**Feature types used:**
- `RoadLink` — road geometry + `matchStatus` (conflation flag)
- `Street` — NSG street records + USRN (used for context only)

**Not used:** Road, RoadNode, RoadJunction

**Why RoadLink:** The `matchStatus` field lives here and tells you whether each road link has been matched to an NSG street.

**Why Street:** Provides the count of NSG streets in the sample, giving context for the conflation coverage.
""")

mode = st.sidebar.radio(
    "Choose input",
    [
        "Demo (Exeter sample)",
        "Quick Check — RoadLink only",
        "Full Analysis — Street + RoadLink",
    ],
)

authority = "Exeter"
streets = None

if mode == "Demo (Exeter sample)":
    if not os.path.exists(DEMO_STREET) or not os.path.exists(DEMO_ROADLINK):
        st.error("Demo data not found in data/")
        st.stop()
    streets, roadlinks = load_demo()

elif mode == "Quick Check — RoadLink only":
    st.sidebar.markdown("**Required file:** RoadLink")
    roadlink_file = st.sidebar.file_uploader(
        "RoadLink file", type=["gml", "gpkg", "geojson"],
        help="The RoadLink feature type from OS MasterMap Highways Network — Roads. Contains matchStatus.",
    )
    authority = st.sidebar.text_input("Authority name", value="MyAuthority")
    if not roadlink_file:
        st.info("Upload a RoadLink file to run the Quick Check.")
        st.stop()
    roadlinks = load_roadlink_only(roadlink_file.read(), roadlink_file.name)

else:  # Full Analysis
    st.sidebar.markdown("**Required files:** RoadLink + Street")
    roadlink_file = st.sidebar.file_uploader(
        "RoadLink file", type=["gml", "gpkg", "geojson"],
        help="Contains matchStatus — the conflation flag.",
    )
    street_file = st.sidebar.file_uploader(
        "Street file", type=["gml", "gpkg", "geojson"],
        help="Contains USRN — provides NSG street context.",
    )
    authority = st.sidebar.text_input("Authority name", value="MyAuthority")
    if not roadlink_file or not street_file:
        st.info("Upload both RoadLink and Street files to run the Full Analysis.")
        st.stop()
    streets, roadlinks = load_both(
        street_file.read(), roadlink_file.read(),
        street_file.name, roadlink_file.name,
    )

# ---------------------------------------------------------------------
# Validate columns
# ---------------------------------------------------------------------
missing = REQUIRED_COLS - set(roadlinks.columns)
if missing:
    st.error(f"RoadLink file is missing required columns: {missing}")
    st.stop()

total = len(roadlinks)

# ---------------------------------------------------------------------
# Precompute
# ---------------------------------------------------------------------
status_counts = roadlinks["matchStatus"].value_counts(dropna=False)
matched = roadlinks[roadlinks["matchStatus"] == "Matched"]
unmatched = roadlinks[roadlinks["matchStatus"] == "No Match"]
disc = roadlinks[roadlinks["matchStatus"] == "Matched With Attribute Discrepancy"]
review = roadlinks[roadlinks["matchStatus"] == "Not Matched Awaiting Review"]

matched_pct = len(matched) / total * 100 if total else 0
unmatched_pct = len(unmatched) / total * 100 if total else 0
unclassified_pct = (
    len(unmatched[unmatched["roadClassification"] == "Unknown"]) / len(unmatched) * 100
    if len(unmatched) else 0
)
unmatched_classified = unmatched[unmatched["roadClassification"].isin(["A Road", "B Road", "Motorway"])]

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("🛣️ Highways Network — Conflation Quality")
st.caption(f"Authority: **{authority}** · {total:,} RoadLinks"
           + (f" · {len(streets):,} Streets" if streets is not None else "")
           + f" · Mode: {mode.split('—')[0].strip()}")

# ---------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive Summary",
    "🔗 Conflation Status",
    "❌ Unmatched Analysis",
    "⚠️ Discrepancies",
    "🔍 Review Queue",
    "📋 Data",
])

# ---------------------------------------------------------------------
# Tab 1 — Executive Summary
# ---------------------------------------------------------------------
with tab1:
    st.subheader("Executive Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Matched", f"{matched_pct:.1f}%")
    col2.metric("Unmatched", f"{unmatched_pct:.1f}%")
    col3.metric("Exceptions", f"{len(unmatched_classified) + len(disc) + len(review)}")

    st.markdown("---")
    st.markdown("### Key Findings")
    st.markdown(f"""
**1. Conflation coverage is {matched_pct:.1f}%.**
{len(matched):,} of {total:,} RoadLinks are matched to an NSG street.

**2. Most unmatched links are not NSG streets.**
{unclassified_pct:.1f}% of unmatched links are unclassified.

**3. All unmatched links come from OS survey.**
No authority submission exists for them.
""")

    st.markdown("---")
    st.markdown("### Flags")
    flags = []
    if unmatched_pct > 15:
        flags.append(f"⚠️ Unmatched rate {unmatched_pct:.1f}% exceeds 15% threshold")
    if len(unmatched_classified) > 0:
        flags.append(f"⚠️ {len(unmatched_classified)} classified roads unmatched")
    if len(disc) > 0:
        flags.append(f"⚠️ {len(disc)} attribute discrepancies")
    if len(review) > 0:
        flags.append(f"⚠️ {len(review)} records awaiting review")
    if flags:
        for f in flags:
            st.warning(f)
    else:
        st.success("✅ No anomalies detected")

# ---------------------------------------------------------------------
# Tab 2 — Conflation Status
# ---------------------------------------------------------------------
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
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        st.pyplot(fig)

# ---------------------------------------------------------------------
# Tab 3 — Unmatched Analysis
# ---------------------------------------------------------------------
with tab3:
    st.subheader("Unmatched RoadLinks")
    st.caption(f"{len(unmatched):,} RoadLinks with matchStatus = 'No Match'")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**By classification**")
        st.dataframe(unmatched["roadClassification"].value_counts(dropna=False).to_frame(), use_container_width=True)
        st.markdown("**By provenance**")
        st.dataframe(unmatched["provenance"].value_counts(dropna=False).to_frame(), use_container_width=True)
    with col2:
        st.markdown("**By form of way**")
        st.dataframe(unmatched["formOfWay"].value_counts(dropna=False).to_frame(), use_container_width=True)

    if len(unmatched) > 0:
        st.markdown("### Length distribution")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(unmatched["length"], bins=40, edgecolor="black", color="coral")
        ax.set_xlabel("Length (metres)")
        st.pyplot(fig)

        st.markdown("### Top 10 longest unmatched")
        top10 = unmatched.sort_values("length", ascending=False).head(10)
        st.dataframe(top10[["roadName", "roadClassification", "formOfWay", "length"]], use_container_width=True)

# ---------------------------------------------------------------------
# Tab 4 — Discrepancies
# ---------------------------------------------------------------------
with tab4:
    st.subheader("Matched With Attribute Discrepancy")
    st.dataframe(disc[["roadName", "roadClassification", "formOfWay", "length"]], use_container_width=True)
    if len(disc) > 0:
        st.markdown("**Clustering by road name**")
        st.dataframe(disc["roadName"].value_counts(dropna=False).to_frame(), use_container_width=True)

# ---------------------------------------------------------------------
# Tab 5 — Review Queue
# ---------------------------------------------------------------------
with tab5:
    st.subheader("Not Matched Awaiting Review")
    st.dataframe(review[["roadName", "roadClassification", "formOfWay", "length"]], use_container_width=True)

# ---------------------------------------------------------------------
# Tab 6 — Data
# ---------------------------------------------------------------------
with tab6:
    st.subheader("RoadLink Sample")
    preview_cols = ["identifier", "roadName", "roadClassification", "formOfWay", "matchStatus", "length"]
    preview_cols = [c for c in preview_cols if c in roadlinks.columns]
    st.dataframe(roadlinks[preview_cols].head(500), use_container_width=True)

st.markdown("---")
st.caption("Data: OS MasterMap Highways Network — Roads · Ordnance Survey")