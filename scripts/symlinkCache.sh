#!/bin/bash

INPUT=$1
OUTPUT=$2
UPDATEYAML=TRUE
# VOLD=V45nano
# VNEW=V49nano

mkdir -p cache/"$OUTPUT"

for file in cache/"$INPUT"/*.parquet; do
    basename=$(basename "$file")
    newname=${basename/$INPUT/$OUTPUT}
    ln -s "$(realpath "$file")" "cache/$OUTPUT/$newname"
done

if [[ $UPDATEYAML == "TRUE" ]]; then
    echo "Updating caching yaml"
    cp configs/$INPUT/caching.yaml configs/$OUTPUT/.
    grep -rl "$INPUT" configs/$OUTPUT/caching.yaml | xargs sed -i "s/$INPUT/$OUTPUT/g"    
fi
# Update caching.yaml
