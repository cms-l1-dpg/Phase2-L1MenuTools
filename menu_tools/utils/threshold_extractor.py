#!/usr/bin/env python3
"""
L1 Trigger Rate-pT Threshold Interpolation Tool for CMS Experiment

This tool interpolates between rate vs pT threshold data points to:
1. Find the pT threshold needed for a desired rate
2. Find the rate for a given pT threshold

Usage:
    python l1_trigger_tool.py <json_file> <l1_object> --rate <rate_khz>
    python l1_trigger_tool.py <json_file> <l1_object> --pt <pt_threshold>

Examples:
    python l1_trigger_tool.py data.json L1nnPuppiTau --rate 1000
    python l1_trigger_tool.py data.json L1nnPuppiTau:default:barrel --pt 25
    python l1_trigger_tool.py data.json L1caloTau --rate 500 --id custom
"""

import json
import argparse
import sys
from scipy.interpolate import interp1d
import numpy as np


def load_data(json_file):
    """Load the JSON data file."""
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_file}'.")
        sys.exit(1)


def build_key(l1_object, id_req="default", region=""):
    """Build the data key from L1 object name, ID requirement, and region."""
    if ":" in l1_object:
        # Handle case where full key is provided
        return l1_object
    else:
        # Build key from components
        key = f"{l1_object}:{id_req}"
        if region:
            key += f":{region}"
        return key


def find_pt_for_rate(data_key, data, target_rate):
    """Find pT threshold for a given target rate using interpolation."""
    if data_key not in data:
        available_keys = list(data.keys())
        print(f"Error: Key '{data_key}' not found in data.")
        print(f"Available keys: {available_keys}")
        return None
    
    x_vals = np.array(data[data_key]['x_values'])  # pT thresholds
    y_vals = np.array(data[data_key]['y_values'])  # rates
    
    # Check if target rate is within range
    min_rate, max_rate = min(y_vals), max(y_vals)
    if target_rate < min_rate or target_rate > max_rate:
        print(f"Warning: Target rate {target_rate} kHz is outside the available range")
        print(f"Available rate range: {min_rate:.2f} - {max_rate:.2f} kHz")
    
    # Since rates typically decrease with increasing pT, we need to interpolate
    # in the reverse direction (rate -> pT)
    # Sort by rate (ascending) for proper interpolation
    sorted_indices = np.argsort(y_vals)
    sorted_rates = y_vals[sorted_indices]
    sorted_pts = x_vals[sorted_indices]
    
    # Create interpolation function: rate -> pT
    try:
        interp_func = interp1d(sorted_rates, sorted_pts, kind='linear', 
                              bounds_error=False, fill_value='extrapolate')
        pt_threshold = float(interp_func(target_rate))
        return pt_threshold
    except Exception as e:
        print(f"Error during interpolation: {e}")
        return None


def find_rate_for_pt(data_key, data, target_pt):
    """Find rate for a given pT threshold using interpolation."""
    if data_key not in data:
        available_keys = list(data.keys())
        print(f"Error: Key '{data_key}' not found in data.")
        print(f"Available keys: {available_keys}")
        return None
    
    x_vals = np.array(data[data_key]['x_values'])  # pT thresholds
    y_vals = np.array(data[data_key]['y_values'])  # rates
    
    # Check if target pT is within range
    min_pt, max_pt = min(x_vals), max(x_vals)
    if target_pt < min_pt or target_pt > max_pt:
        print(f"Warning: Target pT {target_pt} GeV is outside the available range")
        print(f"Available pT range: {min_pt} - {max_pt} GeV")
    
    # Create interpolation function: pT -> rate
    try:
        interp_func = interp1d(x_vals, y_vals, kind='linear', 
                              bounds_error=False, fill_value='extrapolate')
        rate = float(interp_func(target_pt))
        return rate
    except Exception as e:
        print(f"Error during interpolation: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="L1 Trigger Rate-pT Threshold Interpolation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json L1nnPuppiTau --rate 1000
  %(prog)s data.json L1nnPuppiTau:default:barrel --pt 25
  %(prog)s data.json L1caloTau --rate 500 --id custom
        """)
    
    parser.add_argument('json_file', help='JSON file containing rate vs pT data')
    parser.add_argument('l1_object', help='L1 object name (e.g., L1nnPuppiTau)')
    
    # Mutually exclusive group for rate or pT
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--rate', type=float, help='Target rate in kHz (find pT threshold)')
    group.add_argument('--pt', type=float, help='pT threshold in GeV (find rate)')
    
    parser.add_argument('--id', default='default', 
                       help='ID requirement (default: "default")')
    parser.add_argument('--region', default='', 
                       help='Detector region (e.g., "barrel", "endcap")')
    
    args = parser.parse_args()
    
    # Load data
    data = load_data(args.json_file)
    
    # Build data key
    data_key = build_key(args.l1_object, args.id, args.region)
    
    if args.rate is not None:
        # Find pT threshold for target rate
        pt_threshold = find_pt_for_rate(data_key, data, args.rate)
        if pt_threshold is not None:
            print(f"For {data_key}:")
            print(f"Target rate: {args.rate} kHz")
            print(f"Required pT threshold: {pt_threshold:.2f} GeV")
    
    elif args.pt is not None:
        # Find rate for target pT
        rate = find_rate_for_pt(data_key, data, args.pt)
        if rate is not None:
            print(f"For {data_key}:")
            print(f"pT threshold: {args.pt} GeV")
            print(f"Expected rate: {rate:.2f} kHz")


if __name__ == "__main__":
    main()
