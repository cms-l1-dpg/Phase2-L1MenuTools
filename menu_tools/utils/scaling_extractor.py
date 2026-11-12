#!/usr/bin/env python3
"""
L1 Trigger pT Scaling Converter Tool for CMS Experiment

This tool converts between online and offline pT using scaling parameters from YAML files.
The scaling relationship is: offline_pT = slope * online_pT + offset

Usage:
    python pt_scaling_tool.py <yaml_file> --online <online_pt>
    python pt_scaling_tool.py <yaml_file> --offline <offline_pt>
    python pt_scaling_tool.py <scaling_dir> <l1_object> --online <online_pt> [--region <region>]

Examples:
    python pt_scaling_tool.py L1nnPuppiTau:default:barrel.yaml --online 25
    python pt_scaling_tool.py L1nnPuppiTau:default:barrel.yaml --offline 30
    python pt_scaling_tool.py scalings/ L1nnPuppiTau --offline 30 --region barrel
    python pt_scaling_tool.py scalings/ L1nnPuppiTau --offline 30 --id custom --region endcap
"""

import yaml
import argparse
import sys
import os
import glob
from pathlib import Path


def load_scaling_from_file(yaml_file):
    """Load scaling parameters from a YAML file."""
    try:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'slope' not in data or 'offset' not in data:
            print(f"Error: YAML file must contain 'slope' and 'offset' fields.")
            return None, None, None
            
        # Extract object info from filename
        basename = os.path.basename(yaml_file)
        object_key = basename.replace('.yaml', '').replace('.yml', '')
        
        return data['slope'], data['offset'], object_key
        
    except FileNotFoundError:
        print(f"Error: File '{yaml_file}' not found.")
        return None, None, None
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML format in '{yaml_file}': {e}")
        return None, None, None


def find_scaling_file(scaling_dir, l1_object, id_req="default", region=""):
    """Find the appropriate scaling file in a directory."""
    # Build the expected filename
    if ":" in l1_object:
        # Full key provided
        filename = f"{l1_object}.yaml"
    else:
        # Build key from components
        key = f"{l1_object}:{id_req}"
        if region:
            key += f":{region}"
        filename = f"{key}.yaml"
    
    # Look for the file in the directory
    file_path = os.path.join(scaling_dir, filename)
    if os.path.exists(file_path):
        return file_path
    
    # If not found, try to find similar files
    pattern = os.path.join(scaling_dir, f"{l1_object}*.yaml")
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        print(f"Error: No scaling files found for '{l1_object}' in '{scaling_dir}'")
        return None
    
    print(f"Error: Exact file '{filename}' not found.")
    print(f"Available files for {l1_object}:")
    for f in matching_files:
        print(f"  {os.path.basename(f)}")
    return None


def online_to_offline(online_pt, slope, offset):
    """Convert online pT to offline pT using: offline_pT = slope * online_pT + offset"""
    return slope * online_pt + offset


def offline_to_online(offline_pt, slope, offset):
    """Convert offline pT to online pT using: online_pT = (offline_pT - offset) / slope"""
    if slope == 0:
        print("Error: Slope cannot be zero for conversion.")
        return None
    return (offline_pt - offset) / slope


def main():
    parser = argparse.ArgumentParser(
        description="L1 Trigger pT Scaling Converter Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using direct YAML file
  %(prog)s L1nnPuppiTau:default:barrel.yaml --online 25
  %(prog)s L1nnPuppiTau:default:barrel.yaml --offline 30
  
  # Using scaling directory
  %(prog)s scalings/ L1nnPuppiTau --offline 30 --region barrel
  %(prog)s scalings/ L1nnPuppiTau --offline 30 --id custom --region endcap
        """)
    
    parser.add_argument('input', help='YAML file or directory containing scaling files')
    parser.add_argument('l1_object', nargs='?', help='L1 object name (required if input is directory)')
    
    # Mutually exclusive group for online or offline pT
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--online', type=float, help='Online pT in GeV (convert to offline)')
    group.add_argument('--offline', type=float, help='Offline pT in GeV (convert to online)')
    
    parser.add_argument('--id', default='default', 
                       help='ID requirement (default: "default", used only with directory input)')
    parser.add_argument('--region', default='', 
                       help='Detector region (e.g., "barrel", "endcap", used only with directory input)')
    
    args = parser.parse_args()
    
    # Determine if input is a file or directory
    if os.path.isfile(args.input):
        # Direct YAML file
        yaml_file = args.input
        slope, offset, object_key = load_scaling_from_file(yaml_file)
    elif os.path.isdir(args.input):
        # Directory with scaling files
        if not args.l1_object:
            print("Error: L1 object name is required when using directory input.")
            sys.exit(1)
        
        yaml_file = find_scaling_file(args.input, args.l1_object, args.id, args.region)
        if yaml_file is None:
            sys.exit(1)
        
        slope, offset, object_key = load_scaling_from_file(yaml_file)
    else:
        print(f"Error: '{args.input}' is neither a file nor a directory.")
        sys.exit(1)
    
    if slope is None or offset is None:
        sys.exit(1)
    
    print(f"Using scaling for: {object_key}")
    print(f"Scaling parameters: slope = {slope:.6f}, offset = {offset:.6f}")
    print(f"Relationship: offline_pT = {slope:.6f} * online_pT + {offset:.6f}")
    print()
    
    if args.online is not None:
        # Convert online to offline
        offline_pt = online_to_offline(args.online, slope, offset)
        print(f"Online pT:  {args.online:.2f} GeV")
        print(f"Offline pT: {offline_pt:.2f} GeV")
        
    elif args.offline is not None:
        # Convert offline to online
        online_pt = offline_to_online(args.offline, slope, offset)
        if online_pt is not None:
            print(f"Offline pT: {args.offline:.2f} GeV")
            print(f"Online pT:  {online_pt:.2f} GeV")


if __name__ == "__main__":
    main()
