#!/bin/bash

# Script to compare config directories, ignoring version name differences
# Usage: source compare_directories.sh <primary_dir> <comparison_dir>
# This script should be sourced, not executed directly

compare_configs() {
    local PRIMARY_DIR=$1
    local COMPARE_DIR=$2

    # Validate inputs
    if [[ -z "$PRIMARY_DIR" || -z "$COMPARE_DIR" ]]; then
        echo "ERROR: Both directories must be provided"
        echo "Usage: source compare_directories.sh <primary_dir> <comparison_dir>"
        return 1
    fi

    if [[ ! -d "$PRIMARY_DIR" ]]; then
        echo "ERROR: Primary directory does not exist: $PRIMARY_DIR"
        return 1
    fi

    if [[ ! -d "$COMPARE_DIR" ]]; then
        echo "ERROR: Comparison directory does not exist: $COMPARE_DIR"
        return 1
    fi

    # Extract version names from directory paths
    PRIMARY_VERSION=$(basename "$PRIMARY_DIR")
    COMPARE_VERSION=$(basename "$COMPARE_DIR")

    echo "========================================"
    echo "Comparing Config Directories"
    echo "========================================"
    echo "Primary (before):    $PRIMARY_DIR"
    echo "Comparison (after):  $COMPARE_DIR"
    echo ""
    echo "Primary version:     $PRIMARY_VERSION"
    echo "Comparison version:  $COMPARE_VERSION"
    echo "========================================"
    echo ""

    # Directories to compare
    local SUBDIRS=("object_performance" "objects" "rate_plots" "rate_table")
    
    local TOTAL_DIFFERENCES=0
    local TOTAL_ONLY_VERSION_DIFF=0
    local TOTAL_FILES_COMPARED=0
    local TOTAL_MISSING_FILES=0

    for subdir in "${SUBDIRS[@]}"; do
        echo "Checking directory: $subdir/"
        echo "----------------------------------------"
        
        local PRIMARY_SUBDIR="$PRIMARY_DIR/$subdir"
        local COMPARE_SUBDIR="$COMPARE_DIR/$subdir"
        
        # Check if subdirectory exists in both
        if [[ ! -d "$PRIMARY_SUBDIR" ]]; then
            echo "  WARNING: Subdirectory missing in primary: $subdir/"
            echo ""
            continue
        fi
        
        if [[ ! -d "$COMPARE_SUBDIR" ]]; then
            echo "  WARNING: Subdirectory missing in comparison: $subdir/"
            echo ""
            continue
        fi
        
        # Get list of all files from both directories
        local ALL_FILES=$(find "$PRIMARY_SUBDIR" "$COMPARE_SUBDIR" -type f -name "*.yaml" -o -name "*.yml" | \
                         sed -e "s|$PRIMARY_SUBDIR/||" -e "s|$COMPARE_SUBDIR/||" | \
                         grep -v "caching.yaml" | grep -v "caching_signal.yaml" | \
                         sort -u)
        
        if [[ -z "$ALL_FILES" ]]; then
            echo "  No YAML files found in $subdir/"
            echo ""
            continue
        fi
        
        while IFS= read -r file; do
            # Skip caching files
            if [[ "$file" == "caching.yaml" || "$file" == "caching_signal.yaml" ]]; then
                continue
            fi
            
            local PRIMARY_FILE="$PRIMARY_SUBDIR/$file"
            local COMPARE_FILE="$COMPARE_SUBDIR/$file"
            
            # Check if file exists in both directories
            if [[ ! -f "$PRIMARY_FILE" ]]; then
                echo "  ⚠ FILE ONLY IN COMPARISON: $subdir/$file"
                ((TOTAL_MISSING_FILES++))
                continue
            fi
            
            if [[ ! -f "$COMPARE_FILE" ]]; then
                echo "  ⚠ FILE ONLY IN PRIMARY: $subdir/$file"
                ((TOTAL_MISSING_FILES++))
                continue
            fi
            
            ((TOTAL_FILES_COMPARED++))
            
            # Create temporary files with version names normalized
            local TEMP_PRIMARY=$(mktemp)
            local TEMP_COMPARE=$(mktemp)
            
            # Normalize version names in both files
            # Replace version string occurrences with a placeholder
            sed -e "s/${PRIMARY_VERSION}/VERSION_PLACEHOLDER/g" \
                -e "s|configs/${PRIMARY_VERSION}/|configs/VERSION_PLACEHOLDER/|g" \
                "$PRIMARY_FILE" > "$TEMP_PRIMARY"
            
            sed -e "s/${COMPARE_VERSION}/VERSION_PLACEHOLDER/g" \
                -e "s|configs/${COMPARE_VERSION}/|configs/VERSION_PLACEHOLDER/|g" \
                "$COMPARE_FILE" > "$TEMP_COMPARE"
            
            # Compare the normalized files
            if diff -q "$TEMP_PRIMARY" "$TEMP_COMPARE" > /dev/null 2>&1; then
                # Files are identical after normalization
                # Check if they were different before normalization
                if ! diff -q "$PRIMARY_FILE" "$COMPARE_FILE" > /dev/null 2>&1; then
                    echo "  ✓ $subdir/$file - identical (only version name differs)"
                    ((TOTAL_ONLY_VERSION_DIFF++))
                fi
                # If files were already identical, we don't report them (silent success)
            else
                # Files differ even after normalization
                echo "  ✗ DIFFERENCE FOUND: $subdir/$file"
                echo "    Files differ beyond version name. Run this to see details:"
                echo "    git diff --no-index \"$PRIMARY_FILE\" \"$COMPARE_FILE\""
                echo ""
                ((TOTAL_DIFFERENCES++))
            fi
            
            # Clean up temp files
            rm -f "$TEMP_PRIMARY" "$TEMP_COMPARE"
            
        done <<< "$ALL_FILES"
        
        echo ""
    done
    
    # Summary
    echo "========================================"
    echo "SUMMARY"
    echo "========================================"
    echo "Total files compared:              $TOTAL_FILES_COMPARED"
    echo "Files with only version diff:      $TOTAL_ONLY_VERSION_DIFF"
    echo "Files with substantive differences: $TOTAL_DIFFERENCES"
    echo "Files only in one directory:       $TOTAL_MISSING_FILES"
    echo ""
    
    if [[ $TOTAL_DIFFERENCES -eq 0 && $TOTAL_MISSING_FILES -eq 0 ]]; then
        echo "✓ SUCCESS: Directories are equivalent (ignoring version names and caching.yaml)"
        return 0
    else
        echo "⚠ DIFFERENCES DETECTED: See details above"
        return 1
    fi
}

# Execute the comparison function with provided arguments
compare_configs "$1" "$2"

