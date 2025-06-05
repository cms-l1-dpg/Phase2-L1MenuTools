MAX_JOBS=6

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    "$@" &
}


# python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_jetSC8
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_jetSC8
# python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_l1Track
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_l1Track
# python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_firstTrain
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_firstTrain
# python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_jetSC4NG
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_jetSC4NG

# Bisecting
# python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_142pre4
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre4 --v0 V45nano_150pre3
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_150pre3 --v0 V45nano

# Second train PR
# python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_L1EG
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_L1EG


# Bisecting
# python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_142pre2
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre2 --v0 V45nano_142pre3
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre3 --v0 V45nano_142pre4
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre4 --v0 V45nano_150pre1
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_150pre1 --v0 V45nano_150pre2
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_150pre2 --v0 V45nano_150pre3
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_150pre3 --v0 V45nano_151pre1
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre1 --v0 V45nano
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_nanoSC4NG
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_nanoSC4NG --v0 V45nano_L1EG

# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_151pre3


# # Muon RPC Geometry change
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_150pre2 --v0 V45nano_150pre2_RPC
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_150pre2_RPC --v0 V45nano_150pre3

# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_151pre3_D110Fix # hacked 110 fix vs 151pre3
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3_D110Fix --v0 V45nano_151X_D121 # official 110 fix vs hacked one

# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_151X_D110 # verify that D110 is the same
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151X_D110 --v0 V45nano_151X_D116 # look at intermediate version
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151X_D116 --v0 V45nano_151X_D121 # look at fixed version
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151X_D110 --v0 V45nano_151X_D121 # look at fixed version

# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_151X_D121 # look at fixed version directly vs official release



# L1EG mega commit
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano --v0 V45nano_noL1EG
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_noL1EG --v0 V45nano_L1EGupdate1
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_noL1EG --v0 V45nano_L1EG
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EG --v0 V45nano_L1EGupdate1
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate1 --v0 V45nano_L1EGupdate2 # compare PR with previous PR version (but 151X vs 151pre3)
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate1 --v0 V45nano_L1EGupdate1p5 # rebase of update1 on 151pre3
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate1p5 --v0 V45nano_L1EGupdate2 # better comparison of update1 vs update2
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate2 --v0 V45nano_L1EGupdate3 # compare new IDs with identical CMSSW
run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_L1EGupdate3 # compare new IDs with CMSSW 151pre3

# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_L1EGupdate2 # compare commit with version it's based on
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_L1EGupdate1p5 # compare commit with version it's based on

# # L1Track differences
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre3 --v0 V45nano_142pre3_L1Track
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre3_L1Track --v0 V45nano_142pre4

