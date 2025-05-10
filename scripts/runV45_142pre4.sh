# === Initial Caching === #

cache_objects configs/V45nano_142pre4/caching.yaml
python3 menu_tools/caching/merge_arrays.py --version V45nano_142pre4 --sample Hgg
python3 menu_tools/caching/merge_arrays.py --version V45nano_142pre4 --sample DYLL_M50
python3 menu_tools/caching/merge_arrays.py --version V45nano_142pre4 --sample MinBias

# === Object Performance === #

# Electrons
object_performance configs/V45nano_142pre4/object_performance/electron_matching.yaml
object_performance configs/V45nano_142pre4/object_performance/electron_matching_eta.yaml
object_performance configs/V45nano_142pre4/object_performance/electron_trigger.yaml

# Photons
object_performance configs/V45nano_142pre4/object_performance/photons_matching.yaml
object_performance configs/V45nano_142pre4/object_performance/photons_matching_eta.yaml
object_performance configs/V45nano_142pre4/object_performance/photons_trigger.yaml

# Jets
object_performance configs/V45nano_142pre4/object_performance/jets_matching.yaml
object_performance configs/V45nano_142pre4/object_performance/jets_matching_eta.yaml
object_performance configs/V45nano_142pre4/object_performance/jets_trigger.yaml

# Taus
object_performance configs/V45nano_142pre4/object_performance/tau_matching.yaml
object_performance configs/V45nano_142pre4/object_performance/tau_matching_eta.yaml
object_performance configs/V45nano_142pre4/object_performance/tau_matching_highPt.yaml
object_performance configs/V45nano_142pre4/object_performance/tau_trigger.yaml

# Sums
object_performance configs/V45nano_142pre4/object_performance/met_ht_mht.yaml

# Muons
object_performance configs/V45nano_142pre4/object_performance/muon_matching.yaml
object_performance configs/V45nano_142pre4/object_performance/muon_matching_eta.yaml
object_performance configs/V45nano_142pre4/object_performance/muon_trigger.yaml

# TkMuons
object_performance configs/V45nano_142pre4/object_performance/tkmuon_matching.yaml
object_performance configs/V45nano_142pre4/object_performance/tkmuon_matching_eta.yaml
object_performance configs/V45nano_142pre4/object_performance/tkmuon_trigger.yaml

# MuonsTF
object_performance configs/V45nano_142pre4/object_performance/muonTF_matching.yaml
object_performance configs/V45nano_142pre4/object_performance/muonTF_matching_eta.yaml
object_performance configs/V45nano_142pre4/object_performance/muonTF_trigger.yaml

# === Object Rates === #

rate_plots configs/V45nano_142pre4/rate_plots/eg.yaml
rate_plots configs/V45nano_142pre4/rate_plots/muons.yaml
rate_plots configs/V45nano_142pre4/rate_plots/tkmuons.yaml
rate_plots configs/V45nano_142pre4/rate_plots/ht.yaml
rate_plots configs/V45nano_142pre4/rate_plots/met.yaml
rate_plots configs/V45nano_142pre4/rate_plots/jets.yaml
rate_plots configs/V45nano_142pre4/rate_plots/taus.yaml

# === Menu Performance === #

rate_table configs/V45nano_142pre4/rate_table/step1_cfg.yml

# === Extras === #

# object_performance configs/V45nano_142pre4/object_performance/jets_matching_wBTag.yaml

# rate_plots configs/V45nano_142pre4/rate_plots/bjet.yaml
# rate_plots configs/V45nano_142pre4/rate_plots/disp_muons.yaml
