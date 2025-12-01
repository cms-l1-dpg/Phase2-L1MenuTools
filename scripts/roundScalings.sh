#!/bin/bash

for f in L1*.yaml; do
  awk '
    /^offset:/ {
      printf("offset: %.2f\n", $2);
      next
    }
    /^slope:/ {
      printf("slope: %.2f\n", $2);
      next
    }
    { print }
  ' "$f" > tmpfile && mv tmpfile "$f"
done
