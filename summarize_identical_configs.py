#!/usr/bin/env python3
"""
Parse comparison log to find groups of identical configs and filter redundant comparisons.
Usage: python3 summarize_identical_configs.py summary_comparisons.log
"""

import sys
from collections import defaultdict

def find_equivalence_classes(same_pairs):
    """Find groups of configs that are all identical using Union-Find."""
    parent = {}
    
    def find(x):
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])  # Path compression
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Build union-find structure
    for config1, config2 in same_pairs:
        union(config1, config2)
    
    # Group configs by their root
    groups = defaultdict(list)
    all_configs = set()
    for config1, config2 in same_pairs:
        all_configs.add(config1)
        all_configs.add(config2)
    
    for config in all_configs:
        root = find(config)
        groups[root].append(config)
    
    # Sort each group and return as list
    equivalence_classes = []
    for group in groups.values():
        equivalence_classes.append(sorted(group))
    
    # Sort groups by their first element
    equivalence_classes.sort(key=lambda g: g[0])
    
    return equivalence_classes

def get_representative(config, equiv_map):
    """Get the representative (first member) of config's equivalence class."""
    return equiv_map.get(config, config)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 summarize_identical_configs.py summary_comparisons.log")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    same_pairs = []
    different_pairs = []
    
    # Parse the log file
    in_same_section = False
    in_different_section = False
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            if line == "SAME pairs:":
                in_same_section = True
                in_different_section = False
                continue
            elif line == "DIFFERENT pairs:":
                in_same_section = False
                in_different_section = True
                continue
            elif line.startswith("⚠") or line == "":
                in_same_section = False
                in_different_section = False
                continue
            
            if in_same_section and line.startswith("- "):
                # Parse "  - V49nano_142pre1 vs V49nano_151pre1"
                parts = line[2:].split(" vs ")
                if len(parts) == 2:
                    same_pairs.append((parts[0].strip(), parts[1].strip()))
            
            elif in_different_section and line.startswith("- "):
                parts = line[2:].split(" vs ")
                if len(parts) == 2:
                    different_pairs.append((parts[0].strip(), parts[1].strip()))
    
    # Find equivalence classes
    equiv_classes = find_equivalence_classes(same_pairs)
    
    # Create mapping from config to its representative
    config_to_repr = {}
    for equiv_class in equiv_classes:
        representative = equiv_class[0]  # First config in sorted group
        for config in equiv_class:
            config_to_repr[config] = representative
    
    print("=" * 80)
    print("IDENTICAL CONFIG GROUPS (can be merged)")
    print("=" * 80)
    print()
    
    if equiv_classes:
        for i, group in enumerate(equiv_classes, 1):
            if len(group) > 1:  # Only show groups with more than 1 member
                print(f"Group {i}: ({len(group)} configs)")
                print(f"  Representative: {group[0]}")
                print(f"  Identical to:   {', '.join(group[1:])}")
                print()
        
        total_configs = sum(len(g) for g in equiv_classes)
        total_groups = len([g for g in equiv_classes if len(g) > 1])
        total_redundant = sum(len(g) - 1 for g in equiv_classes if len(g) > 1)
        
        print(f"Summary: {total_configs} configs can be reduced to {total_configs - total_redundant} unique configs")
        print(f"         ({total_redundant} configs are duplicates that could be removed)")
        print()
    else:
        print("No identical configs found.")
        print()
    
    # Filter different pairs to avoid redundancy
    print("=" * 80)
    print("DIFFERENT PAIRS (filtered to remove redundant comparisons)")
    print("=" * 80)
    print()
    
    # Only keep pairs where both configs are representatives of their groups
    filtered_different = []
    for config1, config2 in different_pairs:
        repr1 = get_representative(config1, config_to_repr)
        repr2 = get_representative(config2, config_to_repr)
        
        # Only include if this is a comparison between representatives
        if config1 == repr1 and config2 == repr2:
            filtered_different.append((config1, config2))
    
    if filtered_different:
        print(f"Showing {len(filtered_different)} comparisons (reduced from {len(different_pairs)} original)")
        print()
        for config1, config2 in filtered_different:
            print(f"  - {config1} vs {config2}")
    else:
        print("No different pairs to show.")
    
    print()
    print("=" * 80)
    print(f"Original: {len(same_pairs)} same pairs, {len(different_pairs)} different pairs")
    print(f"Filtered: {len(filtered_different)} unique different comparisons")
    print("=" * 80)

if __name__ == "__main__":
    main()

