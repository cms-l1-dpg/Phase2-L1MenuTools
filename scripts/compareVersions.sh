VOLD=$1
VNEW=$2
OUTDIR=${3:-"comparisons"}

MAX_JOBS=1
# run_when_ready() {
#     while [ $(jobs -p | wc -l) -ge $MAX_JOBS ]; do
#         sleep 3
#     done
#     # Extract a meaningful identifier from the config path
#     local filename=$(basename "$2")  # assumes config is 2nd argument
#     local logname=${filename%.*}  # removes file extension
#     echo Submitting $logname
#     "$@" |& tee complogs/${VNEW}vs${VOLD}/${VNEW}vs${VOLD}_${logname}.log &
# }

if [ -z "$VOLD" ] || [ -z "$VNEW" ]; then
    echo "Usage: $0 <oldVersion> <newVersion> [outdir]"
else
    echo $OUTDIR
    mkdir -p complogs/${VNEW}vs${VOLD}
    # run_when_ready source menu_tools/utils/format_diff.sh $VOLD $VNEW $OUTDIR
    # run_when_ready python menu_tools/utils/compare_json-wNano.py --v1 $VOLD --v0 $VNEW --output-dir $OUTDIR
    # run_when_ready python menu_tools/utils/compare_menus.py --vOld $VOLD --vNew $VNEW --output-dir $OUTDIR
    # run_when_ready python menu_tools/utils/compare_menus.py --vOld $VOLD --vNew $VNEW --menu v45_Step2Menu --output-dir $OUTDIR
    python menu_tools/utils/compare_menus.py --vOld $VOLD --vNew $VNEW --output-dir $OUTDIR |& tee complogs/${VNEW}vs${VOLD}/${VNEW}vs${VOLD}_step1.log 
    python menu_tools/utils/compare_menus.py --vOld $VOLD --vNew $VNEW --menu v45_Step2Menu --output-dir $OUTDIR  |& tee complogs/${VNEW}vs${VOLD}/${VNEW}vs${VOLD}_step2.log 
    python menu_tools/utils/compare_json-wNano.py --v1 $VOLD --v0 $VNEW --output-dir $OUTDIR  |& tee complogs/${VNEW}vs${VOLD}/${VNEW}vs${VOLD}_objects.log
    source menu_tools/utils/format_diff.sh $VOLD $VNEW $OUTDIR  |& tee complogs/${VNEW}vs${VOLD}/${VNEW}vs${VOLD}_diff.log 
fi

