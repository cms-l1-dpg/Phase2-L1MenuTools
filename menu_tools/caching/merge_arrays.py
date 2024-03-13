import awkward as ak

version = "V33nano"
sample = "MinBias"
# sample = "Hgg"
pattern = f"cache/{version}/{version}_{sample}_%s.parquet"
objects = ["L1EGbarrel", "L1EGendcap"]
target_object = "L1EG"

print(f"Reading files as {pattern} for {objects}")
arrs = []

for obj in objects:
    arr = ak.from_parquet(pattern % obj)
    arr = ak.Array({f.replace(obj, target_object): arr[f] for f in arr.fields})
    # apply 5 gev cut
    arr = arr[arr[f"{target_object}_pt"] > 5]
    print(obj, arr.fields)
    arrs.append(arr)

print("Merging")
merge_arr = ak.concatenate(arrs, axis=1)
print(merge_arr)
print(f"Writing merged array to: {pattern%target_object}")
ak.to_parquet(merge_arr, pattern % target_object)
