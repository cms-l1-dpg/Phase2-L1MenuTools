# VERSIONS="L1EG 151pre1 150pre2 150pre1 142pre3 142pre2"
# VERSIONS="noL1EG L1EG L1EGupdate1"
# VERSIONS="L1EGupdate1"
# VERSIONS="151pre3"
# VERSIONS="151X_D110 151X_D116 151X_D121 151pre3_D110Fix"
# VERSIONS="151pre3_D110Fix"
# VERSIONS="151pre3_SC8Nano"
# VERSIONS="L1EGupdate2"
VERSIONS="L1EGupdate1p5"
REVISION="250601"
MAX_JOBS=1

for VERSION in $VERSIONS; do
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    echo "Submitting ${VERSION}_${REVISION}"
    mkdir -p logs/V45nano_${VERSION}_${REVISION}
    source scripts/runGeneric.sh V45nano_$VERSION $REVISION &> logs/V45nano_${VERSION}_${REVISION}/V45nano_${VERSION}.log &
done

echo "All jobs submitted, but waiting as some are still running! Check on progress in another tab."
wait
