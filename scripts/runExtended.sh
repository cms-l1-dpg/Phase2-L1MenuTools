VERSION=V50nano
REVISION=$(date +%y%m%d)
# OVERRIDE_VERSION=V50nano_170pre2
OVERRIDE_VERSION=V50nano_170pre2_140PU
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

mkdir -p logs/${OVERRIDE_VERSION}_${REVISION}
# run_when_ready object_performance configs/$VERSION/object_performance/electron_matching_eta_extended.yaml --version ${OVERRIDE_VERSION}
# run_when_ready object_performance configs/$VERSION/object_performance/photons_matching_eta_extended.yaml --version ${OVERRIDE_VERSION}
# run_when_ready object_performance configs/$VERSION/object_performance/tau_matching_eta_extended.yaml --version ${OVERRIDE_VERSION}
rate_table configs/$VERSION/rate_table/step1and2_cfg.yml --version ${OVERRIDE_VERSION}
rate_table configs/$VERSION/rate_table/step1_cfg.yml --version ${OVERRIDE_VERSION}

