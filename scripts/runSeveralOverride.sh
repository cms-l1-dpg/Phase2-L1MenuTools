VERSIONS="V49nano_AR25"
REVISION="251201"
OVER_VER="V49nano_AR25_160pre2_140PU"
OVER_SHORT="160pre2_140PU"
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
    echo "Submitting ${OVER_VER}_${REVISION}"
    mkdir -p logs/${OVER_VER}_${REVISION}
    # run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger.yaml
    source scripts/runGenericOverride.sh $VERSION $REVISION $OVER_VER $OVER_SHORT &> logs/${OVER_VER}_${REVISION}/${OVER_VER}_batch.log &
    echo "Check on progress with e.g: tail -f logs/${OVER_VER}_${REVISION}/*_caching.log logs/${OVER_VER}_${REVISION}/*_batch.log"
done

echo "All jobs submitted! Jobs are running in the background - check with 'jobs' and 'tail -f <logfile>'."
