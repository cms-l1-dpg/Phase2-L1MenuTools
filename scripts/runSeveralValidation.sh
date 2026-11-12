# Plots and tables for several versions in parallel, on existing caches (run the caching first).
#
# Usage: scripts/runSeveralValidation.sh VERSION [VERSION ...]
#   e.g. scripts/runSeveralValidation.sh V50nano_{170pre5_SC8mass,170pre5_SC8mass_140PU} V49nano_AR25
#   The configs/ dir for each version is found from its name (see runGenericValidation.sh);
#   set CONFIGDIR to force one for all. REVISION (default: today) can also be set from the
#   environment, e.g. REVISION=251201 scripts/...
VERSIONS="$@"
REVISION=${REVISION:-$(date +%y%m%d)}
# MAX_JOBS=${MAX_JOBS:-1}
MAX_JOBS=2

if [[ -z $VERSIONS ]]; then
    echo "Usage: scripts/runSeveralValidation.sh VERSION [VERSION ...]"
    return 1 2>/dev/null || exit 1
fi

PIDS=()  # own PID list + `kill -0` rather than counting `jobs -p`, see runGenericValidation.sh
for VERSION in $VERSIONS; do
    while true; do
        ALIVE=()
        for p in "${PIDS[@]}"; do kill -0 $p 2>/dev/null && ALIVE+=($p); done
        PIDS=("${ALIVE[@]}")
        [ ${#PIDS[@]} -lt $MAX_JOBS ] && break
        sleep 3
    done
    echo "Submitting ${VERSION}_${REVISION}"
    mkdir -p logs/${VERSION}_${REVISION}
    source scripts/runGenericValidation.sh $VERSION $REVISION $CONFIGDIR &> logs/${VERSION}_${REVISION}/${VERSION}_batch.log &
    PIDS+=($!)
    echo "Check on progress with e.g: tail -f logs/${VERSION}_${REVISION}/*_batch.log"
done

echo "All jobs submitted! Jobs are running in the background - check with 'jobs' and 'tail -f <logfile>'."
