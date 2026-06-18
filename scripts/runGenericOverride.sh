VERSION=$1
REVISION=$2
OVERRIDE_VERSION=$3
OERRIDE_SHORT=$4
MAX_JOBS=6

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    # Extract a meaningful identifier from the config path
    local filename=$(basename "$2")  # assumes config is 2nd argument
    local logname=${filename%.*}  # removes file extension
    echo Submitting $logname
    "$@" &> logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_${logname}.log &
}

mkdir -p logs/${VERSION}_${REVISION}
# === Initial Caching === #

echo "Running caching"

(
    cache_objects configs/$VERSION/cache_objects/caching_${OVERRIDE_SHORT}.yaml &> logs/${VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
    python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample Hgg &>> logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
    python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample DYLL_M50 &>> logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
    python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample MinBias &>> logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
) &

echo "Waiting for caching"
wait
echo "Caching complete"

# === Object Performance (Matching) === #

# Electrons
run_when_ready object_performance configs/$VERSION/object_performance/electron_matching.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/electron_matching_eta.yaml --version ${OVERRIDE_VERSION}

# Photons
run_when_ready object_performance configs/$VERSION/object_performance/photons_matching.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/photons_matching_eta.yaml --version ${OVERRIDE_VERSION}

# Jets
run_when_ready object_performance configs/$VERSION/object_performance/jets_matching.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_eta.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_wBTag.yaml --version ${OVERRIDE_VERSION}

# Muons
run_when_ready object_performance configs/$VERSION/object_performance/muon_matching.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/muon_matching_eta.yaml --version ${OVERRIDE_VERSION}

# TkMuons
run_when_ready object_performance configs/$VERSION/object_performance/tkmuon_matching.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/tkmuon_matching_eta.yaml --version ${OVERRIDE_VERSION}

# MuonsTF
run_when_ready object_performance configs/$VERSION/object_performance/muonTF_matching.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/muonTF_matching_eta.yaml --version ${OVERRIDE_VERSION}

# Taus
run_when_ready object_performance configs/$VERSION/object_performance/tau_matching.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/tau_matching_eta.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/tau_matching_highPt.yaml --version ${OVERRIDE_VERSION}

# === Object Performance (Triggers/Scalings) === #

run_when_ready object_performance configs/$VERSION/object_performance/electron_trigger.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/met_ht_mht.yaml --version ${OVERRIDE_VERSION} # Sums (all in one!)
run_when_ready object_performance configs/$VERSION/object_performance/jets_trigger.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml --version ${OVERRIDE_VERSION} # step 2
run_when_ready object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml --version ${OVERRIDE_VERSION} # step 2
run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger.yaml --version ${OVERRIDE_VERSION} # includes step 2 disp muons
# run_when_ready object_performance configs/$VERSION/object_performance/tkmuon_trigger.yaml --version ${OVERRIDE_VERSION} # commented as it takes a long time
run_when_ready object_performance configs/$VERSION/object_performance/muonTF_trigger.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/tau_trigger.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/photons_trigger.yaml --version ${OVERRIDE_VERSION} # submit later so it's more likely to complete after electrons

# # === Print Configs (Objects) === #
# run_when_ready python menu_tools/utils/exportDefs.py -t objects configs/$VERSION/objects

echo "Waiting for scalings"
wait
echo "Scalings complete"

source scripts/swapToElectronScalings.sh $OVERRIDE_VERSION # Explicit scalings swap in case photons finish first

# === Menu Performance === #

run_when_ready rate_table configs/$VERSION/rate_table/step1_cfg.yml --version ${OVERRIDE_VERSION}
run_when_ready rate_table configs/$VERSION/rate_table/step2_cfg.yml --version ${OVERRIDE_VERSION}
run_when_ready rate_table configs/$VERSION/rate_table/step1and2_cfg.yml --version ${OVERRIDE_VERSION} # prepping to study step 2

# === Object Rates === #

run_when_ready rate_plots configs/$VERSION/rate_plots/eg.yaml --version ${OVERRIDE_VERSION}
run_when_ready rate_plots configs/$VERSION/rate_plots/muons.yaml --version ${OVERRIDE_VERSION}
run_when_ready rate_plots configs/$VERSION/rate_plots/tkmuons.yaml --version ${OVERRIDE_VERSION}
run_when_ready rate_plots configs/$VERSION/rate_plots/ht.yaml --version ${OVERRIDE_VERSION}
run_when_ready rate_plots configs/$VERSION/rate_plots/met.yaml --version ${OVERRIDE_VERSION}
run_when_ready rate_plots configs/$VERSION/rate_plots/jets.yaml --version ${OVERRIDE_VERSION} # includes ext jets
run_when_ready rate_plots configs/$VERSION/rate_plots/jets_sc8.yaml --version ${OVERRIDE_VERSION} # step 2
run_when_ready rate_plots configs/$VERSION/rate_plots/taus.yaml --version ${OVERRIDE_VERSION}
run_when_ready rate_plots configs/$VERSION/rate_plots/bjet.yaml --version ${OVERRIDE_VERSION}
run_when_ready rate_plots configs/$VERSION/rate_plots/disp_muons.yaml --version ${OVERRIDE_VERSION} # step 2

# # === Print Configs (Menus) === #
# run_when_ready python menu_tools/utils/exportDefs.py -t triggers configs/$VERSION/rate_table

echo "Plots and tables finished submitting!"
