# VERSIONS="L1EG 151pre1 150pre2 150pre1 142pre3 142pre2"
# VERSIONS="noL1EG L1EG L1EGupdate1"
# VERSIONS="L1EGupdate1"
# VERSIONS="151pre3"
# VERSIONS="151X_D110 151X_D116 151X_D121 151pre3_D110Fix"
# VERSIONS="151pre3_D110Fix"
# VERSIONS="151pre3_SC8Nano"
# VERSIONS="L1EGupdate2"
# NOTE: above versions assumed V45nano in the name

# VERSIONS="V48nano_151pre3 V48nano_L1EGupdate2"
# VERSIONS="V49nano_151pre3 V49nano_L1EGupdate2"
VERSIONS="V49nano_151pre3_E2ENNVtx V49nano_E2ENNVtxOff"
REVISION="250611"
MAX_JOBS=2

# run_when_ready() {
#     while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
#         sleep 3
#     done
#     # Extract a meaningful identifier from the config path
#     local filename=$(basename "$2")  # assumes config is 2nd argument
#     local logname=${filename%.*}  # removes file extension
#     echo Submitting $logname
#     "$@" | tee -a logs/${VERSION}_${REVISION}/${VERSION}_${logname}.log &
#     # "$@" &> logs/${VERSION}_${REVISION}/${VERSION}_${logname}.log &
# }

for VERSION in $VERSIONS; do
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    echo "Submitting ${VERSION}_${REVISION}"
    mkdir -p logs/${VERSION}_${REVISION}
    # run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger.yaml
    source scripts/runGeneric.sh $VERSION $REVISION &> logs/${VERSION}_${REVISION}/${VERSION}_batch.log &
done

echo "All jobs submitted, but waiting as some are still running! Checking progress with tail -f."
tail -f logs/*_${REVISION}/*_batch.log
wait
