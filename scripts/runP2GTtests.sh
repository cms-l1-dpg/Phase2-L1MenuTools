MAX_JOBS=4

run_when_ready() {
    while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
        sleep 3
    done
    # Extract a meaningful identifier from the config path
    local filename=$(basename "$2")  # assumes config is 2nd argument
    local logname=${filename%.*}  # removes file extension
    echo Submitting $logname
    "$@" & # |& tee complogs/${VNEW}vs${VOLD}/${VNEW}vs${VOLD}_${logname}.log &
}

S="--scalings V50nano_170pre6 --truncated"

# run_when_ready rate_table configs/V50nano/rate_table/step1_cfg.yml     --version V50nano_170pre7_P2GT_Update3          $S
# run_when_ready rate_table configs/V50nano/rate_table/step1and2_cfg.yml --version V50nano_170pre7_P2GTstep1and2_Update3 $S
run_when_ready rate_table configs/V50nano/rate_table/step1_P2GT_cfg.yml     --version V50nano_170               $S
run_when_ready rate_table configs/V50nano/rate_table/step1and2_P2GT_cfg.yml --version V50nano_170_P2GTstep1and2 $S
run_when_ready rate_table configs/V50nano/rate_table/step1p5_cfg.yml        --version V50nano_170_P2GTstep1p5   $S
run_when_ready rate_table configs/V50nano/rate_table/v0p0_cfg.yml           --version V50nano_170_P2GTv0p0      $S

wait

# run_when_ready p2gt_compare --version V50nano_170pre7_P2GT_Update3          --menu v45_Step1Menu     --p2gt step1_2024     $S
# run_when_ready p2gt_compare --version V50nano_170pre7_P2GTstep1and2_Update3 --menu v45_Step1and2Menu --p2gt step1and2_2026 $S
run_when_ready p2gt_compare --version V50nano_170               --menu v45_Step1Menu_P2GT      --p2gt step1_2024     $S
run_when_ready p2gt_compare --version V50nano_170_P2GTstep1and2 --menu v45_Step1and2Menu_P2GT --p2gt step1and2_2026 $S
run_when_ready p2gt_compare --version V50nano_170_P2GTstep1p5   --menu v45_Step1p5Menu        --p2gt step1p5_2026   $S
run_when_ready p2gt_compare --version V50nano_170_P2GTv0p0      --menu v45_V0p0Menu           --p2gt v0p0_2026      $S
