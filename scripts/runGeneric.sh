VERSION=$1
REVISION=$2
MAX_JOBS=5

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    # Extract a meaningful identifier from the config path
    local filename=$(basename "$2")  # assumes config is 2nd argument
    local logname=${filename%.*}  # removes file extension
    echo Submitting $logname
    "$@" &> logs/${VERSION}_${REVISION}/${VERSION}_${logname}.log &
}

mkdir -p logs/${VERSION}_${REVISION}
# === Initial Caching === #

echo "Running caching"

(
    cache_objects configs/$VERSION/caching.yaml &> logs/${VERSION}_${REVISION}/${VERSION}_caching.log
    python3 menu_tools/caching/merge_arrays.py --version $VERSION --sample Hgg &>> logs/${VERSION}_${REVISION}/${VERSION}_caching.log
    python3 menu_tools/caching/merge_arrays.py --version $VERSION --sample DYLL_M50 &>> logs/${VERSION}_${REVISION}/${VERSION}_caching.log
    python3 menu_tools/caching/merge_arrays.py --version $VERSION --sample MinBias &>> logs/${VERSION}_${REVISION}/${VERSION}_caching.log
) &

echo "Waiting for caching"
wait
echo "Caching complete"

# === Object Performance (Matching) === #

# Electrons
run_when_ready object_performance configs/$VERSION/object_performance/electron_matching.yaml
run_when_ready object_performance configs/$VERSION/object_performance/electron_matching_eta.yaml

# Photons
run_when_ready object_performance configs/$VERSION/object_performance/photons_matching.yaml
run_when_ready object_performance configs/$VERSION/object_performance/photons_matching_eta.yaml

# Jets
run_when_ready object_performance configs/$VERSION/object_performance/jets_matching.yaml
run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_eta.yaml
run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_wBTag.yaml

# Muons
run_when_ready object_performance configs/$VERSION/object_performance/muon_matching.yaml
run_when_ready object_performance configs/$VERSION/object_performance/muon_matching_eta.yaml

# TkMuons
run_when_ready object_performance configs/$VERSION/object_performance/tkmuon_matching.yaml
run_when_ready object_performance configs/$VERSION/object_performance/tkmuon_matching_eta.yaml

# MuonsTF
run_when_ready object_performance configs/$VERSION/object_performance/muonTF_matching.yaml
run_when_ready object_performance configs/$VERSION/object_performance/muonTF_matching_eta.yaml

# Taus
run_when_ready object_performance configs/$VERSION/object_performance/tau_matching.yaml
run_when_ready object_performance configs/$VERSION/object_performance/tau_matching_eta.yaml
run_when_ready object_performance configs/$VERSION/object_performance/tau_matching_highPt.yaml

# === Object Performance (Triggers/Scalings) === #

run_when_ready object_performance configs/$VERSION/object_performance/electron_trigger.yaml
run_when_ready object_performance configs/$VERSION/object_performance/met_ht_mht.yaml # Sums (all in one!)
run_when_ready object_performance configs/$VERSION/object_performance/jets_trigger.yaml
run_when_ready object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml # step 2
run_when_ready object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml # step 2
run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger.yaml # includes step 2 disp muons
run_when_ready object_performance configs/$VERSION/object_performance/tkmuon_trigger.yaml
run_when_ready object_performance configs/$VERSION/object_performance/muonTF_trigger.yaml
run_when_ready object_performance configs/$VERSION/object_performance/tau_trigger.yaml
run_when_ready object_performance configs/$VERSION/object_performance/photons_trigger.yaml # submit later so it's more likely to complete after electrons

# === Print Configs (Objects) === #
run_when_ready python menu_tools/utils/exportDefs.py -t objects configs/$VERSION/objects

echo "Waiting for scalings"
wait
echo "Scalings complete"

swapToElectronScalings.sh $VERSION # Explicit scalings swap in case photons finish first

# === Menu Performance === #

run_when_ready rate_table configs/$VERSION/rate_table/step1_cfg.yml
run_when_ready rate_table configs/$VERSION/rate_table/step2_cfg.yml
# run_when_ready rate_table configs/$VERSION/rate_table/step1and2_cfg.yml # prepping to study step 2

# === Print Configs (Menus) === #
run_when_ready python menu_tools/utils/exportDefs.py -t triggers configs/$VERSION/rate_table

# === Object Rates === #

run_when_ready rate_plots configs/$VERSION/rate_plots/eg.yaml
run_when_ready rate_plots configs/$VERSION/rate_plots/muons.yaml
run_when_ready rate_plots configs/$VERSION/rate_plots/tkmuons.yaml
run_when_ready rate_plots configs/$VERSION/rate_plots/ht.yaml
run_when_ready rate_plots configs/$VERSION/rate_plots/met.yaml
run_when_ready rate_plots configs/$VERSION/rate_plots/jets.yaml # includes ext jets
run_when_ready rate_plots configs/$VERSION/rate_plots/jets_sc8.yaml # step 2
run_when_ready rate_plots configs/$VERSION/rate_plots/taus.yaml
run_when_ready rate_plots configs/$VERSION/rate_plots/bjet.yaml
run_when_ready rate_plots configs/$VERSION/rate_plots/disp_muons.yaml # step 2

echo "Plots and tables finished!"
