"""HLT ParT tau candidates: the hltAK4PuppiJet inside the ParT acceptance, slimmed.

p2nano v2 stores the HLT ParT AK4 tagger (hltParticleTransformerDiscriminatorsJetTags)
for every hltAK4PuppiJet inside its acceptance (ParT_inputFilled: raw pT > 5 GeV,
|eta| < 2.1), in every event; outside it the scores are -10. The HLT ParT di-tau path
HLT_DoubleMediumPFPuppiParTTauh30_eta2p1 (filter
hltDoublePFJets30ParTTauhTagMediumWPL2DoubleTau, TauTagFilter) cuts on the UNcorrected
hltAK4PFPuppiJets: >= 2 jets with pT > 30 GeV, |eta| < 2.1 and TauvsAll > 0.11645 (no
pT correction, no matching to the L1 taus), after the L1 seed L1_pDoublePuppiTau52_52.

The full jet object is too large for the turn-on code on the big samples (it loads all
fields), so this writes, next to the input parquet,
    <version>_<sample>_hltAK4PuppiJetParT.parquet
with the jets having ParT_inputFilled == 1 and raw pT > --min-pt (default 10 GeV),
fields
    pt (raw, as the HLT path), eta, phi, ptCorr (= pt * jecFactor of the nano),
    TauvsAll, prob_{b,c,uds,g,taup,taum}, hadronFlavour, partonFlavour,
sorted by pt. Streams one parquet row group at a time.

Usage (after caching / merging hltAK4PuppiJet of a p2nano v2 cache):
    python3 menu_tools/caching/make_hlt_jets_part.py \
        --version V50nano_170pre6HLTv2 --sample HHTo2B2Tau
"""

import argparse
import os

import awkward as ak

from menu_tools.utils import constants

SRC = "hltAK4PuppiJet"
TARGET = "hltAK4PuppiJetParT"
FIELDS = {
    "pt": "pt",
    "eta": "eta",
    "phi": "phi",
    "TauvsAll": "ParT_TauvsAll",
    "prob_b": "ParT_prob_b",
    "prob_c": "ParT_prob_c",
    "prob_uds": "ParT_prob_uds",
    "prob_g": "ParT_prob_g",
    "prob_taup": "ParT_prob_taup",
    "prob_taum": "ParT_prob_taum",
    "hadronFlavour": "hadronFlavour",
    "partonFlavour": "partonFlavour",
}


def slim(jets: ak.Array, min_pt: float) -> ak.Array:
    sel = (jets[f"{SRC}_ParT_inputFilled"] == 1) & (jets[f"{SRC}_pt"] > min_pt)
    j = jets[sel]
    out = {f"{TARGET}_{k}": j[f"{SRC}_{v}"] for k, v in FIELDS.items()}
    out[f"{TARGET}_ptCorr"] = j[f"{SRC}_pt"] * j[f"{SRC}_jecFactor"]
    arr = ak.zip(out)
    return arr[ak.argsort(arr[f"{TARGET}_pt"], axis=-1, ascending=False)]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", required=True)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--min-pt", type=float, default=10.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    pattern = os.path.join(
        constants.CACHE_DIR, args.version, f"{args.version}_{args.sample}_%s.parquet"
    )
    target = pattern % TARGET
    if os.path.exists(target) and not args.overwrite:
        print(f"{target} exists, skipping")
        return
    cols = [f"{SRC}_{v}" for v in FIELDS.values()] + [
        f"{SRC}_ParT_inputFilled",
        f"{SRC}_jecFactor",
    ]
    n_rg = ak.metadata_from_parquet(pattern % SRC)["num_row_groups"]
    n_ev = 0

    def _iter():
        nonlocal n_ev
        for rg in range(n_rg):
            arr = slim(
                ak.from_parquet(pattern % SRC, columns=cols, row_groups=[rg]),
                args.min_pt,
            )
            n_ev += len(arr)
            yield arr

    ak.to_parquet_row_groups(_iter(), target + ".tmp")
    os.replace(target + ".tmp", target)
    print(f"Wrote {target}: {n_ev} events")


if __name__ == "__main__":
    main()
