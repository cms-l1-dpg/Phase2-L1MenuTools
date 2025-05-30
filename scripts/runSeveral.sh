# VERSIONS="L1EG 151pre1 150pre2 150pre1 142pre3 142pre2"
# VERSIONS="noL1EG L1EG L1EGupdate1"
VERSIONS="L1EGupdate1"
# VERSIONS="151pre3"
REVISION="250528"

MAX_JOBS=10

for VERSION in $VERSIONS; do
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    (
	source scripts/runGeneric.sh V45nano_$VERSION &> logs/V45nano_${VERSION}_${REVISION}.log
    ) &
done

wait
