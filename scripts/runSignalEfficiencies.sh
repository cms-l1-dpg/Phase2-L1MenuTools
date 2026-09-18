# MENU=1p5
MENU=1
VERSION="V50nano_170pre3"
REVISION=$1
LOGDIR=${VERSION}_signalEff_$REVISION
SIGNALS="DYLL_M50 Hgg HHTo4B HHTo2B2Tau TT VBFHToTauTau VBFHToBB VBFHToInv"

mkdir logs/$LOGDIR
for signal in $SIGNALS; do
  { \time -v rate_table configs/V50nano/rate_table/step${MENU}_cfg.yml \
        --version $VERSION --signal $signal ; } \
        |& tee logs/$LOGDIR/${VERSION}_step${MENU}_${signal}_signalEff.log
done

   # { \time -v rate_table configs/V50nano/rate_table/step${MENU}_cfg.yml \
   #      --version $VERSION ; } \
   #      |& tee logs/$LOGDIR/${VERSION}_step${MENU}_minBias.log
