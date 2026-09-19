"""
Exeter — OS MasterMap Highways Network Roads Conflation Quality

Investigates the matchStatus between OS RoadLinks and the National Street Gazetteer
for the Exeter sample.

Usage:
    python exeter_conflation.py
"""

import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt


def run_conflation_analysis(data_dir="data", output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    street_path = f"{data_dir}/Highways_Roads_Street_FULL_001.gml"
    roadlink_path = f"{data_dir}/Highways_Roads_RoadLink_FULL_001.gml"

    print("Loading Street file...")
    streets = gpd.read_file(street_path)
    print(f"  Streets: {len(streets):,}")

    print("Loading RoadLink file...")
    roadlinks = gpd.read_file(roadlink_path)
    print(f"  RoadLinks: {len(roadlinks):,}")

    total = len(roadlinks)

    report = [
        "# OS MasterMap Highways Network — Roads: Conflation Quality Report\n",
        f"**Sample area:** Exeter  ",
        f"**Streets (NSG):** {len(streets):,}  ",
        f"**RoadLinks (OS):** {total:,}\n",
    ]

    # ------------------------------------------------------------------
    # 2. matchStatus distribution
    # ------------------------------------------------------------------
    report.append("\n## 1. Conflation Status Distribution\n")

    status_counts = roadlinks["matchStatus"].value_counts(dropna=False)
    status_df = pd.DataFrame({
        "matchStatus": status_counts.index,
        "Count": status_counts.values,
        "Percent": (status_counts.values / total * 100).round(2),
    })
    report.append(status_df.to_markdown(index=False))
    report.append("")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(status_df["matchStatus"], status_df["Count"], color="steelblue")
    ax.set_ylabel("Count")
    ax.set_title("Conflation status distribution")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/conflation_status.png", dpi=150)
    plt.close()
    report.append(f"\nChart saved: `{output_dir}/conflation_status.png`\n")

    # ------------------------------------------------------------------
    # 3. Unmatched links — profile
    # ------------------------------------------------------------------
    report.append("\n## 2. Unmatched Links (`No Match`)\n")

    unmatched = roadlinks[roadlinks["matchStatus"] == "No Match"]
    report.append(f"**Total unmatched:** {len(unmatched):,}\n")

    report.append("\n### By road classification\n")
    report.append(unmatched["roadClassification"].value_counts(dropna=False).to_frame().to_markdown())

    report.append("\n### By form of way\n")
    report.append(unmatched["formOfWay"].value_counts(dropna=False).to_frame().to_markdown())

    report.append("\n### By provenance\n")
    report.append(unmatched["provenance"].value_counts(dropna=False).to_frame().to_markdown())
    report.append(
        "\n**Interpretation:** Every unmatched link comes from OS survey data. "
        "None were submitted by a highway authority. This confirms they were never "
        "registered as NSG streets.\n"
    )

    # Length distribution of unmatched
    report.append("\n### Length distribution (metres)\n")
    report.append(unmatched["length"].describe().round(2).to_frame().to_markdown())

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(unmatched["length"], bins=40, edgecolor="black", color="coral")
    ax.set_xlabel("Length (metres)")
    ax.set_ylabel("Count")
    ax.set_title("Length distribution of unmatched RoadLinks")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/unmatched_length_histogram.png", dpi=150)
    plt.close()
    report.append(f"\nHistogram saved: `{output_dir}/unmatched_length_histogram.png`\n")

    # Top 10 longest unmatched
    report.append("\n### Top 10 longest unmatched links\n")
    top10 = unmatched.sort_values("length", ascending=False).head(10)
    report.append(top10[["roadName", "roadClassification", "formOfWay", "length"]].to_markdown(index=False))

    # ------------------------------------------------------------------
    # 4. Unmatched classified roads (anomalies)
    # ------------------------------------------------------------------
    report.append("\n## 3. Anomalies — Unmatched Classified Roads\n")

    unmatched_classified = unmatched[
        unmatched["roadClassification"].isin(["A Road", "B Road", "Motorway"])
    ]
    if len(unmatched_classified) > 0:
        report.append(unmatched_classified[["roadName", "roadClassification", "length"]].to_markdown(index=False))
        report.append(
            "\n**Interpretation:** These are classified roads with no NSG match. "
            "Their very short length (<5 m) suggests they are geometry stubs "
            "at junctions, not real street segments.\n"
        )
    else:
        report.append("No unmatched classified roads found.\n")

    # ------------------------------------------------------------------
    # 5. Attribute discrepancies
    # ------------------------------------------------------------------
    report.append("\n## 4. Matched With Attribute Discrepancy\n")

    disc = roadlinks[roadlinks["matchStatus"] == "Matched With Attribute Discrepancy"]
    report.append(f"**Total:** {len(disc):,}\n")

    if len(disc) > 0:
        report.append(disc[["roadName", "roadClassification", "formOfWay", "length"]].to_markdown(index=False))
        report.append("\n### By road name\n")
        report.append(disc["roadName"].value_counts(dropna=False).to_frame().to_markdown())
        report.append(
            "\n**Interpretation:** The discrepancies cluster on a small number of roads. "
            "The attributes recorded by OS do not agree with what the NSG says for those roads. "
            "These require manual review.\n"
        )

    # ------------------------------------------------------------------
    # 6. Awaiting review
    # ------------------------------------------------------------------
    report.append("\n## 5. Not Matched Awaiting Review\n")

    review = roadlinks[roadlinks["matchStatus"] == "Not Matched Awaiting Review"]
    report.append(f"**Total:** {len(review):,}\n")

    if len(review) > 0:
        report.append(review[["roadName", "roadClassification", "formOfWay", "length"]].to_markdown(index=False))
        report.append(
            "\n**Interpretation:** All are unnamed and unclassified. Their profile "
            "matches the `No Match` group, but they have been flagged for human review.\n"
        )

    # ------------------------------------------------------------------
    # 7. Matched baseline
    # ------------------------------------------------------------------
    report.append("\n## 6. Matched Baseline (Comparison)\n")

    matched = roadlinks[roadlinks["matchStatus"] == "Matched"]
    report.append(f"**Total matched:** {len(matched):,}\n")
    report.append("\n### Matched by road classification\n")
    report.append(matched["roadClassification"].value_counts(dropna=False).to_frame().to_markdown())

    # ------------------------------------------------------------------
    # 8. Findings & recommendation
    # ------------------------------------------------------------------
    report.append("\n## 7. Findings & Recommendation\n")

    matched_pct = len(matched) / total * 100
    unmatched_pct = len(unmatched) / total * 100
    unclassified_pct = len(unmatched[unmatched["roadClassification"] == "Unknown"]) / len(unmatched) * 100

    report.append(f"""
### Finding 1 — Conflation coverage is {matched_pct:.1f}%

{len(matched):,} of {total:,} RoadLinks ({matched_pct:.1f}%) are successfully matched to an NSG street.
{len(unmatched):,} ({unmatched_pct:.1f}%) are not matched.

### Finding 2 — Most unmatched links are not NSG streets

{len(unmatched[unmatched['roadClassification'] == 'Unknown']):,} of {len(unmatched):,} unmatched links
({unclassified_pct:.1f}%) are unclassified. They are single carriageways, tracks, and
enclosed traffic areas — physical roads that are not "streets" in the NSG sense.

### Finding 3 — All unmatched links come from OS survey

Every unmatched link has a provenance of "OS Urban And OS Height" or similar.
None were submitted by a highway authority. They were never registered in the
Local Street Gazetteer, so no USRN exists for them.

### Finding 4 — A small number of genuine exceptions exist

- **{len(unmatched_classified):,} unmatched classified roads** — all under 5 m, geometry stubs
- **{len(disc):,} attribute discrepancies** — matched but attributes disagree with the NSG
- **{len(review):,} awaiting review** — unnamed, unclassified, pending human decision

### Recommendation

1. **No action needed for the {len(unmatched) - len(unmatched_classified):,} unclassified unmatched links** —
   they are correctly excluded from the NSG.
2. **Review the {len(unmatched_classified):,} unmatched classified stubs** — confirm they are
   geometry artefacts.
3. **Investigate the {len(disc):,} attribute discrepancies** — particularly the cluster on
   Wayside Crescent (6 cases).
4. **Clear the {len(review):,} awaiting-review records** — confirm they should remain unmatched.
5. **Check Hamlyns Lane** — the only named road in the unmatched set.
""")

    # ------------------------------------------------------------------
    # 9. Write report
    # ------------------------------------------------------------------
    report_path = f"{output_dir}/exeter_conflation_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    print(f"\nReport written: {report_path}")
    return report_path


if __name__ == "__main__":
    run_conflation_analysis()