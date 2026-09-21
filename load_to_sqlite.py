import sqlite3
import geopandas as gpd

streets = gpd.read_file("data/Highways_Roads_Street_FULL_001.gml")
roadlinks = gpd.read_file("data/Highways_Roads_RoadLink_FULL_001.gml")

print("Streets:", len(streets))
print("RoadLinks:", len(roadlinks))

streets_attrs = streets.drop(columns="geometry")
roadlinks_attrs = roadlinks.drop(columns="geometry")

conn = sqlite3.connect("data/exeter.db")
streets_attrs.to_sql("streets", conn, if_exists="replace", index=False)
roadlinks_attrs.to_sql("roadlinks", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX IF NOT EXISTS idx_matchStatus ON roadlinks(matchStatus)")
conn.commit()
conn.close()

print("Done. Database created: data/exeter.db")
