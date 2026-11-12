# VERSION="V49nano_RelVal"
VERSION="V50nano"
# OVERRIDE_SHORT="170pre3_3rdTrain"
# OVERRIDE_SHORT="170pre3"
# OVERRIDE_SHORT="170pre3_140PU"
OVERRIDE_SHORT="170pre2"
# OVERRIDE_SHORT="170pre2_140PU"
# OVERRIDE_SHORT="170pre1_MuonOMTFUpdate1"
# OVERRIDE_SHORT="170pre2_JetWord"
# OVERRIDE_SHORT="170pre2_JetWord_140PU"
# OVERRIDE_SHORT="MuonShowerwL1"
# OVERRIDE_SHORT="MuonShower"
# OVERRIDE_SHORT="RelValwL1"
OVERRIDE_VERSION="${VERSION}_${OVERRIDE_SHORT}"
# OVERRIDE_VERSION="${VERSION}" #_${OVERRIDE_SHORT}"
REVISION=$(date +%y%m%d)
MAX_JOBS=6

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    # Extract a meaningful identifier from the config path
    local filename=$(basename "$2")  # assumes config is 2nd argument
    local logname=${filename%.*}  # removes file extension
    echo Submitting $logname
    "$@" |& tee logs/${OVERRIDE_VERSION}_${REVISION}/${OVERRIDE_VERSION}_${logname}.log &
}

mkdir logs/${OVERRIDE_VERSION}_${REVISION}
run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger_VLoose.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger_Loose.yaml --version ${OVERRIDE_VERSION} 
run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger_Medium.yaml --version ${OVERRIDE_VERSION}
run_when_ready object_performance configs/$VERSION/object_performance/muon_trigger_Tight.yaml --version ${OVERRIDE_VERSION} 
