import awkward as ak

version = "V32nano"
sample = "Hgg"
pattern = f"cache/f{version}/{version}_{sample}_%s.parquet"
objects = ["L1EGbarrel","L1EGendcap"]
target_object = "L1EG"

print(f"Reading files as {pattern} for {objects}")
# arrs = [ak.from_parquet(pattern%obj) for obj in objects]
## rename fields to be consistent
# arrs [ak.zip({f.replace(obj):arr[f] for f in arr.fields}) for arr in arrs]
arrs = []

for obj in objects:
    arr = ak.from_parquet(pattern%obj)
    arr = ak.Array({f.replace(obj,target_object):arr[f] for f in arr.fields})
    print(obj, arr.fields)
    arrs.append(arr)

# reprocess -> ak.unzip
# arrs = [ak.Array(dict(zip([f.split("_")[-1] for f in arr.fields],ak.unzip(arr)))) for arr in arrs]
print("Merging")
merge_arr = ak.concatenate(arrs, axis=1)
print(merge_arr)
print(f"Writing merged array to: {pattern%target_object}")
ak.to_parquet(merge_arr, pattern%target_object)
