# VERSIONS="V49nano_AR25_VtxFindOff"
VERSIONS="V49nano_AR25_VtxOnlyAssoc V49nano_AR25_VtxBothOn" #V49nano_151pre3_L1EGupdate4 V49nano_151pre3_VtxOnlyFind V49nano_151pre3_VtxOnlyAssoc V49nano_151pre3_DispVtx"
REVISION="250618_egamma"
MAX_JOBS=10

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    # Extract a meaningful identifier from the config path
    local filename=$(basename "$2")  # assumes config is 2nd argument
    local logname=${filename%.*}  # removes file extension
    echo Submitting $logname
    "$@" | tee -a logs/${VERSION}_${REVISION}/${VERSION}_${logname}.log &
    # "$@" &> logs/${VERSION}_${REVISION}/${VERSION}_${logname}.log &
}

for VERSION in $VERSIONS; do
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    echo "Submitting ${VERSION}_${REVISION}"
    mkdir -p logs/${VERSION}_${REVISION}
    rm outputs/$VERSION/object_performance/scalings/L1EG*
    rm outputs/$VERSION/object_performance/scalings/L1tkPhoton*
    rm outputs/$VERSION/object_performance/scalings/L1tkElectron*
    
    # Electrons
    run_when_ready object_performance configs/$VERSION/object_performance/electron_matching.yaml
    run_when_ready object_performance configs/$VERSION/object_performance/electron_matching_eta.yaml
    run_when_ready object_performance configs/$VERSION/object_performance/electron_trigger.yaml

    # Photons
    run_when_ready object_performance configs/$VERSION/object_performance/photons_matching.yaml
    run_when_ready object_performance configs/$VERSION/object_performance/photons_matching_eta.yaml
    run_when_ready object_performance configs/$VERSION/object_performance/photons_trigger.yaml
    
    # === Print Configs (Objects) === #
    run_when_ready python menu_tools/utils/exportDefs.py -t objects configs/$VERSION/objects

    echo "Waiting for scalings"
    wait
    echo "Scalings complete"

    source scripts/swapToElectronScalings.sh $VERSION # Explicit scalings swap in case photons finish first

    # === Menu Performance === #

    run_when_ready rate_table configs/$VERSION/rate_table/step1_cfg.yml
    run_when_ready rate_table configs/$VERSION/rate_table/step2_cfg.yml
    run_when_ready rate_table configs/$VERSION/rate_table/step1and2_cfg.yml # prepping to study step 2

    # === Object Rates === #

    run_when_ready rate_plots configs/$VERSION/rate_plots/eg.yaml

    # === Print Configs (Menus) === #
    run_when_ready python menu_tools/utils/exportDefs.py -t triggers configs/$VERSION/rate_table

    echo "Plots and tables finished submitting!"
done

echo "All jobs submitted! Jobs are running in the background - check with 'jobs' and 'tail -f <logfile>'."
