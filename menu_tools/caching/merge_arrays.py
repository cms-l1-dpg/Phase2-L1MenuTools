import awkward as ak
import argparse
import os

# Set up argument parser
parser = argparse.ArgumentParser(description='Merge parquet files with custom version and sample')
parser.add_argument('--version', type=str, default="V45nano", help='Version to use')
parser.add_argument('--sample', type=str, default="Hgg", help='Sample to use')
args = parser.parse_args()

version = args.version
sample = args.sample
pattern = f"cache/{version}/{version}_{sample}_%s.parquet"
objects = ["L1EGbarrel", "L1EGendcap"]
target_object = "L1EG"
target_file = pattern % target_object

# Check if target file already exists
if os.path.exists(target_file):
    print(f"Target file {target_file} already exists, skipping merge")
else:
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
        print(f"Writing merged array to: {target_file}")
        ak.to_parquet(merge_arr, target_file)
