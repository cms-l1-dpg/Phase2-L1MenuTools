#!/bin/sh

python menu_tools/caching/merge_arrays.py --version V45nano_140PU --sample MinBias

rate_plots configs/V45nano_140PU/rate_plots/bjet.yaml
echo "B-jet rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/disp_muons.yaml
echo "Displaced muon rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/eg.yaml
echo "Electron and photon rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/ht.yaml
echo "HT rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/jets.yaml
echo "Jet rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/met.yaml
echo "MET rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/muons.yaml
echo "Muon rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/taus.yaml
echo "Tau rate plots generated."

rate_plots configs/V45nano_140PU/rate_plots/tkmuons.yaml
echo "Track muon rate plots generated."
