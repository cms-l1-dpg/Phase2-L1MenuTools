MENU=1p5
# MENU=1
VERSION="V50nano_170pre3"

SIGNALS="DYLL_M50 Hgg HHTo4B HHTo2B2Tau TT VBFHToTauTau VBFHToBB VBFHToInv"

for signal in $SIGNALS; do
    rate_table configs/V50nano/rate_table/step${MENU}_cfg.yml \
        --version $VERSION --signal $signal \
        | tee logs/${VERSION}_step${MENU}_${signal}_signalEff.log
done
