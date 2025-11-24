#!/bin/sh

sample="configs/V45nano_140PU/object_performance"

for file in $sample/*; do
    object_performance $file
    echo "ran $file"
done
