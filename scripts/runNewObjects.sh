VERSION=$1
MAX_JOBS=5

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    "$@" &
}

RERUN="TRUE"
if [[ $RERUN == "TRUE" ]]; then
    # object_performance configs/$VERSION/object_performance/jets_matching.yaml
    # object_performance configs/$VERSION/object_performance/jets_matching_eta.yaml
    # object_performance configs/$VERSION/object_performance/jets_sc8_matching.yaml
    # object_performance configs/$VERSION/object_performance/jets_sc8_matching_eta.yaml
    # object_performance configs/$VERSION/object_performance/jets_matching_wBTag.yaml
    # object_performance configs/$VERSION/object_performance/jets_matching_wCTag.yaml
    # object_performance configs/$VERSION/object_performance/jets_matching_wLightTag.yaml
    # object_performance configs/$VERSION/object_performance/jets_matching_wGTag.yaml
    # object_performance configs/$VERSION/object_performance/jets_trigger.yaml
    # object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml
    # object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml
    # rate_table configs/$VERSION/rate_table/step2_cfg.yml
    # rate_plots configs/$VERSION/rate_plots/jets.yaml

    run_when_ready object_performance configs/$VERSION/object_performance/jets_matching.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_eta.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_sc8_matching.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_sc8_matching_eta.yaml
    run_when_ready object_performance configs/$VERSION/object_performance/met_ht_mht.yaml
    run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_wBTag.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_wCTag.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_wLightTag.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_matching_wGTag.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_trigger.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml
    # run_when_ready object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml
    wait
    run_when_ready rate_table configs/$VERSION/rate_table/step2_newTJM_cfg.yml
    run_when_ready rate_plots configs/$VERSION/rate_plots/jets.yaml
fi

