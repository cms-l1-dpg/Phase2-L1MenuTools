VERSION="V49nano_RelVal"
# VERSION="V50nano"
# OVERRIDE_SHORT="170pre3_3rdTrain"
# OVERRIDE_SHORT="170pre3"
# OVERRIDE_SHORT="170pre2"
# OVERRIDE_SHORT="170pre2_140PU"
# OVERRIDE_SHORT="170pre1_MuonOMTFUpdate1"
# OVERRIDE_SHORT="170pre2_JetWord"
# OVERRIDE_SHORT="170pre2_JetWord_140PU"
# OVERRIDE_SHORT="MuonShowerwL1"
# OVERRIDE_SHORT="MuonShower"
OVERRIDE_SHORT="RelValwL1"
OVERRIDE_VERSION="${VERSION}_${OVERRIDE_SHORT}"
# OVERRIDE_VERSION="${VERSION}" #_${OVERRIDE_SHORT}"
REVISION=$(date +%y%m%d)

# echo "Running caching for ${VERSION} subversion ${OVERRIDE_VERSION} - Revision = ${REVISION}"
echo "Running caching for ${VERSION} subversion ${OVERRIDE_VERSION} (short is ${OVERRIDE_SHORT}) - Revision = ${REVISION}"

mkdir logs/${OVERRIDE_VERSION}_${REVISION}
cache_objects configs/$VERSION/cache_objects/caching_${OVERRIDE_SHORT}.yaml |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# # cache_objects configs/$VERSION/caching.yaml |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample Hgg |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample DYLL_M50 |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample TT |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample VBFHToTauTau |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample VBFHToBB |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample VBFHToInv |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample HHTo4B |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
# python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample HHTo2B2Tau |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample MinBias |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
python3 menu_tools/caching/merge_arrays.py --version $OVERRIDE_VERSION --sample ZEE |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_caching.log
