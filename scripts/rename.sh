#!/bin/bash
OLDVERSION=$1
NEWVERSION=$2
MODE=${3:-1}   # 1=outputs (default), 2=cache, 3=both

rename_version() {
    local HEADDIR=$1

    while IFS= read -r dir; do
        newdir="${dir/$OLDVERSION/$NEWVERSION}"
        echo "--- Renaming directory: $dir -> $newdir"
        mv "$dir" "$newdir"

	find -L "$newdir" -depth -name "*${OLDVERSION}*" -not -path "$newdir" | while IFS= read -r file; do
	    dir=$(dirname "$file")
	    base=$(basename "$file")
	    newbase="${base//$OLDVERSION/$NEWVERSION}"
	    echo "Renaming: $file -> $dir/$newbase"
	    mv "$file" "$dir/$newbase"
	done

        echo "Updating file contents in $newdir..."
        grep -rl "$OLDVERSION" "$newdir" \
            --exclude="*.parquet" \
            --exclude="*.png" \
            | xargs -r sed -i "s/$OLDVERSION/$NEWVERSION/g"

    done < <(find -L "$HEADDIR" -maxdepth 1 -type d -name "$OLDVERSION")
}

run_for() {
    local HEADDIR=$1
    if find -L "$HEADDIR" -maxdepth 1 -type d -name "$OLDVERSION" | grep -q .; then
        rename_version "$HEADDIR"
    else
        echo "ERROR: No directory named '$OLDVERSION' found under $HEADDIR, please check"
    fi
}

if [ "$MODE" -eq 1 ] || [ "$MODE" -eq 3 ]; then
    run_for outputs
fi

if [ "$MODE" -eq 2 ] || [ "$MODE" -eq 3 ]; then
    run_for cache
fi
