#!/bin/bash

INPUT=$1
OUTPUT=$2
VOLD=V45nano
VNEW=V49nano

mkdir -p cache/"$OUTPUT"

for file in cache/"$INPUT"/*.parquet; do
    basename=$(basename "$file")
    newname=${basename/$VOLD/$VNEW}
    ln -s "$(realpath "$file")" "cache/$OUTPUT/$newname"
done
