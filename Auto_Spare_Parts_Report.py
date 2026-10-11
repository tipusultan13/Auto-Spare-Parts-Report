# Import Libraries #

import pandas as pd
import re

# Import Data #

application_status= pd.read_csv("/Users/tipusultan/Documents/GitHub/Auto-Spare-Parts-Report/Data/application_status.csv")
applications= pd.read_csv("/Users/tipusultan/Documents/GitHub/Auto-Spare-Parts-Report/Data/applications.csv")
compatibility= pd.read_csv("/Users/tipusultan/Documents/GitHub/Auto-Spare-Parts-Report/Data/compatibility.csv")
product_category= pd.read_csv("/Users/tipusultan/Documents/GitHub/Auto-Spare-Parts-Report/Data/product_category.csv")
seller= pd.read_csv("/Users/tipusultan/Documents/GitHub/Auto-Spare-Parts-Report/Data/seller.csv")
vehicle_type= pd.read_csv("/Users/tipusultan/Documents/GitHub/Auto-Spare-Parts-Report/Data/vehicle_type.csv")
vehicles= pd.read_csv("/Users/tipusultan/Documents/GitHub/Auto-Spare-Parts-Report/Data/vehicles.csv")

## Prepare Data ##

# Join "applications + application_status" #
application_status = application_status.rename(columns={"id": "status_id"})
len(applications)
applications = applications.merge(application_status, on = "status_id", how = "left")
len(applications)
applications["status_name"].isna().mean() * 100

# Join "applications + seller" #

seller = seller.rename(columns={"id": "seller_id"})[["seller_id", "seller_name"]]
applications = applications.merge(seller, on = "seller_id", how = "left")
len(applications)
applications["status_name"].isna().mean() * 100

# Join "applications" + "vehicles_type" #

vehicle_type = vehicle_type.rename(columns={"id": "vehicle_type_id"})
applications = applications.merge(vehicle_type, on = "vehicle_type_id", how = "left")
applications["type_name"].isna().mean() * 100
len(applications)

# Generate "manufacturer" #

lookup = {
    re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", m.lower())).strip(): m
    for m in vehicles["manufacturer_name"].dropna().unique()
}
lookup.pop("", None)
pattern = r"\b(" + "|".join(map(re.escape, sorted(lookup, key=len, reverse=True))) + r")\b"
found = (
    applications["headline"]
    .str.lower()
    .str.replace(r"[^a-z0-9\s]", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.findall(pattern)
    .apply(lambda f: list(dict.fromkeys(lookup[x] for x in f)) if isinstance(f, list) else [])
)
applications["manufacturer"] = found.apply(lambda ms: " / ".join(ms) or None)
applications["model"] = (
    pd.Series(
        [
            re.sub(r"\b(" + "|".join(map(re.escape, ms)) + r")\b", " ", h, flags=re.I) if ms else None
            for h, ms in zip(applications["headline"], found)
        ],
        index=applications.index,
    )
    .str.replace(r"(\s*/\s*){2,}", " / ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip(" /")
)
applications["manufacturer"].isna().mean() * 100
applications[["manufacturer", "model"]] = applications[["manufacturer", "model"]].fillna("unknown")

# Join "application + product_category"

name = product_category.set_index("id")["category_name"]
parent = product_category.set_index("id")["parent_category_id"].astype("Int64")
cur = product_category["id"]
chain = []
while cur.notna().any():
    chain.append(cur.map(name).rename(len(chain)))
    cur = cur.map(parent)
hierarchy = (
    pd.concat(chain, axis=1)
    .apply(lambda r: r.dropna().iloc[::-1].reset_index(drop=True), axis=1)
    .rename(columns=lambda c: f"level_{c + 1}")
)
product_category = product_category.join(hierarchy)
product_category = product_category.rename(columns={"id": "category_id"})
applications = applications.merge(product_category, on = "category_id", how = "left")
len(applications)
applications["level_1"].isna().mean() * 100
applications["year"] = pd.to_datetime(applications["app_register_date"], errors="coerce").dt.year
print(applications)

# Save the progress #
#applications.to_csv("applications.csv", index=False)

# Manufacturer view # 
applications_v2 = (
    applications
    .assign(manufacturer=applications["manufacturer"].str.split(" / "))
    .explode("manufacturer")
    .reset_index(drop=True)
)

applications_v2["price_unique"] = applications_v2["price_usd"].where(~applications_v2.duplicated("app_id"), 0)
applications_v2.to_csv("applications_v2.csv", index=False)
print(applications_v2)