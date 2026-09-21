import geopandas as gpd
import matplotlib.pyplot as plt

roadlinks = gpd.read_file("data/Highways_Roads_RoadLink_FULL_001.gml")

colors = {
    "Matched": "lightgrey",
    "No Match": "red",
    "Matched With Attribute Discrepancy": "purple",
    "Not Matched Awaiting Review": "gold",
}

# Map 1 — full network
fig, ax = plt.subplots(figsize=(14, 14))
for status, color in colors.items():
    subset = roadlinks[roadlinks["matchStatus"] == status]
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, linewidth=0.4, label=f"{status} ({len(subset):,})")

ax.set_title("Exeter RoadLinks by matchStatus", fontsize=16)
ax.legend(loc="upper right", fontsize=10)
ax.set_axis_off()
plt.tight_layout()
plt.savefig("figures/python_matchstatus_map.png", dpi=200, bbox_inches="tight")
plt.close()
print("Saved: figures/python_matchstatus_map.png")

# Map 2 — unmatched only
unmatched = roadlinks[roadlinks["matchStatus"] == "No Match"]
fig, ax = plt.subplots(figsize=(14, 14))
unmatched.plot(ax=ax, color="red", linewidth=0.6)
ax.set_title(f"Unmatched RoadLinks ({len(unmatched):,})", fontsize=16)
ax.set_axis_off()
plt.tight_layout()
plt.savefig("figures/python_unmatched_only.png", dpi=200, bbox_inches="tight")
plt.close()
print("Saved: figures/python_unmatched_only.png")
