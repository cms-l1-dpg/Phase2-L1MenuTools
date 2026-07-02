#!/bin/bash

# Wrapper to compare pairs of config subdirectories and summarize results
# Usage: source compare_all_configs.sh [configs_dir] [--everything] [--skip REGEX]... [--min-base N] [--no-default-skip] [--debug]
# Notes:
# - Default mode (no --everything):
#   - Filters to V44nano and above
#   - Skips legacy sets by default (V29-V32, V29_13X, V32nano..V43nano; including _* suffixes)
#   - Groups by primary base (e.g. V45nano) and only compares variants with different suffixes
# - --everything disables default filters and grouping, reproducing the original all-pairs behavior
# - You can add extra skips with repeated --skip REGEX; use --min-base to change nano threshold
# - This script is intended to be sourced (not executed) so it can call the
#   existing comparison script which is also designed to be sourced.

compare_all_configs() {
    # Defaults
    local CONFIGS_DIR="./configs"
    local EVERYTHING_MODE=false
    local DEFAULT_SKIP=true
    local MIN_BASE=46   # apply to names like V<NUM>nano
    local MAX_BASE=48   # apply to names like V<NUM>nano
    local USER_SKIP_PATTERNS=()
    local DEBUG=false

    # Parse args
    local CONFIGS_DIR_SET=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --everything)
                EVERYTHING_MODE=true
                ;;
            --skip)
                shift
                [[ -n "$1" ]] && USER_SKIP_PATTERNS+=("$1")
                ;;
            --min-base)
                shift
                MIN_BASE="$1"
                ;;
            --max-base)
                shift
                MAX_BASE="$1"
                ;;
            --no-default-skip)
                DEFAULT_SKIP=false
                ;;
            --debug)
                DEBUG=true
                ;;
            -h|--help)
                echo "Usage: source compare_all_configs.sh [configs_dir] [--everything] [--skip REGEX]... [--min-base N] [--no-default-skip] [--debug]"
                return 0
                ;;
            *)
                # First non-flag argument is the configs dir
                if [[ -z "$CONFIGS_DIR_SET" ]]; then
                    CONFIGS_DIR="$1"
                    CONFIGS_DIR_SET=1
                else
                    echo "ERROR: Unknown argument: $1"
                    return 1
                fi
                ;;
        esac
        shift
    done

    if [[ -z "$CONFIGS_DIR" ]]; then
        echo "ERROR: Configs directory must be provided"
        echo "Usage: source compare_all_configs.sh [configs_dir] [--everything] [--skip REGEX]... [--min-base N]"
        return 1
    fi

    if [[ ! -d "$CONFIGS_DIR" ]]; then
        echo "ERROR: Configs directory does not exist: $CONFIGS_DIR"
        return 1
    fi

    # Locate the single-compare script relative to this file
    local SCRIPT_DIR
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local COMPARE_SCRIPT="$SCRIPT_DIR/compare_directories.sh"

    if [[ ! -f "$COMPARE_SCRIPT" ]]; then
        echo "ERROR: Required script not found: $COMPARE_SCRIPT"
        return 1
    fi

    # Build skip patterns
    local ALL_SKIP_PATTERNS=()
    if [[ "$EVERYTHING_MODE" == false && "$DEFAULT_SKIP" == true ]]; then
        # Legacy sets and early nano versions (include suffixes via ($|_))
        ALL_SKIP_PATTERNS+=(
            '^V(29|30|31|32)($|_)'
            '^V29_13X($|_)'
            '^V(3[2-9]|4[0-3])nano($|_)'
        )
    fi
    if (( ${#USER_SKIP_PATTERNS[@]} > 0 )); then
        ALL_SKIP_PATTERNS+=("${USER_SKIP_PATTERNS[@]}")
    fi

    # Helper: check if a name matches any skip pattern
    _name_is_skipped() {
        local name="$1"
        if (( ${#ALL_SKIP_PATTERNS[@]} == 0 )); then
            return 1
        fi
        local pat
        for pat in "${ALL_SKIP_PATTERNS[@]}"; do
            if [[ "$name" =~ $pat ]]; then
                return 0
            fi
        done
        return 1
    }

    # Discover and filter immediate subdirectories
    local FOUND_NAMES
    mapfile -t FOUND_NAMES < <(find "$CONFIGS_DIR" -mindepth 1 -maxdepth 1 -type d -printf "%f\n" | sort)

    local DIRS=()
    local name
    for name in "${FOUND_NAMES[@]}"; do
        # Apply skip patterns (default + user) - in everything mode, respect only user-supplied skips
        if _name_is_skipped "$name"; then
            continue
        fi
        if [[ "$EVERYTHING_MODE" == false ]]; then
            # Enforce minimum base for nano-style names
            if [[ "$name" =~ ^V([0-9]+)nano(($|_).*)?$ ]]; then
                local base_num="${BASH_REMATCH[1]}"
                if (( base_num < MIN_BASE )); then
                    continue
                elif (( base_num > MAX_BASE )); then
                    continue
                fi
            fi
        fi
        DIRS+=("$name")
    done

    local NUM_DIRS=${#DIRS[@]}
    if (( NUM_DIRS < 2 )); then
        echo "ERROR: After filtering, need at least two subdirectories in $CONFIGS_DIR"
        return 1
    fi

    echo "========================================"
    if [[ "$EVERYTHING_MODE" == true ]]; then
        echo "Bulk Config Comparison (everything mode)"
    else
        echo "Bulk Config Comparison (group-by-base; V${MIN_BASE}nano+ by default)"
    fi
    echo "========================================"
    echo "Configs directory: $CONFIGS_DIR"
    echo "Subdirectories considered ($NUM_DIRS): ${DIRS[*]}"
    echo "========================================"
    echo ""

    local total_pairs=0
    local same_pairs=0
    local different_pairs=0
    local SAME_LIST=()
    local DIFF_LIST=()

    # Helper to extract base and suffix
    _extract_base_and_suffix() {
        local name="$1"
        local base="$name"
        local suffix=""
        # Accept optional separators or none between base and suffix
        # Examples matched: V45nano, V45nano_142pre2, V45nano-142pre3, V45nano142pre4
        if [[ "$name" =~ ^(V[0-9]+nano)[._-]?(.*)$ ]]; then
            base="${BASH_REMATCH[1]}"
            suffix="${BASH_REMATCH[2]}"
        fi
        echo "$base|$suffix"
    }

    if [[ "$EVERYTHING_MODE" == true ]]; then
        # Compare all pairs
        if [[ "$DEBUG" == true ]]; then
            echo "[DEBUG] EVERYTHING mode: NUM_DIRS=$NUM_DIRS"
        fi
        for (( i=0; i<NUM_DIRS-1; i++ )); do
            for (( j=i+1; j<NUM_DIRS; j++ )); do
                local D1="${DIRS[i]}"
                local D2="${DIRS[j]}"
                local P1="$CONFIGS_DIR/$D1"
                local P2="$CONFIGS_DIR/$D2"

                if [[ "$DEBUG" == true ]]; then
                    echo "[DEBUG] Pair candidate (everything): $D1  vs  $D2"
                fi
                (( total_pairs++ ))

                local output
                local status
                local __tmp_out
                __tmp_out=$(mktemp)
                ( source "$COMPARE_SCRIPT" "$P1" "$P2" ) > "$__tmp_out" 2>&1
                status=$?
                output=$(cat "$__tmp_out")
                rm -f "$__tmp_out"

                if [[ $status -eq 0 ]]; then
                    echo "✓ SAME: $D1  vs  $D2"
                    SAME_LIST+=("$D1 vs $D2")
                    (( same_pairs++ ))
                else
                    local compared
                    compared=$(grep -E "^Total files compared:" <<< "$output" | awk -F: '{print $2}' | xargs)
                    local only_version
                    only_version=$(grep -E "^Files with only version diff:" <<< "$output" | awk -F: '{print $2}' | xargs)
                    local substantive
                    substantive=$(grep -E "^Files with substantive differences:" <<< "$output" | awk -F: '{print $2}' | xargs)
                    local missing
                    missing=$(grep -E "^Files only in one directory:" <<< "$output" | awk -F: '{print $2}' | xargs)

                    # Check for plotting-only differences
                    local flags
                    flags=$(grep -E "^FLAGS:" <<< "$output")
                    local diff_note=""
                    if [[ -n "$flags" ]]; then
                        local perf=$(echo "$flags" | grep -o 'PERF=[0-9]' | cut -d= -f2)
                        local plots=$(echo "$flags" | grep -o 'PLOTS=[0-9]' | cut -d= -f2)
                        local obj=$(echo "$flags" | grep -o 'OBJ=[0-9]' | cut -d= -f2)
                        local table=$(echo "$flags" | grep -o 'TABLE=[0-9]' | cut -d= -f2)

                        if [[ "$obj" == "0" && "$table" == "0" ]]; then
                            if [[ "$perf" == "1" || "$plots" == "1" ]]; then
                                diff_note=" [PLOTTING ONLY]"
                            fi
                        fi
                    fi

                    echo "✗ DIFFERENT: $D1  vs  $D2  (compared: ${compared:-?}, only-version: ${only_version:-?}, substantive: ${substantive:-?}, missing: ${missing:-?})$diff_note"
                    DIFF_LIST+=("$D1 vs $D2$diff_note")
                    (( different_pairs++ ))
                fi
            done
        done
    else
        # Group by base and only compare variants with different suffixes
        declare -A BASE_TO_VARIANTS=()
        local base suffix key
        for name in "${DIRS[@]}"; do
            IFS='|' read -r base suffix <<< "$(_extract_base_and_suffix "$name")"
            if [[ -z "${BASE_TO_VARIANTS[$base]}" ]]; then
                BASE_TO_VARIANTS[$base]="$name"
            else
                BASE_TO_VARIANTS[$base]="${BASE_TO_VARIANTS[$base]} $name"
            fi
        done

        if [[ "$DEBUG" == true ]]; then
            echo "[DEBUG] Groups (base -> variants):"
            for key in "${!BASE_TO_VARIANTS[@]}"; do
                echo "[DEBUG]   $key -> ${BASE_TO_VARIANTS[$key]}"
            done
            echo ""
        fi

        for key in "${!BASE_TO_VARIANTS[@]}"; do
            # Split variants list
            read -r -a VARS <<< "${BASE_TO_VARIANTS[$key]}"
            local n=${#VARS[@]}
            if (( n < 2 )); then
                continue
            fi
            for (( i=0; i<n-1; i++ )); do
                for (( j=i+1; j<n; j++ )); do
                    local D1="${VARS[i]}"
                    local D2="${VARS[j]}"
                    IFS='|' read -r _ base_suffix1 <<< "$(_extract_base_and_suffix "$D1")"
                    IFS='|' read -r _ base_suffix2 <<< "$(_extract_base_and_suffix "$D2")"
                    # Only compare if suffixes differ (including empty vs non-empty)
                    if [[ "$base_suffix1" == "$base_suffix2" ]]; then
                        continue
                    fi
                    if [[ "$DEBUG" == true ]]; then
                        echo "[DEBUG] Pair candidate: $D1  vs  $D2  (suffixes: '${base_suffix1}' vs '${base_suffix2}')"
                    fi
                    local P1="$CONFIGS_DIR/$D1"
                    local P2="$CONFIGS_DIR/$D2"

                    (( total_pairs++ ))

                    local output
                    local status
                    local __tmp_out
                    __tmp_out=$(mktemp)
                    ( source "$COMPARE_SCRIPT" "$P1" "$P2" ) > "$__tmp_out" 2>&1
                    status=$?
                    output=$(cat "$__tmp_out")
                    rm -f "$__tmp_out"

                    if [[ $status -eq 0 ]]; then
                        echo "✓ SAME: $D1  vs  $D2"
                        SAME_LIST+=("$D1 vs $D2")
                        (( same_pairs++ ))
                    else
                        local compared
                        compared=$(grep -E "^Total files compared:" <<< "$output" | awk -F: '{print $2}' | xargs)
                        local only_version
                        only_version=$(grep -E "^Files with only version diff:" <<< "$output" | awk -F: '{print $2}' | xargs)
                        local substantive
                        substantive=$(grep -E "^Files with substantive differences:" <<< "$output" | awk -F: '{print $2}' | xargs)
                        local missing
                        missing=$(grep -E "^Files only in one directory:" <<< "$output" | awk -F: '{print $2}' | xargs)

                        # Check for plotting-only differences
                        local flags
                        flags=$(grep -E "^FLAGS:" <<< "$output")
                        local diff_note=""
                        if [[ -n "$flags" ]]; then
                            local perf=$(echo "$flags" | grep -o 'PERF=[0-9]' | cut -d= -f2)
                            local plots=$(echo "$flags" | grep -o 'PLOTS=[0-9]' | cut -d= -f2)
                            local obj=$(echo "$flags" | grep -o 'OBJ=[0-9]' | cut -d= -f2)
                            local table=$(echo "$flags" | grep -o 'TABLE=[0-9]' | cut -d= -f2)

                            if [[ "$obj" == "0" && "$table" == "0" ]]; then
                                if [[ "$perf" == "1" || "$plots" == "1" ]]; then
                                    diff_note=" [PLOTTING ONLY]"
                                fi
                            fi
                        fi

                        echo "✗ DIFFERENT: $D1  vs  $D2  (compared: ${compared:-?}, only-version: ${only_version:-?}, substantive: ${substantive:-?}, missing: ${missing:-?})$diff_note"
                        DIFF_LIST+=("$D1 vs $D2$diff_note")
                        (( different_pairs++ ))
                    fi
                done
            done
        done
    fi

    echo ""
    echo "========================================"
    echo "OVERALL SUMMARY"
    echo "========================================"
    echo "Total pairs:      $total_pairs"
    echo "Pairs SAME:       $same_pairs"
    echo "Pairs DIFFERENT:  $different_pairs"
    echo ""

    if (( total_pairs == 0 )); then
        echo "No variant pairs found to compare under current filters."
        if [[ "$EVERYTHING_MODE" == false ]]; then
            echo "Tip: ensure there are at least two directories sharing the same base (e.g. 'V45nano' and 'V45nano_...')."
            echo "     You can run with --debug to see grouping and pair candidates, or use --everything to compare across bases."
        fi
        echo ""
    fi

    if (( same_pairs > 0 )); then
        echo "SAME pairs:"
        for p in "${SAME_LIST[@]}"; do
            echo "  - $p"
        done
        echo ""
    fi

    if (( different_pairs > 0 )); then
        echo "DIFFERENT pairs:"
        for p in "${DIFF_LIST[@]}"; do
            echo "  - $p"
        done
        echo ""
    fi

    if (( different_pairs == 0 )); then
        echo "✓ All config directories are equivalent pairwise (ignoring version names and caching.yaml)"
        return 0
    else
        echo "⚠ Some pairs differ. See above."
        return 1
    fi
}

# Execute the bulk comparison with provided arguments when sourced
compare_all_configs "$@"



