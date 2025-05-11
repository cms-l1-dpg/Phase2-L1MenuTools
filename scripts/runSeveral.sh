VERSIONS="L1EG 151pre1 150pre3 150pre2 150pre1 142pre3 142pre2"

for VERSION in $VERSIONS; do
    source scripts/runGeneric.sh V45nano_$VERSION |& tee logs/V45nano_${VERSION}_taus.log
done
