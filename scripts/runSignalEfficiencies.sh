MENU=1p5
# MENU=1
VERSION="V50nano_170pre3"

SIGNALS="DYLL Hgg HHbbbb HHbbtautau TT VBFHToTauTau VBFHToBB VBFHToInv"

for signal in $SIGNALS; do
    rate_table configs/V50nano/rate_table/step${MENU}_${signal}_cfg.yml --version $VERSION | tee logs/${VERSION}_step${MENU}_signalEff.log
done
