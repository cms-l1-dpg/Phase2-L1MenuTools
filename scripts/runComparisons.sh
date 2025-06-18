MAX_JOBS=3

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    "$@" &
}

# E2ENNVtx Comparisons
# source scripts/compareVersions.sh V49nano_151pre3 V49nano_151pre3_E2ENNVtx  "comparisons/e2eNNVtx"
# source scripts/compareVersions.sh V49nano_151pre3 V49nano_151pre3_E2ENNVtxOff "comparisons/e2eNNVtx"
# source scripts/compareVersions.sh V49nano_151pre3_E2ENNVtxOff V49nano_151pre3_E2ENNVtx "comparisons/e2eNNVtx"
# source scripts/compareVersions.sh V49nano_AR24 V49nano_142pre1 "comparisons/ar25"
# source scripts/compareVersions.sh V49nano_AR24 V49nano_151pre3 "comparisons/ar25"
# source scripts/compareVersions.sh V49nano_151pre3 V49nano_AR25 "comparisons/ar25"
# source scripts/compareVersions.sh V49nano_142pre1 V49nano_151pre3 "comparisons/ar25"

# run_when_ready source scripts/compareVersions.sh V49nano_151pre3 V49nano_L1EGupdate3 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V49nano_L1EGupdate2 V49nano_L1EGupdate3 "comparisons/thirdTrain"

# run_when_ready source scripts/compareVersions.sh V49nano_AR25_VtxFindOff V49nano_AR25 "comparisons/ar25"
# run_when_ready source scripts/compareVersions.sh V48_AR25_VtxFindOff V49nano_AR25 "comparisons/ar25"
# run_when_ready source scripts/compareVersions.sh V49nano_AR24 V49nano_AR25 "comparisons/ar25"
# run_when_ready source scripts/compareVersions.sh V49nano_151pre3 V49nano_AR25 "comparisons/ar25"
# run_when_ready source scripts/compareVersions.sh V49nano_151pre3 V49nano_AR25_VtxFindOff "comparisons/ar25"

# run_when_ready source scripts/compareVersions.sh V49nano_AR24 V49nano_151pre3 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V38nano_DT12x V49nano_AR24 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V49nano_AR24 V49nano_L1EGupdate2 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V49nano_AR24 V49nano_142pre1 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V44nano V49nano_142pre1 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V49nano_142pre1 V49nano_151pre3 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V49nano_142pre1 V49nano_151pre1 "comparisons/thirdTrain"
# run_when_ready source scripts/compareVersions.sh V49nano_151pre1 V49nano_151pre3 "comparisons/thirdTrain"

# python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V45nano_151pre3 --output-dir "comparisons/thirdTrain" --menu-vOld v44_Step1Menu |& tee complogs/V45nano_151pre3vsV44nano_step1.log
# python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V45nano_151pre3 --output-dir "comparisons/thirdTrain" --menu-vOld v44_Step2Menu --menu-vNew v45_Step2Menu |& tee complogs/V45nano_151pre3vsV44nano_step2.log
# python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V49nano_151pre3 --output-dir "comparisons/thirdTrain" --menu-vOld v44_Step1Menu |& tee complogs/V49nano_151pre3vsV44nano_step1.log
# python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V49nano_151pre3 --output-dir "comparisons/thirdTrain" --menu-vOld v44_Step2Menu --menu-vNew v45_Step2Menu |& tee complogs/V49nano_151pre3vsV44nano_step2.log
# python menu_tools/utils/compare_menus.py --vOld V45nano_151pre3 --vNew V49nano_151pre3 --output-dir "comparisons/thirdTrain" |& tee complogs/V49nano_151pre3vsV45nano_151pre3_step1.log
# python menu_tools/utils/compare_menus.py --vOld V45nano_151pre3 --vNew V49nano_151pre3 --output-dir "comparisons/thirdTrain" --menu v45_Step2Menu |& tee complogs/V49nano_151pre3vsV45nano_151pre3_step2.log
# python menu_tools/utils/compare_menus.py --vOld V49nano_151pre3 --vNew V49nano_L1EGupdate2 --output-dir "comparisons/thirdTrain" |& tee complogs/V49nano_L1EGupdate2vsV49nano_151pre3_step1.log
# python menu_tools/utils/compare_menus.py --vOld V49nano_151pre3 --vNew V49nano_L1EGupdate2 --output-dir "comparisons/thirdTrain" --menu v45_Step2Menu |& tee complogs/V49nano_L1EGupdate2vsV49nano_151pre3_step2.log

# python menu_tools/utils/compare_menus.py --vOld V38nano_DT12x --vNew V49nano_151pre3 --menu-vOld menu_Step1 --output-dir "comparisons/thirdTrain"
# python menu_tools/utils/compare_menus.py --vOld V38nano_DT12x --vNew V49nano_151pre3 --menu-vOld menu_Step2 --menu-vNew v45_Step2Menu --output-dir "comparisons/thirdTrain"

# python menu_tools/utils/compare_menus.py --vOld V38nano_DT12x --vNew V49nano_AR24 --menu-vOld menu_Step1 --output-dir "comparisons/thirdTrain"
# python menu_tools/utils/compare_menus.py --vOld V49nano_AR24 --vNew V49nano_151pre3 --output-dir "comparisons/thirdTrain"
# python menu_tools/utils/compare_menus.py --vOld V49nano_AR24 --vNew V49nano_151pre3 --menu v45_Step2Menu --output-dir "comparisons/thirdTrain"
# python menu_tools/utils/compare_menus.py --vOld V49nano_AR24 --vNew V49nano_151pre3 --menu v45_Step1and2Menu --output-dir "comparisons/thirdTrain"
# python menu_tools/utils/compare_menus.py --vOld V38nano_DT12x --vNew V49nano_AR24 --menu-vOld menu_Step2 --menu-vNew v45_Step2Menu --output-dir "comparisons/thirdTrain"

# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V49nano_151pre3 --v0 V49nano_L1EGupdate2 --output-dir "comparisons/thirdTrain"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V49nano_151pre3 --v0 V49nano_L1EGupdate2 --output-dir "comparisons/thirdTrain"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_151pre3 --output-dir "comparisons/thirdTrain"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V45nano_151pre3 --output-dir "comparisons/thirdTrain"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V49nano_151pre3 --output-dir "comparisons/thirdTrain"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V44nano --v0 V49nano_151pre3 --output-dir "comparisons/thirdTrain"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V49nano_151pre3 --output-dir "comparisons/thirdTrain"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V49nano_151pre3 --output-dir "comparisons/thirdTrain"

# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V49nano_AR24 --v0 V49nano_AR25 --output-dir "comparisons/ar25"
run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V49nano_AR25_VtxFindOff --v0 V49nano_AR25 --output-dir "comparisons/ar25"



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

# run_when_ready python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V49nano_142pre1 --output-dir "comparisons/thirdTrain"  --menu-vOld v44_Step1Menu

# Bisecting
# python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V45nano_142pre2 --output-dir "comparisons/bisecting" --menu-vOld v44_Step1Menu
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V45nano_142pre2 --output-dir "comparisons/bisecting"  --menu-vOld v44_Step1Menu
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_142pre2 --vNew V45nano_142pre3 --output-dir "comparisons/bisecting"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_142pre3 --vNew V45nano_142pre4 --output-dir "comparisons/bisecting"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_142pre4 --vNew V45nano_150pre1 --output-dir "comparisons/bisecting"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_150pre1 --vNew V45nano_150pre2 --output-dir "comparisons/bisecting"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_150pre2 --vNew V45nano_150pre3 --output-dir "comparisons/bisecting"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_150pre3 --vNew V45nano_151pre1 --output-dir "comparisons/bisecting"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_151pre1 --vNew V45nano --output-dir "comparisons/bisecting"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano --vNew V45nano_151pre3 --output-dir "comparisons/bisecting"

# # Fixed IDs - plots
# # run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V46nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V47nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V46nano_151pre3 --v0 V47nano_151pre3 --output-dir "comparisons/correctedIDs"
# # python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate2 --v0 V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate3 --v0 V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate2 --v0 V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate3 --v0 V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V46nano_L1EGupdate2 --v0 V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V46nano_151pre3 --v0 V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V47nano_151pre3 --v0 V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"

# # Fixed IDs - menus
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_151pre3 --vNew V46nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_151pre3 --vNew V47nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V46nano_151pre3 --vNew V47nano_151pre3 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate2 --vNew V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate3 --vNew V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate2 --vNew V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate3 --vNew V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V46nano_L1EGupdate2 --vNew V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V46nano_151pre3 --vNew V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V47nano_151pre3 --vNew V47nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"

# # Fixed IDs - plots
# # run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V46nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V48nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V46nano_151pre3 --v0 V48nano_151pre3 --output-dir "comparisons/correctedIDs"
# # python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate2 --v0 V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate3 --v0 V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate2 --v0 V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_L1EGupdate3 --v0 V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V46nano_L1EGupdate2 --v0 V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V46nano_151pre3 --v0 V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V48nano_151pre3 --v0 V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"

# # Fixed IDs - menus
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_151pre3 --vNew V46nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_151pre3 --vNew V48nano_151pre3 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V46nano_151pre3 --vNew V48nano_151pre3 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate2 --vNew V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate3 --vNew V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate2 --vNew V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V45nano_L1EGupdate3 --vNew V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V46nano_L1EGupdate2 --vNew V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# # run_when_ready python menu_tools/utils/compare_menus.py --vOld V46nano_151pre3 --vNew V46nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V48nano_151pre3 --vNew V48nano_L1EGupdate2 --output-dir "comparisons/correctedIDs"



# # Reproducing V44nano - menus
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V44nano_Oct24 --vNew V44nano --menu v44_Step1Menu --output-dir "comparisons/validationOct24"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V38nano_Oct24 --vNew V38nano --menu menu_Step1 --output-dir "comparisons/validationOct24"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V38nano_DT12x_Oct24 --vNew V38nano_DT12x --menu menu_Step1 --output-dir "comparisons/validationOct24"

# # Reproducing V44nano - plots
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V44nano_Oct24 --v0 V44nano --output-dir "comparisons/validationOct24"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V38nano_Oct24 --v0 V38nano --output-dir "comparisons/validationOct24"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V38nano_DT12x_Oct24 --v0 V49nano_AR24 --output-dir "comparisons/ar25"
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V38nano_DT12x_Oct24 --v0 V49nano_AR25 --output-dir "comparisons/ar25"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V38nano_DT12x_Oct24 --vNew V49nano_AR24 --menu-vOld menu_Step1 --output-dir "comparisons/ar25"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V38nano_DT12x_Oct24 --vNew V49nano_AR25 --menu-vOld menu_Step1 --output-dir "comparisons/ar25"

# Reproducing V44nano
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V44nano --vNew V44nano --menu-vOld v44_Step1Menu_gtneq --menu-vNew v44_Step1Menu --output-dir "comparisons/validationOct24"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V44nano_Oct24 --vNew V44nano --menu-vOld v44_Step1Menu --menu-vNew v44_Step1Menu_gtneq --output-dir "comparisons/validationOct24"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V44nano_Oct24 --vNew V44nano --menu-vOld v44_Step1Menu --menu-vNew v44_Step1Menu_gtneq_oldScalings --output-dir "comparisons/validationOct24"
# run_when_ready python menu_tools/utils/compare_menus.py --vOld V44nano_Oct24 --vNew V44nano --menu-vOld v44_Step1Menu --menu-vNew v44_Step1Menu_oldScalings --output-dir "comparisons/validationOct24"



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
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_L1EGupdate3 # compare new IDs with CMSSW 151pre3

# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_L1EGupdate2 # compare commit with version it's based on
# run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 V45nano_151pre3 --v0 V45nano_L1EGupdate1p5 # compare commit with version it's based on

# # L1Track differences
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre3 --v0 V45nano_142pre3_L1Track
# python menu_tools/utils/compare_json-wNano.py --v1 V45nano_142pre3_L1Track --v0 V45nano_142pre4

