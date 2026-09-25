# MENU=1p5
MENU=1
# VERSION="V50nano_170pre3_140PU"
VERSION="V50nano_170pre3"
REVISION=$1
LOGDIR=${VERSION}_signalEff_$REVISION
SIGNALS="DYLL_M50 Hgg HHTo4B HHTo2B2Tau TT VBFHToTauTau VBFHToBB VBFHToInv"
# SIGNALS="DYLL_M50 Hgg TT VBFHToTauTau"
# SIGNALS="TT"

mkdir logs/$LOGDIR
for signal in $SIGNALS; do
  { \time -v rate_table configs/V50nano/rate_table/step${MENU}_cfg.yml \
        --version $VERSION --signal $signal ; } \
        |& tee logs/$LOGDIR/${VERSION}_step${MENU}_${signal}_signalEff.log
done

  # { MENU_TABLE_CHUNK=5000 \time -v rate_table configs/V50nano/rate_table/step${MENU}_cfg.yml \
  #       --version $VERSION --signal $signal ; } \
  #       |& tee logs/$LOGDIR/${VERSION}_step${MENU}_${signal}_chunk5k_signalEff.log
  # { MENU_TABLE_CHUNK=2000 \time -v rate_table configs/V50nano/rate_table/step${MENU}_cfg.yml \
  #       --version $VERSION --signal $signal ; } \
  #       |& tee logs/$LOGDIR/${VERSION}_step${MENU}_${signal}_chunk2k_signalEff.log

