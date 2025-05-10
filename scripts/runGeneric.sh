VERSION=$1

# === Initial Caching === #

cache_objects configs/$VERSION/caching.yaml
# python3 menu_tools/caching/merge_arrays.py --version $VERSION --sample Hgg
# python3 menu_tools/caching/merge_arrays.py --version $VERSION --sample DYLL_M50
# python3 menu_tools/caching/merge_arrays.py --version $VERSION --sample MinBias

# === Object Performance === #

# # Electrons
# object_performance configs/$VERSION/object_performance/electron_matching.yaml
# object_performance configs/$VERSION/object_performance/electron_matching_eta.yaml
# object_performance configs/$VERSION/object_performance/electron_trigger.yaml

# # Photons
# object_performance configs/$VERSION/object_performance/photons_matching.yaml
# object_performance configs/$VERSION/object_performance/photons_matching_eta.yaml
# object_performance configs/$VERSION/object_performance/photons_trigger.yaml

# # Jets
# object_performance configs/$VERSION/object_performance/jets_matching.yaml
# object_performance configs/$VERSION/object_performance/jets_matching_eta.yaml
# object_performance configs/$VERSION/object_performance/jets_trigger.yaml

# Taus
object_performance configs/$VERSION/object_performance/tau_matching.yaml
object_performance configs/$VERSION/object_performance/tau_matching_eta.yaml
object_performance configs/$VERSION/object_performance/tau_matching_highPt.yaml
object_performance configs/$VERSION/object_performance/tau_trigger.yaml

# # Sums
# object_performance configs/$VERSION/object_performance/met_ht_mht.yaml

# # Muons
# object_performance configs/$VERSION/object_performance/muon_matching.yaml
# object_performance configs/$VERSION/object_performance/muon_matching_eta.yaml
# object_performance configs/$VERSION/object_performance/muon_trigger.yaml

# # TkMuons
# object_performance configs/$VERSION/object_performance/tkmuon_matching.yaml
# object_performance configs/$VERSION/object_performance/tkmuon_matching_eta.yaml
# object_performance configs/$VERSION/object_performance/tkmuon_trigger.yaml

# # MuonsTF
# object_performance configs/$VERSION/object_performance/muonTF_matching.yaml
# object_performance configs/$VERSION/object_performance/muonTF_matching_eta.yaml
# object_performance configs/$VERSION/object_performance/muonTF_trigger.yaml

# # === Object Rates === #

# rate_plots configs/$VERSION/rate_plots/eg.yaml
# rate_plots configs/$VERSION/rate_plots/muons.yaml
# rate_plots configs/$VERSION/rate_plots/tkmuons.yaml
# rate_plots configs/$VERSION/rate_plots/ht.yaml
# rate_plots configs/$VERSION/rate_plots/met.yaml
# rate_plots configs/$VERSION/rate_plots/jets.yaml
# rate_plots configs/$VERSION/rate_plots/taus.yaml

# # === Menu Performance === #

# rate_table configs/$VERSION/rate_table/step1_cfg.yml

# === Extras === #

# object_performance configs/$VERSION/object_performance/jets_matching_wBTag.yaml

# rate_plots configs/$VERSION/rate_plots/bjet.yaml
# rate_plots configs/$VERSION/rate_plots/disp_muons.yaml
