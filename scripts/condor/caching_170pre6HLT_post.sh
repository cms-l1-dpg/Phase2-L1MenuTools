#!/bin/bash
# Post-processing of the chunked V50nano_170pre6HLT caching for one sample (run from the
# checkout, after all chunk jobs of the sample succeeded):
#   merge_chunks.py -> <version>_<sample>_<object>.parquet (incl. hltPFPuppiHT, the HLT HT object)
#   make_hlt_sums.py -> hltPuppiJetSums (HT/MHT of hltAK4PuppiJet, pt > 30, |eta| < 2.4)
#   make_hlt_jets_corr.py -> hltAK4PuppiJetCorr, hltPuppiJetCorrSums (HLT JEC applied)
#   merge_arrays.py  -> L1EG (L1EGbarrel + L1EGendcap, pt > 5)
#   caching_170pre6HLT_post.sh <sample> <files per job used for the caching>
set -euo pipefail
SAMPLE="$1"; FPJ="$2"
CFG=configs/V50nano/cache_objects/caching_170pre6_HLT.yaml
VERSION=V50nano_170pre6HLT
python3 menu_tools/caching/merge_chunks.py "$CFG" --files-per-job "$FPJ" --samples "$SAMPLE"
python3 menu_tools/caching/make_hlt_sums.py --version "$VERSION" --sample "$SAMPLE"
python3 menu_tools/caching/make_hlt_jets_corr.py --version "$VERSION" --sample "$SAMPLE"
python3 menu_tools/caching/merge_arrays.py --version "$VERSION" --sample "$SAMPLE"
